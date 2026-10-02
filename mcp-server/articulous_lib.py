import bpy
import random
import math

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

