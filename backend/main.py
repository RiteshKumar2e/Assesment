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
    from .agents import GeneratorAgent, ValidatorAgent, MAX_RETRIES
except ImportError:
    from agents import GeneratorAgent, ValidatorAgent, MAX_RETRIES

app = FastAPI(title="Guided Component Architect API")

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
    current_code = ""
    errors: Optional[List[str]] = None
    logs: List[str] = []
    used_model = "unknown"
    t_start = time.time()

    colors  = design_system.get("tokens", {}).get("colors", {})
    ds_ver  = design_system.get("version", "3.0.0")
    short_p = request.prompt[:60] + ("..." if len(request.prompt) > 60 else "")

    logs.append(f'[INIT]      Agent initialized — prompt received')
    logs.append(f'[INIT]      "{short_p}"')
    logs.append(f'[DESIGN]    Loading design-system.json v{ds_ver}')
    logs.append(f'[DESIGN]    primary={colors.get("primary","N/A")}  borderRadius=8px  font=Inter')
    logs.append(f'[DESIGN]    glassBg={colors.get("glassBg","rgba(255,255,255,0.1)")}')
    logs.append(f'[DESIGN]    {len(design_system.get("rules",[]))} governance rules injected into LLM context')

    for attempt in range(MAX_RETRIES + 1):  # 1 generation + MAX_RETRIES repair attempts

        if attempt == 0:
            logs.append(f'[GEN]       Building prompt — Generator Agent (raw code output enforced)')
            logs.append(f'[GEN]       Stack: Angular 17+ standalone · Tailwind CSS · TypeScript')
            logs.append(f'[GROQ]      Connecting to Groq API (10-model cascade, temp=0.2)...')
        else:
            logs.append(f'[RETRY]     Self-correction triggered — Repair Agent activated')
            logs.append(f'[RETRY]     Injecting {len(errors or [])} error(s) into repair prompt')
            logs.append(f'[GROQ]      Re-calling Groq API with error context...')

        try:
            current_code, used_model = await generator.generate(
                request.prompt,
                request.prev_code if attempt == 0 else current_code,
                errors,
            )
            elapsed = round(time.time() - t_start, 2)
            logs.append(f'[GROQ]      Response received — {len(current_code):,} chars ({elapsed}s)')

        except RuntimeError as e:
            logs.append(f'[ERROR]     Groq API unreachable — {e}')
            logs.append(f'[ERROR]     Verify GROQ_API_KEY in backend/.env')
            return GenerationResponse(
                code=f"// GROQ API ERROR\n// {e}",
                iterations=attempt + 1,
                logs=logs,
                success=False,
                model=None,
            )

        logs.append(f'[LINT]      Linter-Agent running deterministic validation...')
        logs.append(f'[LINT]      [1/4] Syntax: brackets {{}} [] () · @Component · standalone: true')
        logs.append(f'[LINT]      [2/4] Token: primaryColor #6366f1 present?')
        logs.append(f'[LINT]      [3/4] Token: borderRadius 8px / rounded-* present?')
        logs.append(f'[LINT]      [4/4] Token: fontFamily Inter · glassBg rgba check')

        result = validator.validate(current_code)

        if result["valid"]:
            elapsed = round(time.time() - t_start, 2)
            logs.append(f'[LINT]      All checks passed — 0 violations')
            logs.append(f'[OK]        Component is valid and design-system compliant')
            logs.append(f'[OUTPUT]    Completed in {attempt + 1} iteration(s) · {elapsed}s total')
            return GenerationResponse(
                code=current_code,
                iterations=attempt + 1,
                logs=logs,
                success=True,
                model=used_model,
            )

        errors = result["errors"]
        logs.append(f'[LINT]      Validation failed — {len(errors)} violation(s) detected')
        for err in errors:
            logs.append(f'[LINT]      ↳ {err}')

        if attempt < MAX_RETRIES:
            logs.append(f'[RETRY]     Preparing error context for self-correction loop...')

    elapsed = round(time.time() - t_start, 2)
    logs.append(f'[WARN]      Max retries ({MAX_RETRIES}) reached — returning best available output ({elapsed}s)')
    return GenerationResponse(
        code=current_code,
        iterations=MAX_RETRIES + 1,
        logs=logs,
        success=False,
        model=used_model,
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
