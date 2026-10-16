"""Inspect the editable Blender file without changing or rendering it."""
import json
from pathlib import Path
import sys

import bpy

OUT = Path(__file__).resolve().parent
hero = bpy.data.scenes['01 · AquaBeacon / Animation']
bpy.context.window.scene = hero


def snapshot(frame):
    hero.frame_set(frame)
    bpy.context.view_layer.update()
    state = {}
    for obj in hero.objects:
        values = [round(v, 6) for row in obj.matrix_world for v in row]
        if obj.type == 'CURVE':
            values.append(round(obj.data.bevel_factor_end, 6))
        state[obj.name] = values
    for mat in bpy.data.materials:
        if mat.node_tree:
            for node in mat.node_tree.nodes:
                if node.name == 'Visibility':
                    state[mat.name + ' / alpha'] = round(node.inputs[0].default_value, 6)
                if node.type == 'BSDF_PRINCIPLED':
                    state[mat.name + ' / emission'] = round(node.inputs['Emission Strength'].default_value, 6)
    return state


pose = snapshot(98)
for frame in (99, 120, 150):
    assert snapshot(frame) == pose, f'Final hold changes at frame {frame}'

fonts = []
for font in bpy.data.fonts:
    if font.filepath and font.filepath != '<builtin>':
        packed = font.packed_file is not None
        assert packed, f'Font is not embedded: {font.name}'
        fonts.append({'name': font.name, 'embedded': packed})

assert hero.frame_start == 1 and hero.frame_end == 150
assert hero.render.fps == 30
assert hero.camera is not None

report = {
    'blender_version': bpy.app.version_string,
    'animation_frames': [hero.frame_start, hero.frame_end],
    'fps': hero.render.fps,
    'final_hold_identical_at_frames': [98, 99, 120, 150],
    'embedded_fonts': fonts,
    'scenes': [{'name': scene.name, 'objects': len(scene.objects), 'resolution': [scene.render.resolution_x, scene.render.resolution_y], 'transparent': scene.render.film_transparent} for scene in bpy.data.scenes if scene.name[:2] in ('01', '02', '03', '04')],
}
(OUT / 'blend_inspection.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=False, indent=2))

if '--save-preview' in sys.argv:
    hero.frame_set(120)
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                area.spaces.active.region_3d.view_perspective = 'CAMERA'
                area.spaces.active.shading.type = 'MATERIAL'
                area.spaces.active.shading.use_scene_world = True
                area.spaces.active.shading.use_scene_lights = True
                area.spaces.active.overlay.show_overlays = False
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'aquabeacon_brand.blend'))
