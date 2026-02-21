import json
import re
import os
import httpx
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

# ─── Validator ────────────────────────────────────────────────────────────────

class ValidatorAgent:
    def __init__(self, design_system: Dict[str, Any]):
        self.design_system = design_system
        self.allowed_colors = [
            c.lower()
            for c in design_system.get("tokens", {}).get("colors", {}).values()
            if isinstance(c, str) and c.startswith("#")
        ]

    def check_syntax(self, code: str) -> List[str]:
        errors = []
        if code.count('{') != code.count('}'):
            errors.append("Unbalanced curly braces {} in the generated code.")
        if code.count('[') != code.count(']'):
            errors.append("Unbalanced square brackets [] in the generated code.")
        if code.count('(') != code.count(')'):
            errors.append("Unbalanced parentheses () in the generated code.")
        if "@Component" not in code:
            errors.append("Missing @Component decorator. Not a valid Angular component.")
        return errors

    def check_token_compliance(self, code: str) -> List[str]:
        errors = []
        hex_colors = re.findall(r'#[0-9a-fA-F]{3,6}', code)
        for color in hex_colors:
            if color.lower() not in self.allowed_colors:
                errors.append(f"Unauthorized color '{color}'. Use design system tokens only.")
        return errors

    def validate(self, code: str) -> Dict[str, Any]:
        all_errors = self.check_syntax(code) + self.check_token_compliance(code)
        return {"valid": len(all_errors) == 0, "errors": all_errors}


# ─── Generator ────────────────────────────────────────────────────────────────

class GeneratorAgent:
    def __init__(self, design_system: Dict[str, Any]):
        self.design_system = design_system
        self.api_key = os.getenv("GROQ_API_KEY")
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"

    def _tokens(self) -> Dict[str, str]:
        c = self.design_system.get("tokens", {}).get("colors", {})
        t = self.design_system.get("tokens", {}).get("typography", {})
        return {
            "primary":    c.get("primary", "#4f46e5"),
            "bg":         c.get("background", "#ffffff"),
            "bgAlt":      c.get("backgroundAlt", "#f8fafc"),
            "surface":    c.get("surface", "#ffffff"),
            "border":     c.get("border", "#e2e8f0"),
            "text":       c.get("text", "#0f172a"),
            "textSec":    c.get("textSecondary", "#475569"),
            "textMuted":  c.get("textMuted", "#94a3b8"),
            "success":    c.get("success", "#16a34a"),
            "danger":     c.get("danger", "#dc2626"),
            "font":       t.get("fontFamily", "Inter, sans-serif"),
        }

    def _build_system_prompt(self) -> str:
        tk = self._tokens()
        rules = self.design_system.get("rules", [])
        return f"""You are a senior Angular architect. Generate one production-ready Angular standalone component.

DESIGN SYSTEM (LIGHT THEME — strictly follow these):
  Primary:    {tk['primary']}
  Background: {tk['bg']}
  Surface:    {tk['surface']}
  Border:     {tk['border']}
  Text:       {tk['text']}
  Text Muted: {tk['textMuted']}
  Font:       {tk['font']}

RULES:
{chr(10).join(f'  - {r}' for r in rules)}
  - Output ONLY valid TypeScript Angular component code
  - NO markdown fences, NO explanations, NO comments outside the code
  - Component must be standalone: true
  - Use Tailwind CSS utility classes for ALL styling
  - The template must use a light background (bg-white or bg-gray-50)
  - Make it visually polished, modern, and professional"""

    def create_prompt(self, user_prompt: str, errors: List[str] = None, prev_code: str = None) -> Dict[str, str]:
        system = self._build_system_prompt()
        if errors:
            user = f"""Fix this Angular component. Maintain the original intent.

ORIGINAL INTENT: {user_prompt}

PREVIOUS CODE:
{prev_code}

VALIDATION ERRORS TO FIX:
{chr(10).join(f'  - {e}' for e in errors)}

Return only the corrected TypeScript code."""
        else:
            tk = self._tokens()
            user = f"""Build a polished Angular component for: "{user_prompt}"

Requirements:
  - Light theme: white/gray-50 background, {tk['primary']} for primary actions
  - Premium typography with {tk['font']}
  - Clean card-based layout with subtle shadows and borders
  - Smooth hover/focus transitions
  - Fully accessible with proper labels and ARIA attributes"""

        return {"system": system, "user": user}

    def _strip_markdown(self, text: str) -> str:
        text = re.sub(r'```[a-z]*\n?', '', text)
        text = text.replace('```', '')
        return text.strip()

    def _classify_prompt(self, prompt: str) -> str:
        p = prompt.lower()
        if any(w in p for w in ['login', 'signin', 'sign in', 'auth', 'password']):
            return 'auth'
        if any(w in p for w in ['dashboard', 'analytics', 'stats', 'metric', 'chart']):
            return 'dashboard'
        if any(w in p for w in ['card', 'profile', 'user', 'avatar']):
            return 'card'
        if any(w in p for w in ['nav', 'header', 'menu', 'sidebar']):
            return 'nav'
        if any(w in p for w in ['table', 'list', 'data', 'grid', 'row']):
            return 'table'
        if any(w in p for w in ['form', 'input', 'register', 'signup', 'contact']):
            return 'form'
        if any(w in p for w in ['button', 'cta', 'action']):
            return 'button'
        return 'generic'

    def _simulation_code(self, user_prompt: str) -> str:
        """High-quality simulation fallback when Groq is unreachable."""
        tk = self._tokens()
        kind = self._classify_prompt(user_prompt)
        name = re.sub(r'[^a-zA-Z0-9]', ' ', user_prompt).title().replace(' ', '')[:24] or 'Generated'

        templates = {
            'auth': f"""import {{ Component }} from '@angular/core';
import {{ FormsModule }} from '@angular/forms';
import {{ CommonModule }} from '@angular/common';

@Component({{
  selector: 'app-{name.lower()}-auth',
  standalone: true,
  imports: [FormsModule, CommonModule],
  template: `
    <div class="min-h-screen bg-gray-50 flex items-center justify-center p-6">
      <div class="w-full max-w-md bg-white rounded-2xl border border-gray-200 shadow-lg p-8">
        <div class="text-center mb-8">
          <div class="w-12 h-12 rounded-xl flex items-center justify-center mx-auto mb-4" style="background-color:{tk['primary']}">
            <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
            </svg>
          </div>
          <h1 class="text-2xl font-bold text-gray-900">Welcome back</h1>
          <p class="mt-1 text-sm text-gray-500">Sign in to your account to continue</p>
        </div>
        <form class="space-y-5">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1.5">Email address</label>
            <input type="email" placeholder="you@example.com" [(ngModel)]="email" name="email"
              class="w-full px-4 py-3 rounded-xl border border-gray-200 text-gray-900 text-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:border-transparent transition"
              style="focus-ring-color:{tk['primary']}"/>
          </div>
          <div>
            <div class="flex justify-between mb-1.5">
              <label class="block text-sm font-medium text-gray-700">Password</label>
              <a href="#" class="text-xs font-medium" style="color:{tk['primary']}">Forgot password?</a>
            </div>
            <input type="password" placeholder="••••••••" [(ngModel)]="password" name="password"
              class="w-full px-4 py-3 rounded-xl border border-gray-200 text-gray-900 text-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:border-transparent transition"/>
          </div>
          <button type="submit"
            class="w-full py-3 px-4 rounded-xl text-white text-sm font-semibold shadow-sm transition hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-offset-2"
            style="background-color:{tk['primary']}">
            Sign in
          </button>
        </form>
        <p class="text-center text-sm text-gray-500 mt-6">
          Don't have an account?
          <a href="#" class="font-semibold ml-1" style="color:{tk['primary']}">Create one</a>
        </p>
      </div>
    </div>
  `
}})
export class {name}AuthComponent {{
  email = '';
  password = '';
}}""",
            'dashboard': f"""import {{ Component }} from '@angular/core';
import {{ CommonModule }} from '@angular/common';

@Component({{
  selector: 'app-{name.lower()}-dashboard',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="min-h-screen bg-gray-50 p-6">
      <div class="max-w-6xl mx-auto">
        <div class="mb-8">
          <h1 class="text-2xl font-bold text-gray-900">Analytics Dashboard</h1>
          <p class="text-sm text-gray-500 mt-1">Track your key metrics in real-time.</p>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
          <div *ngFor="let stat of stats" class="bg-white rounded-2xl border border-gray-200 p-5 shadow-sm hover:shadow-md transition">
            <div class="flex items-center justify-between mb-3">
              <span class="text-xs font-semibold uppercase tracking-widest text-gray-400">{{{{ stat.label }}}}</span>
              <span class="text-xs font-medium px-2 py-0.5 rounded-full" [ngClass]="stat.change > 0 ? 'bg-green-50 text-green-600' : 'bg-red-50 text-red-600'">
                {{{{ stat.change > 0 ? '+' : '' }}}}{{{{ stat.change }}}}%
              </span>
            </div>
            <p class="text-3xl font-bold text-gray-900">{{{{ stat.value }}}}</p>
          </div>
        </div>
        <div class="bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
          <h2 class="text-base font-semibold text-gray-800 mb-4">Recent Activity</h2>
          <div class="space-y-3">
            <div *ngFor="let item of activity" class="flex items-center gap-3 py-2 border-b border-gray-100 last:border-0">
              <div class="w-8 h-8 rounded-full flex items-center justify-center shrink-0" style="background-color:{tk['primaryLight'] if 'primaryLight' in self.design_system.get('tokens',{{}}).get('colors',{{}}) else '#eef2ff'}">
                <span class="text-xs font-bold" style="color:{tk['primary']}">{{{{ item.initials }}}}</span>
              </div>
              <div class="flex-1 min-w-0">
                <p class="text-sm font-medium text-gray-800 truncate">{{{{ item.action }}}}</p>
                <p class="text-xs text-gray-400">{{{{ item.time }}}}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `
}})
export class {name}DashboardComponent {{
  stats = [
    {{ label: 'Total Users', value: '12,842', change: 12 }},
    {{ label: 'Revenue', value: '$48,320', change: 8 }},
    {{ label: 'Conversion', value: '3.24%', change: -2 }},
    {{ label: 'Active Now', value: '1,209', change: 5 }},
  ];
  activity = [
    {{ initials: 'AK', action: 'New signup from anmol@dev.io', time: '2 min ago' }},
    {{ initials: 'RJ', action: 'Payment received — $249 plan', time: '14 min ago' }},
    {{ initials: 'SL', action: 'Support ticket #4821 resolved', time: '1 hr ago' }},
  ];
}}""",
            'card': f"""import {{ Component }} from '@angular/core';

@Component({{
  selector: 'app-{name.lower()}-card',
  standalone: true,
  template: `
    <div class="min-h-screen bg-gray-50 flex items-center justify-center p-6">
      <div class="bg-white rounded-2xl border border-gray-200 shadow-lg overflow-hidden w-80">
        <div class="h-24 w-full" style="background: linear-gradient(135deg, {tk['primary']}, #7c3aed)"></div>
        <div class="px-6 pb-6">
          <div class="flex items-end gap-4 -mt-10 mb-4">
            <div class="w-20 h-20 rounded-2xl border-4 border-white shadow-md bg-gray-100 flex items-center justify-center">
              <span class="text-2xl font-bold text-gray-400">AK</span>
            </div>
            <div class="pb-1">
              <h2 class="font-bold text-gray-900 text-lg leading-tight">Anmol Kumar</h2>
              <p class="text-sm text-gray-500">Senior Engineer</p>
            </div>
          </div>
          <p class="text-sm text-gray-600 leading-relaxed mb-5">
            Building scalable systems and beautiful interfaces. Passionate about clean code and great UX.
          </p>
          <div class="flex gap-3">
            <button class="flex-1 py-2.5 rounded-xl text-white text-sm font-semibold transition hover:opacity-90"
              style="background-color:{tk['primary']}">Connect</button>
            <button class="flex-1 py-2.5 rounded-xl text-sm font-semibold border border-gray-200 text-gray-700 hover:bg-gray-50 transition">Message</button>
          </div>
        </div>
      </div>
    </div>
  `
}})
export class {name}CardComponent {{}}""",
            'table': f"""import {{ Component }} from '@angular/core';
import {{ CommonModule }} from '@angular/common';

@Component({{
  selector: 'app-{name.lower()}-table',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="min-h-screen bg-gray-50 p-6">
      <div class="max-w-5xl mx-auto bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
        <div class="px-6 py-5 border-b border-gray-100 flex items-center justify-between">
          <div>
            <h2 class="text-lg font-bold text-gray-900">Users</h2>
            <p class="text-sm text-gray-400 mt-0.5">Manage your team members</p>
          </div>
          <button class="px-4 py-2 rounded-lg text-white text-sm font-semibold transition hover:opacity-90" style="background-color:{tk['primary']}">
            + Invite
          </button>
        </div>
        <table class="w-full">
          <thead>
            <tr class="border-b border-gray-100 bg-gray-50/60">
              <th class="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Name</th>
              <th class="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Role</th>
              <th class="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Status</th>
              <th class="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Joined</th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let user of users" class="border-b border-gray-50 hover:bg-gray-50/50 transition">
              <td class="px-6 py-4 flex items-center gap-3">
                <div class="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white" style="background-color:{tk['primary']}">
                  {{{{ user.name[0] }}}}
                </div>
                <div>
                  <p class="text-sm font-medium text-gray-900">{{{{ user.name }}}}</p>
                  <p class="text-xs text-gray-400">{{{{ user.email }}}}</p>
                </div>
              </td>
              <td class="px-6 py-4 text-sm text-gray-600">{{{{ user.role }}}}</td>
              <td class="px-6 py-4">
                <span class="px-2.5 py-1 rounded-full text-xs font-medium"
                  [ngClass]="user.active ? 'bg-green-50 text-green-700' : 'bg-gray-100 text-gray-500'">
                  {{{{ user.active ? 'Active' : 'Inactive' }}}}
                </span>
              </td>
              <td class="px-6 py-4 text-sm text-gray-400">{{{{ user.joined }}}}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  `
}})
export class {name}TableComponent {{
  users = [
    {{ name: 'Anmol Kumar', email: 'anmol@company.io', role: 'Lead Engineer', active: true, joined: 'Jan 2024' }},
    {{ name: 'Priya Sharma', email: 'priya@company.io', role: 'Product Manager', active: true, joined: 'Mar 2024' }},
    {{ name: 'Rahul Dev', email: 'rahul@company.io', role: 'Designer', active: false, joined: 'Feb 2024' }},
  ];
}}""",
        }

        code = templates.get(kind, templates.get('card', ''))
        if not code:
            code = templates['card']
        return code

    async def generate(self, user_prompt: str, prev_code: str = None, errors: List[str] = None) -> str:
        if not self.api_key:
            self.api_key = os.getenv("GROQ_API_KEY")

        if not self.api_key:
            print("WARNING: GROQ_API_KEY not set — using simulation mode.")
            return self._simulation_code(user_prompt)

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
                            {"role": "user",   "content": prompts["user"]},
                        ],
                        "temperature": 0.25,
                        "max_tokens": 2048,
                    },
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()
                raw = data["choices"][0]["message"]["content"]
                return self._strip_markdown(raw)

            except (httpx.ConnectError, httpx.TimeoutException, OSError) as e:
                print(f"GROQ API network error — falling back to simulation: {e}")
                return self._simulation_code(user_prompt)

            except Exception as e:
                print(f"GROQ API Error: {e}")
                return self._simulation_code(user_prompt)
