# Guided Component Architect 🏗️

An agentic pipeline that transforms natural language descriptions into valid, design-compliant Angular components.

## 🚀 Architecture: The Agentic Loop

The system operates on a **Generate-Validate-Correct** cycle:

1.  **Token Injection**: The `design-tokens.json` are injected into the system prompt to guide the LLM's styling decisions.
2.  **Generation (Generator)**: The LLM generates an Angular component using Angular Material and Tailwind CSS.
3.  **Validation (Linter-Agent)**:
    *   **Syntax Check**: Ensures basic Angular structure and TypeScript validity.
    *   **Design Compliance**: Scans the code for CSS/Tailwind values and compares them against the `design-tokens.json`.
4.  **Self-Correction**: If the Linter-Agent finds discrepancies (e.g., unauthorized colors or syntax errors), it passes the error log back to the Generator for a second pass.

## 🛠️ Components

-   `design-tokens.json`: The "Source of Truth" for styles.
-   `src/validator.py`: The logic for syntax and token validation.
-   `src/generator.py`: The orchestration logic for the agentic loop.
-   `main.py`: CLI entry point.

## ⚙️ Installation

```bash
pip install rich # Optional for better UI
```

## 📖 Usage

Run the architect with a prompt:

```bash
python main.py --prompt "A sleek glassmorphism login card"
```

## 🛡️ Design System Constraint

The architect is strictly bound to:
-   **Primary Color**: `#6366f1`
-   **Border Radius**: `8px` (md), `12px` (lg)
-   **Glass Effect**: `rgba(255, 255, 255, 0.1)`

Any attempt to use colors outside this range will be flagged and corrected by the Linter-Agent.
