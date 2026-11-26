import os
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

BASE_DIR = Path(__file__).parent.resolve()
IS_VERCEL = bool(os.environ.get("VERCEL"))

if IS_VERCEL:
    OUTPUTS_DIR = Path("/tmp/outputs")
else:
    OUTPUTS_DIR = BASE_DIR / "outputs"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

STATIC_DIR = BASE_DIR / "public" if (BASE_DIR / "public").exists() else BASE_DIR / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)

def load_env():
    env_file = BASE_DIR / ".env"
    if env_file.exists():
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())

load_env()

API_KEY = os.environ.get("COMET_API_KEY", "").strip()
BASE_URL = os.environ.get("COMET_BASE_URL", "https://api.cometapi.com/v1").rstrip("/")

app = FastAPI(title="CometAI Studio", description="All-in-one AI Studio for Code, Image & Video")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/outputs", StaticFiles(directory=str(OUTPUTS_DIR)), name="outputs")

def get_auth_headers():
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "User-Agent": "CometAI-Studio/1.0"
    }

def format_error_message(status_code: int, raw_text: str) -> str:
    try:
        data = json.loads(raw_text)
        # Check quota error
        msg = data.get("message") or data.get("error", {}).get("message") or raw_text
        if "insufficient_user_quota" in raw_text or "remaining quota" in raw_text:
            return f"⚠️ Insufficient CometAPI Credits: {msg}. Image & Video models require ~$0.02 - $0.05 per generation. Please top up your CometAPI account. Code models are still active!"
        if status_code == 503 or "temporarily unavailable" in raw_text:
            return "⚠️ Model Temporarily Unavailable: Upstream provider is temporarily offline for this model. Please select an active model (e.g. GPT-4o or DeepSeek R1)."
        return f"API Error: {msg}"
    except Exception:
        return f"Error ({status_code}): {raw_text}"

class CodeGenRequest(BaseModel):
    prompt: str
    model: str = "gpt-4o"
    system_prompt: Optional[str] = "You are an expert software engineer. Provide clean, production-ready code."

class ImageGenRequest(BaseModel):
    prompt: str
    model: str = "flux-2-flex"
    size: str = "1024x1024"

class VideoGenRequest(BaseModel):
    prompt: str
    model: str = "omni-fast"
    seconds: int = 4
    aspect_ratio: str = "16:9"
    resolution: str = "720p"

@app.get("/api/health")
async def health_check():
    return {
        "status": "online",
        "has_key": bool(API_KEY),
        "key_prefix": API_KEY[:6] + "..." if len(API_KEY) > 6 else ""
    }

@app.get("/api/models")
async def get_models():
    return {
        "code": [
            {"id": "gpt-4o", "name": "GPT-4o (OpenAI) • Flagship", "badge": "Active"},
            {"id": "deepseek-r1", "name": "DeepSeek R1 • Reasoning SOTA", "badge": "Active"},
            {"id": "deepseek-v3", "name": "DeepSeek V3 • Fast & Accurate", "badge": "Active"},
            {"id": "deepseek-chat", "name": "DeepSeek Chat", "badge": "Active"}
        ],
        "image": [
            {"id": "flux-2-flex", "name": "FLUX 2 Flex • High Fidelity", "badge": "SOTA"},
            {"id": "flux-dev", "name": "FLUX Dev • Photorealistic", "badge": "Popular"},
            {"id": "flux-2-max", "name": "FLUX 2 Max • Maximum Quality", "badge": "Pro"}
        ],
        "video": [
            {"id": "omni-fast", "name": "Omni Fast • Responsive 720p", "badge": "Active"},
            {"id": "happyhorse-1.1", "name": "HappyHorse 1.1 • Video Motion", "badge": "Active"}
        ]
    }

@app.post("/api/generate/code")
async def generate_code_endpoint(req: CodeGenRequest):
    if not API_KEY:
        raise HTTPException(status_code=400, detail="API key is missing.")

    url = f"{BASE_URL}/chat/completions"
    payload = {
        "model": req.model,
        "messages": [
            {"role": "system", "content": req.system_prompt},
            {"role": "user", "content": req.prompt}
        ]
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            resp = await client.post(url, headers=get_auth_headers(), json=payload)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")

        if resp.status_code != 200:
            err_msg = format_error_message(resp.status_code, resp.text)
            raise HTTPException(status_code=resp.status_code, detail=err_msg)

        data = resp.json()
        code_content = data["choices"][0]["message"]["content"]
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"code_{timestamp}.md"
        filepath = OUTPUTS_DIR / filename
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(code_content)

        return {
            "success": True,
            "content": code_content,
            "model": req.model,
            "saved_file": filename,
            "file_url": f"/outputs/{filename}"
        }

@app.post("/api/generate/image")
async def generate_image_endpoint(req: ImageGenRequest):
    if not API_KEY:
        raise HTTPException(status_code=400, detail="API key is missing.")

    width, height = 1024, 1024
    if "x" in req.size:
        try:
            parts = req.size.lower().split("x")
            width, height = int(parts[0]), int(parts[1])
        except Exception:
            width, height = 1024, 1024

    model_name = req.model.replace("black-forest-labs/", "")
    if model_name not in ("flux-2-flex", "flux-dev", "flux-2-max"):
        model_name = "flux-2-flex"

    url = f"https://api.cometapi.com/flux/v1/{model_name}"
    payload = {
        "prompt": req.prompt,
        "width": width,
        "height": height
    }

    async with httpx.AsyncClient(timeout=180.0) as client:
        try:
            resp = await client.post(url, headers=get_auth_headers(), json=payload)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")

        if resp.status_code not in (200, 201, 202):
            err_msg = format_error_message(resp.status_code, resp.text)
            raise HTTPException(status_code=resp.status_code, detail=err_msg)

        data = resp.json()
        task_id = data.get("id")
        poll_url = data.get("polling_url") or f"https://api.cometapi.com/flux/v1/get_result?id={task_id}"

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"image_{timestamp}.png"
        filepath = OUTPUTS_DIR / filename

        for _ in range(40):
            await asyncio.sleep(2)
            p_resp = await client.get(poll_url, headers=get_auth_headers())
            if p_resp.status_code == 200:
                p_data = p_resp.json()
                status = p_data.get("status", "").lower()
                if status in ("ready", "success", "completed"):
                    image_url = p_data.get("result", {}).get("sample") or p_data.get("url")
                    if not image_url:
                        raise HTTPException(status_code=500, detail="Ready status but no image sample URL returned.")
                    
                    img_resp = await client.get(image_url, headers={"User-Agent": "Mozilla/5.0"})
                    with open(filepath, "wb") as f:
                        f.write(img_resp.content)

                    return {
                        "success": True,
                        "filename": filename,
                        "file_url": f"/outputs/{filename}",
                        "prompt": req.prompt,
                        "model": model_name
                    }
                elif status in ("failed", "error"):
                    raise HTTPException(status_code=500, detail="Image generation failed upstream.")

        raise HTTPException(status_code=504, detail="Image rendering timed out. Please try again.")

@app.post("/api/generate/video")
async def generate_video_endpoint(req: VideoGenRequest):
    if not API_KEY:
        raise HTTPException(status_code=400, detail="API key is missing.")

    url = f"{BASE_URL}/videos"
    model_name = req.model if req.model in ("omni-fast", "happyhorse-1.1") else "omni-fast"
    payload = {
        "model": model_name,
        "prompt": req.prompt,
        "seconds": str(req.seconds),
        "aspect_ratio": req.aspect_ratio,
        "resolution": req.resolution
    }

    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            resp = await client.post(url, headers=get_auth_headers(), json=payload)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to submit video task: {str(e)}")

        if resp.status_code not in (200, 201, 202):
            err_msg = format_error_message(resp.status_code, resp.text)
            raise HTTPException(status_code=resp.status_code, detail=err_msg)

        task_data = resp.json()
        task_id = task_data.get("task_id") or task_data.get("id")
        if not task_id:
            raise HTTPException(status_code=500, detail=f"No task ID returned: {task_data}")

        status_url = f"{BASE_URL}/videos/{task_id}"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"video_{timestamp}.mp4"
        filepath = OUTPUTS_DIR / filename

        for _ in range(45):
            await asyncio.sleep(5)
            s_resp = await client.get(status_url, headers=get_auth_headers())
            if s_resp.status_code == 200:
                s_data = s_resp.json()
                status = s_data.get("status", "").lower()
                if status in ("completed", "succeeded", "success"):
                    video_url = s_data.get("url") or s_data.get("video_url")
                    if video_url:
                        v_resp = await client.get(video_url)
                        with open(filepath, "wb") as f:
                            f.write(v_resp.content)
                    else:
                        content_url = f"{BASE_URL}/videos/{task_id}/content"
                        c_resp = await client.get(content_url, headers=get_auth_headers())
                        with open(filepath, "wb") as f:
                            f.write(c_resp.content)

                    return {
                        "success": True,
                        "filename": filename,
                        "file_url": f"/outputs/{filename}",
                        "prompt": req.prompt,
                        "model": model_name
                    }
                elif status in ("failed", "error"):
                    err_msg = s_data.get("error", "Unknown video generation failure")
                    raise HTTPException(status_code=500, detail=f"Generation failed: {err_msg}")

        raise HTTPException(status_code=504, detail="Video rendering timed out. Please check back shortly.")

@app.get("/api/gallery")
async def get_gallery():
    items = []
    for f in sorted(OUTPUTS_DIR.iterdir(), key=os.path.getmtime, reverse=True):
        if f.is_file() and not f.name.startswith("."):
            ext = f.suffix.lower()
            kind = "code" if ext in (".md", ".txt", ".json", ".py", ".js") else ("image" if ext in (".png", ".jpg", ".jpeg", ".webp") else "video")
            items.append({
                "filename": f.name,
                "url": f"/outputs/{f.name}",
                "kind": kind,
                "size_kb": round(f.stat().st_size / 1024, 1),
                "created_at": datetime.fromtimestamp(f.stat().st_mtime).strftime("%b %d, %H:%M")
            })
    return {"items": items}

@app.get("/")
async def root():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "CometAI Studio API is running."}

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
