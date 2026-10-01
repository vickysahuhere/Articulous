# Articulous: Autonomous Agentic Animation Studio

Articulous is a plugin for Google Antigravity that transforms your AI assistant into a full-pipeline 3D Animator connected directly to Blender.

## Installation

1. **Install Dependencies**: The MCP server requires the `mcp` Python package.
   Run: `pip install -r requirements.txt`

2. **Ensure Blender is in PATH**: The plugin launches Blender in the background. You must ensure `blender` is accessible from your command line / terminal. 
   *(On Windows, add `C:\Program Files\Blender Foundation\Blender X.X` to your Environment Variables PATH).*

3. **Install the Plugin**: 
   Move this entire `articulous` folder into your Antigravity global plugins directory:
   `~/.gemini/config/plugins/articulous`

4. **Restart Antigravity**.

## Usage

Simply open a new Antigravity conversation and type:
> "Make a 3D animation of a bouncing ball."

Articulous will take over, design the scene, run introspection checks, ask for your approval on blockouts, and render the final animation autonomously using your existing Antigravity account limits!
