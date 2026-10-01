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

# Force GPU Compute (OPTIX/CUDA)
try:
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'OPTIX'
    bpy.context.scene.cycles.device = 'GPU'
    for d in prefs.get_devices()[0]:
        d.use = True
except Exception:
    try:
        prefs = bpy.context.preferences.addons['cycles'].preferences
        prefs.compute_device_type = 'CUDA'
        bpy.context.scene.cycles.device = 'GPU'
        for d in prefs.get_devices()[0]:
            d.use = True
    except Exception:
        pass

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

@mcp.tool()
def articulous_create_project_folder(project_name: str) -> str:
    """
    Creates a dedicated project folder on the user's Desktop to store all renders, frames, and final videos for this project.
    Returns the absolute path to the newly created project folder.
    Always use this tool at the very beginning of a project!
    """
    import os
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    base_dir = os.path.join(desktop, "Articulous_Projects")
    
    # Create a safe folder name
    safe_name = "".join([c for c in project_name if c.isalpha() or c.isdigit() or c in (' ', '-', '_')]).rstrip()
    safe_name = safe_name.replace(" ", "_")
    
    project_dir = os.path.join(base_dir, safe_name)
    
    os.makedirs(project_dir, exist_ok=True)
    return project_dir

@mcp.tool()
def articulous_add_cinematic_camera_rig(target_name: str, radius: float = 10.0, height: float = 5.0) -> str:
    """Creates a cinematic camera rig. It spawns a circular Bezier curve around the origin, attaches a camera to it, and tracks the camera to the specified target object."""
    script = f'''
import bpy
import math

# Find target
target = bpy.data.objects.get("{target_name}")
if not target:
    print(f"Error: Could not find target object '{target_name}'")
else:
    # Create circular path
    bpy.ops.curve.primitive_bezier_circle_add(radius={radius}, location=(0, 0, {height}))
    path = bpy.context.active_object
    
    # Create camera
    bpy.ops.object.camera_add(location=(0, {radius}, {height}))
    cam = bpy.context.active_object
    bpy.context.scene.camera = cam
    
    # Constrain camera to path
    constraint = cam.constraints.new('FOLLOW_PATH')
    constraint.target = path
    constraint.use_curve_follow = True
    
    # Animate path
    path.data.path_duration = bpy.context.scene.frame_end
    
    # Track to target
    track = cam.constraints.new('TRACK_TO')
    track.target = target
    track.track_axis = 'TRACK_NEGATIVE_Z'
    track.up_axis = 'UP_Y'
    
    print("Cinematic Camera Rig added successfully.")
'''
    return run_blender_headless(script)

@mcp.tool()
def articulous_apply_compositing_effects(bloom: bool = True, lens_distortion: bool = True) -> str:
    """Automatically wires up Blender's compositor to add professional cinematic effects like Bloom (Glare) and Chromatic Aberration."""
    script = f'''
import bpy
bpy.context.scene.use_nodes = True
tree = bpy.context.scene.node_tree
links = tree.links

# Clear default nodes
for n in tree.nodes: tree.nodes.remove(n)

render_layers = tree.nodes.new('CompositorNodeRLayers')
composite = tree.nodes.new('CompositorNodeComposite')
last_node = render_layers

if {bloom}:
    glare = tree.nodes.new('CompositorNodeGlare')
    glare.glare_type = 'FOG_GLOW'
    glare.mix = -0.8
    links.new(last_node.outputs[0], glare.inputs[0])
    last_node = glare

if {lens_distortion}:
    lens = tree.nodes.new('CompositorNodeLensdist')
    lens.inputs['Dispersion'].default_value = 0.05
    lens.inputs['Projector'].default_value = True
    links.new(last_node.outputs[0], lens.inputs[0])
    last_node = lens

links.new(last_node.outputs[0], composite.inputs[0])
print("Cinematic compositing applied.")
'''
    return run_blender_headless(script)

@mcp.tool()
def articulous_fix_floating_objects() -> str:
    """Uses the physics engine to calculate gravity for 20 frames, letting all objects fall naturally to the floor, then bakes their resting positions. Prevents floating objects."""
    script = '''
import bpy

# Add floor if missing
if "CollisionFloor" not in bpy.data.objects:
    bpy.ops.mesh.primitive_plane_add(size=100, location=(0,0,0))
    floor = bpy.context.active_object
    floor.name = "CollisionFloor"
    bpy.ops.rigidbody.object_add()
    floor.rigid_body.type = 'PASSIVE'
    floor.hide_render = True

# Add active physics to all meshes above Z=0
for obj in bpy.context.scene.objects:
    if obj.type == 'MESH' and obj.name != "CollisionFloor" and obj.location.z > 0.1:
        bpy.context.view_layer.objects.active = obj
        bpy.ops.rigidbody.object_add()
        obj.rigid_body.type = 'ACTIVE'

# Bake to frame 20 and apply transforms
bpy.context.scene.frame_set(20)
for obj in bpy.context.scene.objects:
    if obj.type == 'MESH' and obj.rigid_body and obj.rigid_body.type == 'ACTIVE':
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.visual_transform_apply()
        bpy.ops.rigidbody.object_remove()

bpy.context.scene.frame_set(1)
print("Gravity settled. Floating objects fixed.")
'''
    return run_blender_headless(script)

if __name__ == "__main__":
    mcp.run()
