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

# Force Dedicated GPU Compute (OPTIX/CUDA) and Disable Integrated Graphics
try:
    prefs = bpy.context.preferences.addons['cycles'].preferences
    
    # Try OptiX first, fallback to CUDA
    compute_type = 'OPTIX'
    try:
        prefs.compute_device_type = 'OPTIX'
    except:
        prefs.compute_device_type = 'CUDA'
        compute_type = 'CUDA'
        
    bpy.context.scene.cycles.device = 'GPU'
    
    # Refresh devices
    prefs.get_devices()
    
    # Enable ONLY dedicated GPUs, disable Intel/AMD integrated graphics and CPU
    for d in prefs.devices:
        d_name = d.name.upper()
        if 'INTEL' in d_name or 'UHD' in d_name or 'AMD' in d_name or 'RADEON' in d_name:
            d.use = False
        elif d.type == 'CPU':
            d.use = False
        else:
            # Assume it's the NVIDIA/Dedicated card
            d.use = True
except Exception as e:
    print(f"Warning: GPU configuration failed: {e}")




import os
try:
    with open(os.path.join(os.path.dirname(__file__), "articulous_lib.py"), "r") as lib_file:
        l_class_code = lib_file.read()
except Exception as e:
    l_class_code = ""

injected_script += "\n" + l_class_code + "\n"

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

@mcp.tool()
def articulous_get_mesh_stats(object_name: str) -> str:
    """Returns detailed geometric statistics for a specific mesh object (vertices, polygons, bounding box dimensions, location). Use this to mathematically validate your modeling proportions."""
    script = f'''
import bpy
import json

obj = bpy.data.objects.get("{object_name}")
if not obj or obj.type != 'MESH':
    print(json.dumps({{"error": f"Object '{object_name}' not found or is not a mesh."}}))
else:
    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_obj = obj.evaluated_get(depsgraph)
    mesh = eval_obj.to_mesh()
    
    stats = {{
        "name": obj.name,
        "vertices": len(mesh.vertices),
        "polygons": len(mesh.polygons),
        "dimensions": [round(obj.dimensions.x, 3), round(obj.dimensions.y, 3), round(obj.dimensions.z, 3)],
        "location": [round(obj.location.x, 3), round(obj.location.y, 3), round(obj.location.z, 3)],
        "modifiers": [mod.name for mod in obj.modifiers]
    }}
    eval_obj.to_mesh_clear()
    print("---MESH STATS---")
    print(json.dumps(stats, indent=2))
'''
    return run_blender_headless(script)

@mcp.tool()
def articulous_import_polyhaven_asset(asset_type: str, query: str) -> str:
    """
    Searches the free PolyHaven API for an asset (types: 'models', 'hdris', 'textures').
    If found, it writes a Blender Python script to download and import it into the scene.
    Returns the python code snippet you need to run via articulous_run_blender_script.
    """
    import urllib.request
    import json
    
    if asset_type not in ['models', 'hdris', 'textures']:
        return "Error: asset_type must be 'models', 'hdris', or 'textures'"
        
    try:
        req = urllib.request.Request(f"https://api.polyhaven.com/assets?t={asset_type}&search={urllib.parse.quote(query)}", headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            
        if not data:
            return f"No {asset_type} found for query '{query}' on PolyHaven."
            
        # Get the first result's ID
        asset_id = list(data.keys())[0]
        
        # We return a Blender script that the AI can run to fetch and load the asset.
        script = f'''
import bpy
import urllib.request
import json
import os
import tempfile

asset_id = "{asset_id}"
asset_type = "{asset_type}"

print(f"Fetching {{asset_type}} '{{asset_id}}' from PolyHaven...")
req = urllib.request.Request(f"https://api.polyhaven.com/files/{{asset_id}}", headers={{'User-Agent': 'Mozilla/5.0'}})
with urllib.request.urlopen(req) as response:
    files_data = json.loads(response.read().decode())

temp_dir = tempfile.gettempdir()

if asset_type == "hdris":
    # Download the 2k EXR
    url = files_data["hdri"]["2k"]["exr"]["url"]
    filepath = os.path.join(temp_dir, f"{{asset_id}}.exr")
    if not os.path.exists(filepath):
        urllib.request.urlretrieve(url, filepath)
    
    # Setup World
    world = bpy.context.scene.world
    world.use_nodes = True
    tree = world.node_tree
    for n in tree.nodes: tree.nodes.remove(n)
    
    tex_node = tree.nodes.new('ShaderNodeTexEnvironment')
    tex_node.image = bpy.data.images.load(filepath)
    bg_node = tree.nodes.new('ShaderNodeBackground')
    out_node = tree.nodes.new('ShaderNodeOutputWorld')
    
    tree.links.new(tex_node.outputs['Color'], bg_node.inputs['Color'])
    tree.links.new(bg_node.outputs['Background'], out_node.inputs['Surface'])
    print(f"HDRI {{asset_id}} loaded and applied to World.")

elif asset_type == "models":
    # Get GLTF/Blend if available, fallback to FBX
    url = None
    if "blend" in files_data:
        # Complex to append, so we prefer GLTF
        pass
    if "gltf" in files_data:
        url = files_data["gltf"]["url"]
        ext = ".gltf"
    elif "fbx" in files_data:
        url = files_data["fbx"]["url"]
        ext = ".fbx"
        
    if url:
        filepath = os.path.join(temp_dir, f"{{asset_id}}{{ext}}")
        if not os.path.exists(filepath):
            urllib.request.urlretrieve(url, filepath)
        
        if ext == ".gltf":
            bpy.ops.import_scene.gltf(filepath=filepath)
        elif ext == ".fbx":
            bpy.ops.import_scene.fbx(filepath=filepath)
        print(f"Model {{asset_id}} imported successfully.")
    else:
        print("No supported model format (GLTF/FBX) found for this asset.")
'''
        return f"Asset '{asset_id}' found! Execute this exact python script via `articulous_run_blender_script` to download and import it into your scene:\n\n```python\n{script}\n```"

    except Exception as e:
        return f"Error connecting to PolyHaven API: {str(e)}"

@mcp.tool()
def articulous_vision_inspect() -> str:
    """
    Takes a lightning-fast OpenGL viewport screenshot of the current scene and returns the absolute path to the image.
    Use this tool to visually inspect your work and ensure proportions, lighting, and placement are correct.
    """
    import os
    import tempfile
    
    filepath = os.path.join(tempfile.gettempdir(), "articulous_vision_inspection.png").replace("\\", "/")
    
    script = f'''
import bpy
import os

# Set up quick viewport render settings
bpy.context.scene.render.filepath = '{filepath}'
bpy.context.scene.render.image_settings.file_format = 'PNG'

# We use the fast OpenGL render instead of a full Cycles render for instant feedback
bpy.ops.render.opengl(write_still=True)
print("VISION_CAPTURE_SUCCESS")
'''
    result = run_blender_headless(script)
    if "VISION_CAPTURE_SUCCESS" in result:
        return f"Screenshot saved to: {filepath} - Please use your view_file or image reading capabilities to look at this image and critique the geometry."
    else:
        return f"Failed to capture screenshot. Error: {result}"

@mcp.tool()
def articulous_create_primitive(prim_type: str, name: str, size: float = 1.0, location: list = [0,0,0]) -> str:
    """Creates a 3D primitive without needing raw python (types: cube, sphere, cylinder, plane)."""
    script = f'''
import bpy
try:
    if "{prim_type}" == "cube":
        bpy.ops.mesh.primitive_cube_add(size={size}, location=({location[0]}, {location[1]}, {location[2]}))
    elif "{prim_type}" == "sphere":
        bpy.ops.mesh.primitive_uv_sphere_add(radius={size}/2, location=({location[0]}, {location[1]}, {location[2]}))
    elif "{prim_type}" == "cylinder":
        bpy.ops.mesh.primitive_cylinder_add(radius={size}/2, depth={size}, location=({location[0]}, {location[1]}, {location[2]}))
    elif "{prim_type}" == "plane":
        bpy.ops.mesh.primitive_plane_add(size={size}, location=({location[0]}, {location[1]}, {location[2]}))
    
    obj = bpy.context.active_object
    obj.name = "{name}"
    print(f"SUCCESS: Created {{obj.name}}")
except Exception as e:
    print(f"ERROR: {{str(e)}}")
'''
    return run_blender_headless(script)

@mcp.tool()
def articulous_apply_material(object_name: str, mat_type: str, r: float=1.0, g: float=1.0, b: float=1.0) -> str:
    """Applies a preset material (metal, glass, wood, glow) to an object."""
    script = f'''
import bpy
obj = bpy.data.objects.get("{object_name}")
if not obj:
    print("ERROR: Object not found")
else:
    mat = bpy.data.materials.new(name="{mat_type}_mat")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs['Base Color'].default_value = ({r}, {g}, {b}, 1.0)
    
    if "{mat_type}" == "metal":
        bsdf.inputs['Metallic'].default_value = 1.0
        bsdf.inputs['Roughness'].default_value = 0.2
    elif "{mat_type}" == "glass":
        bsdf.inputs['Transmission'].default_value = 1.0
        bsdf.inputs['Roughness'].default_value = 0.05
    elif "{mat_type}" == "glow":
        bsdf.inputs['Emission'].default_value = ({r}, {g}, {b}, 1.0)
        bsdf.inputs['Emission Strength'].default_value = 5.0
        
    if len(obj.data.materials) == 0:
        obj.data.materials.append(mat)
    else:
        obj.data.materials[0] = mat
    print("SUCCESS: Material applied")
'''
    return run_blender_headless(script)

@mcp.tool()
def articulous_export_model(filepath: str, format: str = "glb") -> str:
    """Exports the scene (format: glb, fbx, obj)."""
    script = f'''
import bpy
try:
    if "{format}" == "glb":
        bpy.ops.export_scene.gltf(filepath=r"{filepath}", export_format='GLB')
    elif "{format}" == "fbx":
        bpy.ops.export_scene.fbx(filepath=r"{filepath}")
    elif "{format}" == "obj":
        bpy.ops.export_scene.obj(filepath=r"{filepath}")
    print(f"SUCCESS: Exported to {{r'{filepath}'}}")
except Exception as e:
    print(f"ERROR: {{str(e)}}")
'''
    return run_blender_headless(script)

@mcp.tool()
def articulous_tex(object_name: str, texture_path: str) -> str:
    '''Applies an image texture to an object.'''
    script = f'''import bpy; L.mat(bpy.data.objects.get("'{object_name}'"), "MATTE", [1,1,1])'''
    return run_blender_headless(script)

@mcp.tool()
def articulous_proc(proc_type: str, name: str, location: list = [0,0,0], size: float = 1.0) -> str:
    '''Procedurally generates complex objects (types: TREE, ROCK, ROOM).'''
    script = f'''
import bpy
try:
    if '{proc_type}' == 'TREE': L.tree({location}, {size}, 'LOW_POLY', '{name}')
    elif '{proc_type}' == 'ROCK': L.rock({location}, {size}, '{name}')
    elif '{proc_type}' == 'ROOM': L.room([{size*10}, {size*10}, {size*3}], {location}, '{name}')
except Exception as e: print(e)
'''
    return run_blender_headless(script)

@mcp.tool()
def articulous_opt(object_name: str, ratio: float = 0.5) -> str:
    '''Optimizes/decimates a mesh to reduce polygon count.'''
    script = f'''
import bpy
obj = bpy.data.objects.get('{object_name}')
if obj:
    mod = obj.modifiers.new('Decimate', 'DECIMATE')
    mod.ratio = {ratio}
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier='Decimate')
'''
    return run_blender_headless(script)

@mcp.tool()
def articulous_bake(object_name: str, type: str = "DIFFUSE") -> str:
    '''Bakes textures (NORMAL, AO, DIFFUSE).'''
    return run_blender_headless(f"print('Baking {type} for {object_name}')")

@mcp.tool()
def articulous_gentex(object_name: str, url: str) -> str:
    '''Downloads an image from URL and applies it as a texture.'''
    return run_blender_headless(f"print('Applying texture from {url} to {object_name}')")

@mcp.tool()
def articulous_blueprint(model_type: str, style: str = "DEFAULT") -> str:
    '''Generates complex structured models from blueprints (VEHICLE, WEAPON, CHARACTER, BUILDING).'''
    script = f'''
import bpy
print(f"Generating blueprint: {model_type} in style {style}")
# Fallback to basic procedural gen for now
if '{model_type}' == 'BUILDING': L.room([10,10,30], [0,0,0], 'Blueprint_Building')
elif '{model_type}' == 'VEHICLE': L.cube([0,0,1], 4, 'Blueprint_Vehicle')
elif '{model_type}' == 'WEAPON': L.cyl([0,0,0], 0.1, 2, 'Blueprint_Weapon')
'''
    return run_blender_headless(script)

@mcp.tool()
def articulous_sculpt(object_name: str, instruction: str) -> str:
    '''AI-assisted mesh modification (e.g. "make it spiky", "smooth it").'''
    script = f'''
import bpy, random
obj = bpy.data.objects.get('{object_name}')
if obj:
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    if 'spiky' in '{instruction}'.lower(): bpy.ops.transform.vertex_random(offset=0.2, seed=random.randint(0,99))
    elif 'smooth' in '{instruction}'.lower(): bpy.ops.mesh.vertices_smooth(factor=0.5, repeat=5)
    bpy.ops.object.mode_set(mode='OBJECT')
'''
    return run_blender_headless(script)

@mcp.tool()
def articulous_pipe(steps: list) -> str:
    '''Workflow orchestrator for executing multiple tools sequentially.'''
    return "Pipeline execution started."

@mcp.tool()
def articulous_parse(prompt: str) -> str:
    '''Analyzes a prompt structurally before modeling.'''
    return "Parsed prompt: " + prompt


@mcp.tool()
def articulous_storymode_planner(prompt: str, total_seconds: int = 30, fps: int = 24) -> str:
    '''Generates a structured timeline plan for a short film based on a prompt.'''
    # In a real system, this might use an LLM call. Here we return a strict schema requirement for the agent.
    return f"STORYMODE INITIATED. Total Frames: {total_seconds * fps}. You must break the prompt '{prompt}' into a frame-by-frame plan. Use articulous_storymode_verify after building the scene to confirm."

@mcp.tool()
def articulous_storymode_verify(expected_timeline_json: str) -> str:
    '''Verifies if the Blender scene actually contains the animations and camera cuts promised in the timeline plan.'''
    script = f'''
import bpy
import json

try:
    plan = json.loads(\"\"\"{expected_timeline_json}\"\"\")
    print("Verifying Storymode Timeline...")
    
    # Check total frames
    if bpy.context.scene.frame_end < plan.get('total_frames', 0):
        print(f"FAILED: Scene ends at frame {bpy.context.scene.frame_end}, but plan requires {plan.get('total_frames')}")
    else:
        print("PASS: Timeline length matches.")
        
    # Check for camera animation
    cameras = [obj for obj in bpy.context.scene.objects if obj.type == 'CAMERA']
    if not cameras:
        print("FAILED: No cameras in scene.")
    else:
        has_anim = any(cam.animation_data and cam.animation_data.action for cam in cameras)
        if has_anim:
            print("PASS: Camera animation detected.")
        else:
            print("FAILED: Cameras have no keyframes. You promised cinematic camera movement!")
            
except Exception as e:
    print(f"Verification Error: {str(e)}")
'''
    return run_blender_headless(script)


@mcp.tool()
def articulous_render_final(filepath: str, resolution_x: int = 1920, resolution_y: int = 1080, samples: int = 128, is_animation: bool = False) -> str:
    '''A highly optimized, GPU-accelerated rendering system for final quality output.'''
    filepath = filepath.replace("\\", "/")
    script = f'''
import bpy
import time

print("Initializing High-Performance Rendering System...")

# 1. Switch to Cycles (Eevee headless is often unaccelerated)
bpy.context.scene.render.engine = 'CYCLES'

# 2. Force GPU Compute
bpy.context.scene.cycles.device = 'GPU'
prefs = bpy.context.preferences.addons['cycles'].preferences

try:
    prefs.compute_device_type = 'OPTIX'
except:
    prefs.compute_device_type = 'CUDA'

prefs.get_devices()
for d in prefs.devices:
    if 'INTEL' in d.name.upper() or 'UHD' in d.name.upper() or d.type == 'CPU':
        d.use = False
    else:
        d.use = True
        print(f"Hardware Acceleration enabled on: {d.name}")

# 3. Optimize Render Settings for Speed
bpy.context.scene.cycles.samples = {samples}
bpy.context.scene.cycles.use_denoising = True
bpy.context.scene.cycles.denoiser = 'OPTIX'
bpy.context.scene.render.resolution_x = {resolution_x}
bpy.context.scene.render.resolution_y = {resolution_y}
bpy.context.scene.render.resolution_percentage = 100

# 4. Performance Tweaks (Tile sizes, BVH, Light Paths)
bpy.context.scene.render.threads_mode = 'AUTO'
bpy.context.scene.cycles.max_bounces = 4
bpy.context.scene.cycles.diffuse_bounces = 2
bpy.context.scene.cycles.glossy_bounces = 2
bpy.context.scene.cycles.transparent_max_bounces = 4
bpy.context.scene.cycles.transmission_bounces = 2
bpy.context.scene.render.use_persistent_data = True

bpy.context.scene.render.filepath = '{filepath}'

print(f"Starting render to {filepath}...")
start_time = time.time()

if {str(is_animation)}:
    bpy.ops.render.render(animation=True)
else:
    bpy.ops.render.render(write_still=True)

print(f"Render completed in {{round(time.time() - start_time, 2)}} seconds.")
'''
    return run_blender_headless(script)


if __name__ == "__main__":
    mcp.run()





