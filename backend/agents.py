import json
import re
import os
import httpx
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
        self.api_key = os.getenv("GROQ_API_KEY")
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"

    def create_prompt(self, user_prompt: str, errors: List[str] = None, prev_code: str = None) -> Dict[str, str]:
        primary = self.design_system.get('tokens', {}).get('colors', {}).get('primary', '#6366f1')
        bg = self.design_system.get('tokens', {}).get('colors', {}).get('background', '#0f172a')
        font = self.design_system.get('tokens', {}).get('typography', {}).get('fontFamily', 'Inter, sans-serif')
        
        system_prompt = f"""You are a senior Angular architect. Generate a single-file Angular standalone component.
STRICT DESIGN SYSTEM RULES:
- Primary Color: {primary}
- Background: {bg}
- Font: {font}
- Use Tailwind CSS for all styling.
- Component MUST be 'standalone: true'.
- Output ONLY raw code. No markdown, no explanations.
"""
        if errors:
            user_message = f"""FIX THIS COMPONENT. 
PREVIOUS CODE:
{prev_code}

VALIDATION ERRORS:
{chr(10).join(errors)}

User's original intent: {user_prompt}
Fix the errors and maintain the design system."""
        else:
            user_message = f"Build an Angular component for: {user_prompt}. Ensure it looks premium and uses {primary} as the highlight color."

        return {"system": system_prompt, "user": user_message}

    def _strip_conversational_text(self, text: str) -> str:
        text = re.sub(r'```[a-z]*\n', '', text)
        text = text.replace('```', '')
        return text.strip()

    async def generate(self, user_prompt: str, prev_code: str = None, errors: List[str] = None) -> str:
        if not self.api_key:
            return "// ERROR: GROQ_API_KEY not found in .env"

        prompts = self.create_prompt(user_prompt, errors, prev_code)
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.api_url,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": "llama-3.3-70b-versatile",
                        "messages": [
                            {"role": "system", "content": prompts["system"]},
                            {"role": "user", "content": prompts["user"]}
                        ],
                        "temperature": 0.2
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                raw_output = data["choices"][0]["message"]["content"]
                return self._strip_conversational_text(raw_output)
            except Exception as e:
                print(f"GROQ API Error: {str(e)}")
                return f"// API Error: Unable to reach Groq. Feature downgraded to simulation mode."
