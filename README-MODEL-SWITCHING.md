# AI Model Switching Guide

This system now supports easy AI model switching to test different performance characteristics.

## Quick Start

### 1. Switch Models
```bash
# Run the model switcher
uv run python scripts/switch_model.py
```

### 2. Restart Agent
```bash
# Stop current agent (Ctrl+C if running)
# Then restart with new model
uv run python agent/processor.py
```

### 3. View Current Model
The dashboard sidebar now shows the currently active AI model.

## Available Serverless Models (Verified Working)

| Model | Speed | Capability | Best For |
|-------|-------|------------|----------|
| **Mixtral 8x7B** | Fast | High | General fraud detection (recommended) |
| **Llama 3.3 70B** | Medium | Highest | Latest capabilities and reasoning |
| **Llama 3.2 3B** | Fastest | Basic | Lightweight, fast processing |
| **DeepSeek R1 Llama 70B** | Medium | Very High | Advanced reasoning and analysis |
| **DeepSeek R1 Qwen 14B** | Fast | High | Efficient reasoning tasks |
| **Qwen 2.5 7B** | Fast | Good | Balanced performance |
| **Qwen 2.5 72B** | Slow | Very High | Complex analysis and reasoning |
| **Mistral 7B** | Fast | Good | Alternative fast option |

## Testing Different Models

### Performance Comparison Workflow:
1. Generate some test transactions with the current model
2. Note the processing times and decision quality
3. Switch to a different model using `scripts/switch_model.py`
4. Restart the agent
5. Generate similar transactions and compare results

### Metrics to Compare:
- **Processing Speed**: Time from transaction to decision
- **Decision Quality**: Accuracy of fraud detection
- **Reasoning Quality**: Clarity and logic of AI explanations
- **Tool Usage**: How effectively the model uses available tools
- **Error Rate**: Failed API calls or processing errors

## Environment Variable

The model is controlled by the `TOGETHER_MODEL` variable in `.env`:

```bash
# Default (recommended)
TOGETHER_MODEL=mistralai/Mixtral-8x7B-Instruct-v0.1

# Latest and most capable
TOGETHER_MODEL=meta-llama/Llama-3.3-70B-Instruct-Turbo

# Fastest lightweight model  
TOGETHER_MODEL=meta-llama/Llama-3.2-3B-Instruct-Turbo

# Advanced reasoning
TOGETHER_MODEL=deepseek-ai/deepseek-r1-distill-llama-70b
```

## Notes

- Model changes require an agent restart to take effect
- The dashboard will show the current model in the sidebar
- All models use the same fraud detection tools and logic
- Performance will vary based on model size and complexity
- Some models may have different API rate limits or costs