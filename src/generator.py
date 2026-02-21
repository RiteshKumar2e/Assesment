import json
import os
import sys
import re
try:
    from .validator import CodeValidator
except ImportError:
    from validator import CodeValidator

class GuidedArchitect:
    def __init__(self, tokens_path):
        self.tokens_path = tokens_path
        with open(tokens_path, 'r') as f:
            self.tokens = json.load(f)
        self.validator = CodeValidator(tokens_path)

    def system_prompt(self):
        return f"""
You are a Senior Angular Developer. Your task is to generate a standalone Angular component based on a user description.
STRICT RULES:
1. ONLY output raw code. No conversational filler.
2. Use Tailwind CSS for styling.
3. You MUST use the following design tokens for ALL colors and styles. Do not use random hex codes.
Tokens: {json.dumps(self.tokens, indent=2)}

Output format:
```typescript
// component-name.component.ts
... content ...
```
"""

    def generate_component(self, user_description, retry_count=2):
        print(f"[*] Starting generation for: {user_description}")
        
        # In a real scenario, this would call OpenAI/Anthropic API
        # Here we define the prompt that would be sent
        full_prompt = self.system_prompt() + f"\nUser Request: {user_description}"
        
        # Simulating the LLM call for the purpose of this architecture demo
        # For the final output, I (the agent) will provide the code
        print("[!] In a production environment, this would call the LLM API.")
        
        # Simulation of the loop:
        # 1. Get code from LLM
        # 2. Validate
        # 3. If fail, re-prompt with errors
        
        return full_prompt

    def run_pipeline(self, user_prompt, llm_callback):
        """
        llm_callback: a function that takes a prompt and returns LLM output string
        """
        current_prompt = self.system_prompt() + f"\nUser Request: {user_prompt}"
        
        for attempt in range(3):
            print(f"\n[Attempt {attempt + 1}] Generating code...")
            generated_code = llm_callback(current_prompt)
            
            # Extract code from markdown if present
            code_match = re.search(r'```typescript\n(.*?)```', generated_code, re.DOTALL)
            if code_match:
                code_content = code_match.group(1)
            else:
                code_content = generated_code

            print("[*] Validating code...")
            is_valid, message = self.validator.full_validation(code_content)
            
            if is_valid:
                print("[+] Validation passed!")
                return code_content
            else:
                print(f"[-] Validation failed: {message}")
                print("[*] Preparing self-correction prompt...")
                current_prompt += f"\n\nERROR IN PREVIOUS OUTPUT:\n{message}\nPlease fix the errors and provide the corrected code."
                
        print("[!] Max retries reached. Returning last generated code.")
        return code_content

if __name__ == "__main__":
    architect = GuidedArchitect('design-tokens.json')
    print(architect.system_prompt())
