"""Build the Venus reel scene in Blender 4.5 (procedural: no downloaded assets).
Run inside Blender (via MCP execute, or `blender -b -P blender/build_scene.py`).
Reads blender/timing.json (from the voice-over) so every camera move lands on its line.
Vertical 1080 x 1920, 30 fps, EEVEE.
"""
import bpy, json, math, pathlib
from mathutils import Vector

HERE = pathlib.Path(globals().get("__file__", "") or bpy.path.abspath("//build_scene.py")).resolve().parent
TIMING = json.loads((pathlib.Path(globals().get("REEL_ROOT", str(HERE.parent))) / "blender" / "timing.json").read_text())
FPS = TIMING["fps"]; END = math.ceil(TIMING["total"] * FPS)
seg = {s["id"]: (round(s["start"] * FPS), round(s["end"] * FPS)) for s in TIMING["segments"]}

# ---------------------------------------------------------------- reset
# clear the scene without a factory reset (a reset would also unload the MCP add-on in a live Blender)
for coll in (bpy.data.objects, bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras, bpy.data.worlds, bpy.data.actions):
    for block in list(coll): coll.remove(block)
sc = bpy.context.scene
sc.render.fps = FPS; sc.frame_start = 1; sc.frame_end = END
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1080, 1920, 100
try: sc.render.engine = "BLENDER_EEVEE_NEXT"
except TypeError: sc.render.engine = "BLENDER_EEVEE"
sc.eevee.taa_render_samples = 24
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Punchy"

def mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; return m, m.node_tree.nodes, m.node_tree.links
def principled(nodes): return next(n for n in nodes if n.type == "BSDF_PRINCIPLED")
def output(nodes): return next(n for n in nodes if n.type == "OUTPUT_MATERIAL")

# ---------------------------------------------------------------- world: stars
w = bpy.data.worlds.new("Space"); sc.world = w; w.use_nodes = True
wn, wl = w.node_tree.nodes, w.node_tree.links
bg = next(n for n in wn if n.type == "BACKGROUND")
tc = wn.new("ShaderNodeTexCoord"); vor = wn.new("ShaderNodeTexVoronoi"); vor.inputs["Scale"].default_value = 420
ramp = wn.new("ShaderNodeValToRGB"); ramp.color_ramp.elements[0].position = 0.0; ramp.color_ramp.elements[0].color = (1, 1, 1, 1)
ramp.color_ramp.elements[1].position = 0.035; ramp.color_ramp.elements[1].color = (0, 0, 0, 1)
noise = wn.new("ShaderNodeTexNoise"); noise.inputs["Scale"].default_value = 60
mul = wn.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
add = wn.new("ShaderNodeMixRGB"); add.blend_type = "ADD"; add.inputs[0].default_value = 1; add.inputs[1].default_value = (0.004, 0.005, 0.012, 1)
wl.new(tc.outputs["Generated"], vor.inputs["Vector"]); wl.new(vor.outputs["Distance"], ramp.inputs["Fac"])
wl.new(tc.outputs["Generated"], noise.inputs["Vector"]); wl.new(ramp.outputs["Color"], mul.inputs[0]); wl.new(noise.outputs["Fac"], mul.inputs[1])
wl.new(mul.outputs[0], add.inputs[2]); wl.new(add.outputs[0], bg.inputs["Color"]); bg.inputs["Strength"].default_value = 1.6

# ---------------------------------------------------------------- Sun (origin)
bpy.ops.mesh.primitive_uv_sphere_add(radius=2.2, segments=64, ring_count=32, location=(0, 0, 0)); sun = bpy.context.object; sun.name = "Sun"
bpy.ops.object.shade_smooth()
m, n, l = mat("SunGlow"); p = principled(n); n.remove(p)
em = n.new("ShaderNodeEmission"); em.inputs["Strength"].default_value = 4.5
sn = n.new("ShaderNodeTexNoise"); sn.inputs["Scale"].default_value = 6; sn.inputs["Detail"].default_value = 10
sr = n.new("ShaderNodeValToRGB"); sr.color_ramp.elements[0].color = (1.0, 0.42, 0.08, 1); sr.color_ramp.elements[1].color = (1.0, 0.86, 0.45, 1)
l.new(sn.outputs["Fac"], sr.inputs["Fac"]); l.new(sr.outputs["Color"], em.inputs["Color"]); l.new(em.outputs[0], output(n).inputs["Surface"])
sun.data.materials.append(m)
sun.visible_shadow = False            # the light sits inside this sphere: it must not block it
bpy.ops.object.light_add(type="POINT", location=(0, 0, 0)); lamp = bpy.context.object; lamp.name = "SunLight"
lamp.data.energy = 9000; lamp.data.color = (1.0, 0.93, 0.82); lamp.data.shadow_soft_size = 2.2

# ---------------------------------------------------------------- Venus: banded, swirling clouds + rim haze
R_ORBIT = 9.0
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=128, ring_count=64); venus = bpy.context.object; venus.name = "Venus"
bpy.ops.object.shade_smooth()
m, n, l = mat("VenusClouds"); p = principled(n); p.inputs["Roughness"].default_value = 0.75
tcn = n.new("ShaderNodeTexCoord"); mp = n.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1, 1, 2.6)
dn = n.new("ShaderNodeTexNoise"); dn.inputs["Scale"].default_value = 2.2; dn.inputs["Detail"].default_value = 12; dn.inputs["Distortion"].default_value = 1.4
wave = n.new("ShaderNodeTexWave"); wave.wave_type = "BANDS"; wave.bands_direction = "Z"; wave.inputs["Scale"].default_value = 1.6
wave.inputs["Distortion"].default_value = 14; wave.inputs["Detail"].default_value = 8; wave.inputs["Detail Scale"].default_value = 1.5
mix = n.new("ShaderNodeMix"); mix.data_type = "FLOAT"; mix.inputs["Factor"].default_value = 0.72
vr = n.new("ShaderNodeValToRGB"); E = vr.color_ramp.elements
E[0].position, E[0].color = 0.2, (0.62, 0.42, 0.16, 1); E[1].position, E[1].color = 0.85, (0.98, 0.86, 0.58, 1)
mid = E.new(0.52); mid.color = (0.86, 0.66, 0.34, 1)
l.new(tcn.outputs["Object"], mp.inputs["Vector"]); l.new(mp.outputs["Vector"], dn.inputs["Vector"]); l.new(mp.outputs["Vector"], wave.inputs["Vector"])
l.new(wave.outputs["Fac"], mix.inputs["A"]); l.new(dn.outputs["Fac"], mix.inputs["B"]); l.new(mix.outputs["Result"], vr.inputs["Fac"])
l.new(vr.outputs["Color"], p.inputs["Base Color"])
venus.data.materials.append(m)

bpy.ops.mesh.primitive_uv_sphere_add(radius=1.045, segments=96, ring_count=48); haze = bpy.context.object; haze.name = "VenusHaze"
bpy.ops.object.shade_smooth(); haze.parent = venus
m, n, l = mat("Haze"); p = principled(n); n.remove(p)
lw = n.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.5
pw = n.new("ShaderNodeMath"); pw.operation = "POWER"; pw.inputs[1].default_value = 3.0
em = n.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (1.0, 0.8, 0.5, 1); em.inputs["Strength"].default_value = 0.9
tr = n.new("ShaderNodeBsdfTransparent"); ms = n.new("ShaderNodeMixShader")
l.new(lw.outputs["Facing"], pw.inputs[0]); l.new(pw.outputs[0], ms.inputs["Fac"]); l.new(tr.outputs[0], ms.inputs[1]); l.new(em.outputs[0], ms.inputs[2]); l.new(ms.outputs[0], output(n).inputs["Surface"])
try: m.surface_render_method = "BLENDED"
except AttributeError: m.blend_method = "BLEND"
haze.data.materials.append(m)
haze.visible_shadow = False          # the haze must not shade the planet under it

# spin axis + a marker pin, so one full turn is visible
def glow(name, color, strength):
    m, n, l = mat(name); p = principled(n); n.remove(p); em = n.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = color; em.inputs["Strength"].default_value = strength; l.new(em.outputs[0], output(n).inputs["Surface"]); return m
bpy.ops.mesh.primitive_cylinder_add(radius=0.012, depth=3.0); axis = bpy.context.object; axis.name = "SpinAxis"; axis.parent = venus
axis.data.materials.append(glow("AxisGlow", (0.55, 0.85, 1.0, 1), 6))
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.06, location=(0, -1.02, 0.25)); pin = bpy.context.object; pin.name = "Marker"; pin.parent = venus
pin.data.materials.append(glow("MarkerGlow", (0.4, 0.9, 1.0, 1), 30))

# orbit ring around the Sun
bpy.ops.mesh.primitive_torus_add(major_radius=R_ORBIT, minor_radius=0.018, major_segments=256, minor_segments=8); ring = bpy.context.object; ring.name = "Orbit"
ring.data.materials.append(glow("OrbitGlow", (1.0, 0.8, 0.5, 1), 2.5))

# ---------------------------------------------------------------- animation (keys every frame: exact, deterministic)
def ease(x): x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)
def lerp(a, b, t): return a + (b - a) * t
def venus_pos(f):                       # slow drift along the orbit for the whole film
    th = math.radians(-60 + 40 * (f / END)); return Vector((R_ORBIT * math.cos(th), R_ORBIT * math.sin(th), 0))

s_spin, e_spin = seg["spin"]; s_orbit, e_orbit = seg["orbit"]; s_back, e_back = seg["back"]; s_cta = seg["cta"][0]
def spin_angle(f):                      # retrograde (negative); exactly one turn during "spin"
    base = -0.15 * (f / FPS)
    turn = -2 * math.pi * ease((f - s_spin) / max(1, e_spin - s_spin))
    return base + turn

bpy.ops.object.camera_add(); cam = bpy.context.object; cam.name = "Camera"; sc.camera = cam
cam.data.lens = 40; cam.data.sensor_fit = "VERTICAL"; cam.data.sensor_height = 36; cam.data.clip_end = 500
bpy.ops.object.empty_add(location=(0, 0, 0)); tgt = bpy.context.object; tgt.name = "CamTarget"
tc_ = cam.constraints.new("TRACK_TO"); tc_.target = tgt; tc_.track_axis = "TRACK_NEGATIVE_Z"; tc_.up_axis = "UP_Y"
axis.hide_render = False

def shot(f):
    """camera position and look-at point for frame f, blended between the line shots"""
    v = venus_pos(f); out = v.normalized()                 # direction from Sun to Venus
    side = Vector((-out.y, out.x, 0))                      # along the orbit
    close = (v + (-out) * 3.9 + Vector((0, 0, 0.35)), v)                          # Sun-lit face, Venus fills frame
    spin = (v + (-out) * 4.2 + Vector((0, 0, 1.4)), v)                            # a bit higher: axis + pin visible
    wide = (v * 0.5 + Vector((0, 0, 26)) + side * -6, v * 0.45)                   # above the orbit: Sun + Venus + ring
    # from Venus's night side looking sunward: the Sun starts hidden behind the planet, then rises over its edge
    limb_a = (v + out * 2.6 + Vector((0, 0, -0.05)), v * 0.55 + Vector((0, 0, 1.1)))
    limb_b = (v + out * 2.6 + Vector((0, 0, 1.45)), v * 0.55 + Vector((0, 0, 1.1)))
    final = (v + (-out) * 6.5 + side * 2.0 + Vector((0, 0, 1.6)), v * 0.75)
    keys = [(0, close), (s_spin, close), (s_spin + 20, spin), (s_orbit - 4, spin), (s_orbit + 40, wide), (s_back - 4, wide),
            (s_back + 30, limb_a), (s_cta - 2, limb_b), (s_cta + 40, final), (END + 1, final)]
    for (fa, A), (fb, B) in zip(keys, keys[1:]):
        if fa <= f <= fb:
            t = ease((f - fa) / max(1, fb - fa))
            return A[0].lerp(B[0], t), A[1].lerp(B[1], t)
    return keys[-1][1]

push = lambda f: 1 - 0.08 * ease(f / max(1, s_spin))       # slow push-in during the hook
for f in range(1, END + 1):
    v = venus_pos(f)
    venus.location = v; venus.keyframe_insert("location", frame=f)
    venus.rotation_euler = (0, 0, spin_angle(f)); venus.keyframe_insert("rotation_euler", frame=f)
    pos, look = shot(f)
    if f < s_spin: pos = look + (pos - look) * push(f)
    cam.location = pos; cam.keyframe_insert("location", frame=f)
    tgt.location = look; tgt.keyframe_insert("location", frame=f)
# axis and pin show only while the spin is explained
for obj in (axis, pin):
    for f, vis in ((1, True), (s_spin - 1, True), (s_spin, False), (e_orbit, False), (e_orbit + 1, True)):
        obj.hide_render = vis; obj.keyframe_insert("hide_render", frame=f)
        obj.hide_viewport = vis; obj.keyframe_insert("hide_viewport", frame=f)
# the orbit ring only while the orbit is explained (it cuts across the close shots otherwise)
for f, hide in ((1, True), (s_orbit - 1, True), (s_orbit, False), (s_back + 30, False), (s_back + 31, True)):
    ring.hide_render = hide; ring.keyframe_insert("hide_render", frame=f); ring.hide_viewport = hide; ring.keyframe_insert("hide_viewport", frame=f)
for c in (venus, cam, tgt):
    if c.animation_data and c.animation_data.action:
        for fc in getattr(c.animation_data.action, "fcurves", []):
            for k in fc.keyframe_points: k.interpolation = "LINEAR"

# ---------------------------------------------------------------- compositor: glow
sc.use_nodes = True; ct = sc.node_tree
for nd in list(ct.nodes): ct.nodes.remove(nd)
rl = ct.nodes.new("CompositorNodeRLayers"); gl = ct.nodes.new("CompositorNodeGlare"); co = ct.nodes.new("CompositorNodeComposite")
gl.glare_type = "FOG_GLOW"
for attr, val in (("quality", "HIGH"), ("threshold", 0.9), ("size", 8), ("mix", 0.0)):
    try: setattr(gl, attr, val)
    except Exception: pass
ct.links.new(rl.outputs["Image"], gl.inputs["Image"]); ct.links.new(gl.outputs["Image"], co.inputs["Image"])

sc.render.image_settings.file_format = "JPEG"; sc.render.image_settings.quality = 95
sc.frame_set(1)
print(f"scene built: {END} frames at {FPS} fps; segments {seg}")

# headless build (`blender -b -P blender/build_scene.py`): save the .blend next to this script for the render step
if bpy.app.background:
    bpy.ops.wm.save_as_mainfile(filepath=str(HERE / "venus-reel.blend"))
    print("saved", HERE / "venus-reel.blend")
