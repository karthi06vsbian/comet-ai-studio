# CometAI Studio 🚀

A modern, high-performance AI Studio web application for generating **Code**, **Images**, and **Videos** using multi-model endpoints (GPT-4o, DeepSeek R1, DeepSeek V3, FLUX 2 Flex, FLUX Dev, Omni Fast).

![CometAI Studio](https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=1200&auto=format&fit=crop&q=80)

---

## ✨ Features

- **💻 Code Architect:** High-speed code synthesis with reasoning support via `GPT-4o`, `DeepSeek R1`, and `DeepSeek V3`.
- **🎨 Vision Canvas:** Photorealistic artwork and design generation with `FLUX 2 Flex`, `FLUX Dev`, and `FLUX 2 Max`.
- **🎬 Cinema Motion:** Text-to-scene video rendering powered by `Omni Fast` (720p HD).
- **📂 Creation Library:** Automatic local history tracking and one-click asset downloads.
- **⚡ Modern Dark Glassmorphism UI:** Built with Tailwind CSS, Plus Jakarta Sans, JetBrains Mono, and Lucide icons.

---

## 🛠️ Tech Stack

- **Backend:** Python FastAPI & Uvicorn (Asynchronous REST API)
- **Frontend:** Vanilla JS, Tailwind CSS, Lucide Icons, Highlight.js, Marked.js
- **Deployment:** Vercel Serverless (Python runtime) & Local CLI

---

## 🚀 Quick Start (Local)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/comet-ai-studio.git
   cd comet-ai-studio
   ```

2. **Configure Environment:**
   Create a `.env` file in the root directory:
   ```bash
   COMET_API_KEY=your_cometapi_key_here
   COMET_BASE_URL=https://api.cometapi.com/v1
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the App:**
   ```bash
   ./start.sh
   # or
   python3 -m uvicorn server:app --host 127.0.0.1 --port 8000 --reload
   ```
   Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser!

---

## 🌐 Deploying to Vercel

1. **Import the project:**
   - Push your code to GitHub.
   - Go to [Vercel Dashboard](https://vercel.com/dashboard) and click **"Add New..." > "Project"**.
   - Select your GitHub repository `comet-ai-studio`.

2. **Set Environment Variables:**
   Under **Settings > Environment Variables**, add:
   - `COMET_API_KEY`: `your_cometapi_key_here`
   - `COMET_BASE_URL`: `https://api.cometapi.com/v1`

3. **Deploy:**
   Click **Deploy**! Vercel will automatically configure the Python serverless function and static assets.
