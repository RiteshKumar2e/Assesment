    # 🚀 Guided Component Architect

A high-performance "Generator-Validator-Corrector" pipeline that transforms natural language descriptions into production-ready, styled **Angular 17+** components. 

The system utilizes an agentic loop powered by **Groq's LPU™ Inference Engine** for ultra-low latency self-correction cycles.

## 🔗 Live Demo
- **Live:** [https://assesment-flame.vercel.app/](https://assesment-flame.vercel.app/)

---

## 🏗️ Architecture: The Agentic Loop

The system implements a classic 3-step agentic pattern with strict reinforcement:

1.  **Generator Agent (LLM)**: Uses a low-temperature (0.2) model to produce raw Angular source code based on user prompts and `design-system.json` tokens.
2.  **Linter-Agent (Validator)**: 
    *   **Syntax Check**: Validates TypeScript/Angular structure.
    *   **Design Token Compliance**: Ensures zero-hardcoded colors; only allowed design system values are permitted.
3.  **Self-Correction Loop**: On failure, specific error logs are fed back to a Repair Agent. The loop continues for up to 2 remedial iterations until the code passes all linter checks.

---

## 🛠️ Tech Stack

- **Frontend**: React (Vite) + Tailwind CSS + Lucide Icons
- **Backend**: FastAPI + Python (Asynchronous model cascade)
- **AI Engine**: Groq (Llama-3 models)
- **Design Governance**: Centralized `design-system.json`

---

## 📂 Project Structure

- `backend/`: Python FastAPI application managing the agentic logic and Groq integration.
- `frontend/`: React-based architect dashboard with live visual mapping and log streaming.
- `design-system.json`: The source of truth for design tokens (Primary color, border-radius, fonts).

---

## 🚀 Getting Started

### Prerequisites
- Node.js 18+
- Python 3.9+
- Groq API Key (Set as `GROQ_API_KEY` in `backend/.env`)

### Local Development

#### 1. Backend Setup
```bash
cd backend
pip install -r requirements.txt
python main.py
```
*API will run at `http://localhost:8080`*

#### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
*Dashboard will run at `http://localhost:5173`*

---

## 🚢 Deployment

### Frontend (Vercel)
The frontend is configured for Vercel. Ensure the `VITE_API_URL` (if used) or the fetch URL in `App.tsx` points to the production backend.

### Backend (Render/Railway)
The backend is optimized for Render.
- **Root Directory**: `backend`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python main.py` or `uvicorn main:app --host 0.0.0.0 --port 10000`

---

## 🛡️ Security & Governance

The pipeline includes a multi-layered defense system against **Prompt Injection**:

1.  **Sanitization Agent**: Scans inputs for malicious keywords (e.g., "ignore previous instructions").
2.  **Structural Delimiters**: Isolates user requests within `<user_request>` tags to prevent instruction hijacking.
3.  **Instruction Anchoring**: Critical rules are re-emphasized *after* user input to leverage model recency bias.
4.  **Deterministic Validation**: The Linter-Agent acts as a final guard, rejecting any output that doesn't conform to strict Angular/Design System rules.

---

## 📜 Design Rules (design-system.json)
The system strictly enforces:
- **Primary Color**: `#6366f1` (Indigo 600)
- **Border Radius**: `8px` (rounded-lg)
- **Typography**: Inter
- **Transparency**: Glassmorphism background tokens

---

## 📖 Workflows
Internal engineering documents are available in `.agent/workflows/`:
- `prompt_injection_prevention.md`: Detailed strategy for securing the LLM pipeline.
