# Guided Component Architect

A sophisticated pipeline that transforms natural language descriptions into valid, styled Angular components while adhering to a strict design system.

## 🚀 Architectural Choice: Groq Powered Agentic Loops
To ensure a high-performance developer experience, this system utilizes **Groq's LPU™ Inference Engine**. We selected Groq specifically for its **ultra-low-latency generation**, which allows our "Generator-Validator-Corrector" loops to run near-instantaneously. This architecture enables multiple self-correction cycles without taxing the user's focus, making complex UI generation feel fluid.

## Agentic Loop Architecture

The system implements a classic "Generator-Validator-Corrector" agentic pattern with strict reinforcement:

1.  **Input**: Natural language prompt + `design-system.json` tokens.
2.  **Generator Agent**: Uses a low-temperature (0.2) model with strict system instructions to produce raw Angular source code.
3.  **Linter-Agent (Validator)**: 
    *   **Syntax Check**: Validates basic TypeScript/Angular structure.
    *   **Design Token Compliance**: Ensures zero-hardcoded colors; only allowed design system values are permitted.
4.  **Self-Correction (The Loop)**: On failure, the specific error logs are fed back to the Generator for up to 2 remedial iterations.
5.  **Clean Output**: Implements custom regex stripping to ensure raw code delivery (zero conversational text).

## Structure

-   `backend/`: Python FastAPI application managing the agentic logic and Groq integration.
-   `frontend/`: React-based architect dashboard with live visual mapping.
-   `design-system.json`: The source of truth for design tokens.

## Setup & Running

### Requirements
- Python 3.9+
- Node.js 18+
- Groq API Key (Set as `GROQ_API_KEY` in `.env`)

### Execution
```bash
# Backend
cd backend && pip install -r requirements.txt
python main.py

# Frontend
cd frontend && npm install && npm start
```
