# 🎬 Articulous: The Autonomous AI Animation Studio

**Articulous** is a plugin that turns your Google Antigravity AI into a professional 3D animator. 

Just type a prompt, and the AI will invisibly open Blender in the background, build the scene, ask for your feedback, and render a final MP4 video in styles like *Genshin Impact*, *Pixar*, or *Cyberpunk*. No Blender experience required!

---

## 🛠️ Step-by-Step Installation

Don't worry if you aren't a programmer! Just follow these 4 simple steps to get set up:

### Step 1: Install the Python Requirements
Open your computer's Terminal (or Command Prompt) and copy-paste this exact command, then hit Enter:
```cmd
pip install mcp "imageio[ffmpeg]"
```
*(This installs the background communication tool and the video stitcher).*

### Step 2: Download and Install the Plugin
1. Open your Terminal (or Command Prompt).
2. Copy-paste this exact command to download the code:
   ```cmd
   git clone https://github.com/vickysahuhere/Articulous.git
   ```
3. Open your File Explorer and find the `Articulous` folder you just downloaded.
4. Move that entire `Articulous` folder into your Antigravity plugins directory. On Windows, this is usually located here:
   `C:\Users\YOUR_USERNAME\.gemini\config\plugins\` 
   *(Note: If the `plugins` folder doesn't exist yet, just create it).*

### Step 3: Tell Windows where Blender is
The AI needs to know where Blender lives on your computer so it can run it in the background:
1. Press your **Windows Key**, type **Environment Variables**, and hit Enter.
2. Click the **Environment Variables...** button at the bottom.
3. In the list, double-click on the one named **Path**.
4. Click **New** and paste the folder where your Blender program is installed. (Usually something like `C:\Program Files\Blender Foundation\Blender 4.2` or wherever you installed Blender 5).
5. Click **OK** on all the windows to save.

### Step 4: Restart
Completely close the Antigravity application and open it again so it loads your new plugin.

---

## 🚀 How to Use It

It is magically simple. 

1. Open a new chat in Antigravity.
2. Type a message like: 
   > *"Articulous, make a 3D animation of a glowing neon car driving down a street."*
3. The AI will immediately take over! It will ask you which art style you want, show you low-poly preview screenshots for your approval, and automatically render the finished MP4 video.
4. **Find your video:** Articulous automatically creates a folder on your computer at `Desktop/Articulous_Projects/`. Inside, you will find a dedicated folder for your animation containing the final `.mp4` video, the preview images, and the raw `.blend` files!
