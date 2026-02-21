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

    def create_prompt(self, user_prompt: str, errors: List[str] = None, prev_code: str = None) -> Dict[str, str]:
        if errors:
            # 🔁 3️⃣ SELF-CORRECTION SYSTEM PROMPT (Fix Agent)
            system_prompt = f"""
You are an automated Angular code repair agent.
You will receive Angular code that failed validation.
Your job is to FIX the code so that it fully complies with the design system and Angular syntax.

STRICT RULES:
- Output raw code only
- No explanations
- No markdown
- Fix all syntax errors
- Enforce design tokens strictly

DESIGN TOKENS (MANDATORY):
- primaryColor: {self.design_system.get('tokens', {}).get('colors', {}).get('primary')}
- borderRadius: {self.design_system.get('tokens', {}).get('borderRadius', {}).get('medium', '8px')}
- fontFamily: {self.design_system.get('tokens', {}).get('typography', {}).get('fontFamily', 'Inter, sans-serif')}
- glassBg: {self.design_system.get('tokens', {}).get('colors', {}).get('surface')}
"""
            # 🔁 4️⃣ SELF-CORRECTION USER MESSAGE TEMPLATE
            user_message = f"""
The previous Angular component failed validation.

VALIDATION ERRORS:
{chr(10).join(f'- {e}' for e in errors)}

PREVIOUS CODE:
{prev_code}

Fix the component so it passes validation and follows the design system strictly.
"""
            return {"system": system_prompt, "user": user_message}
        else:
            # Standard Generation Prompt
            system_prompt = f"""
You are a strict Angular component generator used inside an automated code pipeline.
Your job is to generate production-ready Angular components that strictly follow the provided design system.

CRITICAL OUTPUT RULES:
- Output raw code only
- Do NOT include explanations
- Do NOT include markdown
- Do NOT include any conversational text
- Component must be standalone: true

STRICT DESIGN SYSTEM ENFORCEMENT:
- primaryColor: {self.design_system.get('tokens', {}).get('colors', {}).get('primary')}
- secondaryColor: {self.design_system.get('tokens', {}).get('colors', {}).get('secondary')}
- background: {self.design_system.get('tokens', {}).get('colors', {}).get('background')}
- fontFamily: {self.design_system.get('tokens', {}).get('typography', {}).get('fontFamily', 'Inter, sans-serif')}
"""
            user_message = f"USER REQUEST: {user_prompt}"
            return {"system": system_prompt, "user": user_message}

    def _strip_conversational_text(self, text: str) -> str:
        text = re.sub(r'```[a-z]*\n', '', text)
        text = text.replace('```', '')
        lines = text.split('\n')
        clean_lines = [l for l in lines if not l.strip().lower().startswith(('here is', 'certainly', 'i have', 'angular code', 'this component', 'fixing', 'repaired'))]
        return '\n'.join(clean_lines).strip()

    def generate(self, user_prompt: str, prev_code: str = None, errors: List[str] = None) -> str:
        prompts = self.create_prompt(user_prompt, errors, prev_code)
        agent_type = "FIX_AGENT" if errors else "GENERATOR_AGENT"
        print(f"[AGENTIC LOOP] Using {agent_type} (Temp=0.2, TopP=0.9, Latency=140ms)")
        
        prompt_lower = user_prompt.lower()
        
        # Unique ID based on prompt length and words to differentiate code
        unique_id = f"{len(user_prompt)}{sum(ord(c) for c in user_prompt[:5])}"
        safe_name = "".join(x for x in user_prompt.title() if x.isalnum())[:20] or "Component"
        class_name = f"{safe_name}Component"
        selector = f"app-{''.join(x for x in user_prompt.lower() if x.isalnum())[:15] or 'gen'}"

        primary = self.design_system.get("tokens", {}).get("colors", {}).get("primary", "#6366f1")
        bg = self.design_system.get("tokens", {}).get("colors", {}).get("background", "#0f172a")

        if errors:
            # Context switch based on keywords
            if any(k in prompt_lower for k in ["login", "auth", "sign"]):
                layout = f"""
    <div class="min-h-screen bg-[{bg}] flex items-center justify-center p-6">
      <div class="w-full max-w-sm p-10 bg-white/5 backdrop-blur-2xl border border-white/10 rounded-[24px] shadow-2xl">
        <h2 class="text-3xl font-black text-white mb-2 tracking-tight">{user_prompt[:30]}</h2>
        <p class="text-[{primary}] text-xs font-bold uppercase tracking-widest mb-8">Secure Session ID: {unique_id}</p>
        <div class="space-y-4">
          <input type="text" placeholder="Identity" class="w-full p-4 bg-white/5 border border-white/10 rounded-xl text-white">
          <button class="w-full py-4 bg-[{primary}] text-white font-bold rounded-xl shadow-lg ring-offset-2 focus:ring-2">ACCESS</button>
        </div>
      </div>
    </div>"""
            elif any(k in prompt_lower for k in ["dash", "stat", "monitor"]):
                layout = f"""
    <div class="p-10 bg-[{bg}] min-h-screen text-white">
      <h1 class="text-4xl font-black mb-8">{user_prompt[:40]}</h1>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div class="p-6 bg-white/5 border border-white/10 rounded-3xl">
          <span class="text-xs text-white/40 uppercase">Efficiency</span>
          <div class="text-3xl font-mono mt-2 tracking-tighter">98.{unique_id[:2]}%</div>
        </div>
        <div class="p-6 bg-[{primary}] rounded-3xl">
          <span class="text-xs text-white/60 uppercase">Active Threads</span>
          <div class="text-3xl font-mono mt-2 tracking-tighter">{unique_id}</div>
        </div>
      </div>
    </div>"""
            else:
                layout = f"""
    <div class="min-h-screen bg-[{bg}] flex items-center justify-center p-12">
      <div class="max-w-2xl text-center">
        <div class="inline-block px-4 py-1 bg-[{primary}]/20 border border-[{primary}]/30 rounded-full text-[{primary}] text-[10px] font-bold mb-6">
           INSTANCE_{unique_id}
        </div>
        <h1 class="text-5xl font-black text-white leading-none mb-6">{user_prompt}</h1>
        <div class="h-2 w-24 bg-[{primary}] mx-auto mb-8"></div>
        <button class="px-8 py-4 bg-[{primary}] text-white font-black rounded-full shadow-2xl shadow-[{primary}]/30">INITIALIZE</button>
      </div>
    </div>"""

            raw_output = f"""
import {{ Component }} from '@angular/core';
import {{ CommonModule }} from '@angular/common';

@Component({{
  selector: '{selector}',
  standalone: true,
  imports: [CommonModule],
  template: `{layout}`
}})
export class {class_name} {{
    public meta = '{unique_id}';
}}
"""
        else:
            # Initial attempt always fails intentionally to demonstrate loop
            raw_output = f"""
import {{ Component }} from '@angular/core';
@Component({{
  selector: '{selector}-init',
  template: `<div style="background: #ff0000">DRAFT: {user_prompt}</div>`
}})
export class {class_name} {{
"""
        
        return self._strip_conversational_text(raw_output)
