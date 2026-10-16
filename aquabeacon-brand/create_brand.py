"""Build original AquaBeacon brand assets in Blender 5.2.

Run: blender --background --python create_brand.py -- --mode stills
     blender --background aquabeacon_brand.blend --python create_brand.py -- --mode animation
"""
import argparse
import json
import math
from pathlib import Path
import shutil
import sys

import bpy
from mathutils import Vector

OUT = Path(__file__).resolve().parent
FONT_DIR = Path(r"C:\Users\ryupc\.codex\plugins\cache\claude-cowork\anthropic-skills\1.0.0\skills\canvas-design\canvas-fonts")


def linear(hex_color):
    rgb = [int(hex_color[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb) + (1,)


def material(name, color, metallic=0.0, roughness=0.32, emission=0.0, fading=False):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = linear(color)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = linear(color)
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Emission Color'].default_value = linear(color)
    bsdf.inputs['Emission Strength'].default_value = emission
    if fading:
        transparent = nodes.new('ShaderNodeBsdfTransparent')
        mix = nodes.new('ShaderNodeMixShader')
        mix.name = 'Visibility'
        mat.node_tree.links.new(transparent.outputs[0], mix.inputs[1])
        mat.node_tree.links.new(bsdf.outputs[0], mix.inputs[2])
        mat.node_tree.links.new(mix.outputs[0], nodes.get('Material Output').inputs[0])
        mix.inputs[0].default_value = 1
        if hasattr(mat, 'surface_render_method'):
            mat.surface_render_method = 'DITHERED'
    return mat


def link(scene, name, data=None):
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    return obj


def new_scene(name, width, height, transparent=False):
    scene = bpy.data.scenes.new(name)
    bpy.context.window.scene = scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 128
    scene.cycles.use_denoising = True
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.018
    scene.cycles.device = 'GPU'
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = 100
    scene.render.use_persistent_data = True
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.render.film_transparent = transparent
    scene.render.fps = 30
    scene.frame_start = 1
    scene.frame_end = 150
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.look = 'None'
    scene.view_settings.exposure = 0
    scene.view_settings.gamma = 1
    scene.world = bpy.data.worlds.new(name + ' World')
    scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value = linear('7497AB')
    scene.world.node_tree.nodes['Background'].inputs[1].default_value = 0.35
    return scene


def camera(scene, scale, center=(0, 0)):
    data = bpy.data.cameras.new(scene.name + ' Camera')
    obj = link(scene, scene.name + ' Camera', data)
    obj.location = (center[0], center[1], 16)
    obj.rotation_euler = (0, 0, 0)
    data.type = 'ORTHO'
    data.ortho_scale = scale
    data.lens = 52
    scene.camera = obj
    return obj


def area(scene, name, loc, energy, size, color, target=(0, 0, 0)):
    data = bpy.data.lights.new(name, 'AREA')
    data.energy = energy
    data.shape = 'DISK'
    data.size = size
    data.color = linear(color)[:3]
    obj = link(scene, name, data)
    obj.location = loc
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()


def lighting(scene):
    area(scene, 'Softbox / upper left', (-3, 5, 7), 520, 5, 'C7F5FF')
    area(scene, 'Softbox / right', (5, 1, 5), 340, 4, '68D7EF')
    area(scene, 'Softbox / warm edge', (-4, -2, 3), 100, 3, 'FFFFFF')


def face(scene, name, points, mat, parent=None, depth=0.17, bevel=0.045):
    curve = bpy.data.curves.new(name, 'CURVE')
    curve.dimensions = '2D'
    curve.resolution_u = 24
    curve.fill_mode = 'BOTH'
    curve.extrude = depth / 2
    curve.bevel_depth = bevel
    curve.bevel_resolution = 4
    spline = curve.splines.new('POLY')
    spline.points.add(len(points) - 1)
    for p, xy in zip(spline.points, points):
        p.co = (*xy, 0, 1)
    spline.use_cyclic_u = True
    obj = link(scene, name, curve)
    obj.data.materials.append(mat)
    obj.parent = parent
    return obj


def line(scene, name, points, width, mat, parent=None, bezier=False):
    curve = bpy.data.curves.new(name, 'CURVE')
    curve.dimensions = '3D'
    curve.resolution_u = 24
    curve.bevel_depth = width
    curve.bevel_resolution = 4
    curve.use_fill_caps = True
    if bezier:
        spline = curve.splines.new('BEZIER')
        spline.bezier_points.add(len(points) - 1)
        for p, xy in zip(spline.bezier_points, points):
            p.co = (*xy, 0.16)
            p.handle_left_type = 'AUTO'
            p.handle_right_type = 'AUTO'
    else:
        spline = curve.splines.new('POLY')
        spline.points.add(len(points) - 1)
        for p, xy in zip(spline.points, points):
            p.co = (*xy, 0.16, 1)
    obj = link(scene, name, curve)
    obj.data.materials.append(mat)
    obj.parent = parent
    return obj


def arc(scene, name, radius, width, mat, parent=None):
    points = []
    for i in range(81):
        a = math.radians(28 + 124 * i / 80)
        points.append((radius * math.cos(a), 0.82 + radius * math.sin(a)))
    return line(scene, name, points, width, mat, parent)


def mark(scene, name, origin=(0, 0, 0), animated=False):
    root = link(scene, name)
    root.location = origin
    teal = material(name + ' / aqua ceramic', '20D9D2', 0.24, 0.28, 0.12)
    blue = material(name + ' / ocean blue', '239FCF', 0.25, 0.29, 0.12)
    signal = material(name + ' / beacon', 'B9FFFF', 0.12, 0.22, 1.0)
    wave_mat = material(name + ' / waterline', '69F5E1', 0.2, 0.26, 0.22)
    left = face(scene, name + ' / A left', [(-1.0, -1.0), (-0.65, -1.0), (-0.10, 0.52), (-0.40, 0.52)], teal, root)
    right = face(scene, name + ' / A right', [(0.65, -1.0), (1.0, -1.0), (0.40, 0.52), (0.10, 0.52)], blue, root)
    wave = line(scene, name + ' / water wave', [(-0.65, -0.40), (-0.33, -0.27), (0.02, -0.37), (0.33, -0.49), (0.65, -0.36)], 0.085, wave_mat, root, True)
    dot_points = [(0.15 * math.cos(t * 2 * math.pi / 64), 0.82 + 0.15 * math.sin(t * 2 * math.pi / 64)) for t in range(64)]
    dot = face(scene, name + ' / light source', dot_points, signal, root, 0.16, 0.018)
    inner = arc(scene, name + ' / signal 01', 0.45, 0.041, teal, root)
    outer = arc(scene, name + ' / signal 02', 0.76, 0.038, blue, root)
    if animated:
        for ob, start, end in [(left, 12, 38), (right, 17, 43)]:
            for frame, scale in [(1, 0.001), (start, 0.001), (end, 1.0)]:
                ob.scale = (scale,) * 3
                ob.keyframe_insert('scale', frame=frame)
        for frame, scale in [(1, 0.001), (7, 0.001), (18, 1.16), (26, 1.0)]:
            dot.scale = (scale,) * 3
            dot.keyframe_insert('scale', frame=frame)
        for ob, start, end in [(wave, 26, 51), (inner, 18, 38), (outer, 28, 48)]:
            for frame, factor in [(1, 0.0), (start, 0.0), (end, 1.0)]:
                ob.data.bevel_factor_end = factor
                ob.data.keyframe_insert('bevel_factor_end', frame=frame)
        for frame, x, scale, ry in [(1, 0, 1.10, -0.4), (42, 0, 1.10, -0.1), (78, -2.94, 0.92, -0.07), (150, -2.94, 0.92, -0.07)]:
            root.location = (x, 0, 0)
            root.scale = (scale,) * 3
            root.rotation_euler = (0.04, ry, 0)
            root.keyframe_insert('location', frame=frame)
            root.keyframe_insert('scale', frame=frame)
            root.keyframe_insert('rotation_euler', frame=frame)
        strength = signal.node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
        for frame, value in [(1, 0.3), (15, 2.4), (35, 0.65), (76, 1.5), (90, 0.65), (150, 0.65)]:
            strength.default_value = value
            strength.keyframe_insert('default_value', frame=frame)
    return root


def text(scene, name, body, location, size, mat, font, spacing=1.0):
    data = bpy.data.curves.new(name, 'FONT')
    data.body = body
    data.font = font
    data.size = size
    data.space_character = spacing
    data.extrude = 0.008
    data.bevel_depth = 0.003
    data.bevel_resolution = 2
    data.align_y = 'BOTTOM_BASELINE'
    obj = link(scene, name, data)
    obj.location = location
    data.materials.append(mat)
    return obj


def fade(mat, frames):
    factor = mat.node_tree.nodes['Visibility'].inputs[0]
    for frame, value in frames:
        factor.default_value = value
        factor.keyframe_insert('default_value', frame=frame)


def wordmark(scene, animated=False, tagline=True):
    font = bpy.data.fonts.load(str(FONT_DIR / 'InstrumentSans-Regular.ttf'))
    mono = bpy.data.fonts.load(str(FONT_DIR / 'DMMono-Regular.ttf'))
    aqua = material(scene.name + ' / word Aqua', 'EAF9FF', 0, 0.4, 1, animated)
    beacon = material(scene.name + ' / word Beacon', '55DCD7', 0, 0.4, 1, animated)
    ob = text(scene, 'Wordmark / Aqua', 'Aqua', (-1.33, -0.18, 0.15), 1.11, aqua, font)
    bpy.context.view_layer.update()
    second_x = ob.location.x + ob.dimensions.x + 0.052
    text(scene, 'Wordmark / Beacon', 'Beacon', (second_x, -0.18, 0.15), 1.11, beacon, font)
    if animated:
        for mat in (aqua, beacon):
            fade(mat, [(1, 0), (58, 0), (84, 1), (150, 1)])
    if tagline:
        submat = material(scene.name + ' / subline', '87ADBF', 0, 0.5, 1, animated)
        text(scene, 'Descriptor', 'LIGHT + SOUND / UNDERWATER POSITIONING', (-1.30, -0.83, 0.16), 0.178, submat, mono, 1.05)
        if animated:
            fade(submat, [(1, 0), (75, 0), (98, 1), (150, 1)])


def background(scene):
    mat = bpy.data.materials.new('Deep water / radial field')
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    output = nodes.new('ShaderNodeOutputMaterial')
    emission = nodes.new('ShaderNodeEmission')
    coord = nodes.new('ShaderNodeTexCoord')
    dist = nodes.new('ShaderNodeVectorMath')
    dist.operation = 'DISTANCE'
    dist.inputs[1].default_value = (0.47, 0.53, 0)
    ramp = nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = 0.02
    ramp.color_ramp.elements[0].color = linear('103443')
    ramp.color_ramp.elements[1].position = 0.63
    ramp.color_ramp.elements[1].color = linear('050F20')
    mat.node_tree.links.new(coord.outputs['Generated'], dist.inputs[0])
    mat.node_tree.links.new(dist.outputs['Value'], ramp.inputs[0])
    mat.node_tree.links.new(ramp.outputs[0], emission.inputs[0])
    mat.node_tree.links.new(emission.outputs[0], output.inputs[0])
    ob = face(scene, 'Background', [(-9, -5.2), (9, -5.2), (9, 5.2), (-9, 5.2)], mat, depth=0, bevel=0)
    ob.location.z = -0.65


def ripple(scene, name, start):
    mat = material(name + ' / fade', '2DC6D1', 0.05, 0.45, 0.6, True)
    points = [(1.05 * math.cos(i * math.tau / 160), 0.25 + 1.05 * math.sin(i * math.tau / 160)) for i in range(161)]
    obj = line(scene, name, points, 0.010, mat)
    obj.location.z = -0.25
    for frame, scale in [(1, 0.1), (start, 0.1), (start + 40, 2.9), (start + 45, 3.1)]:
        obj.scale = (scale,) * 3
        obj.keyframe_insert('scale', frame=frame)
    fade(mat, [(1, 0), (start, 0), (start + 5, 0.20), (start + 22, 0.12), (start + 40, 0), (150, 0)])


def rounded_rect(size, radius, steps=16):
    points = []
    for cx, cy, angle in [(size / 2 - radius, size / 2 - radius, 0), (-size / 2 + radius, size / 2 - radius, 90), (-size / 2 + radius, -size / 2 + radius, 180), (size / 2 - radius, -size / 2 + radius, 270)]:
        for i in range(steps + 1):
            a = math.radians(angle + 90 * i / steps)
            points.append((cx + radius * math.cos(a), cy + radius * math.sin(a)))
    return points


def configure_gpu():
    prefs = bpy.context.preferences.addons['cycles'].preferences
    selected = []
    for backend in ('OPTIX', 'CUDA'):
        try:
            prefs.compute_device_type = backend
            prefs.get_devices()
            selected = [d for d in prefs.devices if d.type != 'CPU']
            if selected:
                for device in prefs.devices:
                    device.use = device.type != 'CPU'
                print('GPU_SELECTED', backend, [d.name for d in selected], flush=True)
                break
        except Exception as exc:
            print('GPU_BACKEND_UNAVAILABLE', backend, str(exc), flush=True)
    if not selected:
        for scene in bpy.data.scenes:
            if scene.render.engine == 'CYCLES':
                scene.cycles.device = 'CPU'


def build():
    # Factory-startup objects are in their own unused scene; no user file is opened.
    hero = new_scene('01 · AquaBeacon / Animation', 1920, 1080)
    camera(hero, 12.8, (0, 0.3))
    lighting(hero)
    background(hero)
    mark(hero, 'AquaBeacon symbol / animated', animated=True)
    wordmark(hero, animated=True)
    ripple(hero, 'Acoustic pulse / 01', 26)
    ripple(hero, 'Acoustic pulse / 02', 39)
    hero.timeline_markers.new('BEACON ON', frame=15)
    hero.timeline_markers.new('LIGHT + SOUND', frame=43)
    hero.timeline_markers.new('WORDMARK REVEAL', frame=70)
    hero.timeline_markers.new('FINAL LOCKUP', frame=100)

    icon = new_scene('02 · App icon', 1024, 1024, True)
    camera(icon, 4.28, (0, 0.22))
    lighting(icon)
    badge_mat = material('Icon / midnight ceramic', '071727', 0.18, 0.33, 0.35)
    badge = face(icon, 'App icon / rounded tile', rounded_rect(3.75, 0.68), badge_mat, depth=0.18, bevel=0.055)
    badge.location = (0, 0.22, -0.38)
    root = mark(icon, 'App icon / symbol')
    root.scale = (1.03,) * 3
    root.rotation_euler = (0.035, -0.065, 0)

    transparent = new_scene('03 · Symbol transparent', 1024, 1024, True)
    camera(transparent, 3.4, (0, 0.27))
    lighting(transparent)
    mark(transparent, 'Transparent symbol')

    lockup = new_scene('04 · Logo transparent', 2400, 900, True)
    camera(lockup, 10.6, (0, 0.22))
    lighting(lockup)
    root = mark(lockup, 'Transparent lockup / symbol', (-2.94, 0, 0))
    root.scale = (0.92,) * 3
    wordmark(lockup, tagline=False)

    for scene in [hero, icon, transparent, lockup]:
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                area.spaces.active.region_3d.view_perspective = 'CAMERA'
                area.spaces.active.shading.type = 'MATERIAL'
                area.spaces.active.shading.use_scene_world = True
                area.spaces.active.shading.use_scene_lights = True
                area.spaces.active.overlay.show_overlays = False
    configure_gpu()
    bpy.context.window.scene = hero
    hero.frame_set(120)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'aquabeacon_brand.blend'))
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'aquabeacon_brand.blend'))
    return hero, icon, transparent, lockup


def render_stills(scenes):
    for scene, filename in zip(scenes, ['aquabeacon_logo.png', 'aquabeacon_icon.png', 'aquabeacon_symbol_transparent.png', 'aquabeacon_logo_transparent.png']):
        bpy.context.window.scene = scene
        scene.frame_set(120)
        scene.render.filepath = str(OUT / filename)
        print('RENDER_STILL', filename, flush=True)
        bpy.ops.render.render(write_still=True)
    hero = scenes[0]
    bpy.context.window.scene = hero
    for frame in (15, 40, 70, 100):
        hero.frame_set(frame)
        hero.render.resolution_percentage = 50
        hero.render.filepath = str(OUT / 'preview' / f'frame_{frame:03d}.png')
        bpy.ops.render.render(write_still=True)
    hero.frame_set(120)
    hero.render.resolution_percentage = 100
    hero.render.filepath = '//frames/aquabeacon_'
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'aquabeacon_brand.blend'))


def render_animation():
    configure_gpu()
    hero = bpy.data.scenes['01 · AquaBeacon / Animation']
    bpy.context.window.scene = hero
    hero.render.resolution_percentage = 100
    hero.cycles.samples = 64
    hero.render.image_settings.file_format = 'PNG'
    hero.render.image_settings.color_mode = 'RGB'
    hero.render.use_persistent_data = True
    # Every animated property is constant from frame 98 onward. Render that
    # final pose once and copy it for the remaining, intentionally static hold.
    # Complete PNGs from an earlier render are reusable when resuming.
    for frame in range(1, 99):
        destination = OUT / 'frames' / f'aquabeacon_{frame:04d}.png'
        if destination.exists() and destination.read_bytes().endswith(b'IEND\xaeB\x60\x82'):
            continue
        hero.frame_set(frame)
        hero.render.filepath = str(destination)
        bpy.ops.render.render(write_still=True)
    final_pose = OUT / 'frames' / 'aquabeacon_0098.png'
    for frame in range(99, 151):
        shutil.copyfile(final_pose, OUT / 'frames' / f'aquabeacon_{frame:04d}.png')


def main():
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['stills', 'animation', 'build'], default='stills')
    opts = parser.parse_args(args)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'preview').mkdir(exist_ok=True)
    (OUT / 'frames').mkdir(exist_ok=True)
    if opts.mode == 'animation':
        render_animation()
    else:
        scenes = build()
        if opts.mode == 'stills':
            render_stills(scenes)
    (OUT / 'render_info.json').write_text(json.dumps({'blender': bpy.app.version_string, 'fps': 30, 'frames': 150, 'duration_seconds': 5, 'resolution': [1920, 1080], 'active_scene': bpy.context.scene.name}, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
