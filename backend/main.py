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
    MAX_ATTEMPTS = 3
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
    logs.append(f'[DESIGN]    primary={colors.get("primary","N/A")}  background={colors.get("background","N/A")}')
    logs.append(f'[DESIGN]    Design tokens injected into LLM context')

    for attempt in range(MAX_ATTEMPTS):

        if attempt == 0:
            logs.append(f'[GEN]       Building prompt — raw code output enforced, no filler')
            logs.append(f'[GEN]       Stack: Angular 17+ standalone · Tailwind CSS · TypeScript')
            logs.append(f'[GROQ]      Connecting to Groq API...')
        else:
            logs.append(f'[RETRY]     Self-correction triggered — {len(errors or [])} error(s) found')
            logs.append(f'[RETRY]     Injecting validator error logs into correction prompt')
            logs.append(f'[GROQ]      Re-calling Groq API with fix context...')

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

        logs.append(f'[LINT]      Linter-Agent running validation checks...')
        logs.append(f'[LINT]      Checking syntax: brackets {{}} [] () and @Component decorator')
        logs.append(f'[LINT]      Checking design token compliance: hex colors vs JSON palette')

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

        if attempt < MAX_ATTEMPTS - 1:
            logs.append(f'[RETRY]     Preparing error context for self-correction loop...')

    elapsed = round(time.time() - t_start, 2)
    logs.append(f'[WARN]      Max attempts reached — returning best available output ({elapsed}s)')
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
