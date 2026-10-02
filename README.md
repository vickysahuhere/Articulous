# 🎬 Articulous: The Ultimate Autonomous AI Animation Studio

**Articulous** is an advanced AI plugin that turns Google Antigravity into a professional 3D artist, animator, and director. 

Whether you want the AI to secretly build and render a full animated short film in the background, or you want to sit side-by-side with the AI and watch it sculpt in your live Blender window, Articulous handles it all with **100% feature parity**.

---

## 🌟 The Two Modes of Articulous

When you give Articulous a prompt, it will ask you how you want to work:

### 1. Articulous Live (Interactive Mode)
* **What it is:** You open Blender, start the bundled Articulous Live server, and the AI connects directly to your viewport.
* **Why use it:** You can literally watch the AI build, sculpt, and texture your scene in real-time. It has 17 dedicated tools for procedural generation, mesh optimization, and blueprinting.
* **Requirements:** You must have Blender open and click "Start Server".

### 2. Articulous Zero (Headless Render Farm Mode)
* **What it is:** You type a prompt and walk away. The AI invisibly boots Blender in the background, builds the scene, and stitches a final MP4 video.
* **Why use it:** Fully automatic. Zero Blender knowledge required. Thanks to recent updates, Articulous Zero now uses the **exact same 17 advanced tools** as Live Mode! 
* **The GPU Render Engine:** Zero mode features rticulous_render_final, a high-performance system that forcefully disables integrated graphics, locks onto your dedicated NVIDIA GPU, and uses OptiX raytracing for lightning-fast renders.

### 🎬 STORYMODE
If you ask for an animation (e.g. "Create a 30-second short film"), Articulous automatically enters **STORYMODE**. 
1. **The Planner:** The AI mathematically breaks your prompt into a strict frame-by-frame timeline.
2. **The Verifier:** Before rendering, the AI runs a rigorous inspection on the scene. If it forgot to animate the camera, the Verifier fails, and the AI is forced to fix its code before rendering!

---

## 🛠️ Step-by-Step Installation

### Step 1: Install Python Requirements
Open your computer's Terminal (or Command Prompt) and run:
`cmd
pip install mcp "imageio[ffmpeg]"
`

### Step 2: Install the Plugin into Antigravity
1. Open your Terminal and clone the repository:
   `cmd
   git clone https://github.com/vickysahuhere/Articulous.git
   `
2. Move the entire downloaded Articulous folder into your Antigravity plugins directory. On Windows, this is usually:
   C:\Users\YOUR_USERNAME\.gemini\config\plugins\

### Step 3: Tell Windows where Blender is
For Articulous Zero (Headless Mode) to work, it needs to find Blender:
1. Press your **Windows Key**, type **Environment Variables**, and hit Enter.
2. Click **Environment Variables...** at the bottom.
3. In the list, double-click **Path**.
4. Click **New** and paste the folder where your Blender program is installed (e.g., C:\Program Files\Blender Foundation\Blender 4.2).
5. Click **OK** to save.

### Step 4: Install the Live Add-on (For Interactive Mode)
If you want to use the live, real-time mode, you must install the bundled Blender add-on:
1. Open Blender.
2. Go to **Edit > Preferences > Add-ons**.
3. Click **Install...** at the top right, navigate to the Articulous folder you just cloned, select ddon/articulous_live_connector.py, and click **Install Add-on**.
4. **Check the box** next to "Interface: Articulous Live Connector" to enable it.
5. In your 3D Viewport, press **N** to open the side panel, click the **Articulous** tab, and click **Start Server**.

### Step 5: Restart
Completely close and reopen the Antigravity application so it loads the new plugin.

---

## 🚀 How to Use It

1. Open a new chat in Antigravity.
2. Type a message like: 
   > *"Articulous, make a 3D animation of a glowing neon car driving down a street."*
3. The AI will ask if you want to use Live Mode or Zero Mode.
4. **Find your renders:** Articulous automatically saves everything (videos, preview screenshots, and raw .blend files) to Desktop/Articulous_Projects/.
