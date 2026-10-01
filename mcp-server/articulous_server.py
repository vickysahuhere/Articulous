from mcp.server.fastmcp import FastMCP
import subprocess
import tempfile
import os
import sys

# Initialize the FastMCP server
mcp = FastMCP("Articulous Blender Bridge")

import os

WORKING_BLEND = os.path.join(tempfile.gettempdir(), "articulous_working_state.blend")

def run_blender_headless(python_script_content: str) -> str:
    """Helper to run a script in blender headless mode and return output. Persists state via a blend file."""
    blender_executable = "blender" 
    
    # Auto-inject code to load previous state and save new state
    injected_script = f"""
import bpy
import os
import sys

# Catch all output
try:
    if os.path.exists(r'{WORKING_BLEND}'):
        bpy.ops.wm.open_mainfile(filepath=r'{WORKING_BLEND}')
    
{chr(10).join('    ' + line for line in python_script_content.split(chr(10)))}

    bpy.ops.wm.save_mainfile(filepath=r'{WORKING_BLEND}')
except Exception as e:
    import traceback
    print("ARTICULOUS_ERROR:", traceback.format_exc(), file=sys.stderr)
    sys.exit(1)
"""

    with tempfile.NamedTemporaryFile(delete=False, suffix=".py", mode='w', encoding='utf-8') as f:
        f.write(injected_script)
        script_path = f.name
        
    try:
        # Run blender in background mode (-b) and execute the python script (-P)
        result = subprocess.run(
            [blender_executable, "-b", "-P", script_path],
            capture_output=True, text=True, check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error executing Blender Python:\n{e.stderr}\n\nStdout context:\n{e.stdout}"
    except FileNotFoundError:
        return "Error: 'blender' command not found. Ensure Blender is installed and added to your system PATH."
    finally:
        os.remove(script_path)

@mcp.tool()
def articulous_run_blender_script(script: str) -> str:
    """
    Executes arbitrary Python code inside Blender's environment (bpy).
    Use this to create objects, modify the scene, add materials, and add keyframes.
    The script should use print() to output any results you need back.
    """
    return run_blender_headless(script)

@mcp.tool()
def articulous_get_scene_graph() -> str:
    """Returns a JSON string representing the current Blender scene graph (objects, types, locations)."""
    script = '''
import bpy
import json

scene_data = []
for obj in bpy.context.scene.objects:
    scene_data.append({
        "name": obj.name,
        "type": obj.type,
        "location": [obj.location.x, obj.location.y, obj.location.z]
    })
print("---SCENE GRAPH---")
print(json.dumps(scene_data, indent=2))
'''
    return run_blender_headless(script)

@mcp.tool()
def articulous_render_preview(filepath: str) -> str:
    """Renders the current camera view to an image file and returns the status."""
    filepath = filepath.replace("\\", "/")
    script = f'''
import bpy
bpy.context.scene.render.filepath = '{filepath}'
bpy.ops.render.render(write_still=True)
print(f"Render saved successfully to {filepath}")
'''
    return run_blender_headless(script)

@mcp.tool()
def articulous_stitch_frames_to_mp4(frame_directory: str, output_filepath: str, framerate: int = 24) -> str:
    """Stitches a directory of PNG sequence frames into an MP4 video file. Use this if Blender cannot natively export MP4."""
    try:
        import imageio.v3 as iio
        import glob
        import os
        
        frames = sorted(glob.glob(os.path.join(frame_directory, '*.png')))
        if not frames:
            return 'Error: No PNG frames found in directory.'
        
        # Read first frame to ensure dimensions are divisible by 2 (required by standard h264 codecs)
        first_frame = iio.imread(frames[0])
        height, width = first_frame.shape[:2]
        height = height - (height % 2)
        width = width - (width % 2)

        # Write to MP4 (imageio automatically handles downloading a lightweight ffmpeg binary if needed)
        iio.imwrite(output_filepath, 
                   (iio.imread(f)[0:height, 0:width] for f in frames), 
                   extension='.mp4', 
                   fps=framerate)
                   
        return f'Success! Video saved to {output_filepath}'
    except ImportError:
        return 'Error: imageio library is missing. Run: pip install "imageio[ffmpeg]"'
    except Exception as e:
        return f'Error stitching video: {str(e)}'

if __name__ == "__main__":
    mcp.run()
