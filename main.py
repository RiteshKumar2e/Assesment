import argparse
import sys
import os
from src.generator import GuidedArchitect

def mock_llm_callback(prompt):
    """
    Simulated LLM response. 
    First call returns invalid code to demonstrate self-correction.
    """
    if "ERROR IN PREVIOUS OUTPUT" not in prompt:
        # Initial attempt - Intentional error: Using a wrong color #FF0000
        return """
```typescript
import { Component } from '@angular/core';

@Component({
  selector: 'app-login-card',
  standalone: true,
  template: `
    <div class="p-8 rounded-lg shadow-xl" style="background: #FF0000">
      <h2 class="text-2xl font-bold">Login</h2>
      <input type="text" class="border p-2 rounded" placeholder="Username">
    </div>
  `
})
export class LoginCardComponent {}
```
"""
    else:
        # Corrected attempt - Using token color #6366f1
        return """
```typescript
import { Component } from '@angular/core';

@Component({
  selector: 'app-login-card',
  standalone: true,
  template: `
    <div class="p-8 rounded-[12px] shadow-xl bg-white/10 backdrop-blur-md border border-white/20" style="color: #6366f1">
      <h2 class="text-2xl font-bold mb-4">Login</h2>
      <div class="space-y-4">
        <input type="text" class="w-full p-2 rounded-[8px] border border-gray-200" placeholder="Email">
        <button class="w-full py-2 bg-[#6366f1] text-white rounded-[8px] hover:opacity-90 transition">
          Sign In
        </button>
      </div>
    </div>
  `
})
export class LoginCardComponent {}
```
"""

def main():
    parser = argparse.ArgumentParser(description="Guided Component Architect")
    parser.add_argument("--prompt", type=str, help="Description of the component to build")
    args = parser.parse_args()

    if not args.prompt:
        print("Usage: python main.py --prompt \"description\"")
        sys.exit(1)

    print("="*50)
    print("      GUIDED COMPONENT ARCHITECT v1.0")
    print("="*50)

    # Ensure we are in the right directory if running from elsewhere
    tokens_path = os.path.join(os.path.dirname(__file__), 'design-tokens.json')
    
    architect = GuidedArchitect(tokens_path)
    
    # In a real app, you'd pass an actual LLM caller here.
    # We use our mock to demonstrate the self-correction loop.
    final_code = architect.run_pipeline(args.prompt, mock_llm_callback)

    print("\n" + "="*50)
    print("      FINAL ARCHITECTED COMPONENT")
    print("="*50 + "\n")
    print(final_code)
    
    # Save output
    output_dir = "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    with open(os.path.join(output_dir, "generated-component.ts"), "w") as f:
        f.write(final_code)
        
    print(f"\n[✔] Component saved to {output_dir}/generated-component.ts")

if __name__ == "__main__":
    main()
