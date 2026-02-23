import json
import re
import os
import httpx
from typing import List, Dict, Any, Optional, Tuple
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

# ─── Recommended model settings from master prompt pack ───────────────────────
TEMPERATURE  = 0.2
TOP_P        = 0.9
MAX_TOKENS   = 3000
MAX_RETRIES  = 2          # validator retries before giving up


# ═══════════════════════════════════════════════════════════════════════════════
# VALIDATOR  (Deterministic — no LLM involved)
# ═══════════════════════════════════════════════════════════════════════════════

class ValidatorAgent:
    """
    Linter-Agent: deterministic validation only.
    Checks per master prompt pack:
      1. Design token compliance  (primary color, border-radius, font, glassBg)
      2. Syntax sanity            (balanced brackets, Angular @Component, standalone)
    """

    PRIMARY_COLOR = "#6366f1"
    BORDER_RADIUS = "8px"
    FONT_FAMILY   = "Inter"
    GLASS_BG      = "rgba(255,255,255,0.1)"

    def __init__(self, design_system: Dict[str, Any] = None):
        # Optionally override tokens from design_system JSON
        if design_system:
            colors = design_system.get("tokens", {}).get("colors", {})
            self.PRIMARY_COLOR = colors.get("primary", self.PRIMARY_COLOR)
            self.GLASS_BG      = colors.get("glassBg",  self.GLASS_BG)


    def validate(self, code: str) -> Dict[str, Any]:
        errors: List[str] = []

        # ── 1. Angular structure ────────────────────────────────────────────
        if "@Component" not in code:
            errors.append("Missing @Component decorator — not a valid Angular component.")

        if "standalone: true" not in code:
            errors.append("Component must declare `standalone: true`.")

        # ── 2. Syntax sanity — bracket balance ─────────────────────────────
        if code.count("{") != code.count("}"):
            errors.append(f"Unbalanced curly braces {{ }} ({code.count('{')} open, {code.count('}')} close).")

        if code.count("[") != code.count("]"):
            errors.append(f"Unbalanced square brackets [ ] ({code.count('[')} open, {code.count(']')} close).")

        if code.count("(") != code.count(")"):
            errors.append(f"Unbalanced parentheses ( ) ({code.count('(')} open, {code.count(')')} close).")

        # ── 3. Design token — primary color ────────────────────────────────
        # Must reference #6366f1 somewhere (bg, text, border etc.)
        if self.PRIMARY_COLOR not in code and "indigo" not in code.lower() and "primary" not in code.lower():
            errors.append(
                f"Design token violation: primary color {self.PRIMARY_COLOR} not found. "
                "Use #6366f1 or Tailwind `indigo-*` classes for CTAs and highlights."
            )

        # ── 4. Design token — border radius ────────────────────────────────
        # Must reference rounded-* or 8px
        has_radius = (
            "rounded" in code or
            self.BORDER_RADIUS in code or
            "border-radius" in code
        )
        if not has_radius:
            errors.append(
                f"Design token violation: borderRadius '{self.BORDER_RADIUS}' not applied. "
                "Use `rounded-lg` (Tailwind) or `border-radius: 8px`."
            )

        # ── 5. Design token — font family ──────────────────────────────────
        if self.FONT_FAMILY not in code:
            errors.append(
                f"Design token violation: fontFamily '{self.FONT_FAMILY}' not referenced. "
                "Ensure Inter is applied via CSS or class."
            )

        # ── 6. Closed HTML tags (basic check) ──────────────────────────────
        unclosed = re.findall(r'<(?!br|hr|img|input|meta|link|!)\s*(\w+)[^>]*(?<!/)>', code)
        closed   = re.findall(r'</(\w+)>', code)
        open_set  = {}
        for tag in unclosed:
            open_set[tag] = open_set.get(tag, 0) + 1
        for tag in closed:
            if tag in open_set:
                open_set[tag] -= 1
        truly_unclosed = {t: c for t, c in open_set.items() if c > 0 and t not in ('br','hr','img','input','meta','link')}
        if truly_unclosed:
            # Only flag if it's a significant structural tag
            structural = {t for t in truly_unclosed if t in ('div','section','article','main','header','footer','form','ul','ol','table','tr','td','th','span','p','h1','h2','h3','button','nav')}
            if structural:
                errors.append(f"Unclosed HTML tag(s): {', '.join(f'<{t}>' for t in structural)}.")

        return {"valid": len(errors) == 0, "errors": errors}


# ═══════════════════════════════════════════════════════════════════════════════
# GENERATOR  (LLM via Groq)
# ═══════════════════════════════════════════════════════════════════════════════

# ── Exact system prompts from master prompt pack ──────────────────────────────

GENERATOR_SYSTEM_PROMPT = """\
You are a governed Angular component generation engine inside an automated agentic pipeline.
Convert natural language UI requests into ONE production-ready Angular 17+ standalone component.

━━━ ABSOLUTE OUTPUT RULES (VIOLATION = PIPELINE FAILURE) ━━━
1.  Output RAW TypeScript ONLY. Zero markdown, zero prose, zero ``` fences.
2.  Start the output with "import" — nothing before it.
3.  The file must be a single self-contained Angular standalone component.
4.  Include ALL necessary imports at the top.
5.  Use @Component with: selector, standalone: true, imports: [...], template: `...`, styles: [`...`].
6.  Template must be a backtick template literal — multi-line HTML inside.
7.  All HTML tags must be properly opened and closed.
8.  All TypeScript brackets { } [ ] ( ) must be balanced.
9.  Do NOT use external stylesheet files — keep styles inside the styles array.
10. Do NOT include constructor() unless needed.

━━━ MANDATORY DESIGN TOKENS ━━━
primary color  : #6366f1  (use for buttons, links, highlights, borders)
border-radius  : 8px      (use rounded-lg in Tailwind = 8px)
font-family    : Inter, sans-serif
glass overlay  : rgba(255,255,255,0.1)
background     : #ffffff or #f8fafc
text           : #0f172a

━━━ STYLING RULES ━━━
- Use Tailwind CSS utility classes exclusively for layout, spacing, colors.
- Map primary color via: bg-indigo-600, text-indigo-600, border-indigo-600, hover:bg-indigo-700.
- Use rounded-lg (= 8px) on every button, input, card.
- Apply font-sans class on the root wrapper for Inter font.
- Add hover:, focus: and transition classes for interactivity.
- Include realistic placeholder text — NOT lorem ipsum.
- Every input must have a label, placeholder, and appropriate type.
- Add at least ONE interactive element with visual feedback on hover/click.

━━━ REQUIRED OUTPUT SKELETON ━━━
import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-<kebab-name>',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="min-h-screen bg-gray-50 font-sans flex items-center justify-center p-6">
      <!-- YOUR COMPONENT HTML HERE -->
    </div>
  `,
  styles: [`
    /* Inter font */
    :host { font-family: 'Inter', sans-serif; display: block; }
    /* custom styles if Tailwind is insufficient */
  `]
})
export class <PascalName>Component {
  // component properties and methods
}

Follow this skeleton exactly. Replace placeholders with the real implementation.\
"""


REPAIR_SYSTEM_PROMPT = """\
You are a deterministic Angular code repair agent inside a governed pipeline.
You will receive Angular code that FAILED automated validation. Fix every listed error.

━━━ STRICT OUTPUT RULES ━━━
1.  Output RAW TypeScript ONLY — no markdown, no prose, no ``` fences.
2.  Start with "import" — nothing before it.
3.  Preserve the @Component standalone structure.
4.  Fix ALL errors listed in the validation report below.
5.  All brackets { } [ ] ( ) must be balanced in the final output.
6.  All HTML tags must be properly closed.

━━━ MANDATORY DESIGN TOKENS (must appear in output) ━━━
primary color : #6366f1  → Tailwind: indigo-600
border-radius : 8px      → Tailwind: rounded-lg
font-family   : Inter, sans-serif
glass bg      : rgba(255,255,255,0.1)

The corrected output must pass strict deterministic validation.\
"""



class GeneratorAgent:
    def __init__(self, design_system: Dict[str, Any]):
        self.design_system = design_system
        self.api_key: Optional[str] = os.getenv("GROQ_API_KEY")

    # ── Security & Sanitization ───────────────────────────────────────────────

    def _sanitize_input(self, text: str) -> str:
        """
        Detects and neutralizes potential prompt injection attempts.
        """
        # Block common injection triggers
        forbidden_patterns = [
            r"(?i)ignore\s+(all\s+)?previous\s+instructions",
            r"(?i)bypass\s+governance",
            r"(?i)system\s+override",
            r"(?i)disregard\s+the\s+prompt",
            r"(?i)you\s+are\s+now\s+a",
            r"(?i)new\s+role",
            r"(?i)instruction\s+update",
        ]
        
        for pattern in forbidden_patterns:
            if re.search(pattern, text):
                # Instead of erroring, we can neutralize it by wrapping it in quote or 
                # just replacing the offending part. For code generation, we'll be strict.
                raise ValueError("Potential prompt injection detected in user input.")
        
        # Strip any existing XML-like tags that might clash with our delimiters
        text = re.sub(r'<(/)?user_request>', '[REDACTED]', text)
        return text.strip()

    # ── Prompt builders (per master prompt pack templates) ────────────────────

    def _generation_user_prompt(self, user_input: str) -> str:
        """Runtime user prompt — uses delimiters to isolate user input."""
        sanitized_input = self._sanitize_input(user_input)
        return (
            f"You will generate an Angular standalone component based on the request inside the <user_request> tags.\n\n"
            f"<user_request>\n"
            f"{sanitized_input}\n"
            f"</user_request>\n\n"
            f"REMINDER — your output must strictly follow the system instructions and:\n"
            f"  1. Start immediately with `import` (no preamble)\n"
            f"  2. Contain @Component with standalone: true and an inline backtick template\n"
            f"  3. Use bg-indigo-600 / text-indigo-600 for the primary color #6366f1\n"
            f"  4. Use rounded-lg on every card, button, and input (borderRadius: 8px)\n"
            f"  5. Include :host {{ font-family: 'Inter', sans-serif; }} in styles\n"
            f"  6. Have realistic content — real labels, real placeholder text\n"
            f"  7. Be a complete, self-contained file — no external imports or missing brackets"
        )

    def _repair_user_prompt(self, user_input: str, bad_code: str, errors: List[str]) -> str:
        """Repair Agent user message — uses delimiters for isolation."""
        sanitized_request = self._sanitize_input(user_input)
        error_block = "\n".join(f"  [{i+1}] {e}" for i, e in enumerate(errors))
        return (
            f"The previously generated Angular component failed deterministic validation.\n\n"
            f"Original user request inside <user_request>:\n"
            f"<user_request>\n"
            f"{sanitized_request}\n"
            f"</user_request>\n\n"
            f"Validation errors detected by the Linter-Agent:\n"
            f"{error_block}\n\n"
            f"Previous (broken) code for reference:\n"
            f"--- START BROKEN CODE ---\n"
            f"{bad_code}\n"
            f"--- END BROKEN CODE ---\n\n"
            f"Produce a fully corrected version. Fix every listed error.\n"
            f"Ensure all design tokens are present in the final output.\n"
            f"Output must start immediately with `import` — no preamble, no markdown fences."
        )


    # ── Groq call with model cascade ──────────────────────────────────────────

    async def _call_groq(self, system: str, user: str) -> Tuple[str, str]:
        """Try each model in cascade. Returns (cleaned_code, model_used)."""
        if not self.api_key:
            self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise RuntimeError("GROQ_API_KEY is not set in backend/.env")

        last_error = ""
        for model in GROQ_MODELS:
            try:
                async with httpx.AsyncClient(timeout=45.0) as client:
                    response = await client.post(
                        GROQ_URL,
                        headers={"Authorization": f"Bearer {self.api_key}"},
                        json={
                            "model":       model,
                            "messages": [
                                {"role": "system", "content": system},
                                {"role": "user",   "content": user},
                            ],
                            "temperature": TEMPERATURE,
                            "top_p":       TOP_P,
                            "max_tokens":  MAX_TOKENS,
                        },
                    )
                    response.raise_for_status()
                    raw = response.json()["choices"][0]["message"]["content"]
                    return self._clean(raw), model

            except httpx.HTTPStatusError as e:
                last_error = f"{model} → HTTP {e.response.status_code}"
                if e.response.status_code in (400, 404):
                    continue       # model not available — try next
                raise              # auth / rate-limit — stop
            except (httpx.ConnectError, httpx.TimeoutException) as e:
                raise RuntimeError(f"Cannot reach Groq API: {e}") from e
            except Exception as e:
                last_error = f"{model} → {e}"
                continue

        raise RuntimeError(f"All 10 Groq models failed. Last: {last_error}")

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _clean(self, text: str) -> str:
        """
        Strip ALL markdown/prose wrapping from LLM output so the code starts
        cleanly with `import` and ends at the last closing brace.
        """
        text = text.strip()

        # 1. Remove opening fence: ```typescript, ```ts, ```angular, ``` etc.
        text = re.sub(r'^```[a-zA-Z]*\s*\n?', '', text, flags=re.MULTILINE)

        # 2. Remove closing fence
        text = re.sub(r'\n?```\s*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'```', '', text)   # catch any stray fences

        # 3. Find the real start — first 'import ' or '@Component'
        start = len(text)
        for marker in ("import ", "@Component", "import{", "import\n"):
            idx = text.find(marker)
            if idx != -1 and idx < start:
                start = idx
        text = text[start:]

        # 4. Find the real end — last closing brace of the class
        last_brace = text.rfind("}")
        if last_brace != -1:
            text = text[:last_brace + 1]

        return text.strip()


    # ── Public API ────────────────────────────────────────────────────────────

    async def generate(
        self,
        user_prompt: str,
        prev_code: str = None,
        errors: List[str] = None,
    ) -> Tuple[str, str]:
        """
        Returns (code, model_used).

        On first call  → uses Generator system prompt + generation user template.
        On retry call  → uses Repair system prompt + repair user template.
        """
        if errors and prev_code:
            system = REPAIR_SYSTEM_PROMPT
            user   = self._repair_user_prompt(user_prompt, prev_code, errors)
        else:
            system = GENERATOR_SYSTEM_PROMPT
            user   = self._generation_user_prompt(user_prompt)

        return await self._call_groq(system, user)
