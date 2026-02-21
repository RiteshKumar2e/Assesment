import json
import os
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()

try:
    from .agents import GeneratorAgent, ValidatorAgent
except ImportError:
    from agents import GeneratorAgent, ValidatorAgent

app = FastAPI(title="Guided Component Architect API v2")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(BASE_DIR, "design-system.json")) as f:
    design_system = json.load(f)

generator = GeneratorAgent(design_system)
validator  = ValidatorAgent(design_system)


class GenerationRequest(BaseModel):
    prompt: str
    prev_code: Optional[str] = None


class GenerationResponse(BaseModel):
    code: str
    iterations: int
    logs: List[str]
    success: bool
    model: Optional[str] = None


@app.post("/generate", response_model=GenerationResponse)
async def generate_component(request: GenerationRequest):
    MAX_ATTEMPTS = 3
    current_code = ""
    errors: Optional[List[str]] = None
    logs: List[str] = []
    used_model = "unknown"
    t_start = time.time()

    short_prompt = request.prompt[:70] + ("..." if len(request.prompt) > 70 else "")
    ds_name    = design_system.get("name", "Architect Design System")
    ds_version = design_system.get("version", "3.0.0")
    ds_theme   = design_system.get("theme", "light")
    colors     = design_system.get("tokens", {}).get("colors", {})
    rules      = design_system.get("rules", [])

    # ─── PHASE 1: Design System ───────────────────────────────────────────────
    logs.append("━━━ PHASE 1 — DESIGN SYSTEM LOADING ━━━")
    logs.append(f"  System : {ds_name} v{ds_version} ({ds_theme} theme)")
    logs.append(f"  Tokens : {len(colors)} color tokens loaded")
    logs.append(f"  Primary: {colors.get('primary', 'N/A')}  |  BG: {colors.get('background', 'N/A')}")
    logs.append(f"  Rules  : {len(rules)} enforcement rule(s) injected into prompt")
    logs.append(f"  Prompt : \"{short_prompt}\"")
    logs.append(f"  Max Self-Correction Loops: {MAX_ATTEMPTS}")

    for attempt in range(MAX_ATTEMPTS):

        # ─── PHASE 2: Generator ───────────────────────────────────────────────
        phase_label = "INITIAL GENERATION" if attempt == 0 else f"SELF-CORRECTION — ATTEMPT #{attempt}"
        logs.append(f"")
        logs.append(f"━━━ PHASE 2 — GENERATOR [{attempt + 1}/{MAX_ATTEMPTS}] ━━━")
        logs.append(f"  Action : {phase_label}")
        if attempt == 0:
            logs.append(f"  Mode   : Constructing prompt with design system context")
            logs.append(f"  Tech   : Angular 17+ standalone | Tailwind CSS | TypeScript")
        else:
            logs.append(f"  Mode   : Re-prompting model with {len(errors or [])} validation error(s)")
            logs.append(f"  Input  : Previous code + error context injected into prompt")
        logs.append(f"  Groq   : Trying model cascade (10 models, best-first)...")

        try:
            current_code, used_model = await generator.generate(
                request.prompt,
                request.prev_code if attempt == 0 else current_code,
                errors,
            )
            elapsed = round(time.time() - t_start, 2)
            logs.append(f"  Model  : {used_model}")
            logs.append(f"  Output : {len(current_code):,} chars of TypeScript received ({elapsed}s)")

        except RuntimeError as e:
            logs.append(f"")
            logs.append(f"━━━ FATAL ERROR ━━━")
            logs.append(f"  Groq API unreachable: {e}")
            logs.append(f"  Action : Verify GROQ_API_KEY in backend/.env")
            return GenerationResponse(
                code=f"// GROQ API ERROR\n// {e}\n// Check your GROQ_API_KEY and network connectivity.",
                iterations=attempt + 1,
                logs=logs,
                success=False,
                model=None,
            )

        # ─── PHASE 3: Validator (Linter-Agent) ───────────────────────────────
        logs.append(f"")
        logs.append(f"━━━ PHASE 3 — LINTER-AGENT (VALIDATOR) ━━━")
        logs.append(f"  Check 1 of 3 : Syntax validation (brackets, decorators)...")
        logs.append(f"  Check 2 of 3 : Design token compliance (hex color audit)...")
        logs.append(f"  Check 3 of 3 : Angular standalone structure check...")

        result = validator.validate(current_code)

        if result["valid"]:
            elapsed = round(time.time() - t_start, 2)
            logs.append(f"  Result : ✓ ALL CHECKS PASSED — 0 violations found")
            logs.append(f"")
            logs.append(f"━━━ PHASE 4 — COMPLETE ━━━")
            logs.append(f"  Status    : SUCCESS")
            logs.append(f"  Iteration : {attempt + 1} of {MAX_ATTEMPTS}")
            logs.append(f"  Model     : {used_model}")
            logs.append(f"  Time      : {elapsed}s total")
            logs.append(f"  Component : standalone: true | Light theme | Tailwind CSS")
            return GenerationResponse(
                code=current_code,
                iterations=attempt + 1,
                logs=logs,
                success=True,
                model=used_model,
            )
        else:
            errors = result["errors"]
            logs.append(f"  Result : ✗ {len(errors)} VIOLATION(S) DETECTED")
            for i, err in enumerate(errors, 1):
                logs.append(f"    [{i}] {err}")

            # ─── PHASE 4: Self-Correction ─────────────────────────────────────
            if attempt < MAX_ATTEMPTS - 1:
                logs.append(f"")
                logs.append(f"━━━ PHASE 4 — SELF-CORRECTION LOOP ━━━")
                logs.append(f"  Trigger  : Validation failed — {len(errors)} error(s) found")
                logs.append(f"  Action   : Packaging error context for LLM feedback...")
                logs.append(f"  Feedback : Error logs will be injected as correction prompt")
                logs.append(f"  Next     : Retrying generation (attempt {attempt + 2} of {MAX_ATTEMPTS})...")

    elapsed = round(time.time() - t_start, 2)
    logs.append(f"")
    logs.append(f"━━━ PHASE 4 — COMPLETE (WITH WARNINGS) ━━━")
    logs.append(f"  Status    : MAX ATTEMPTS REACHED")
    logs.append(f"  Time      : {elapsed}s")
    logs.append(f"  Note      : Returning best available output")
    return GenerationResponse(
        code=current_code,
        iterations=MAX_ATTEMPTS,
        logs=logs,
        success=False,
        model=used_model,
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
