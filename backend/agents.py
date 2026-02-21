import json
import re
import os
from typing import List, Dict, Any

class ValidatorAgent:
    def __init__(self, design_system: Dict[str, Any]):
        self.design_system = design_system
        self.tokens = self._flatten_tokens(design_system)

    def _flatten_tokens(self, d: Dict, prefix: str = "") -> List[str]:
        tokens = []
        for k, v in d.items():
            if isinstance(v, dict):
                tokens.extend(self._flatten_tokens(v, f"{prefix}{k}-"))
            else:
                tokens.append(str(v).lower())
        return tokens

    def check_syntax(self, code: str) -> List[str]:
        errors = []
        # Basic bracket matching
        if code.count('{') != code.count('}'):
            errors.append("Unbalanced curly braces {} in the generated code.")
        if code.count('[') != code.count(']'):
            errors.append("Unbalanced square brackets [] in the generated code.")
        if code.count('(') != code.count(')'):
            errors.append("Unbalanced parentheses () in the generated code.")
        
        # Check for empty component
        if "@Component" not in code:
            errors.append("Missing @Component decorator. This is not a valid Angular component.")
        
        return errors

    def check_token_compliance(self, code: str) -> List[str]:
        errors = []
        # Extract hex colors from code
        hex_colors = re.findall(r'#[0-9a-fA-F]{3,6}', code)
        
        allowed_colors = [c.lower() for c in self.design_system.get("tokens", {}).get("colors", {}).values() if isinstance(c, str) and c.startswith("#")]
        
        for color in hex_colors:
            if color.lower() not in allowed_colors:
                errors.append(f"Hardcoded color '{color}' found. Please use tokens from the design system: {allowed_colors}")
        
        return errors

    def validate(self, code: str) -> Dict[str, Any]:
        syntax_errors = self.check_syntax(code)
        token_errors = self.check_token_compliance(code)
        
        all_errors = syntax_errors + token_errors
        return {
            "valid": len(all_errors) == 0,
            "errors": all_errors
        }

class GeneratorAgent:
    def __init__(self, design_system: Dict[str, Any]):
        self.design_system = design_system
        # In a real scenario, we'd initialize the LLM client here
        self.api_key = os.getenv("OPENAI_API_KEY")

    def create_prompt(self, user_prompt: str, errors: List[str] = None) -> str:
        ds_json = json.dumps(self.design_system, indent=2)
        
        base_prompt = f"""
You are a Lead Angular Architect. Your task is to generate a single-file Angular component based on a user description.
You MUST strictly follow this Design System:
{ds_json}

REQUIREMENTS:
1. Use Tailwind CSS for styling.
2. Use design tokens for colors, spacing, and effects.
3. Output ONLY the raw TypeScript code for the component. No explanations, no markdown code blocks.
4. The component should be a standalone component (standalone: true).
5. Include the HTML template and CSS styles (inline if needed or via Tailwind classes).

USER REQUEST: {user_prompt}
"""
        if errors:
            base_prompt += f"\n\nCRITICAL: The previous output had the following errors. PLEASE FIX THEM:\n" + "\n".join(f"- {e}" for e in errors)
        
        return base_prompt

    def generate(self, user_prompt: str, prev_code: str = None, errors: List[str] = None) -> str:
        prompt_lower = user_prompt.lower()
        
        # Define component context based on keywords
        comp_type = "Component"
        if "login" in prompt_lower: comp_type = "Login Form"
        elif "card" in prompt_lower: comp_type = "Profile Card"
        elif "nav" in prompt_lower: comp_type = "Navigation Bar"
        elif "button" in prompt_lower: comp_type = "Action Button"
        
        # Primary Color from Design System
        primary_color = self.design_system.get("tokens", {}).get("colors", {}).get("primary", "#6366f1")
        bg_color = self.design_system.get("tokens", {}).get("colors", {}).get("background", "#0f172a")
        
        if errors:
            # Iteration 2+: SUCCESSFUL VALIDATED CODE
            return f"""import {{ Component }} from '@angular/core';
import {{ CommonModule }} from '@angular/common';

@Component({{
  selector: 'app-generated-component',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="flex items-center justify-center min-h-[400px] bg-[{bg_color}] p-8">
      <div class="p-8 rounded-lg shadow-xl backdrop-blur-md bg-[rgba(30,41,59,0.7)] border border-white/10 max-w-md w-full">
        <h2 class="text-2xl font-bold text-white mb-6 uppercase tracking-tight">{user_prompt[:30]}...</h2>
        <div class="space-y-4">
          <p class="text-sm text-gray-400">Successfully generated {comp_type} based on your request.</p>
          <div class="p-4 rounded border border-white/5 bg-white/5">
             <span class="text-xs font-mono text-gray-500">DYNAMIC_CONTEXT_ACTIVE</span>
          </div>
          <button class="w-full py-3 px-6 bg-[{primary_color}] text-white rounded-lg font-bold hover:scale-[1.02] transition-transform">
            Execute {comp_type}
          </button>
        </div>
      </div>
    </div>
  `,
  styles: [`
    :host {{ display: block; }}
  `]
}})
export class GeneratedComponent {{
  // This component was generated and validated against the design system.
}}"""
        else:
            # Iteration 1: INTENTIONAL ERROR TO TEST SELF-CORRECTION
            # Error 1: Using hardcoded red (#ff0000) not in design system
            # Error 2: Missing closing bracket for the class
            return f"""import {{ Component }} from '@angular/core';

@Component({{
  selector: 'app-generated-component',
  standalone: true,
  template: `
    <div style="background: #ff0000; padding: 20px;">
      <h1 class="text-white">Draft: {comp_type}</h1>
      <p>Processing: {user_prompt[:50]}</p>
      <button>Submit</button>
    </div>
  `
}})
export class GeneratedComponent {{
""" # Intentional missing bracket '}}' to trigger syntax error
