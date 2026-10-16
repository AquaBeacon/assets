"""Blender source for the AquaBeacon 60-second public introduction.

The diagram is deliberately schematic. Light tracks the child, and the child's
two downward cameras observe the seabed. No light-scanning of the seabed.
"""
import argparse
import importlib.util
import json
import math
import shutil
import sys
import time
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BASE = HERE / 'source_scene.py'
if not BASE.exists():
    shutil.copy2(ROOT.parent / 'aquabeacon-explainer' / 'build_scene.py', BASE)
spec = importlib.util.spec_from_file_location('diagram_base', BASE)
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
base.OUT = HERE
base.W, base.H = 1300, 1080
FPS = 30
MODES = {'meadow':120, 'gps':72, 'overview':72, 'sound':72,
         'light':72, 'position':72, 'mapping':120}


def shade(name, hex_color, roughness=.6, emission=None):
    m = bpy.data.materials.get(name)
    if m is None:
        return
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = base.col(hex_color)
    p.inputs['Roughness'].default_value = roughness
    if emission is not None:
        p.inputs['Emission Color'].default_value = base.col(hex_color)
        p.inputs['Emission Strength'].default_value = emission


def build():
    refs = base.build()
    scene = refs['scene']
    scene.name = 'AquaBeacon / 60 second introduction'
    scene.render.fps = FPS
    scene.frame_end = 60 * FPS
    scene.eevee.taa_render_samples = 64
    scene.render.image_settings.compression = 15
    shade('Ocean / back wall', '23666F', .85)
    shade('Seabed / sand', '829D92', .9)
    shade('World coordinates / grid', '78AAAB', .8, .02)
    shade('Aqua / float', '20BDB8', .42)
    shade('Ivory / hull', 'F0F5E8', .48)
    shade('Graphite / structure', '183C48', .55)
    shade('Light / aqua', '20D9D2', .4, .5)
    shade('Sound / amber', 'F3B44E', .5, .4)
    shade('Map / registered point cloud', '70BD88', .4, .7)
    for i,c in enumerate(['368C64','237765','59AB75']):
        shade('Seagrass / '+str(i),c,.8)

    # The float has a simple weatherproof top, with no unsupported solar function.
    for ob in scene.objects:
        if ob.name.startswith(('Ocean / surface','Seabed grid')):
            ob.hide_render = True
            ob.hide_viewport = True
        if ob.name.startswith('Parent / panel strips'):
            ob.hide_render = True
            ob.hide_viewport = True
        if ob.name.startswith('Parent / solar panel'):
            ob.data.materials.clear()
            ob.data.materials.append(bpy.data.materials['Ivory / hull'])
            ob.name = 'Parent / weatherproof lid'
    for ob in list(refs['light']):
        if ob.name.startswith('Light / tracking beam'):
            refs['light'].remove(ob)
            ob.hide_render = True
            ob.hide_viewport = True
    # Survey imagery, rather than a projected scanning line, creates the map.
    for ob in list(refs['mapping']):
        if ob.name.startswith(('Mapping / image scan','Mapping / downward camera')):
            refs['mapping'].remove(ob)
            ob.hide_render = True
            ob.hide_viewport = True
    refs['scan'].hide_render = True
    refs['scan'].hide_viewport = True

    # Slightly fuller seagrass emphasizes the environmental use case.
    plants = [o for o in scene.objects if o.name.startswith('Seagrass /')]
    refs['plants'] = plants
    for ob in plants:
        ob['initial_y'] = ob.location.y

    # Small outlined camera frustums are explanatory geometry, not a laser.
    mapmat = bpy.data.materials['Map / registered point cloud']
    footprint = []
    for x in (-.47,.47):
        start = base.CHILD + Vector((x,-.43,-.43))
        for end in [(0.25,-1.15,.13),(2.0,-1.15,.13),(2.0,.12,.13),(.25,.12,.13)]:
            ob = base.tube('Survey camera / field of view',[start,end],.005,mapmat)
            footprint.append(ob)
    refs['mapping'].extend(footprint)
    refs['camera_default'] = (scene.camera.location.copy(), scene.camera.rotation_euler.copy(), scene.camera.data.ortho_scale)
    return refs


def mode_at(t):
    if t < 7: return 'meadow'
    if t < 14: return 'gps'
    if t < 19: return 'overview'
    if t < 28: return 'sound'
    if t < 36: return 'light'
    if t < 42: return 'position'
    if t < 46: return 'mapping'
    return 'overview'


def update(refs, mode, t, frame=None):
    scene = refs['scene']
    base.update(refs, 'overview' if mode=='meadow' else mode, t)
    refs['scan'].hide_render = True
    refs['scan'].hide_viewport = True
    # A common 2.4s phase keeps loops seamless in the graphic explanation.
    phase = math.tau * t / (4 if mode in ('meadow','mapping') else 2.4)
    refs['boat'].rotation_euler = (.009*math.sin(phase), .007*math.cos(phase), 0)
    refs['child'].location = base.CHILD + Vector((0,0,.025*math.sin(phase)))
    refs['target'].location = refs['child'].location
    refs['light_dot'].location = base.CHILD+Vector((.02,-.1,.63))+(base.LIGHT_TARGET-base.CHILD-Vector((.02,-.1,.63)))*((t/2.4)%1)
    for i,ob in enumerate(refs['plants']):
        ob.rotation_euler.y = .045*math.sin(phase+i*.71)
        ob.rotation_euler.x = .028*math.cos(phase+i*.47)
    if mode=='meadow':
        for group in ('gps','sound','light','position','mapping'):
            for ob in refs[group]:
                ob.hide_render=True
                ob.hide_viewport=True
        scene.camera.location = (7,-11,6.8)
        target=Vector((0,0,2.4))
        scene.camera.rotation_euler=(target-scene.camera.location).to_track_quat('-Z','Y').to_euler()
        scene.camera.data.ortho_scale = 10.0
    else:
        loc,rot,scale=refs['camera_default']
        scene.camera.location=loc
        scene.camera.rotation_euler=rot
        scene.camera.data.ortho_scale=scale
    for ob in scene.objects:
        if ob.name.startswith('Satellite /'):
            ob.hide_render = mode=='meadow'
            ob.hide_viewport = mode=='meadow'
    if frame is not None:
        for ob in scene.objects:
            for key in ('hide_render','hide_viewport'):
                ob.keyframe_insert(key,frame=frame)
        movers=[refs['boat'],refs['child'],refs['target'],refs['light_dot'],refs['gps_dot'],scene.camera]+refs['rings']+refs['plants']
        for ob in movers:
            ob.keyframe_insert('location',frame=frame)
            ob.keyframe_insert('rotation_euler',frame=frame)
            ob.keyframe_insert('scale',frame=frame)
        scene.camera.data.keyframe_insert('ortho_scale',frame=frame)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--mode',choices=['preview','all','build'],default='preview')
    ap.add_argument('--only',default='')
    ap.add_argument('--force',action='store_true',help='Regenerate existing rendered frames after a scene change.')
    args=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    (HERE/'render').mkdir(parents=True,exist_ok=True)
    refs=build();scene=refs['scene']
    if args.mode=='build':
        # Bake sample-controlled animated objects, and exact shot boundaries.
        boundaries={1,211,421,571,841,1081,1261,1381,1621,1800}
        frames=sorted(set(range(1,1801,3))|boundaries)
        for frame in frames:
            t=(frame-1)/FPS
            update(refs,mode_at(t),t,frame)
        for t,name in [(0,'藻場'),(7,'位置の課題'),(14,'AquaBeacon'),(19,'音で距離'),(28,'光で方向'),(36,'位置推定'),(42,'後処理の地図化'),(46,'実験記録は編集シーン'),(54,'将来の活用')]:
            scene.timeline_markers.new(name,frame=t*FPS+1)
        scene.frame_set(450)
        for screen in bpy.data.screens:
            for area in screen.areas:
                if area.type=='VIEW_3D':
                    area.spaces.active.region_3d.view_perspective='CAMERA'
                    area.spaces.active.overlay.show_overlays=False
        bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'AquaBeacon_60s_scene.blend'))
        return
    modes=args.only.split(',') if args.only else list(MODES)
    for mode in modes:
        count=MODES[mode]
        folder=HERE/'render'/mode
        folder.mkdir(exist_ok=True)
        if args.mode=='preview':
            update(refs,mode,1.0)
            scene.render.filepath=str(HERE/'render'/f'{mode}_still.png')
            start=time.time();bpy.ops.render.render(write_still=True)
            print('STILL',mode,'seconds',round(time.time()-start,2),flush=True)
        else:
            for i in range(count):
                dest=folder/f'{i+1:04d}.png'
                if dest.exists() and not args.force:continue
                update(refs,mode,i/FPS)
                scene.render.filepath=str(dest)
                bpy.ops.render.render(write_still=True)
            print('COMPLETE',mode,count,flush=True)
    update(refs,'overview',0)
    bpy.context.view_layer.update();base.projections(scene)
    (HERE/'scene_info.json').write_text(json.dumps({'fps':FPS,'size':[1300,1080],'modes':MODES,'blender':bpy.app.version_string},indent=2),encoding='utf-8')


if __name__=='__main__':main()
