#!/usr/bin/env python3
"""
CometAPI Multi-Model Generator (Code, Image, and Video)
Works with standard Python 3 (no pip dependencies required).
"""

import os
import sys
import json
import time
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

# 1. Environment & Setup
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

def load_env():
    env_file = BASE_DIR / ".env"
    if env_file.exists():
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ.setdefault(key.strip(), val.strip())

load_env()

API_KEY = os.environ.get("COMET_API_KEY", "").strip()
BASE_URL = os.environ.get("COMET_BASE_URL", "https://api.cometapi.com/v1").rstrip("/")
DEFAULT_CODE_MODEL = os.environ.get("DEFAULT_CODE_MODEL", "gpt-4o")
DEFAULT_IMAGE_MODEL = os.environ.get("DEFAULT_IMAGE_MODEL", "flux-schnell")
DEFAULT_VIDEO_MODEL = os.environ.get("DEFAULT_VIDEO_MODEL", "omni-fast")

def get_headers(content_type="application/json"):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "User-Agent": "Antigravity-CometClient/1.0"
    }
    if content_type:
        headers["Content-Type"] = content_type
    return headers

def make_request(url, data=None, headers=None, method=None):
    if headers is None:
        headers = get_headers()
    
    req_data = None
    if data is not None:
        if isinstance(data, dict):
            req_data = json.dumps(data).encode("utf-8")
        elif isinstance(data, (bytes, str)):
            req_data = data if isinstance(data, bytes) else data.encode("utf-8")

    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        return e.code, err_body
    except urllib.error.URLError as e:
        return 0, str(e.reason)

# 2. Code & Text Generation
def generate_code(prompt: str, model: str = None) -> str:
    model = model or DEFAULT_CODE_MODEL
    print(f"\n[Code Generation] Model: {model}")
    print(f"[Prompt]: {prompt}\n")

    url = f"{BASE_URL}/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are an expert programmer and software architect. Provide clean, well-documented code."},
            {"role": "user", "content": prompt}
        ]
    }

    status, resp_bytes = make_request(url, data=payload)
    if status == 200:
        res = json.loads(resp_bytes.decode("utf-8"))
        content = res["choices"][0]["message"]["content"]
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_file = OUTPUT_DIR / f"code_{timestamp}.md"
        with open(out_file, "w") as f:
            f.write(content)
        
        print("--- Output ---")
        print(content)
        print(f"\n[Saved to]: {out_file}")
        return content
    else:
        print(f"[Error {status}]: {resp_bytes}")
        return ""

# 3. Image Generation
def generate_image(prompt: str, model: str = None, size: str = "1024x1024") -> str:
    model = model or DEFAULT_IMAGE_MODEL
    print(f"\n[Image Generation] Model: {model} | Size: {size}")
    print(f"[Prompt]: {prompt}\n")

    url = f"{BASE_URL}/images/generations"
    payload = {
        "model": model,
        "prompt": prompt,
        "size": size
    }

    status, resp_bytes = make_request(url, data=payload)
    if status == 200:
        res = json.loads(resp_bytes.decode("utf-8"))
        data_item = res.get("data", [{}])[0]
        image_url = data_item.get("url")
        b64_json = data_item.get("b64_json")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_file = OUTPUT_DIR / f"image_{timestamp}.png"

        if image_url:
            print(f"[Downloading image from]: {image_url}")
            img_req = urllib.request.Request(image_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(img_req) as img_resp:
                with open(out_file, "wb") as f:
                    f.write(img_resp.read())
            print(f"[Saved image]: {out_file}")
            return str(out_file)
        elif b64_json:
            import base64
            with open(out_file, "wb") as f:
                f.write(base64.b64decode(b64_json))
            print(f"[Saved image]: {out_file}")
            return str(out_file)
        else:
            print(f"[Response]: {res}")
            return ""
    else:
        print(f"[Error {status}]: {resp_bytes}")
        return ""

# 4. Video Generation
def generate_video(prompt: str, model: str = None, seconds: int = 4, aspect_ratio: str = "16:9", resolution: str = "720p") -> str:
    model = model or DEFAULT_VIDEO_MODEL
    print(f"\n[Video Generation] Model: {model} | {seconds}s | {aspect_ratio} | {resolution}")
    print(f"[Prompt]: {prompt}\n")

    url = f"{BASE_URL}/videos"
    payload = {
        "model": model,
        "prompt": prompt,
        "seconds": seconds,
        "aspect_ratio": aspect_ratio,
        "resolution": resolution
    }

    status, resp_bytes = make_request(url, data=payload)
    if status not in (200, 201, 202):
        print(f"[Error initiating video task {status}]: {resp_bytes}")
        return ""

    res = json.loads(resp_bytes.decode("utf-8"))
    task_id = res.get("task_id") or res.get("id")
    if not task_id:
        print(f"[Warning: No task ID returned]: {res}")
        return ""

    print(f"[Video Task Created] ID: {task_id}")
    print("Waiting for video rendering to complete (polling status)...")

    # Poll status
    status_url = f"{BASE_URL}/videos/{task_id}"
    for attempt in range(60):
        time.sleep(5)
        st_code, st_bytes = make_request(status_url, method="GET")
        if st_code == 200:
            st_res = json.loads(st_bytes.decode("utf-8"))
            current_status = st_res.get("status", "").lower()
            progress = st_res.get("progress", 0)
            print(f"  > Status: {current_status} ({progress}%)")

            if current_status in ("completed", "succeeded", "success"):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                out_file = OUTPUT_DIR / f"video_{timestamp}.mp4"

                # Check if download URL is provided in json or content endpoint
                video_url = st_res.get("url") or st_res.get("video_url")
                if video_url:
                    print(f"[Downloading video from]: {video_url}")
                    with urllib.request.urlopen(video_url) as v_resp:
                        with open(out_file, "wb") as f:
                            f.write(v_resp.read())
                else:
                    # Fetch from content endpoint
                    content_url = f"{BASE_URL}/videos/{task_id}/content"
                    c_code, c_bytes = make_request(content_url, method="GET")
                    if c_code == 200:
                        with open(out_file, "wb") as f:
                            f.write(c_bytes)

                print(f"[Video Complete & Saved]: {out_file}")
                return str(out_file)

            elif current_status in ("failed", "error"):
                print(f"[Video generation failed]: {st_res.get('error', 'Unknown error')}")
                return ""
        else:
            print(f"  [Status Check Warning {st_code}]: {st_bytes}")

    print("[Timeout]: Video generation took longer than expected. Check task ID later.")
    return ""

# 5. Connection Test
def test_connection():
    print(f"\n--- Testing CometAPI Connection ---")
    print(f"Base URL: {BASE_URL}")
    print(f"API Key: {API_KEY[:6]}...{API_KEY[-4:] if len(API_KEY) > 10 else ''}")
    url = f"{BASE_URL}/models"
    status, resp_bytes = make_request(url, method="GET")
    if status == 200:
        models_data = json.loads(resp_bytes.decode("utf-8"))
        models = [m.get("id") for m in models_data.get("data", [])]
        print(f"[SUCCESS] Connected! {len(models)} models available.")
        print(f"Sample models: {', '.join(models[:8])}...")
    else:
        print(f"[Status {status}]: {resp_bytes}")

# 6. CLI Dispatcher
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("""
Usage:
  python3 generator.py test
  python3 generator.py code  "<prompt>" [model_name]
  python3 generator.py image "<prompt>" [model_name]
  python3 generator.py video "<prompt>" [model_name]

Examples:
  python3 generator.py test
  python3 generator.py code  "Write a Python script to scrape hacker news"
  python3 generator.py image "A cyberpunk futuristic city at dusk, 8k resolution" flux-schnell
  python3 generator.py video "Ocean waves splashing on sandy rocks at sunset" omni-fast
""")
        sys.exit(0)

    cmd = sys.argv[1].lower()
    prompt = sys.argv[2] if len(sys.argv) > 2 else ""
    model_override = sys.argv[3] if len(sys.argv) > 3 else None

    if cmd == "test":
        test_connection()
    elif cmd == "code":
        if not prompt:
            print("Please provide a prompt for code generation.")
        else:
            generate_code(prompt, model=model_override)
    elif cmd == "image":
        if not prompt:
            print("Please provide a prompt for image generation.")
        else:
            generate_image(prompt, model=model_override)
    elif cmd == "video":
        if not prompt:
            print("Please provide a prompt for video generation.")
        else:
            generate_video(prompt, model=model_override)
    else:
        print(f"Unknown command '{cmd}'. Use test, code, image, or video.")
