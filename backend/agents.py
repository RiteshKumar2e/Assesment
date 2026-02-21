import json
import re
import os
import httpx
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

# ─── Groq model cascade — best to fastest ─────────────────────────────────────
GROQ_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-70b-versatile",
    "llama3-70b-8192",
    "mixtral-8x7b-32768",
    "llama-3.1-8b-instant",
    "llama3-8b-8192",
    "gemma2-9b-it",
    "llama-3.2-90b-vision-preview",
    "llama-3.2-11b-vision-preview",
    "gemma-7b-it",
]

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


# ─── Validator ────────────────────────────────────────────────────────────────

class ValidatorAgent:
    def __init__(self, design_system: Dict[str, Any]):
        self.allowed_colors = [
            c.lower()
            for c in design_system.get("tokens", {}).get("colors", {}).values()
            if isinstance(c, str) and c.startswith("#")
        ]

    def validate(self, code: str) -> Dict[str, Any]:
        errors: List[str] = []

        # Must be an Angular component
        if "@Component" not in code:
            errors.append("Missing @Component decorator — not a valid Angular component.")

        # Must be standalone
        if "standalone: true" not in code:
            errors.append("Component must declare standalone: true.")

        # Bracket balance
        if code.count("{") != code.count("}"):
            errors.append("Unbalanced curly braces {}.")
        if code.count("[") != code.count("]"):
            errors.append("Unbalanced square brackets [].")
        if code.count("(") != code.count(")"):
            errors.append("Unbalanced parentheses ().")

        # Token compliance (soft) — only flag clearly wrong hex codes
        hex_codes = re.findall(r'#[0-9a-fA-F]{6}', code)
        for h in hex_codes:
            if h.lower() not in self.allowed_colors:
                errors.append(f"Unauthorized color '{h}' — use a design system token.")
            if len(errors) >= 3:  # cap to avoid log spam
                break

        return {"valid": len(errors) == 0, "errors": errors}


# ─── Generator ────────────────────────────────────────────────────────────────

class GeneratorAgent:
    def __init__(self, design_system: Dict[str, Any]):
        self.design_system = design_system
        self.api_key: Optional[str] = os.getenv("GROQ_API_KEY")

    # ── Prompt builders ───────────────────────────────────────────────────────

    def _ds(self) -> Dict[str, Any]:
        return self.design_system.get("tokens", {})

    def _system_prompt(self) -> str:
        colors = self._ds().get("colors", {})
        typo   = self._ds().get("typography", {})
        rules  = self.design_system.get("rules", [])

        return f"""You are a world-class Angular 17+ architect. Generate ONE production-ready Angular standalone component.

═══ DESIGN SYSTEM (LIGHT THEME) ═══
Primary:         {colors.get('primary', '#4f46e5')}
Primary Hover:   {colors.get('primaryHover', '#4338ca')}
Primary Light:   {colors.get('primaryLight', '#eef2ff')}
Background:      {colors.get('background', '#ffffff')}
Background Alt:  {colors.get('backgroundAlt', '#f8fafc')}
Surface:         {colors.get('surface', '#ffffff')}
Border:          {colors.get('border', '#e2e8f0')}
Text:            {colors.get('text', '#0f172a')}
Text Secondary:  {colors.get('textSecondary', '#475569')}
Text Muted:      {colors.get('textMuted', '#94a3b8')}
Success:         {colors.get('success', '#16a34a')}
Danger:          {colors.get('danger', '#dc2626')}
Font:            {typo.get('fontFamily', 'Inter, sans-serif')}

═══ MANDATORY RULES ═══
{chr(10).join(f'{i+1}. {r}' for i, r in enumerate(rules))}
{len(rules)+1}. Output ONLY raw TypeScript. Zero markdown, zero prose, zero ``` fences.
{len(rules)+2}. The template must start with a light background: bg-white or bg-gray-50.
{len(rules)+3}. Every color value must come from the design token list above.
{len(rules)+4}. Use Tailwind CSS classes exclusively — no inline style="" attributes.
{len(rules)+5}. Add Angular animations, hover states, and focus rings for interactivity.
{len(rules)+6}. Include realistic placeholder data — not "Lorem ipsum".

═══ REQUIRED OUTPUT FORMAT ═══
import {{ Component }} from '@angular/core';
import {{ CommonModule }} from '@angular/common';

@Component({{
  selector: 'app-<kebab-case-name>',
  standalone: true,
  imports: [CommonModule, ...],
  template: `<YOUR HTML HERE>`,
}})
export class <PascalCaseName>Component {{ ... }}"""

    def _fix_prompt(self, original_prompt: str, prev_code: str, errors: List[str]) -> str:
        return f"""Fix the following Angular component. Do not change the visual design — only repair the listed errors.

ORIGINAL USER INTENT: {original_prompt}

ERRORS TO FIX:
{chr(10).join(f'  - {e}' for e in errors)}

PREVIOUS CODE:
{prev_code}

Return ONLY the corrected TypeScript. No markdown fences, no explanations."""

    # ── Groq call with model cascade ─────────────────────────────────────────

    async def _call_groq(
        self,
        system: str,
        user: str,
        temp: float = 0.2,
    ) -> tuple[str, str]:
        """Try each model in cascade. Returns (output, model_used)."""
        if not self.api_key:
            self.api_key = os.getenv("GROQ_API_KEY")

        if not self.api_key:
            raise RuntimeError("GROQ_API_KEY is not set in .env")

        last_error = ""
        for model in GROQ_MODELS:
            try:
                async with httpx.AsyncClient(timeout=45.0) as client:
                    response = await client.post(
                        GROQ_URL,
                        headers={"Authorization": f"Bearer {self.api_key}"},
                        json={
                            "model": model,
                            "messages": [
                                {"role": "system", "content": system},
                                {"role": "user",   "content": user},
                            ],
                            "temperature": temp,
                            "max_tokens": 3000,
                        },
                    )
                    response.raise_for_status()
                    data = response.json()
                    raw = data["choices"][0]["message"]["content"]
                    return self._clean(raw), model

            except httpx.HTTPStatusError as e:
                last_error = f"{model} → HTTP {e.response.status_code}"
                if e.response.status_code in (400, 404):
                    continue          # model not available — try next
                raise               # auth error etc — stop immediately

            except (httpx.ConnectError, httpx.TimeoutException) as e:
                raise RuntimeError(f"Cannot reach Groq API: {e}") from e

            except Exception as e:
                last_error = f"{model} → {e}"
                continue

        raise RuntimeError(f"All Groq models failed. Last error: {last_error}")

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _clean(self, text: str) -> str:
        """Strip markdown fences and leading prose."""
        text = re.sub(r'^```[a-z]*\s*', '', text.strip(), flags=re.MULTILINE)
        text = re.sub(r'```\s*$', '', text.strip(), flags=re.MULTILINE)
        # Trim anything before the first `import` or `@Component`
        for marker in ("import ", "@Component"):
            idx = text.find(marker)
            if idx != -1:
                text = text[idx:]
                break
        return text.strip()

    # ── Public API ────────────────────────────────────────────────────────────

    async def generate(
        self,
        user_prompt: str,
        prev_code: str = None,
        errors: List[str] = None,
    ) -> tuple[str, str]:
        """Returns (code, model_used)."""
        system = self._system_prompt()

        if errors and prev_code:
            user = self._fix_prompt(user_prompt, prev_code, errors)
        else:
            colors = self._ds().get("colors", {})
            user = (
                f'Generate a polished Angular component for: "{user_prompt}"\n\n'
                f"Requirements:\n"
                f"  • Light theme — white/gray-50 backgrounds only\n"
                f"  • Primary color {colors.get('primary', '#4f46e5')} for CTAs and highlights\n"
                f"  • Premium card layout with subtle shadow and border\n"
                f"  • Smooth Tailwind transitions on hover/focus\n"
                f"  • Realistic, contextually appropriate placeholder content\n"
                f"  • At least one interactive element with a visual state"
            )

        return await self._call_groq(system, user)
