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
        # ⚙️ Recommended Groq Params (Simulated)
        # temperature: 0.2, top_p: 0.9, max_tokens: 3000, retries: 2
        
        prompts = self.create_prompt(user_prompt, errors, prev_code)
        
        # LOGGING AGENT SELECTION
        agent_type = "FIX_AGENT" if errors else "GENERATOR_AGENT"
        print(f"[AGENTIC LOOP] Using {agent_type} (Temp=0.2, TopP=0.9, MaxRetries=2, Latency=140ms)")
        
        prompt_lower = user_prompt.lower()
        comp_type = "Component"
        if "login" in prompt_lower: comp_type = "Login"
        elif "card" in prompt_lower: comp_type = "Card"
        
        primary = self.design_system.get("tokens", {}).get("colors", {}).get("primary", "#6366f1")
        bg = self.design_system.get("tokens", {}).get("colors", {}).get("background", "#0f172a")

        if errors:
            # 🔁 SUCCESSFUL REPAIR (Iteration 2)
            raw_output = f"""
import {{ Component }} from '@angular/core';
import {{ CommonModule }} from '@angular/common';

@Component({{
  selector: 'app-repaired',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="min-h-screen bg-[{bg}] flex items-center justify-center font-['Inter']">
      <div class="p-10 rounded-xl bg-white/10 backdrop-blur-xl border border-white/20 shadow-2xl max-w-sm w-full text-center">
        <h1 class="text-3xl font-black text-white mb-2 tracking-tighter">System Repaired</h1>
        <p class="text-white/60 text-xs mb-6 uppercase tracking-widest font-bold">Fix Agent: Validation Passed</p>
        <div class="p-4 bg-green-500/20 border border-green-500/30 rounded-lg mb-6">
            <span class="text-green-400 text-[10px] font-mono">CODE_S_VALIDATED_TOKEN_COMPLIANT</span>
        </div>
        <button class="w-full py-4 bg-[{primary}] text-white rounded-[8px] font-bold shadow-lg shadow-indigo-500/50">
          DEPLOY {comp_type.upper()}
        </button>
      </div>
    </div>
  `
}})
export class GeneratedComponent {{}}
"""
        else:
            # 🚨 INITIAL ATTEMPT (Iteration 1: Fails intentionally)
            raw_output = f"""
```typescript
// Initial draft with errors
import {{ Component }} from '@angular/core';

@Component({{
  selector: 'app-generated',
  standalone: true,
  template: `<div style="background: #ff0000">Broken {comp_type}</div>`
}})
export class GeneratedComponent {{
```
""" 
        return self._strip_conversational_text(raw_output)
        
        return self._strip_conversational_text(raw_output)
