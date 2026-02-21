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

    short_prompt = request.prompt[:60] + ("..." if len(request.prompt) > 60 else "")

    logs.append(f"[INIT]     Prompt received: \"{short_prompt}\"")
    logs.append(f"[INIT]     Design System: {design_system.get('name', 'Architect DS')} v{design_system.get('version', '3.0')}")
    logs.append(f"[INIT]     Max self-correction attempts: {MAX_ATTEMPTS}")
    logs.append("[GROQ]     Connecting to Groq API — trying models in cascade...")

    for attempt in range(MAX_ATTEMPTS):
        phase = "Initial generation" if attempt == 0 else f"Self-correction pass #{attempt}"
        logs.append(f"[GEN #{attempt+1}]  {phase} starting...")

        try:
            current_code, used_model = await generator.generate(
                request.prompt,
                request.prev_code if attempt == 0 else current_code,
                errors,
            )
            logs.append(f"[GEN #{attempt+1}]  Model selected: {used_model}")
            logs.append(f"[GEN #{attempt+1}]  Response received — {len(current_code)} chars of TypeScript")
        except RuntimeError as e:
            logs.append(f"[ERROR]    Groq API unreachable: {e}")
            return GenerationResponse(
                code=f"// GROQ API ERROR: {e}\n// Check your GROQ_API_KEY and network connectivity.",
                iterations=attempt + 1,
                logs=logs,
                success=False,
                model=None,
            )

        logs.append(f"[LINT]     Running design system validator...")
        result = validator.validate(current_code)

        if result["valid"]:
            elapsed = round(time.time() - t_start, 2)
            logs.append(f"[LINT]     All checks passed — no violations found")
            logs.append(f"[OK]       Component verified in {attempt + 1} iteration(s) | {elapsed}s total")
            logs.append(f"[OUTPUT]   {used_model} | standalone: true | Tailwind CSS | Light theme")
            return GenerationResponse(
                code=current_code,
                iterations=attempt + 1,
                logs=logs,
                success=True,
                model=used_model,
            )
        else:
            errors = result["errors"]
            logs.append(f"[LINT]     {len(errors)} violation(s) found:")
            for err in errors:
                logs.append(f"           ↳ {err}")
            if attempt < MAX_ATTEMPTS - 1:
                logs.append(f"[RETRY]    Sending error context back to model for correction...")

    elapsed = round(time.time() - t_start, 2)
    logs.append(f"[WARN]     Max attempts reached after {elapsed}s — returning best result")
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
