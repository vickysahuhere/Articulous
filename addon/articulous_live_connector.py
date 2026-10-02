bl_info = {
    "name": "MCP Connector v2",
    "blender": (4, 0, 0),
    "category": "Interface",
    "author": "Antigravity",
    "description": "WebSocket server for MCP integration with Antigravity IDE",
    "version": (2, 1, 0),
}

import bpy
import socket
import threading
import json
import queue
import struct
import hashlib
import base64
import time
import math
import random

# Configuration
HOST = '127.0.0.1'
PORT = 9876

# Queue for thread-safe execution
execution_queue = queue.Queue()

# Global state
server_thread = None
ws_server = None
is_server_running = False

# ============================================================================
# OBJECT LIBRARY (L) - Token-Efficient Pre-built Functions
# ============================================================================
# AI can use these short functions in run_script to save tokens
# Example: L.cube([0,0,0], 2, "MyCube") instead of full bpy.ops code

class L:
    """
    Object Library for token-efficient 3D creation.
    All functions use short parameter names to minimize tokens.
    
    Usage in run_script:
        L.cube([0,0,0], 2)           # Create cube at origin, size 2
        L.table([0,0,0])             # Create table
        L.room([10,10,3])            # Create room
        L.mat(obj, 'METAL', [1,0,0]) # Apply red metal material
        L.scatter(obj, 5, [2,2,0])   # Scatter 5 copies
    """
    
    # ========== PRIMITIVES ==========
    @staticmethod
    def cube(l=[0,0,0], s=1, n=None):
        """Create cube. l=location, s=size, n=name"""
        bpy.ops.mesh.primitive_cube_add(size=s, location=tuple(l))
        o = bpy.context.active_object
        if n: o.name = n
        return o
    
    @staticmethod
    def sphere(l=[0,0,0], r=0.5, seg=16, n=None):
        """Create sphere. l=location, r=radius, seg=segments, n=name"""
        bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=seg, ring_count=seg//2, location=tuple(l))
        o = bpy.context.active_object
        if n: o.name = n
        return o
    
    @staticmethod
    def cyl(l=[0,0,0], r=0.5, h=1, n=None):
        """Create cylinder. l=location, r=radius, h=height, n=name"""
        bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, location=tuple(l))
        o = bpy.context.active_object
        if n: o.name = n
        return o
    
    @staticmethod
    def cone(l=[0,0,0], r=0.5, h=1, n=None):
        """Create cone. l=location, r=radius, h=height, n=name"""
        bpy.ops.mesh.primitive_cone_add(radius1=r, depth=h, location=tuple(l))
        o = bpy.context.active_object
        if n: o.name = n
        return o
    
    @staticmethod
    def plane(l=[0,0,0], s=1, n=None):
        """Create plane. l=location, s=size, n=name"""
        bpy.ops.mesh.primitive_plane_add(size=s, location=tuple(l))
        o = bpy.context.active_object
        if n: o.name = n
        return o
    
    @staticmethod
    def torus(l=[0,0,0], R=1, r=0.25, n=None):
        """Create torus. l=location, R=major radius, r=minor radius, n=name"""
        bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, location=tuple(l))
        o = bpy.context.active_object
        if n: o.name = n
        return o
    
    @staticmethod
    def ico(l=[0,0,0], r=0.5, sub=2, n=None):
        """Create icosphere. l=location, r=radius, sub=subdivisions, n=name"""
        bpy.ops.mesh.primitive_ico_sphere_add(radius=r, subdivisions=sub, location=tuple(l))
        o = bpy.context.active_object
        if n: o.name = n
        return o
    
    # ========== FURNITURE ==========
    @staticmethod
    def table(l=[0,0,0], s=1, n=None):
        """Create table with legs. l=location, s=scale, n=name"""
        # Table top
        bpy.ops.mesh.primitive_cube_add(size=1, location=(l[0], l[1], l[2]+s*0.45))
        top = bpy.context.active_object
        top.name = n or f"Table_{random.randint(1000,9999)}"
        top.scale = (s*1.2, s*0.8, s*0.05)
        
        # Legs
        legs = []
        for x, y in [(-0.5, -0.35), (0.5, -0.35), (-0.5, 0.35), (0.5, 0.35)]:
            bpy.ops.mesh.primitive_cube_add(size=1, location=(l[0]+x*s, l[1]+y*s, l[2]+s*0.2))
            leg = bpy.context.active_object
            leg.scale = (s*0.05, s*0.05, s*0.4)
            legs.append(leg)
        
        # Join all
        bpy.ops.object.select_all(action='DESELECT')
        top.select_set(True)
        for leg in legs:
            leg.select_set(True)
        bpy.context.view_layer.objects.active = top
        bpy.ops.object.join()
        bpy.ops.object.transform_apply(scale=True)
        return top
    
    @staticmethod
    def chair(l=[0,0,0], s=1, n=None):
        """Create simple chair. l=location, s=scale, n=name"""
        # Seat
        bpy.ops.mesh.primitive_cube_add(size=1, location=(l[0], l[1], l[2]+s*0.25))
        seat = bpy.context.active_object
        seat.name = n or f"Chair_{random.randint(1000,9999)}"
        seat.scale = (s*0.4, s*0.4, s*0.05)
        
        # Back
        bpy.ops.mesh.primitive_cube_add(size=1, location=(l[0], l[1]+s*0.18, l[2]+s*0.5))
        back = bpy.context.active_object
        back.scale = (s*0.4, s*0.03, s*0.3)
        
        # Legs
        parts = [back]
        for x, y in [(-0.15, -0.15), (0.15, -0.15), (-0.15, 0.15), (0.15, 0.15)]:
            bpy.ops.mesh.primitive_cube_add(size=1, location=(l[0]+x*s, l[1]+y*s, l[2]+s*0.12))
            leg = bpy.context.active_object
            leg.scale = (s*0.03, s*0.03, s*0.25)
            parts.append(leg)
        
        bpy.ops.object.select_all(action='DESELECT')
        seat.select_set(True)
        for p in parts:
            p.select_set(True)
        bpy.context.view_layer.objects.active = seat
        bpy.ops.object.join()
        bpy.ops.object.transform_apply(scale=True)
        return seat
    
    @staticmethod
    def shelf(l=[0,0,0], s=1, shelves=4, n=None):
        """Create bookshelf. l=location, s=scale, shelves=number of shelves, n=name"""
        parts = []
        
        # Side panels
        for x in [-0.45, 0.45]:
            bpy.ops.mesh.primitive_cube_add(size=1, location=(l[0]+x*s, l[1], l[2]+s))
            side = bpy.context.active_object
            side.scale = (s*0.03, s*0.3, s*1)
            parts.append(side)
        
        # Back panel
        bpy.ops.mesh.primitive_cube_add(size=1, location=(l[0], l[1]+s*0.14, l[2]+s))
        back = bpy.context.active_object
        back.scale = (s*0.9, s*0.02, s*1)
        parts.append(back)
        
        # Shelves
        for i in range(shelves):
            h = l[2] + (i+0.5) * s * 2 / shelves
            bpy.ops.mesh.primitive_cube_add(size=1, location=(l[0], l[1], h))
            sh = bpy.context.active_object
            sh.scale = (s*0.9, s*0.3, s*0.02)
            parts.append(sh)
        
        # Join
        base = parts[0]
        base.name = n or f"Shelf_{random.randint(1000,9999)}"
        bpy.ops.object.select_all(action='DESELECT')
        for p in parts:
            p.select_set(True)
        bpy.context.view_layer.objects.active = base
        bpy.ops.object.join()
        bpy.ops.object.transform_apply(scale=True)
        return base
    
    # ========== SPECIAL OBJECTS ==========
    @staticmethod
    def cauldron(l=[0,0,0], s=1, n=None):
        """Create cauldron/pot. l=location, s=scale, n=name"""
        bpy.ops.mesh.primitive_cylinder_add(radius=s*0.4, depth=s*0.5, location=(l[0], l[1], l[2]+s*0.25))
        pot = bpy.context.active_object
        pot.name = n or f"Cauldron_{random.randint(1000,9999)}"
        return pot
    
    @staticmethod
    def potion(l=[0,0,0], s=0.3, color=None, n=None):
        """Create potion bottle. l=location, s=scale, color=[r,g,b], n=name"""
        # Bottle body
        bpy.ops.mesh.primitive_cylinder_add(radius=s*0.3, depth=s*0.6, location=(l[0], l[1], l[2]+s*0.3))
        body = bpy.context.active_object
        body.name = n or f"Potion_{random.randint(1000,9999)}"
        
        # Neck
        bpy.ops.mesh.primitive_cylinder_add(radius=s*0.1, depth=s*0.3, location=(l[0], l[1], l[2]+s*0.75))
        neck = bpy.context.active_object
        
        # Join
        bpy.ops.object.select_all(action='DESELECT')
        body.select_set(True)
        neck.select_set(True)
        bpy.context.view_layer.objects.active = body
        bpy.ops.object.join()
        
        # Apply glass material if color specified
        if color:
            L.mat(body, 'GLASS', color)
        
        return body
    
    @staticmethod
    def book(l=[0,0,0], s=0.3, n=None):
        """Create book. l=location, s=scale, n=name"""
        bpy.ops.mesh.primitive_cube_add(size=1, location=l)
        book = bpy.context.active_object
        book.name = n or f"Book_{random.randint(1000,9999)}"
        book.scale = (s*0.7, s*1, s*0.1)
        bpy.ops.object.transform_apply(scale=True)
        return book
    
    @staticmethod
    def candle(l=[0,0,0], s=0.2, n=None):
        """Create candle. l=location, s=scale, n=name"""
        bpy.ops.mesh.primitive_cylinder_add(radius=s*0.2, depth=s*1, location=(l[0], l[1], l[2]+s*0.5))
        candle = bpy.context.active_object
        candle.name = n or f"Candle_{random.randint(1000,9999)}"
        return candle
    
    # ========== ENVIRONMENT ==========
    @staticmethod
    def room(size=[10,10,3], l=[0,0,0], n=None):
        """Create room (floor + walls, no ceiling). size=[w,d,h], l=location, n=name"""
        parts = []
        w, d, h = size
        
        # Floor
        bpy.ops.mesh.primitive_plane_add(size=1, location=(l[0], l[1], l[2]))
        floor = bpy.context.active_object
        floor.scale = (w/2, d/2, 1)
        parts.append(floor)
        
        # Walls
        walls_data = [
            ((0, -d/2, h/2), (w, 0.1, h)),  # Back
            ((0, d/2, h/2), (w, 0.1, h)),   # Front
            ((-w/2, 0, h/2), (0.1, d, h)),  # Left
            ((w/2, 0, h/2), (0.1, d, h)),   # Right
        ]
        for pos, scale in walls_data:
            bpy.ops.mesh.primitive_cube_add(size=1, location=(l[0]+pos[0], l[1]+pos[1], l[2]+pos[2]))
            wall = bpy.context.active_object
            wall.scale = (scale[0]/2, scale[1]/2, scale[2]/2)
            parts.append(wall)
        
        # Join
        base = parts[0]
        base.name = n or "Room"
        bpy.ops.object.select_all(action='DESELECT')
        for p in parts:
            p.select_set(True)
        bpy.context.view_layer.objects.active = base
        bpy.ops.object.join()
        bpy.ops.object.transform_apply(scale=True)
        return base
    
    @staticmethod
    def tree(l=[0,0,0], s=2, style='LOW_POLY', n=None):
        """Create tree. l=location, s=size, style=LOW_POLY/REALISTIC, n=name"""
        # Trunk
        bpy.ops.mesh.primitive_cylinder_add(radius=s*0.1, depth=s, location=(l[0], l[1], l[2]+s/2))
        trunk = bpy.context.active_object
        trunk.name = n or f"Tree_{random.randint(1000,9999)}"
        
        # Foliage
        if style == 'LOW_POLY':
            bpy.ops.mesh.primitive_ico_sphere_add(radius=s*0.5, subdivisions=2, location=(l[0], l[1], l[2]+s*1.2))
        else:
            bpy.ops.mesh.primitive_uv_sphere_add(radius=s*0.5, location=(l[0], l[1], l[2]+s*1.2))
        foliage = bpy.context.active_object
        
        # Join
        bpy.ops.object.select_all(action='DESELECT')
        trunk.select_set(True)
        foliage.select_set(True)
        bpy.context.view_layer.objects.active = trunk
        bpy.ops.object.join()
        return trunk
    
    @staticmethod
    def rock(l=[0,0,0], s=1, n=None):
        """Create rock. l=location, s=size, n=name"""
        bpy.ops.mesh.primitive_ico_sphere_add(radius=s/2, subdivisions=2, location=tuple(l))
        rock = bpy.context.active_object
        rock.name = n or f"Rock_{random.randint(1000,9999)}"
        
        # Deform for rock look
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.transform.vertex_random(offset=s*0.15, seed=random.randint(0,9999))
        bpy.ops.object.mode_set(mode='OBJECT')
        
        rock.scale = (1+random.uniform(-0.2,0.2), 1+random.uniform(-0.2,0.2), 0.7+random.uniform(-0.2,0.2))
        bpy.ops.object.transform_apply(scale=True)
        return rock
    
    # ========== MATERIALS ==========
    @staticmethod
    def mat(obj, preset='MATTE', c=[0.8,0.8,0.8]):
        """Apply material. obj=object, preset=MATTE/METAL/GLASS/WOOD/GLOW, c=color[r,g,b]"""
        presets = {
            'MATTE': {'m': 0, 'r': 1},
            'METAL': {'m': 1, 'r': 0.3},
            'GLASS': {'m': 0, 'r': 0, 't': 1},
            'PLASTIC': {'m': 0, 'r': 0.4},
            'WOOD': {'m': 0, 'r': 0.7},
            'GLOW': {'m': 0, 'r': 0.5, 'e': 5},
        }
        cfg = presets.get(preset.upper(), presets['MATTE'])
        
        mat = bpy.data.materials.new(name=f"{obj.name}_{preset}")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs['Base Color'].default_value = (c[0], c[1], c[2], 1)
            bsdf.inputs['Metallic'].default_value = cfg.get('m', 0)
            bsdf.inputs['Roughness'].default_value = cfg.get('r', 0.5)
            if 't' in cfg:
                bsdf.inputs['Transmission Weight'].default_value = cfg['t']
            if 'e' in cfg:
                bsdf.inputs['Emission Strength'].default_value = cfg['e']
        
        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)
        return mat
    
    # ========== UTILITIES ==========
    @staticmethod
    def dup(obj, l=None):
        """Duplicate object. obj=source, l=new location"""
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.duplicate()
        new = bpy.context.active_object
        if l:
            new.location = tuple(l)
        return new
    
    @staticmethod
    def scatter(obj, n=5, area=[2,2,0], seed=None):
        """Scatter copies. obj=source, n=count, area=[x,y,z] spread, seed=random seed"""
        if seed:
            random.seed(seed)
        copies = []
        for i in range(n):
            new = L.dup(obj, [
                obj.location.x + random.uniform(-area[0], area[0]),
                obj.location.y + random.uniform(-area[1], area[1]),
                obj.location.z + random.uniform(-area[2], area[2]),
            ])
            new.rotation_euler[2] = random.uniform(0, math.pi*2)
            scale = random.uniform(0.8, 1.2)
            new.scale = (scale, scale, scale)
            copies.append(new)
        return copies
    
    @staticmethod
    def clear():
        """Delete all mesh objects in scene."""
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()
    
    @staticmethod
    def move(obj, l):
        """Move object. obj=object, l=[x,y,z]"""
        obj.location = tuple(l)
        return obj
    
    @staticmethod
    def rot(obj, r):
        """Rotate object. obj=object, r=[x,y,z] in degrees"""
        obj.rotation_euler = (math.radians(r[0]), math.radians(r[1]), math.radians(r[2]))
        return obj
    
    @staticmethod
    def scale(obj, s):
        """Scale object. obj=object, s=scale or [x,y,z]"""
        if isinstance(s, (int, float)):
            obj.scale = (s, s, s)
        else:
            obj.scale = tuple(s)
        return obj

# ============================================================================
# WebSocket Server Implementation
# ============================================================================

class SimpleWebSocket:
    """Minimal WebSocket server using stdlib only."""
    
    GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
    
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = None
        self.client = None
        self.running = False
        
    def start(self):
        self.running = True
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.settimeout(1.0)
        self.socket.bind((self.host, self.port))
        self.socket.listen(1)
        print(f"[MCP] Server listening on ws://{self.host}:{self.port}")
        
    def stop(self):
        self.running = False
        if self.client:
            try: self.client.close()
            except: pass
        if self.socket:
            try: self.socket.close()
            except: pass
        print("[MCP] Server stopped")
        
    def accept(self):
        if not self.socket or not self.running:
            return False
        try:
            self.client, addr = self.socket.accept()
            self.client.settimeout(1.0)
            print(f"[MCP] Client connected from {addr}")
            return self._handshake()
        except socket.timeout:
            return False
        except:
            return False
            
    def _handshake(self):
        try:
            data = self.client.recv(4096).decode('utf-8')
            if not data:
                return False
            headers = {}
            for line in data.split('\r\n')[1:]:
                if ': ' in line:
                    k, v = line.split(': ', 1)
                    headers[k.lower()] = v
            if headers.get('upgrade', '').lower() != 'websocket':
                return False
            key = headers.get('sec-websocket-key', '')
            accept = base64.b64encode(hashlib.sha1((key + self.GUID).encode()).digest()).decode()
            response = f"HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: {accept}\r\n\r\n"
            self.client.send(response.encode())
            return True
        except:
            return False
            
    def recv(self):
        if not self.client or not self.running:
            return None
        try:
            header = self.client.recv(2)
            if len(header) < 2:
                return None
            opcode = header[0] & 0x0F
            masked = (header[1] & 0x80) >> 7
            length = header[1] & 0x7F
            if length == 126:
                length = struct.unpack('>H', self.client.recv(2))[0]
            elif length == 127:
                length = struct.unpack('>Q', self.client.recv(8))[0]
            mask = self.client.recv(4) if masked else b'\x00\x00\x00\x00'
            payload = b''
            while len(payload) < length:
                chunk = self.client.recv(min(4096, length - len(payload)))
                if not chunk:
                    break
                payload += chunk
            if masked:
                payload = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
            if opcode == 0x8:
                self.client.close()
                self.client = None
                return None
            elif opcode == 0x1:
                return payload.decode('utf-8')
            return None
        except socket.timeout:
            return None
        except:
            self.client = None
            return None
            
    def send(self, msg):
        if not self.client:
            return False
        try:
            data = msg.encode('utf-8')
            length = len(data)
            if length <= 125:
                frame = bytes([0x81, length]) + data
            elif length <= 65535:
                frame = bytes([0x81, 126]) + struct.pack('>H', length) + data
            else:
                frame = bytes([0x81, 127]) + struct.pack('>Q', length) + data
            self.client.send(frame)
            return True
        except:
            return False

# ============================================================================
# Command Handlers
# ============================================================================

def handle_create_primitive(params):
    """Create a 3D primitive object."""
    primitive_type = params.get("primitive_type", "CUBE").upper()
    name = params.get("name")
    size = params.get("size", 1.0)
    location = tuple(params.get("location", [0, 0, 0]))
    rotation = params.get("rotation", [0, 0, 0])
    segments = params.get("segments", 32)
    
    primitive_ops = {
        "CUBE": lambda: bpy.ops.mesh.primitive_cube_add(size=size, location=location),
        "SPHERE": lambda: bpy.ops.mesh.primitive_uv_sphere_add(radius=size/2, segments=segments, ring_count=segments//2, location=location),
        "CYLINDER": lambda: bpy.ops.mesh.primitive_cylinder_add(radius=size/2, depth=size, vertices=segments, location=location),
        "CONE": lambda: bpy.ops.mesh.primitive_cone_add(radius1=size/2, depth=size, vertices=segments, location=location),
        "PLANE": lambda: bpy.ops.mesh.primitive_plane_add(size=size, location=location),
        "TORUS": lambda: bpy.ops.mesh.primitive_torus_add(major_radius=size/2, minor_radius=size/6, location=location),
        "MONKEY": lambda: bpy.ops.mesh.primitive_monkey_add(size=size, location=location),
        "CIRCLE": lambda: bpy.ops.mesh.primitive_circle_add(radius=size/2, vertices=segments, location=location),
        "GRID": lambda: bpy.ops.mesh.primitive_grid_add(size=size, location=location),
    }
    
    if primitive_type not in primitive_ops:
        return {"error": f"Unknown primitive: {primitive_type}", "available": list(primitive_ops.keys())}
    
    primitive_ops[primitive_type]()
    obj = bpy.context.active_object
    if name:
        obj.name = name
    if rotation != [0, 0, 0]:
        obj.rotation_euler = rotation
    # Compact: {n:"Cube",t:"MESH",l:[0,0,0]}
    return {"n": obj.name, "t": obj.type, "l": [round(v, 2) for v in obj.location]}

def handle_export_model(params):
    """Export model(s) to file format."""
    import os
    
    object_names = params.get("object_names", [])
    format_type = params.get("format", "GLB").upper()
    output_path = params.get("output_path", "")
    apply_modifiers = params.get("apply_modifiers", True)
    
    if not output_path:
        return {"error": "output_path is required"}
    
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    bpy.ops.object.select_all(action='DESELECT')
    objects_to_export = []
    
    if object_names:
        for name in object_names:
            obj = bpy.data.objects.get(name)
            if obj:
                obj.select_set(True)
                objects_to_export.append(obj)
    else:
        for obj in bpy.data.objects:
            if obj.visible_get() and obj.type == 'MESH':
                obj.select_set(True)
                objects_to_export.append(obj)
    
    if not objects_to_export:
        return {"error": "No objects to export"}
    
    if format_type == "FBX":
        bpy.ops.export_scene.fbx(filepath=output_path, use_selection=True, use_mesh_modifiers=apply_modifiers)
    elif format_type in ["GLB", "GLTF"]:
        bpy.ops.export_scene.gltf(filepath=output_path, use_selection=True, export_apply=apply_modifiers,
                                   export_format='GLB' if format_type == "GLB" else 'GLTF_SEPARATE')
    elif format_type == "OBJ":
        bpy.ops.wm.obj_export(filepath=output_path, export_selected_objects=True, apply_modifiers=apply_modifiers)
    else:
        return {"error": f"Unsupported format: {format_type}"}
    
    file_size_kb = round(os.path.getsize(output_path) / 1024, 2) if os.path.exists(output_path) else 0
    # Compact: {p:"path.glb",cnt:3,kb:120}
    return {"p": output_path, "cnt": len(objects_to_export), "kb": file_size_kb}

def handle_apply_texture(params):
    """Apply image texture to an object."""
    import os
    
    object_name = params.get("object_name", "")
    texture_path = params.get("texture_path", "")
    uv_project = params.get("uv_project", "AUTO")
    tiling = params.get("tiling", [1, 1])
    
    if not object_name:
        return {"error": "object_name is required"}
    if not texture_path or not os.path.exists(texture_path):
        return {"error": f"Texture file not found: {texture_path}"}
    
    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {"error": f"Object not found: {object_name}"}
    if obj.type != 'MESH':
        return {"error": f"Object must be MESH, got {obj.type}"}
    
    # Generate UVs if needed
    uv_generated = False
    if not obj.data.uv_layers:
        uv_generated = True
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        if uv_project in ["AUTO", "SMART"]:
            bpy.ops.uv.smart_project()
        elif uv_project == "BOX":
            bpy.ops.uv.cube_project()
        elif uv_project == "SPHERE":
            bpy.ops.uv.sphere_project()
        elif uv_project == "CYLINDER":
            bpy.ops.uv.cylinder_project()
        bpy.ops.object.mode_set(mode='OBJECT')
    
    # Create material with texture
    mat_name = f"{object_name}_textured"
    mat = bpy.data.materials.new(name=mat_name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (400, 0)
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    tex_image = nodes.new('ShaderNodeTexImage')
    tex_image.location = (-400, 0)
    tex_image.image = bpy.data.images.load(texture_path)
    mapping = nodes.new('ShaderNodeMapping')
    mapping.location = (-600, 0)
    mapping.inputs['Scale'].default_value[0] = tiling[0]
    mapping.inputs['Scale'].default_value[1] = tiling[1]
    tex_coord = nodes.new('ShaderNodeTexCoord')
    tex_coord.location = (-800, 0)
    
    links.new(tex_coord.outputs['UV'], mapping.inputs['Vector'])
    links.new(mapping.outputs['Vector'], tex_image.inputs['Vector'])
    links.new(tex_image.outputs['Color'], bsdf.inputs['Base Color'])
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)
    
    # Compact: {n:"Cube",m:"CubeMat",uv:1}
    return {"n": object_name, "m": mat.name, "uv": 1 if uv_generated else 0}

def handle_set_material(params):
    """Apply material preset to an object."""
    object_name = params.get("object_name", "")
    preset = params.get("preset", "MATTE").upper()
    color = params.get("color", [0.8, 0.8, 0.8])
    roughness = params.get("roughness")
    metallic = params.get("metallic")
    
    if not object_name:
        return {"error": "object_name is required"}
    
    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {"error": f"Object not found: {object_name}"}
    
    presets = {
        "METALLIC": {"metallic": 1.0, "roughness": 0.3},
        "PLASTIC": {"metallic": 0.0, "roughness": 0.4},
        "GLASS": {"metallic": 0.0, "roughness": 0.0, "transmission": 1.0},
        "WOOD": {"metallic": 0.0, "roughness": 0.7},
        "STONE": {"metallic": 0.0, "roughness": 0.8},
        "FABRIC": {"metallic": 0.0, "roughness": 0.9},
        "EMISSIVE": {"metallic": 0.0, "roughness": 0.5, "emission": 5.0},
        "MATTE": {"metallic": 0.0, "roughness": 1.0},
    }
    
    if preset not in presets:
        return {"error": f"Unknown preset: {preset}", "available": list(presets.keys())}
    
    config = presets[preset].copy()
    if roughness is not None:
        config["roughness"] = roughness
    if metallic is not None:
        config["metallic"] = metallic
    
    mat_name = f"{object_name}_{preset.lower()}"
    mat = bpy.data.materials.new(name=mat_name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (color[0], color[1], color[2], 1.0)
        bsdf.inputs['Metallic'].default_value = config.get("metallic", 0.0)
        bsdf.inputs['Roughness'].default_value = config.get("roughness", 0.5)
        if "transmission" in config:
            bsdf.inputs['Transmission Weight'].default_value = config["transmission"]
        if "emission" in config:
            bsdf.inputs['Emission Strength'].default_value = config["emission"]
    
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)
    
    # Compact: {n:"Cube",m:"CubeMat",p:"GLASS"}
    return {"n": object_name, "m": mat.name, "p": preset}

def handle_generate_procedural(params):
    """Generate procedural objects like trees, rocks, terrain."""
    import random
    import math
    
    proc_type = params.get("proc_type", "TREE").upper()
    style = params.get("style", "LOW_POLY").upper()
    size = params.get("size", 2.0)
    seed = params.get("seed", random.randint(0, 99999))
    location = tuple(params.get("location", [0, 0, 0]))
    complexity = params.get("complexity", "MEDIUM").upper()
    
    random.seed(seed)
    
    # Complexity settings
    complexity_map = {
        "SIMPLE": {"branches": 3, "segments": 4, "rocks": 3},
        "MEDIUM": {"branches": 6, "segments": 8, "rocks": 6},
        "COMPLEX": {"branches": 12, "segments": 16, "rocks": 12},
    }
    settings = complexity_map.get(complexity, complexity_map["MEDIUM"])
    
    try:
        if proc_type == "TREE":
            # Create trunk
            bpy.ops.mesh.primitive_cylinder_add(
                radius=size * 0.1,
                depth=size,
                vertices=settings["segments"],
                location=(location[0], location[1], location[2] + size/2)
            )
            trunk = bpy.context.active_object
            trunk.name = f"Tree_{seed}"
            
            # Create foliage (icosphere for low-poly, UV sphere for realistic)
            foliage_radius = size * 0.6
            if style == "LOW_POLY":
                bpy.ops.mesh.primitive_ico_sphere_add(
                    radius=foliage_radius,
                    subdivisions=2,
                    location=(location[0], location[1], location[2] + size * 1.2)
                )
            else:
                bpy.ops.mesh.primitive_uv_sphere_add(
                    radius=foliage_radius,
                    segments=16,
                    ring_count=12,
                    location=(location[0], location[1], location[2] + size * 1.2)
                )
            foliage = bpy.context.active_object
            foliage.name = f"Foliage_{seed}"
            
            # Join objects
            bpy.ops.object.select_all(action='DESELECT')
            trunk.select_set(True)
            foliage.select_set(True)
            bpy.context.view_layer.objects.active = trunk
            bpy.ops.object.join()
            
            obj = bpy.context.active_object
            verts = len(obj.data.vertices)
            faces = len(obj.data.polygons)
            # Compact: {n:"Tree_1",t:"TREE",v:256,f:128}
            return {"n": obj.name, "t": proc_type, "v": verts, "f": faces}
            
        elif proc_type == "ROCK":
            # Create rock using displaced icosphere
            if style == "LOW_POLY":
                bpy.ops.mesh.primitive_ico_sphere_add(
                    radius=size/2,
                    subdivisions=2,
                    location=location
                )
            else:
                bpy.ops.mesh.primitive_ico_sphere_add(
                    radius=size/2,
                    subdivisions=3,
                    location=location
                )
            
            rock = bpy.context.active_object
            rock.name = f"Rock_{seed}"
            
            # Apply random displacement for rock-like appearance
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.transform.vertex_random(offset=size * 0.15, seed=seed)
            bpy.ops.object.mode_set(mode='OBJECT')
            
            # Random scale for variety
            rock.scale = (
                1 + random.uniform(-0.3, 0.3),
                1 + random.uniform(-0.3, 0.3),
                0.7 + random.uniform(-0.2, 0.2)
            )
            bpy.ops.object.transform_apply(scale=True)
            
            verts = len(rock.data.vertices)
            faces = len(rock.data.polygons)
            return {"n": rock.name, "t": proc_type, "v": verts, "f": faces}
            
        elif proc_type == "TERRAIN":
            # Create terrain grid
            subdivisions = settings["segments"] * 2
            bpy.ops.mesh.primitive_grid_add(
                size=size * 2,
                x_subdivisions=subdivisions,
                y_subdivisions=subdivisions,
                location=location
            )
            terrain = bpy.context.active_object
            terrain.name = f"Terrain_{seed}"
            
            # Apply random displacement for terrain
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.transform.vertex_random(offset=size * 0.2, seed=seed)
            bpy.ops.object.mode_set(mode='OBJECT')
            
            # Smooth the terrain slightly
            bpy.ops.object.shade_smooth()
            
            verts = len(terrain.data.vertices)
            faces = len(terrain.data.polygons)
            return {"n": terrain.name, "t": proc_type, "v": verts, "f": faces}
            
        elif proc_type == "BUILDING":
            # Create simple building
            bpy.ops.mesh.primitive_cube_add(
                size=size,
                location=(location[0], location[1], location[2] + size/2)
            )
            building = bpy.context.active_object
            building.name = f"Building_{seed}"
            
            # Scale for building proportions
            building.scale[2] = 1.5 + random.uniform(0, 1)
            bpy.ops.object.transform_apply(scale=True)
            
            # Add roof
            roof_height = size * 0.3
            bpy.ops.mesh.primitive_cone_add(
                radius1=size * 0.75,
                depth=roof_height,
                vertices=4,
                location=(location[0], location[1], location[2] + size * building.scale[2] + roof_height/2)
            )
            roof = bpy.context.active_object
            roof.rotation_euler[2] = math.radians(45)
            
            # Join
            bpy.ops.object.select_all(action='DESELECT')
            building.select_set(True)
            roof.select_set(True)
            bpy.context.view_layer.objects.active = building
            bpy.ops.object.join()
            
            obj = bpy.context.active_object
            verts = len(obj.data.vertices)
            faces = len(obj.data.polygons)
            return {"n": obj.name, "t": proc_type, "v": verts, "f": faces}
        
        else:
            return {"error": f"Unknown procedural type: {proc_type}"}
            
    except Exception as e:
        return {"error": str(e)}

def handle_optimize_mesh(params):
    """Optimize mesh by reducing polygon count."""
    object_name = params.get("object_name", "")
    target_ratio = params.get("target_ratio", 0.5)
    preserve_uvs = params.get("preserve_uvs", True)
    preserve_bounds = params.get("preserve_bounds", True)
    symmetry = params.get("symmetry", False)
    
    if not object_name:
        return {"error": "object_name is required"}
    
    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {"error": f"Object not found: {object_name}"}
    if obj.type != 'MESH':
        return {"error": f"Object must be MESH, got {obj.type}"}
    
    try:
        # Store original counts
        original_verts = len(obj.data.vertices)
        original_faces = len(obj.data.polygons)
        
        # Add decimate modifier
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        
        modifier = obj.modifiers.new(name="Decimate", type='DECIMATE')
        modifier.ratio = target_ratio
        modifier.use_symmetry = symmetry
        
        if preserve_bounds:
            modifier.decimate_type = 'COLLAPSE'
        
        # Apply modifier
        bpy.ops.object.modifier_apply(modifier="Decimate")
        
        # Get new counts
        new_verts = len(obj.data.vertices)
        new_faces = len(obj.data.polygons)
        
        reduction = round((1 - new_faces / original_faces) * 100, 1) if original_faces > 0 else 0
        
        # Compact: {n:"Cube",before:{v:1000,f:500},after:{v:500,f:250},pct:50}
        return {
            "n": object_name,
            "before": {"v": original_verts, "f": original_faces},
            "after": {"v": new_verts, "f": new_faces},
            "pct": reduction
        }
        
    except Exception as e:
        return {"error": str(e)}

def handle_render_preview(params):
    """Render a preview image of the scene."""
    import os
    import time as time_module
    import math
    
    output_path = params.get("output_path", "")
    resolution = params.get("resolution", [512, 512])
    camera_angle = params.get("camera_angle", "ISOMETRIC")
    samples = params.get("samples", 32)
    transparent = params.get("transparent", False)
    
    if not output_path:
        return {"error": "output_path is required"}
    
    # Ensure directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    try:
        start_time = time_module.time()
        
        scene = bpy.context.scene
        
        # Create or get camera
        cam_data = bpy.data.cameras.new(name="RenderCam")
        cam = bpy.data.objects.new("RenderCam", cam_data)
        bpy.context.collection.objects.link(cam)
        
        # Position camera based on angle
        distance = 10
        if camera_angle == "FRONT":
            cam.location = (0, -distance, 0)
            cam.rotation_euler = (math.radians(90), 0, 0)
        elif camera_angle == "TOP":
            cam.location = (0, 0, distance)
            cam.rotation_euler = (0, 0, 0)
        elif camera_angle == "SIDE":
            cam.location = (distance, 0, 0)
            cam.rotation_euler = (math.radians(90), 0, math.radians(90))
        elif camera_angle == "ISOMETRIC":
            cam.location = (distance * 0.7, -distance * 0.7, distance * 0.7)
            cam.rotation_euler = (math.radians(55), 0, math.radians(45))
        else:  # CURRENT - use active camera
            if scene.camera:
                bpy.data.objects.remove(cam)
                cam = scene.camera
            else:
                cam.location = (distance * 0.7, -distance * 0.7, distance * 0.7)
                cam.rotation_euler = (math.radians(55), 0, math.radians(45))
        
        scene.camera = cam
        
        # Set render settings
        scene.render.resolution_x = resolution[0]
        scene.render.resolution_y = resolution[1]
        scene.render.filepath = output_path
        scene.render.image_settings.file_format = 'PNG' if output_path.lower().endswith('.png') else 'JPEG'
        
        # Set transparent background
        scene.render.film_transparent = transparent
        
        # Set samples (for Cycles or Eevee)
        if scene.render.engine == 'CYCLES':
            scene.cycles.samples = samples
        elif scene.render.engine == 'BLENDER_EEVEE_NEXT':
            scene.eevee.taa_render_samples = samples
        
        # Render
        bpy.ops.render.render(write_still=True)
        
        # Cleanup temp camera if we created one
        if camera_angle != "CURRENT" and cam.name == "RenderCam":
            bpy.data.objects.remove(cam)
            bpy.data.cameras.remove(cam_data)
        
        render_time = round(time_module.time() - start_time, 2)
        file_size_kb = round(os.path.getsize(output_path) / 1024, 2) if os.path.exists(output_path) else 0
        
        # Compact: {p:"out.png",res:[512,512],t:1.5,kb:45}
        return {"p": output_path, "res": resolution, "t": render_time, "kb": file_size_kb}
        
    except Exception as e:
        return {"error": str(e)}

def handle_bake_textures(params):
    """Bake texture maps for game engine export."""
    import os
    import time as time_module
    
    object_name = params.get("object_name", "")
    bake_types = params.get("bake_types", ["DIFFUSE", "NORMAL", "AO"])
    output_dir = params.get("output_dir", "")
    resolution = params.get("resolution", 1024)
    samples = params.get("samples", 64)
    margin = params.get("margin", 4)
    highpoly_source = params.get("highpoly_source")
    cage_extrusion = params.get("cage_extrusion", 0.1)
    
    if not object_name:
        return {"error": "object_name is required"}
    if not output_dir:
        return {"error": "output_dir is required"}
    
    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {"error": f"Object not found: {object_name}"}
    if obj.type != 'MESH':
        return {"error": f"Object must be MESH, got {obj.type}"}
    
    # Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Check for UVs
    if not obj.data.uv_layers:
        return {"error": f"Object {object_name} has no UV map. Run UV unwrap first."}
    
    try:
        start_time = time_module.time()
        baked_maps = []
        
        # Set render engine to Cycles (required for baking)
        original_engine = bpy.context.scene.render.engine
        bpy.context.scene.render.engine = 'CYCLES'
        bpy.context.scene.cycles.samples = samples
        bpy.context.scene.cycles.bake_type = 'COMBINED'
        
        # Select target object
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        
        # Get or create bake material with image texture node
        if not obj.data.materials:
            mat = bpy.data.materials.new(name=f"{object_name}_bake_mat")
            obj.data.materials.append(mat)
        else:
            mat = obj.data.materials[0]
        
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        
        # Bake type mapping
        bake_type_map = {
            'COMBINED': 'COMBINED',
            'DIFFUSE': 'DIFFUSE',
            'NORMAL': 'NORMAL',
            'AO': 'AO',
            'ROUGHNESS': 'ROUGHNESS',
            'METALLIC': 'EMIT',  # Metallic needs special handling
            'EMIT': 'EMIT',
            'SHADOW': 'SHADOW',
        }
        
        for bake_type in bake_types:
            # Create new image for this bake type
            img_name = f"{object_name}_{bake_type.lower()}"
            
            # Set appropriate bit depth and color space
            if bake_type in ['NORMAL']:
                color_space = 'Non-Color'
                use_float = True
            elif bake_type in ['ROUGHNESS', 'METALLIC', 'AO']:
                color_space = 'Non-Color'
                use_float = False
            else:
                color_space = 'sRGB'
                use_float = False
            
            # Create image
            img = bpy.data.images.new(
                name=img_name,
                width=resolution,
                height=resolution,
                alpha=False,
                float_buffer=use_float
            )
            img.colorspace_settings.name = color_space
            
            # Create or get image texture node
            tex_node = None
            for node in nodes:
                if node.type == 'TEX_IMAGE' and node.name == 'BakeTarget':
                    tex_node = node
                    break
            if not tex_node:
                tex_node = nodes.new('ShaderNodeTexImage')
                tex_node.name = 'BakeTarget'
            
            tex_node.image = img
            
            # Make sure the texture node is selected (required for baking)
            for node in nodes:
                node.select = False
            tex_node.select = True
            nodes.active = tex_node
            
            # Set bake settings
            blender_bake_type = bake_type_map.get(bake_type, 'COMBINED')
            bpy.context.scene.render.bake.margin = margin
            bpy.context.scene.render.bake.use_clear = True
            
            # Special handling for different bake types
            if bake_type == 'NORMAL' and highpoly_source:
                # High poly to low poly normal baking
                highpoly = bpy.data.objects.get(highpoly_source)
                if highpoly:
                    bpy.context.scene.render.bake.use_selected_to_active = True
                    bpy.context.scene.render.bake.cage_extrusion = cage_extrusion
                    highpoly.select_set(True)
            else:
                bpy.context.scene.render.bake.use_selected_to_active = False
            
            # Perform bake
            if bake_type == 'DIFFUSE':
                bpy.context.scene.render.bake.use_pass_direct = False
                bpy.context.scene.render.bake.use_pass_indirect = False
                bpy.context.scene.render.bake.use_pass_color = True
                bpy.ops.object.bake(type='DIFFUSE')
            elif bake_type == 'NORMAL':
                bpy.ops.object.bake(type='NORMAL')
            elif bake_type == 'AO':
                bpy.ops.object.bake(type='AO')
            elif bake_type == 'ROUGHNESS':
                bpy.ops.object.bake(type='ROUGHNESS')
            elif bake_type == 'EMIT':
                bpy.ops.object.bake(type='EMIT')
            elif bake_type == 'SHADOW':
                bpy.ops.object.bake(type='SHADOW')
            else:
                bpy.ops.object.bake(type='COMBINED')
            
            # Save image
            output_path = os.path.join(output_dir, f"{img_name}.png")
            img.filepath_raw = output_path
            img.file_format = 'PNG'
            img.save()
            
            baked_maps.append(output_path)
            
            # Clear image from memory
            bpy.data.images.remove(img)
        
        # Restore render engine
        bpy.context.scene.render.engine = original_engine
        
        total_time = round(time_module.time() - start_time, 2)
        
        # Compact: {n:"Cube",maps:["a.png"],res:1024,t:5.2}
        return {"n": object_name, "maps": baked_maps, "res": resolution, "t": total_time}
        
    except Exception as e:
        # Restore render engine on error
        bpy.context.scene.render.engine = original_engine if 'original_engine' in dir() else 'BLENDER_EEVEE_NEXT'
        return {"error": str(e)}

def execute_command(request):
    """Execute command with compact responses for token efficiency."""
    try:
        cmd = request.get('type', '')
        params = request.get('params', {})
        rid = request.get('id', 'x')  # short id key
        
        # Helper for compact responses
        def ok(d): return {"id": rid, "ok": 1, "d": d}
        def err(c, m): return {"id": rid, "ok": 0, "e": {"c": c, "m": m[:100]}}
        
        if cmd == 'ping':
            return ok({"pong": 1})
            
        elif cmd == 'get_version':
            return ok({
                "bl": bpy.app.version_string,
                "addon": ".".join(map(str, bl_info["version"])),
                "sc": bpy.context.scene.name
            })
            
        elif cmd == 'get_scene_info':
            limit = min(params.get('limit', 20), 100)
            offset = params.get('offset', 0)
            verbosity = params.get('verbosity', 'standard')
            objs = []
            total = 0
            for obj in bpy.data.objects:
                total += 1
                if total <= offset:
                    continue
                if len(objs) >= limit:
                    continue
                if verbosity == 'minimal':
                    objs.append({"n": obj.name})
                elif verbosity == 'detailed':
                    info = {"n": obj.name, "t": obj.type,
                            "l": [round(v, 2) for v in obj.location]}
                    if obj.type == 'MESH' and obj.data:
                        info["v"] = len(obj.data.vertices)
                        info["f"] = len(obj.data.polygons)
                    objs.append(info)
                else:
                    objs.append({"n": obj.name, "t": obj.type,
                                 "l": [round(v, 1) for v in obj.location]})
            return ok({"objs": objs, "pg": {"off": offset, "lim": limit, "tot": total, "more": total > offset + limit}})
            
        elif cmd == 'run_script':
            script = params.get('script', '')
            if not script:
                return err("NO_SCRIPT", "No script")
            local_vars = {}
            exec(script, {
                "bpy": bpy, "L": L, "math": math, "random": random,
                "__builtins__": __builtins__
            }, local_vars)
            out = local_vars.get('result', 'ok')
            return ok({"out": out})
        
        elif cmd == 'create_primitive':
            r = handle_create_primitive(params)
            return err("PRIM", r["error"]) if "error" in r else ok(r)
        
        elif cmd == 'export_model':
            r = handle_export_model(params)
            return err("EXPORT", r["error"]) if "error" in r else ok(r)
        
        elif cmd == 'apply_texture':
            r = handle_apply_texture(params)
            return err("TEX", r["error"]) if "error" in r else ok(r)
        
        elif cmd == 'set_material':
            r = handle_set_material(params)
            return err("MAT", r["error"]) if "error" in r else ok(r)
        
        elif cmd == 'generate_procedural':
            r = handle_generate_procedural(params)
            return err("PROC", r["error"]) if "error" in r else ok(r)
        
        elif cmd == 'optimize_mesh':
            r = handle_optimize_mesh(params)
            return err("OPT", r["error"]) if "error" in r else ok(r)
        
        elif cmd == 'render_preview':
            r = handle_render_preview(params)
            return err("RENDER", r["error"]) if "error" in r else ok(r)
        
        elif cmd == 'bake_textures':
            r = handle_bake_textures(params)
            return err("BAKE", r["error"]) if "error" in r else ok(r)
            
        else:
            return err("UNK", f"Unknown: {cmd}")
            
    except Exception as e:
        return {"id": request.get('id', 'x'), "ok": 0, "e": {"c": "ERR", "m": str(e)[:100]}}

# ============================================================================
# Server Loop
# ============================================================================

def server_loop():
    global ws_server, is_server_running
    
    ws_server = SimpleWebSocket(HOST, PORT)
    ws_server.start()
    
    while is_server_running:
        if not ws_server.client:
            ws_server.accept()
            continue
            
        msg = ws_server.recv()
        if msg:
            result = {}
            def run_job():
                try:
                    req = json.loads(msg)
                    result['data'] = execute_command(req)
                except:
                    result['data'] = {"id": "err", "success": False, "error": {"code": "JSON", "message": "Invalid JSON"}}
            execution_queue.put(run_job)
            for _ in range(100):
                if 'data' in result:
                    ws_server.send(json.dumps(result['data'], separators=(',', ':')))
                    break
                time.sleep(0.1)
                
    ws_server.stop()

def process_queue():
    while not execution_queue.empty():
        try:
            job = execution_queue.get_nowait()
            job()
        except:
            pass
    return 0.1

# ============================================================================
# Operators & UI
# ============================================================================

class MCP_OT_StartServer(bpy.types.Operator):
    """Start the MCP Server"""
    bl_idname = "mcp.start_server"
    bl_label = "Start Server"
    
    def execute(self, context):
        global server_thread, is_server_running
        if not is_server_running:
            is_server_running = True
            server_thread = threading.Thread(target=server_loop, daemon=True)
            server_thread.start()
            if not bpy.app.timers.is_registered(process_queue):
                bpy.app.timers.register(process_queue)
            self.report({'INFO'}, f"MCP Server Started on ws://{HOST}:{PORT}")
        return {'FINISHED'}

class MCP_OT_StopServer(bpy.types.Operator):
    """Stop the MCP Server"""
    bl_idname = "mcp.stop_server"
    bl_label = "Stop Server"
    
    def execute(self, context):
        global is_server_running
        if is_server_running:
            is_server_running = False
            if bpy.app.timers.is_registered(process_queue):
                bpy.app.timers.unregister(process_queue)
            self.report({'INFO'}, "MCP Server Stopped")
        return {'FINISHED'}

class MCP_PT_Panel(bpy.types.Panel):
    """MCP Panel in 3D View Sidebar"""
    bl_label = "MCP Connector v2"
    bl_idname = "MCP_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "MCP"

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        if is_server_running:
            box.label(text="Status: Running", icon='CHECKBOX_HLT')
            box.label(text=f"ws://{HOST}:{PORT}")
            box.operator("mcp.stop_server", icon='CANCEL')
        else:
            box.label(text="Status: Stopped", icon='CHECKBOX_DEHLT')
            box.operator("mcp.start_server", icon='PLAY')
        box = layout.box()
        box.label(text="Version: 2.0.0")

# ============================================================================
# Registration
# ============================================================================

classes = (MCP_OT_StartServer, MCP_OT_StopServer, MCP_PT_Panel)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    global is_server_running
    is_server_running = False
    if bpy.app.timers.is_registered(process_queue):
        bpy.app.timers.unregister(process_queue)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
