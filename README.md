# Guided Component Architect

A sophisticated pipeline that transforms natural language descriptions into valid, styled Angular components while adhering to a strict design system.

## Agentic Loop Architecture

The system implements a classic "Generator-Validator-Corrector" agentic pattern:

1.  **Input**: User provided natural language prompt + Design System JSON tokens.
2.  **Generator Agent**: A specialized LLM prompt that includes the design tokens and specific instructions to output standalone Angular component code using Tailwind CSS.
3.  **Linter-Agent (Validator)**: 
    *   **Syntax Check**: Ensures basic code structure (brackets, decorators) are present and correct.
    *   **Design Token Compliance**: Uses regex to find hardcoded values (like hex colors) and cross-references them with the allowed tokens in `design-system.json`.
4.  **Self-Correction**: If the Validator finds errors, the system triggers a feedback loop. It re-prompts the Generator with the specific error logs, asking it to fix the code.
5.  **Output**: The final validated code is returned to the frontend.

## Structure

-   `backend/`: Python FastAPI application managing the agentic logic.
-   `frontend/`: Angular application for the user interface and preview.
-   `design-system.json`: The source of truth for design tokens.

## How to Run

### Backend
```bash
cd backend
pip install -r requirements.txt
python main.py
```

### Frontend
```bash
cd frontend
npm install
npm start
```

## Assumptions
- Tailwind CSS is available in the environment where the generated component will be rendered.
- The system uses a mock LLM logic for demonstration purposes (simulating a failed first attempt and a successful self-correction).
