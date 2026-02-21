import argparse
import sys
import os
import re
from src.generator import GuidedArchitect

def mock_llm_callback(messages):
    """
    Smarter mock that simulates a conversation for multi-turn editing.
    """
    last_user_msg = messages[-1]["content"]
    
    # Check if this is a correction from the validator
    if "ERROR IN PREVIOUS OUTPUT" in last_user_msg:
        return "```typescript\n@Component({ selector: 'app-fixed', template: '<div style=\"color: #6366f1\">Fixed Component</div>' })\nexport class FixedComponent {}\n```"

    # Multi-turn logic
    if "rounded" in last_user_msg.lower():
        return """
```typescript
import { Component } from '@angular/core';

@Component({
  selector: 'app-login-card',
  standalone: true,
  template: `
    <div class="p-8 rounded-[32px] bg-white border border-[#e4e4e7] shadow-xl">
      <h2 class="text-[24px] font-bold text-[#09090b] mb-4">Rounded Version</h2>
      <button class="w-full py-3 bg-[#6366f1] text-[#ffffff] rounded-full font-medium transition-all">
        Fully Rounded Button
      </button>
    </div>
  `
})
export class LoginCardComponent {}
```
"""
    
    if "login" in last_user_msg.lower():
        return """
```typescript
import { Component } from '@angular/core';

@Component({
  selector: 'app-login-card',
  standalone: true,
  template: `
    <div class="p-8 rounded-[12px] bg-white border border-[#e4e4e7] shadow-sm">
      <h2 class="text-[24px] font-bold text-[#09090b] mb-4">Welcome Back</h2>
      <div class="space-y-4">
        <input type="email" placeholder="Email" class="w-full p-3 rounded-[8px] bg-[#f4f4f5] border-none text-[#18181b]">
        <button class="w-full py-3 bg-[#6366f1] text-[#ffffff] rounded-[8px] font-medium transition-all hover:brightness-110">
          Continue
        </button>
      </div>
    </div>
  `
})
export class LoginCardComponent {}
```
"""
    
    return "```typescript\n@Component({ selector: 'app-generic', template: '<div>Dynamic Component</div>' })\nexport class GenericComponent {}\n```"

def generate_preview(code):
    """Generates a static HTML preview using Tailwind CDN."""
    # Extract template content
    template_match = re.search(r'template: `(.*?)`', code, re.DOTALL)
    if not template_match:
        # Fallback if it's not a backtick template
        template_match = re.search(r"template: '(.*?)'", code, re.DOTALL)
    
    html_content = template_match.group(1) if template_match else "<p>Preview not available for this component type.</p>"
    
    preview_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Component Preview</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body {{ font-family: 'Inter', sans-serif; background-color: #f9fafb; }}
    </style>
</head>
<body class="flex items-center justify-center min-h-screen p-10">
    <div id="app">
        {html_content}
    </div>
</body>
</html>
    """
    
    with open("preview.html", "w") as f:
        f.write(preview_html)
    print("\n[预览] Preview generated: preview.html")

def save_output(code, format="ts"):
    output_dir = "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    filename = "generated-component.ts"
    if "export class " in code:
        class_name = code.split("export class ")[1].split(" ")[0].strip("{} \n")
        filename = f"{class_name.lower()}.{format}"
    
    path = os.path.join(output_dir, filename)
    with open(path, "w") as f:
        f.write(code)
    print(f"[✔] Component saved to {path}")

def main():
    parser = argparse.ArgumentParser(description="Guided Component Architect v2.0")
    parser.add_argument("--prompt", type=str, help="Description of the component to build")
    parser.add_argument("--interactive", action="store_true", help="Start an interactive multi-turn session")
    parser.add_argument("--format", type=str, default="ts", choices=["ts", "tsx"], help="Output file format")
    args = parser.parse_args()

    print("="*50)
    print("      GUIDED COMPONENT ARCHITECT v2.0")
    print("="*50)

    tokens_path = os.path.join(os.path.dirname(__file__), 'design-tokens.json')
    architect = GuidedArchitect(tokens_path)

    if args.interactive:
        print("[*] Interactive mode. Type 'exit' to quit.")
        while True:
            user_input = input("\n[Prompt] > ")
            if user_input.lower() in ['exit', 'quit']:
                break
            
            final_code = architect.run_pipeline(user_input, mock_llm_callback)
            print("\n--- GENERATED CODE ---\n")
            print(final_code)
            
            save_output(final_code, args.format)
            generate_preview(final_code)
    else:
        if not args.prompt:
            print("Usage: python main.py --prompt \"description\" or --interactive")
            sys.exit(1)
        
        final_code = architect.run_pipeline(args.prompt, mock_llm_callback)
        print("\n--- GENERATED CODE ---\n")
        print(final_code)
        
        save_output(final_code, args.format)
        generate_preview(final_code)

if __name__ == "__main__":
    main()
