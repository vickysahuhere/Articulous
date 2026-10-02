<div align="center">
  <h1>🎬 Articulous: The Autonomous AI 3D Animation Agent for Blender</h1>
  <p><b>Transform text prompts into high-quality, GPU-rendered 3D animations using Google Antigravity & Model Context Protocol (MCP).</b></p>
  
  <!-- SEO Badges -->
  <img src="https://img.shields.io/badge/Blender-3.0%2B-orange?logo=blender" alt="Blender 3.0+ Compatible">
  <img src="https://img.shields.io/badge/AI-Generative_3D-blue?logo=openai" alt="Generative AI 3D">
  <img src="https://img.shields.io/badge/MCP-Ready-brightgreen" alt="Model Context Protocol">
  <img src="https://img.shields.io/badge/GPU-OptiX%20%7C%20CUDA-green?logo=nvidia" alt="NVIDIA GPU Accelerated">
</div>

---

**Articulous** is a groundbreaking autonomous AI plugin that bridges Large Language Models (LLMs) with professional 3D rendering. By integrating Google Antigravity with Blender, Articulous acts as your personal 3D artist, animator, and technical director. 

Whether you need procedural asset generation, AI-assisted sculpting, or a fully automated text-to-video rendering farm, Articulous handles the entire 3D pipeline natively—no Blender experience required.

---

## 🌟 Core Features & AI Modes

Articulous operates in two distinct modes, providing **100% feature parity** across both interactive and headless workflows:

### 1. Articulous Live (Interactive AI Viewport)
* **Real-time AI Sculpting:** Install the bundled Blender add-on and watch the AI manipulate geometry, apply textures, and generate procedural environments directly in your viewport.
* **17 Dedicated AI Tools:** Features advanced MCP tools for AI blueprinting, mesh optimization (decimation), procedural generation (trees, rocks, architecture), and web-texture mapping.
* **Perfect for:** 3D Artists, Game Developers, and Prompt Engineers who want real-time, iterative control over the AI's modeling process.

### 2. Articulous Zero (Headless AI Render Farm)
* **Text-to-Animation:** Type a prompt and walk away. The AI invisibly boots Blender in the background, writes the Python automation scripts, builds the scene, and stitches a final MP4 video.
* **Hardware-Accelerated GPU Engine:** Zero mode utilizes rticulous_render_final, a high-performance system that automatically disables CPU/integrated graphics, locks onto your dedicated NVIDIA GPU (RTX), and uses OptiX AI denoisers for lightning-fast, photorealistic raytracing.

### 🎬 AI Storymode & Timeline Planner
When you request a video animation, Articulous automatically initiates **STORYMODE**. 
1. **Intelligent Scene Planning:** The LLM mathematically breaks your prompt into a strict frame-by-frame timeline.
2. **Automated Verification:** Before rendering, the AI runs a rigorous geometric inspection on the scene. If it forgot to animate the camera or place keyframes, the Verifier rejects the build, forcing the AI to fix its Python scripts autonomously.

---

## 🛠️ Step-by-Step Installation Guide

### Step 1: Install Python Dependencies
Open your Terminal or Command Prompt and run:
`cmd
pip install mcp "imageio[ffmpeg]"
`

### Step 2: Install the Antigravity Plugin
1. Clone this repository to your machine:
   `cmd
   git clone https://github.com/vickysahuhere/Articulous.git
   `
2. Move the downloaded Articulous folder into your Antigravity plugins directory. On Windows, this is usually:
   C:\Users\YOUR_USERNAME\.gemini\config\plugins\

### Step 3: Configure Environment Variables
For Articulous Zero (Headless Mode) to function, it needs your Blender executable path:
1. Press the **Windows Key**, type **Environment Variables**, and hit Enter.
2. Click **Environment Variables...** at the bottom.
3. In the system variables list, double-click **Path**, click **New**, and paste your Blender installation folder (e.g., C:\Program Files\Blender Foundation\Blender 4.2).
4. Click **OK** to save.

### Step 4: Install the Blender Live Add-on (Interactive Mode)
1. Open Blender.
2. Navigate to **Edit > Preferences > Add-ons**.
3. Click **Install...**, navigate to your cloned repo, select ddon/articulous_live_connector.py, and click **Install Add-on**.
4. **Check the box** next to "Interface: Articulous Live Connector".
5. In your 3D Viewport, press **N** to open the side panel, click the **Articulous** tab, and click **Start Server**.

### Step 5: Restart & Run
Completely close and reopen Antigravity to initialize the new MCP tools.

---

## 🚀 How to Generate 3D Art with AI

1. Open a new chat in Google Antigravity.
2. Enter a generative 3D prompt: 
   > *"Articulous, make a 3D animation of a glowing neon cyberpunk car driving down a rainy street."*
3. The AI will ask to confirm your workflow (Live vs. Zero).
4. **Access your Renders:** Articulous automatically organizes all outputs (MP4 videos, preview screenshots, and raw .blend source files) into a generated folder at Desktop/Articulous_Projects/.

---
*Keywords: AI 3D Generation, Text to 3D, Blender Automation, Generative AI Video, Model Context Protocol MCP, Python 3D, LLM Blender Plugin, Autonomous Agent, OptiX Rendering.*
