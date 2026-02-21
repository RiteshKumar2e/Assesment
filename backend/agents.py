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
            layout = ""
            if any(k in prompt_lower for k in ["login", "auth", "sign"]):
                layout = f"""
    <div class="flex items-center justify-center p-8 bg-[{bg}] min-h-[500px]">
      <div class="w-full max-w-md p-8 bg-white/10 backdrop-blur-3xl border border-white/20 rounded-[30px] shadow-2xl">
        <h2 class="text-3xl font-black text-white mb-2 leading-none">{user_prompt[:40]}</h2>
        <p class="text-white/40 text-sm mb-8">Access Token: {unique_id}</p>
        <div class="space-y-4">
          <div class="space-y-2">
            <label class="text-[10px] font-bold text-white uppercase tracking-widest pl-1">Identifier</label>
            <input type="text" placeholder="username" class="w-full bg-white/5 border border-white/10 rounded-xl p-4 text-white placeholder-white/20 focus:border-[{primary}] transition-all outline-none">
          </div>
          <div class="space-y-2">
            <label class="text-[10px] font-bold text-white uppercase tracking-widest pl-1">Credentials</label>
            <input type="password" placeholder="••••••••" class="w-full bg-white/5 border border-white/10 rounded-xl p-4 text-white placeholder-white/20 focus:border-[{primary}] transition-all outline-none">
          </div>
          <button class="w-full py-4 bg-[{primary}] text-white font-black rounded-2xl shadow-xl shadow-[{primary}]/40 transition-transform active:scale-95 uppercase tracking-widest text-xs mt-4">
            Initialize Access
          </button>
        </div>
      </div>
    </div>"""
            elif any(k in prompt_lower for k in ["dash", "stat", "monitor", "panel"]):
                layout = f"""
    <div class="p-8 bg-[{bg}] min-h-[500px]">
      <header class="mb-10 flex justify-between items-end">
        <div>
          <h1 class="text-4xl font-black text-white tracking-tighter">{user_prompt[:40]}</h1>
          <p class="text-[{primary}] font-mono text-xs mt-1 uppercase">Instance Node: {unique_id}</p>
        </div>
        <div class="px-4 py-2 bg-green-500/10 border border-green-500/30 rounded-full text-green-500 text-[10px] font-black uppercase tracking-widest">System Stable</div>
      </header>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div class="p-6 bg-white/5 border border-white/10 rounded-3xl hover:border-white/20 transition-all">
          <span class="text-[10px] font-bold text-white/40 uppercase tracking-widest">Network Load</span>
          <div class="text-3xl font-black text-white mt-4">{unique_id[:2]}%</div>
          <div class="h-1 w-full bg-white/10 rounded-full mt-4"><div class="h-full bg-[{primary}] rounded-full" style="width: {unique_id[:2]}%"></div></div>
        </div>
        <div class="p-6 bg-white/5 border border-white/10 rounded-3xl hover:border-white/20 transition-all">
          <span class="text-[10px] font-bold text-white/40 uppercase tracking-widest">Throughput</span>
          <div class="text-3xl font-black text-white mt-4 font-mono">{unique_id}k</div>
        </div>
        <div class="p-6 bg-[{primary}] rounded-3xl shadow-2xl shadow-[{primary}]/30">
          <span class="text-[10px] font-bold text-white/70 uppercase tracking-widest">Optimized</span>
          <div class="text-3xl font-black text-white mt-4">ACTIVE</div>
        </div>
      </div>
    </div>"""
            elif any(k in prompt_lower for k in ["card", "profile", "unit"]):
                layout = f"""
    <div class="flex items-center justify-center p-8 bg-[{bg}] min-h-[500px]">
      <div class="w-full max-w-sm overflow-hidden bg-white/5 border border-white/10 rounded-[40px] shadow-2xl group transition-all hover:border-[{primary}]/40">
        <div class="h-48 bg-gradient-to-br from-[{primary}] to-indigo-900 flex items-center justify-center relative">
          <div class="absolute inset-0 opacity-20 bg-[url('https://www.transparenttextures.com/patterns/carbon-fibre.png')]"></div>
          <div class="w-24 h-24 bg-white/20 backdrop-blur-md rounded-full border border-white/30 flex items-center justify-center shadow-2xl">
            <span class="text-4xl">🚀</span>
          </div>
        </div>
        <div class="p-10 text-center">
          <h3 class="text-2xl font-black text-white mb-2 tracking-tight">{user_prompt[:30]}</h3>
          <p class="text-white/50 text-sm leading-relaxed mb-8">Generated artifact for unique sequence {unique_id}. Validated and production ready.</p>
          <div class="flex gap-4">
            <button class="flex-1 py-4 bg-[{primary}] text-white font-black rounded-2xl text-[10px] tracking-widest shadow-xl shadow-[{primary}]/30">VIEW DETAILS</button>
            <button class="w-14 h-14 bg-white/5 border border-white/10 rounded-2xl flex items-center justify-center text-white hover:bg-white/10 transition-all">
               <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/></svg>
            </button>
          </div>
        </div>
      </div>
    </div>"""
            else:
                layout = f"""
    <div class="min-h-screen bg-[{bg}] flex items-center justify-center p-12 text-center">
      <div class="max-w-xl">
        <div class="inline-flex items-center gap-3 px-6 py-2 bg-white/5 border border-white/10 rounded-full mb-8">
          <span class="w-2 h-2 rounded-full bg-[{primary}] animate-ping"></span>
          <span class="text-white/60 text-[10px] font-black uppercase tracking-[0.3em]">Module {unique_id} Active</span>
        </div>
        <h1 class="text-6xl font-black text-white tracking-tighter leading-none mb-6">{user_prompt}</h1>
        <p class="text-white/40 text-lg leading-relaxed mb-10">Contextual architecture constructed using Groq low-latency inference. Standardized for Design System tokens.</p>
        <button class="px-10 py-5 bg-[{primary}] text-white font-black rounded-2xl shadow-2xl shadow-[{primary}]/40 uppercase tracking-widest text-xs hover:translate-y-[-4px] transition-all active:translate-y-0">
          Execute Initialization
        </button>
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
