import os
import json
from src.generator import GuidedArchitect
from main import mock_llm_callback, save_output, generate_preview

def test_multiturn():
    tokens_path = 'design-tokens.json'
    architect = GuidedArchitect(tokens_path)
    
    print("\n--- TURN 1: Initial Generation ---")
    code1 = architect.run_pipeline("A login card", mock_llm_callback)
    print("Code 1 Generated.")
    
    print("\n--- TURN 2: Follow-up (Make it rounded) ---")
    code2 = architect.run_pipeline("Now make the button rounded and the card very circular", mock_llm_callback)
    print("Code 2 Generated with context.")
    
    save_output(code2, "ts")
    generate_preview(code2)
    print("\n[✔] Multi-turn test complete.")

if __name__ == "__main__":
    test_multiturn()
