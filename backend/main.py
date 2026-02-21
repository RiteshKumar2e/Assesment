import json
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
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
design_system_path = os.path.join(BASE_DIR, "design-system.json")

with open(design_system_path, "r") as f:
    design_system = json.load(f)

generator = GeneratorAgent(design_system)
validator = ValidatorAgent(design_system)

class GenerationRequest(BaseModel):
    prompt: str
    prev_code: Optional[str] = None

class GenerationResponse(BaseModel):
    code: str
    iterations: int
    logs: List[str]
    success: bool

@app.post("/generate", response_model=GenerationResponse)
async def generate_component(request: GenerationRequest):
    max_retries = 3
    current_code = ""
    logs = [f"🚀 Agent initialized with prompt: '{request.prompt[:50]}...'"]
    errors = None
    
    for i in range(max_retries):
        phase = "Initial Generation" if i == 0 else f"Self-Correction Loop (Attempt {i})"
        logs.append(f"🧠 {phase}: Analyzing design system and constructing component architecture...")
        
        current_code = generator.generate(request.prompt, request.prev_code or current_code, errors)
        
        logs.append(f"🔍 Validation Phase: Linter-Agent scanning for design system violations...")
        validation_result = validator.validate(current_code)
        
        if validation_result["valid"]:
            logs.append("✅ Validation Successful: Component complies with Design System v1.0")
            logs.append(f"📦 Finalizing artifacts in {i+1} iterations.")
            return GenerationResponse(
                code=current_code,
                iterations=i + 1,
                logs=logs,
                success=True
            )
        else:
            errors = validation_result["errors"]
            logs.append(f"❌ Violation Detected: {', '.join(errors)}")
            logs.append("🔄 Feedback Loop: Redirecting error logs back to Generator Agent...")
            
    return GenerationResponse(
        code=current_code,
        iterations=max_retries,
        logs=logs,
        success=False
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
