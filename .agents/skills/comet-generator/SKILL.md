---
name: comet-generator
description: Generate code, images, and video using CometAPI multi-model endpoints. Use whenever the user asks to generate images, videos, or code with their CometAPI key.
---

# CometAPI Multi-Model Generator

This workspace is configured with CometAPI credentials in `.env` to generate Code, Images, and Videos across 500+ top models.

## Usage

Run the local generator CLI using the `run_command` tool (requires network access / `BypassSandbox: true` if executed outside local offline mode):

### 1. Test Connection & Models
```bash
python3 generator.py test
```

### 2. Code Generation
```bash
python3 generator.py code "Your prompt here" [optional_model_name]
```
- Default model: `gpt-4o` (or `claude-3-5-sonnet-20241022`, `deepseek-v3`, `qwen-2.5-coder-32b-instruct`)
- Outputs saved in `outputs/code_<timestamp>.md`

### 3. Image Generation
```bash
python3 generator.py image "Your visual description" [optional_model_name]
```
- Default model: `flux-schnell` (or `dall-e-3`, `flux-1.1-pro`, `gpt-image-2.6-sunburst`)
- Outputs saved in `outputs/image_<timestamp>.png`

### 4. Video Generation
```bash
python3 generator.py video "Your video description" [optional_model_name]
```
- Default model: `omni-fast` (or `viduq3`, `kling`, `sora-2`)
- Outputs saved in `outputs/video_<timestamp>.mp4`
