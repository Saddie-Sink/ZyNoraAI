import bpy
import math
import os
import sys
from mathutils import Vector

# ============================================================
# ZYNORA ARCHITECTURAL BLENDER GENERATOR
# Blender 4.x
# Generates house model and renders FIVE exterior views.
# ============================================================

# Read optional args passed after "--"
argv = sys.argv
args = []
if "--" in argv:
    args = argv[argv.index("--") + 1:]

OUTPUT_DIR = os.path.abspath(args[0]) if len(args) > 0 else os.path.abspath("./public/renders")
HOUSE_W = float(args[1]) if len(args) > 1 else 30.0
HOUSE_D = float(args[2]) if len(args) > 2 else 19.0
GROUND_H = float(args[3]) if len(args) > 3 else 3.4
UPPER_H = float(args[4]) if len(args) > 4 else 3.2

RENDER_X = 1280
RENDER_Y = 720

# ------------------------------------------------------------
# RESET
# ------------------------------------------------------------

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

# ============================================================
# MATERIALS
# ============================================================

def make_mat(name, color, roughness=0.5, metallic=0.0):
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metallic
    return mat

WHITE = make_mat("Warm White Plaster", (0.78, 0.76, 0.70), 0.58)
PURE_WHITE = make_mat("Tower White", (0.91, 0.89, 0.84), 0.48)
CREAM = make_mat("Cream", (0.72, 0.68, 0.58), 0.60)
TERRACOTTA = make_mat("Terracotta", (0.45, 0.18, 0.08), 0.55)
TERRACOTTA_LIGHT = make_mat("Terracotta Light", (0.60, 0.28, 0.12), 0.50)
WOOD = make_mat("Natural Wood", (0.30, 0.16, 0.075), 0.48)
WOOD_LIGHT = make_mat("Wood Highlight", (0.47, 0.27, 0.11), 0.52)
ANTHRACITE = make_mat("Anthracite", (0.045, 0.055, 0.060), 0.34, 0.15)
METAL = make_mat("Dark Metal", (0.12, 0.14, 0.14), 0.30, 0.65)
GLASS = make_mat("Dark Glass", (0.025, 0.075, 0.10), 0.12, 0.15)
GROUND = make_mat("Grass", (0.12, 0.27, 0.08), 0.90)
ROAD = make_mat("Road", (0.045, 0.050, 0.055), 0.95)
PAVEMENT = make_mat("Pavement", (0.46, 0.46, 0.42), 0.85)

LED = bpy.data.materials.new("Warm LED")
LED.use_nodes = True
led_nodes = LED.node_tree.nodes
led_bsdf = led_nodes.get("Principled BSDF")
if led_bsdf:
    led_bsdf.inputs["Base Color"].default_value = (1.0, 0.30, 0.05, 1)
    if "Emission Color" in led_bsdf.inputs:
        led_bsdf.inputs["Emission Color"].default_value = (1.0, 0.18, 0.03, 1)
    elif "Emission" in led_bsdf.inputs:
        led_bsdf.inputs["Emission"].default_value = (1.0, 0.18, 0.03, 1)
    if "Emission Strength" in led_bsdf.inputs:
        led_bsdf.inputs["Emission Strength"].default_value = 7.0

TREE_TRUNK = make_mat("Tree Trunk", (0.15, 0.07, 0.025), 0.95)
TREE_GREEN = make_mat("Tree Leaves", (0.05, 0.25, 0.035), 0.95)

# ============================================================
# BASIC HELPERS
# ============================================================

def apply_bevel(obj, amount=0.04, segments=2):
    try:
        bevel = obj.modifiers.new(name="Architectural Edge", type="BEVEL")
        bevel.width = amount
        bevel.segments = segments
        bevel.limit_method = "ANGLE"
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=bevel.name)
    except Exception:
        pass

def box(name, location, scale, material, bevel=0.03):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = (scale[0] / 2, scale[1] / 2, scale[2] / 2)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if material:
        obj.data.materials.append(material)
    if bevel:
        apply_bevel(obj, bevel)
    return obj

def cylinder(name, location, radius, depth, material, vertices=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    if material:
        obj.data.materials.append(material)
    return obj

# ============================================================
# WINDOW SYSTEM
# ============================================================

def front_window(name, x, z, width, height, projection=0.15, frame=True, grille=True):
    y = -HOUSE_D / 2 - projection
    box(name + "_glass", (x, y, z), (width, 0.10, height), GLASS, 0.01)

    if frame:
        frame_t = 0.16
        box(name + "_left_frame", (x - width / 2, y - 0.07, z), (frame_t, 0.25, height + 0.20), PURE_WHITE, 0.025)
        box(name + "_right_frame", (x + width / 2, y - 0.07, z), (frame_t, 0.25, height + 0.20), PURE_WHITE, 0.025)
        box(name + "_top_frame", (x, y - 0.07, z + height / 2), (width + 0.25, 0.25, frame_t), PURE_WHITE, 0.025)
        box(name + "_bottom_frame", (x, y - 0.07, z - height / 2), (width + 0.25, 0.25, frame_t), PURE_WHITE, 0.025)

    if grille:
        divisions = 2
        for i in range(1, divisions):
            gx = x - width / 2 + width * i / divisions
            box(name + "_vertical_" + str(i), (gx, y - 0.15, z), (0.055, 0.08, height), ANTHRACITE, 0.01)

def side_window(name, side, y, z, width, height):
    x = HOUSE_W / 2 + 0.06 if side == "right" else -HOUSE_W / 2 - 0.06
    box(name + "_glass", (x, y, z), (0.10, width, height), GLASS, 0.01)
    t = 0.14
    box(name + "_top", (x, y, z + height / 2), (0.22, width + 0.2, t), PURE_WHITE)
    box(name + "_bottom", (x, y, z - height / 2), (0.22, width + 0.2, t), PURE_WHITE)
    box(name + "_left", (x, y - width / 2, z), (0.22, t, height), PURE_WHITE)
    box(name + "_right", (x, y + width / 2, z), (0.22, t, height), PURE_WHITE)

# ============================================================
# HOUSE MASSING
# ============================================================

def build_main_structure():
    # Ground floor main mass
    box("GROUND_MAIN", (0, 0, GROUND_H / 2), (HOUSE_W, HOUSE_D, GROUND_H), WHITE, 0.07)

    # Upper floor central mass
    box("UPPER_MAIN", (-1.5, 0.5, GROUND_H + UPPER_H / 2), (24.5, 15.5, UPPER_H), WHITE, 0.07)

    # TALL LEFT TOWER
    tower_w = 5.4
    tower_d = 5.5
    tower_h = GROUND_H + UPPER_H + 2.1
    box("TALL_WHITE_TOWER", (-HOUSE_W / 2 + tower_w / 2 + 0.7, 2.5, tower_h / 2), (tower_w, tower_d, tower_h), PURE_WHITE, 0.05)

    # REAR / RIGHT UPPER BLOCK
    box("UPPER_RIGHT_BLOCK", (6.2, 2.0, GROUND_H + UPPER_H / 2), (9.0, 11.5, UPPER_H), CREAM, 0.06)

    # TERRACE SLABS
    box("GROUND_ROOF_SLUB", (0, 0, GROUND_H), (HOUSE_W + 0.7, HOUSE_D + 0.7, 0.30), PURE_WHITE, 0.03)
    box("UPPER_ROOF", (-1.5, 0.5, GROUND_H + UPPER_H), (25.0, 16.0, 0.35), PURE_WHITE, 0.03)
    box("TOWER_ROOF", (-HOUSE_W / 2 + tower_w / 2 + 0.7, 2.5, tower_h), (tower_w + 0.35, tower_d + 0.35, 0.32), PURE_WHITE, 0.03)

# ============================================================
# TERRACOTTA BANDS
# ============================================================

def build_terracotta_features():
    box("TERRACOTTA_FRONT_BAND", (2.0, -HOUSE_D / 2 - 0.08, 1.15), (20.5, 0.20, 0.65), TERRACOTTA, 0.025)
    box("TERRACOTTA_UPPER_BAND", (3.5, -HOUSE_D / 2 - 0.10, GROUND_H + 0.55), (14.5, 0.20, 0.72), TERRACOTTA, 0.025)
    box("TERRACOTTA_LEFT_ACCENT", (-8.0, -HOUSE_D / 2 - 0.12, 3.0), (2.2, 0.22, 4.0), TERRACOTTA_LIGHT, 0.025)
    box("TERRACOTTA_RIGHT_ACCENT", (7.5, -HOUSE_D / 2 - 0.11, 5.0), (3.8, 0.22, 0.50), TERRACOTTA, 0.025)

# ============================================================
# WOOD CLADDING
# ============================================================

def build_wood_features():
    box("WOOD_TOWER_PANEL", (-10.0, -HOUSE_D / 2 - 0.15, 4.7), (3.1, 0.24, 3.0), WOOD, 0.025)
    for i in range(7):
        x = -11.25 + i * 0.42
        box("WOOD_TOWER_STRIP_" + str(i), (x, -HOUSE_D / 2 - 0.31, 4.7), (0.08, 0.06, 2.75), WOOD_LIGHT, 0.005)

    box("WOOD_UPPER_BLOCK", (7.4, -HOUSE_D / 2 - 0.16, 5.25), (5.1, 0.25, 2.25), WOOD, 0.025)
    for i in range(5):
        z = 4.35 + i * 0.45
        box("WOOD_UPPER_LINE_" + str(i), (7.4, -HOUSE_D / 2 - 0.31, z), (4.8, 0.06, 0.055), WOOD_LIGHT, 0.005)

    box("WOOD_ENTRY_LEFT", (8.8, -HOUSE_D / 2 - 0.17, 1.75), (1.15, 0.25, 2.85), WOOD, 0.025)
    box("WOOD_ENTRY_RIGHT", (11.0, -HOUSE_D / 2 - 0.17, 1.75), (1.15, 0.25, 2.85), WOOD, 0.025)

# ============================================================
# FRONT & SIDE WINDOWS
# ============================================================

def build_front_windows():
    front_window("LEFT_LARGE_WINDOW", -5.5, GROUND_H + 1.55, 4.6, 2.65, 0.30, True, True)
    front_window("CENTRAL_LARGE_WINDOW", 1.2, GROUND_H + 1.55, 5.0, 2.65, 0.30, True, True)
    front_window("TOWER_VERTICAL_WINDOW", -10.0, GROUND_H + 2.3, 1.45, 4.5, 0.30, True, False)
    front_window("TOWER_LOWER_WINDOW", -10.0, 2.1, 1.55, 1.65, 0.30, True, False)
    front_window("GROUND_RIGHT_WINDOW", 5.3, 1.85, 3.4, 1.8, 0.25, True, False)

def build_side_windows():
    side_window("RIGHT_SIDE_UPPER_1", "right", -2.5, GROUND_H + 1.6, 2.6, 2.1)
    side_window("RIGHT_SIDE_UPPER_2", "right", 3.2, GROUND_H + 1.6, 2.8, 2.1)
    side_window("RIGHT_SIDE_GROUND", "right", 2.0, 1.8, 2.7, 1.7)
    side_window("LEFT_SIDE_UPPER", "left", -1.0, GROUND_H + 1.6, 2.7, 2.2)

# ============================================================
# PORCH / CARPORT
# ============================================================

def build_porch():
    porch_x = 6.0
    porch_y = -HOUSE_D / 2 - 3.0

    box("PORCH_CANOPY", (porch_x, porch_y, 3.55), (11.0, 5.5, 0.42), PURE_WHITE, 0.05)
    box("PORCH_UNDERSIDE", (porch_x, porch_y, 3.32), (10.5, 5.0, 0.12), ANTHRACITE, 0.01)

    for x in (1.8, 10.4):
        box("PORCH_COLUMN", (x, porch_y - 1.7, 1.75), (0.45, 0.45, 3.5), PURE_WHITE, 0.03)

    box("ENTRY_PLATFORM", (7.2, -HOUSE_D / 2 - 0.9, 0.18), (6.5, 2.3, 0.30), PAVEMENT, 0.02)
    box("MAIN_DOOR", (8.7, -HOUSE_D / 2 - 0.22, 1.45), (1.8, 0.12, 2.7), WOOD, 0.025)
    box("DOOR_GLASS", (8.9, -HOUSE_D / 2 - 0.30, 1.6), (0.45, 0.04, 2.15), GLASS, 0.01)

    for x in [3.0, 5.0, 7.0, 9.0]:
        box("PORCH_LED", (x, porch_y - 1.0, 3.23), (0.12, 3.0, 0.055), LED, 0.005)

# ============================================================
# EXTERNAL STAIRCASE
# ============================================================

def build_stairs():
    start_x = 11.8
    start_y = -HOUSE_D / 2 - 2.0
    steps = 10
    for i in range(steps):
        z = 0.15 + i * 0.29
        y = start_y + i * 0.34
        box("STAIR_" + str(i), (start_x, y, z), (3.2, 0.62, 0.28), PAVEMENT, 0.025)

    box("STAIR_SIDE", (start_x + 1.45, start_y + 1.5, 1.55), (0.18, 3.8, 3.0), PURE_WHITE, 0.02)

    for i in range(7):
        y = start_y + i * 0.55
        z = 0.8 + i * 0.29
        cylinder("STAIR_RAIL_POST", (start_x - 1.35, y, z), 0.035, 1.0, METAL, 16)

    rail = box("STAIR_RAIL", (start_x - 1.35, start_y + 1.7, 2.15), (0.07, 4.0, 0.07), METAL, 0.01)
    rail.rotation_euler[0] = math.radians(-10)

# ============================================================
# ROOFTOP TERRACE
# ============================================================

def build_rooftop_terrace():
    terrace_z = GROUND_H + UPPER_H + 0.45
    box("ROOFTOP_TERRACE", (4.0, 1.5, terrace_z), (11.0, 7.0, 0.22), PAVEMENT, 0.025)

    rail_z = terrace_z + 1.15
    xs = [-1.3, 0.4, 2.1, 3.8, 5.5, 7.2, 8.9]
    for x in xs:
        cylinder("TERRACE_POST", (x, -2.0, rail_z / 2 + terrace_z / 2), 0.035, 1.2, METAL, 16)

    for z in (terrace_z + 0.45, terrace_z + 1.15):
        box("TERRACE_RAIL", (3.8, -2.0, z), (11.0, 0.07, 0.07), METAL, 0.01)
    for z in (terrace_z + 0.45, terrace_z + 1.15):
        box("TERRACE_SIDE_RAIL", (9.45, 1.5, z), (0.07, 7.0, 0.07), METAL, 0.01)

# ============================================================
# UPPER DECORATIVE WHITE FRAME & TRIMS
# ============================================================

def build_upper_frame():
    z = GROUND_H + UPPER_H + 0.55
    box("UPPER_FRAME_LEFT", (1.5, -7.5, z), (0.25, 0.25, 4.0), PURE_WHITE, 0.02)
    box("UPPER_FRAME_RIGHT", (7.5, -7.5, z), (0.25, 0.25, 4.0), PURE_WHITE, 0.02)
    box("UPPER_FRAME_TOP", (4.5, -7.5, z + 1.85), (6.25, 0.25, 0.25), PURE_WHITE, 0.02)

def build_dark_trims():
    for z in [GROUND_H + 0.05, GROUND_H + UPPER_H + 0.05]:
        box("DARK_FACADE_LINE", (0, -HOUSE_D / 2 - 0.15, z), (21.0, 0.07, 0.08), ANTHRACITE, 0.005)
    box("DARK_VERTICAL_DIVIDER", (4.1, -HOUSE_D / 2 - 0.18, 2.0), (0.10, 0.08, 3.4), ANTHRACITE, 0.005)

# ============================================================
# LIGHTS
# ============================================================

def add_area_light(name, location, energy, size, color, target):
    data = bpy.data.lights.new(name=name, type="AREA")
    data.energy = energy
    data.shape = "RECTANGLE"
    data.size = size
    data.color = color
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    return obj

def build_lighting():
    add_area_light("DAYLIGHT", (-10, -15, 18), 1300, 12, (1.0, 0.90, 0.78), (0, 0, 2))
    for x in [-8, -3, 3, 8]:
        add_area_light("FACADE_LIGHT", (x, -11, 2.5), 280, 2.0, (1.0, 0.45, 0.18), (x, -8, 3))
    add_area_light("PORCH_LIGHT", (6, -7, 3.2), 500, 5.0, (1.0, 0.38, 0.12), (6, -5, 1))
    add_area_light("RIGHT_SIDE_LIGHT", (17, -2, 6), 650, 5, (1.0, 0.75, 0.50), (10, 0, 3))

    sun_data = bpy.data.lights.new("SUN", type="SUN")
    sun_data.energy = 2.0
    sun_data.angle = math.radians(25)
    sun = bpy.data.objects.new("SUN", sun_data)
    bpy.context.collection.objects.link(sun)
    sun.rotation_euler = (math.radians(28), math.radians(-25), math.radians(-30))

# ============================================================
# GROUND / ROAD / TREES
# ============================================================

def build_environment():
    box("GROUND", (0, 0, -0.20), (65, 55, 0.40), GROUND, 0)
    box("ROAD", (0, -17, -0.05), (65, 8, 0.12), ROAD, 0)
    box("PAVEMENT", (0, -12.5, 0.02), (65, 1.6, 0.15), PAVEMENT, 0)
    box("CURB", (0, -13.4, 0.15), (65, 0.25, 0.30), PURE_WHITE, 0.02)

def build_tree(x, y, scale=1.0):
    cylinder("TREE_TRUNK", (x, y, 2.0 * scale), 0.30 * scale, 4.0 * scale, TREE_TRUNK, 12)
    for dx, dy, dz in [(0, 0, 5.0), (0.8, 0, 5.3), (-0.8, 0, 5.2), (0, 0.7, 5.5), (0, -0.7, 5.3)]:
        bpy.ops.mesh.primitive_ico_sphere_add(
            subdivisions=2, radius=1.5 * scale, location=(x + dx * scale, y + dy * scale, dz * scale)
        )
        leaf = bpy.context.object
        leaf.name = "TREE_CANOPY"
        leaf.data.materials.append(TREE_GREEN)

def build_trees():
    build_tree(-17, -8, 1.2)
    build_tree(17, -8, 1.4)
    build_tree(-18, 8, 1.5)
    build_tree(18, 7, 1.3)

# ============================================================
# CAMERAS
# ============================================================

def look_at(camera, target):
    direction = Vector(target) - camera.location
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()

def create_camera(name, location, target, lens=52):
    data = bpy.data.cameras.new(name)
    camera = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(camera)
    camera.location = location
    data.lens = lens
    look_at(camera, target)
    return camera

def create_cameras():
    cameras = {}
    cameras["01_FRONT"] = create_camera("01_FRONT", (0, -34, 8.0), (0, 0, 4.0), 55)
    cameras["02_FRONT_RIGHT"] = create_camera("02_FRONT_RIGHT", (27, -28, 9.0), (2, 0, 4.0), 52)
    cameras["03_RIGHT"] = create_camera("03_RIGHT", (36, 0, 8.0), (2, 0, 4.0), 52)
    cameras["04_FRONT_LEFT"] = create_camera("04_FRONT_LEFT", (-28, -29, 8.5), (-2, 0, 4.5), 52)
    cameras["05_LEFT_REAR"] = create_camera("05_LEFT_REAR", (-34, 15, 8.0), (-3, 2, 4.2), 52)
    return cameras

# ============================================================
# WORLD & RENDER SETTINGS
# ============================================================

def setup_world():
    world = bpy.context.scene.world
    if not world:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (0.48, 0.63, 0.78, 1)
        bg.inputs["Strength"].default_value = 0.35

def setup_render():
    scene = bpy.context.scene
    # In Blender 4.x EEVEE Next or EEVEE
    try:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    except Exception:
        try:
            scene.render.engine = "BLENDER_EEVEE"
        except Exception:
            scene.render.engine = "CYCLES"

    scene.render.resolution_x = RENDER_X
    scene.render.resolution_y = RENDER_Y
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = False
    try:
        scene.view_settings.look = "AgX - Medium High Contrast"
    except Exception:
        pass

# ============================================================
# BUILD EVERYTHING & RENDER
# ============================================================

def main():
    print("======================================")
    print("ZYNORA :: BUILDING ARCHITECTURAL BLENDER MODEL")
    print(f"  Dimensions: W={HOUSE_W}m, D={HOUSE_D}m, GH={GROUND_H}m, UH={UPPER_H}m")
    print(f"  Output Dir: {OUTPUT_DIR}")
    print("======================================")

    build_main_structure()
    build_terracotta_features()
    build_wood_features()
    build_front_windows()
    build_side_windows()
    build_porch()
    build_stairs()
    build_rooftop_terrace()
    build_upper_frame()
    build_dark_trims()
    build_environment()
    build_trees()
    build_lighting()
    setup_world()
    setup_render()

    cameras = create_cameras()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    scene = bpy.context.scene

    for name, camera in cameras.items():
        print(f"Rendering {name}...")
        scene.camera = camera
        filepath = os.path.join(OUTPUT_DIR, f"{name}.png")
        scene.render.filepath = filepath
        bpy.ops.render.render(write_still=True)
        print(f"  ✓ Saved: {filepath}")

    blend_path = os.path.join(OUTPUT_DIR, "zynora_house.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print(f"\n✓ Blender project saved: {blend_path}")
    print("======================================")
    print("ALL 5 VIEWS RENDERED SUCCESSFULLY")
    print("======================================")

if __name__ == "__main__":
    main()
