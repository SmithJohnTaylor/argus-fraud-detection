#!/usr/bin/env python3
"""
Simple model switching utility for the AI agent
"""

import os
import sys
from pathlib import Path

# Available serverless models (verified working on Together AI)
AVAILABLE_MODELS = {
    "1": {
        "name": "Mixtral 8x7B (Default - Fast)",
        "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
        "description": "Fast, reliable general-purpose model - recommended"
    },
    "2": {
        "name": "Llama 3.3 70B (Latest)", 
        "model": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
        "description": "Latest Llama model with improved capabilities"
    },
    "3": {
        "name": "Llama 3.2 3B (Fastest)",
        "model": "meta-llama/Llama-3.2-3B-Instruct-Turbo", 
        "description": "Smallest, fastest model for basic tasks"
    },
    "4": {
        "name": "DeepSeek R1 Llama 70B (Reasoning)",
        "model": "deepseek-ai/deepseek-r1-distill-llama-70b",
        "description": "Advanced reasoning model based on Llama"
    },
    "5": {
        "name": "DeepSeek R1 Qwen 14B (Reasoning)",
        "model": "deepseek-ai/deepseek-r1-distill-qwen-14b",
        "description": "Efficient reasoning model based on Qwen"
    },
    "6": {
        "name": "Qwen 2.5 7B (Balanced)",
        "model": "Qwen/Qwen2.5-7B-Instruct-Turbo",
        "description": "Balanced speed and capability"
    },
    "7": {
        "name": "Qwen 2.5 72B (Powerful)",
        "model": "Qwen/Qwen2.5-72B-Instruct-Turbo",
        "description": "Large model with strong performance"
    },
    "8": {
        "name": "Mistral 7B (Alternative)",
        "model": "mistralai/Mistral-7B-Instruct-v0.3",
        "description": "Alternative fast model from Mistral"
    }
}

def get_current_model():
    """Get the currently configured model from .env file"""
    env_file = Path(__file__).parent.parent / ".env"
    
    if not env_file.exists():
        return "Not configured"
    
    with open(env_file, 'r') as f:
        for line in f:
            if line.startswith('TOGETHER_MODEL='):
                return line.split('=', 1)[1].strip()
    
    return "Not configured"

def update_env_file(new_model):
    """Update the TOGETHER_MODEL in the .env file"""
    env_file = Path(__file__).parent.parent / ".env"
    
    if not env_file.exists():
        print("❌ .env file not found!")
        return False
    
    # Read all lines
    with open(env_file, 'r') as f:
        lines = f.readlines()
    
    # Update the TOGETHER_MODEL line
    updated = False
    for i, line in enumerate(lines):
        if line.startswith('TOGETHER_MODEL='):
            lines[i] = f"TOGETHER_MODEL={new_model}\n"
            updated = True
            break
    
    # If not found, add it
    if not updated:
        lines.append(f"TOGETHER_MODEL={new_model}\n")
    
    # Write back to file
    with open(env_file, 'w') as f:
        f.writelines(lines)
    
    return True

def main():
    print("🔄 AI Model Switcher")
    print("=" * 50)
    
    # Show current model
    current = get_current_model()
    print(f"Current model: {current}")
    print()
    
    # Show available models
    print("Available models:")
    for key, model_info in AVAILABLE_MODELS.items():
        status = "← CURRENT" if model_info["model"] == current else ""
        print(f"  {key}. {model_info['name']} {status}")
        print(f"     {model_info['description']}")
        print(f"     Model ID: {model_info['model']}")
        print()
    
    # Get user choice
    print("Enter the number of the model you want to use (or 'q' to quit):")
    choice = input("> ").strip()
    
    if choice.lower() == 'q':
        print("Goodbye!")
        return
    
    if choice not in AVAILABLE_MODELS:
        print("❌ Invalid choice!")
        return
    
    # Update the model
    selected_model = AVAILABLE_MODELS[choice]
    print(f"Switching to: {selected_model['name']}")
    print(f"Model ID: {selected_model['model']}")
    
    if update_env_file(selected_model['model']):
        print("✅ Model updated successfully!")
        print()
        print("To apply the changes:")
        print("1. Stop the current agent (Ctrl+C)")
        print("2. Restart the agent: uv run python agent/processor.py")
        print()
        print("The new model will be used for all future transactions.")
    else:
        print("❌ Failed to update model!")

if __name__ == "__main__":
    main()