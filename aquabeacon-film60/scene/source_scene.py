"""Original Blender cutaway diagram for AquaBeacon's operating principle."""
import argparse
import json
import math
from pathlib import Path
import random
import sys

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

OUT = Path(__file__).resolve().parent
FPS = 24
RENDER_FPS = 12
W, H = 1240, 1080
PARENT = Vector((-1.6, 0.3, 4.0))
CHILD = Vector((1.15, -0.1, 1.42))
SOUND_ORIGIN = PARENT + Vector((0.32, -0.13, -0.30))
LIGHT_TARGET = PARENT + Vector((0.08, -0.48, -0.18))


def col(value):
    rgb = [int(value[i:i+2], 16) / 255 for i in (0, 2, 4)]
    return tuple(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in rgb) + (1,)


def mat(name, color, metallic=0, rough=0.35, emission=0, alpha=1):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.diffuse_color = col(color)[:3] + (alpha,)
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = col(color)
    p.inputs['Metallic'].default_value = metallic
    p.inputs['Roughness'].default_value = rough
    p.inputs['Emission Color'].default_value = col(color)
    p.inputs['Emission Strength'].default_value = emission
    p.inputs['Alpha'].default_value = alpha
    if alpha < 1:
        m.surface_render_method = 'DITHERED'
    return m


def parent_obj(obj, root):
    if root:
        obj.parent = root
    return obj


def cube(name, pos, scale, material, bevel=0.08, parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=pos)
    ob = bpy.context.object
    ob.name = name
    ob.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ob.data.materials.append(material)
    if bevel:
        mod = ob.modifiers.new('Soft manufactured edges', 'BEVEL')
        mod.width = bevel
        mod.segments = 3
        ob.modifiers.new('Weighted corner normals', 'WEIGHTED_NORMAL')
    return parent_obj(ob, parent)


def cyl(name, pos, radius, depth, material, parent=None, direction=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=radius, depth=depth, location=pos)
    ob = bpy.context.object
    ob.name = name
    ob.data.materials.append(material)
    for polygon in ob.data.polygons:
        polygon.use_smooth = True
    bevel = ob.modifiers.new('Machined edge', 'BEVEL')
    bevel.width = min(radius * 0.15, 0.04)
    bevel.segments = 3
    ob.modifiers.new('Weighted normals', 'WEIGHTED_NORMAL')
    if direction:
        ob.rotation_euler = Vector(direction).to_track_quat('Z', 'Y').to_euler()
    return parent_obj(ob, parent)


def sphere(name, pos, radius, material, parent=None, scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=radius, location=pos)
    ob = bpy.context.object
    ob.name = name
    ob.scale = scale
    ob.data.materials.append(material)
    for polygon in ob.data.polygons:
        polygon.use_smooth = True
    return parent_obj(ob, parent)


def tube(name, points, width, material, parent=None, bezier=False):
    curve = bpy.data.curves.new(name, 'CURVE')
    curve.dimensions = '3D'
    curve.resolution_u = 12
    curve.bevel_depth = width
    curve.bevel_resolution = 3
    curve.use_fill_caps = True
    if bezier:
        spline = curve.splines.new('BEZIER')
        spline.bezier_points.add(len(points)-1)
        for b, p in zip(spline.bezier_points, points):
            b.co = p
            b.handle_left_type = 'AUTO'
            b.handle_right_type = 'AUTO'
    else:
        spline = curve.splines.new('POLY')
        spline.points.add(len(points)-1)
        for b, p in zip(spline.points, points):
            b.co = (*p, 1)
    ob = bpy.data.objects.new(name, curve)
    bpy.context.scene.collection.objects.link(ob)
    curve.materials.append(material)
    return parent_obj(ob, parent)


def connector(name, start, end, width, material, arrow=False):
    ob = tube(name, [start, end], width, material)
    if arrow:
        vector = Vector(end) - Vector(start)
        bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=width*4, radius2=0, depth=width*10, location=Vector(end)-vector.normalized()*width*5)
        head = bpy.context.object
        head.name = name + ' / direction'
        head.rotation_euler = vector.to_track_quat('Z', 'Y').to_euler()
        head.data.materials.append(material)
        return [ob, head]
    return [ob]


def empty(name, pos=(0,0,0)):
    ob = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = pos
    return ob


def light(name, pos, energy, size, color):
    data = bpy.data.lights.new(name, 'AREA')
    data.energy = energy
    data.shape = 'DISK'
    data.size = size
    data.color = col(color)[:3]
    ob = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = pos
    ob.rotation_euler = (Vector((0,0,2)) - ob.location).to_track_quat('-Z','Y').to_euler()


def build():
    scene = bpy.data.scenes.new('AquaBeacon / 光と音の水中測位')
    bpy.context.window.scene = scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 24
    scene.cycles.use_denoising = True
    scene.cycles.device = 'GPU'
    scene.render.engine = 'BLENDER_EEVEE'
    if hasattr(scene.eevee, 'taa_render_samples'):
        scene.eevee.taa_render_samples = 128
    scene.render.resolution_x, scene.render.resolution_y = W, H
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = True
    scene.render.use_persistent_data = True
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.render.image_settings.compression = 15
    scene.render.fps = FPS
    scene.frame_start, scene.frame_end = 1, 40*FPS
    scene.view_settings.view_transform = 'AgX'
    scene.world = bpy.data.worlds.new('Studio ocean ambient')
    scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value = col('9DC4D8')
    scene.world.node_tree.nodes['Background'].inputs[1].default_value = 0.4
    light('Sun softbox', (-4,-5,10), 1200, 7, 'E7FCFF')
    light('Aqua rim', (5,3,6), 850, 5, '82ECE9')
    light('Front fill', (2,-6,4), 550, 5, 'BCD8FF')

    white=mat('Ivory / hull', 'EAF9FF', 0.1, 0.29)
    dark=mat('Graphite / structure', '163245', 0.35, 0.35)
    teal=mat('Aqua / float', '22CEC9', 0.18, 0.27)
    blue=mat('Blue / photovoltaic', '245999', 0.4, 0.29)
    glass=mat('Camera black glass', '061526', 0.45, 0.12)
    sea=mat('Ocean / back wall', '134859', 0.0, 0.65)
    seabed=mat('Seabed / sand', '2C5660', 0.02, 0.85)
    kelp_mats=[mat('Seagrass / '+str(i), c, 0, 0.65) for i,c in enumerate(['27A982','167B78','42C092'])]
    aqua=mat('Light / aqua', '07E4D3', 0, 0.3, 0.9)
    amber=mat('Sound / amber', 'FFA62B', 0, 0.4, 0.7)
    gps_mat=mat('GPS / white signal', 'DBF9FF', 0, 0.4, 1.5)
    cablemat=mat('Tether / gray', 'A4BDC5', 0.2, 0.4)
    gridmat=mat('World coordinates / grid', '2D919C', 0, 0.65, 0.25)
    mapmat=mat('Map / registered point cloud', '7AFFC8', 0, 0.3, 1.2)
    water=mat('Water surface / transparent', '3EABB8', 0.02, 0.25, 0.05, 0.16)

    cube('Ocean / seabed slab', (0,0,-0.28), (6.4,4.4,0.5), seabed, 0.20)
    cube('Ocean / far cutaway wall', (0,2.18,1.96), (6.4,0.07,4.4), sea, 0.03)
    cube('Ocean / left cutaway wall', (-3.18,0,1.96), (0.07,4.4,4.4), sea, 0.03)
    cube('Ocean / surface', (0,0,4.08), (6.35,4.35,0.018), water, 0)
    for i in range(9):
        x=-3.0+i*0.75
        tube('Seabed grid X / '+str(i), [(x,-2.0,0.005),(x,2.0,0.005)], 0.008, gridmat)
    for i in range(6):
        y=-1.9+i*0.75
        tube('Seabed grid Y / '+str(i), [(-3,y,0.007),(3,y,0.007)], 0.008, gridmat)
    for i in range(7):
        x=-3.0+i*0.9
        pts=[(x, -2.15,4.12),(x+0.15,-1.3,4.12),(x-0.08,-0.4,4.12),(x+0.1,0.6,4.12),(x,2.15,4.12)]
        tube('Surface wave / '+str(i), pts, 0.01, gridmat, bezier=True)

    random.seed(18)
    for n in range(16):
        x=random.uniform(-2.8,2.8); y=random.uniform(-1.8,1.7)
        if x > 0 and y < 0:
            continue
        for blade in range(3):
            height=random.uniform(0.4,1.05)
            sway=random.uniform(-0.28,0.28)
            verts=[]
            for j in range(9):
                z=j/8*height
                xx=x+sway*math.sin(j/8*2.4)+blade*0.06
                width=0.05*(math.sin(j/8*math.pi)*0.7+0.2)
                verts.extend([(xx-width,y+blade*0.035,z),(xx+width,y+blade*0.035,z)])
            faces=[(2*j,2*j+1,2*j+3,2*j+2) for j in range(8)]
            mesh=bpy.data.meshes.new('Seagrass ribbon')
            mesh.from_pydata(verts,[],faces); mesh.update()
            ob=bpy.data.objects.new('Seagrass / '+str(n)+'-'+str(blade),mesh)
            scene.collection.objects.link(ob)
            ob.data.materials.append(kelp_mats[n%3])
            sub=ob.modifiers.new('Soft leaf', 'SUBSURF'); sub.levels=1
    for pos,sc in [((-2,-1.4,0.1),(.45,.32,.18)),((.5,1.3,.12),(.48,.4,.25)),((2,1.5,.1),(.3,.38,.17))]:
        sphere('Seabed rock', pos,1,dark,scale=sc)

    boat=empty('Parent / surface unit', PARENT)
    cube('Parent / deck', (0,0,.18), (1.95,1.26,.2), white,0.13,boat)
    for y in (-0.62,0.62):
        sphere('Parent / pontoon', (0,y,0),0.48,teal,boat,(2.1,.5,.48))
    cube('Parent / electronics', (0,.05,.47),(0.85,0.73,0.42),dark,0.10,boat)
    cube('Parent / solar panel', (0,.08,.71),(0.93,.79,.035),blue,0.03,boat)
    for x in (-.32,-.10,.12,.34):
        tube('Parent / panel strips', [(x,-.28,.733),(x,.43,.733)], .009,white,boat)
    cyl('Parent / GPS mast',(-.65,.17,.82), .032,1.18,white,boat)
    sphere('Parent / GPS antenna',(-.65,.17,1.4),.11,white,boat,(1.2,1.2,.7))
    cyl('Parent / camera body',(.08,-.48,-.13),.18,.23,dark,boat,direction=(1,0,-1))
    cyl('Parent / camera lens',(.18,-.48,-.23),.115,.07,glass,boat,direction=(1,0,-1))
    cyl('Parent / sound transducer',(.32,-.13,-.28),.16,.18,dark,boat)

    child=empty('Child / underwater unit', CHILD)
    cyl('Child / sealed body', (0,0,0),.30,.92,teal,child)
    for z in (-.49,.49):
        cyl('Child / endcap',(0,0,z),.34,.12,dark,child)
    cube('Child / sensor bridge',(0,-.35,-.12),(1.25,.24,.15),white,.04,child)
    for x in (-.47,.47):
        cube('Child / camera pod',(x,-.40,-.25),(.29,.28,.3),dark,.05,child)
        cyl('Child / survey camera',(x,-.43,-.43),.11,.08,glass,child)
    for x in (-.48,.48):
        tube('Child / protective frame',[(x,.25,-.58),(x,.25,.56),(x,-.4,.56),(x,-.4,-.58)],.033,dark,child)
    sphere('Child / upward light',(.02,-.1,.63),.14,aqua,child)
    cyl('Child / sound receiver',(.23,.16,.59),.1,.14,dark,child)
    tube('Child / lower guard',[(-.45,-.4,-.59),(.45,-.4,-.59),(.45,.26,-.59),(-.45,.26,-.59),(-.45,-.4,-.59)],.03,white,child)
    cable=tube('Tether / shared transmit timing',[PARENT+Vector((-.6,.2,.1)),(-2.05,.0,3.55),(-1.5,-.08,2.3),CHILD+Vector((-.2,.13,.6))],.022,cablemat,bezier=True)

    satellite=empty('GPS satellite',(-1.20,1.0,6.60))
    cube('Satellite / bus',(0,0,0),(.43,.46,.43),white,.055,satellite)
    for x in (-.65,.65):
        cube('Satellite / solar array',(x,0,0),(0.78,.61,.04),blue,.02,satellite)
        for dx in (-.2,0,.2):
            tube('Satellite / cells',[(x+dx,-.26,.04),(x+dx,.26,.04)],.009,white,satellite)
    satellite.rotation_euler=(.12,-.15,-.15)
    gps_line=connector('GPS / satellite to surface',(-1.2,1,6.36), PARENT+Vector((-.65,.17,1.4)),.018,gps_mat,True)
    gps_dot=sphere('GPS / traveling fix',(-1.2,1,6.36),.065,gps_mat)

    sound_rings=[]
    for n in range(3):
        pts=[(math.cos(a*math.tau/80),math.sin(a*math.tau/80),0) for a in range(81)]
        ring=tube('Sound / traveling wave '+str(n+1),pts,.027,amber)
        sound_rings.append(ring)
    sound_axis=connector('Sound / propagation',SOUND_ORIGIN,CHILD+Vector((.23,.16,.59)),.014,amber,True)
    light_axis=connector('Light / child to parent',CHILD+Vector((.02,-.1,.63)),LIGHT_TARGET,.026,aqua,True)
    light_dot=sphere('Light / traveling beacon',CHILD+Vector((.02,-.1,.63)),.08,aqua)
    beam_mat=mat('Light / camera sight cone','49E4E4',0,.5,.5,.10)
    start=CHILD+Vector((.02,-.1,.63)); vec=LIGHT_TARGET-start
    bpy.ops.mesh.primitive_cone_add(vertices=48,radius1=.26,radius2=.045,depth=vec.length,location=(start+LIGHT_TARGET)/2)
    beam=bpy.context.object; beam.name='Light / tracking beam'
    beam.rotation_euler=vec.to_track_quat('Z','Y').to_euler(); beam.data.materials.append(beam_mat)

    target=empty('Position / reticle',CHILD)
    position_objects=[]
    for a,b in [((-.55,0,0),(.55,0,0)),((0,-.55,0),(0,.55,0)),((0,0,-.7),(0,0,.8))]:
        position_objects.append(tube('Position / coordinate axis',[a,b],.013,mapmat,target))
    for n in range(3):
        pts=[]
        for i in range(65):
            angle=i/64*math.tau
            p=[.65*math.cos(angle),.65*math.sin(angle),0]
            if n==1: p=[p[0],0,p[1]]
            if n==2: p=[0,p[0],p[1]]
            pts.append(p)
        position_objects.append(tube('Position / solved coordinate sphere',pts,.01,mapmat,target))

    mapping=[]
    for x in range(7):
        for y in range(6):
            px=.05+x*.42; py=-1.55+y*.38
            z=.075+.06*math.sin(x*.9)*math.cos(y*.8)
            dot=sphere('Mapping / georeferenced sample', (px,py,z),.035,mapmat)
            mapping.append(dot)
    mapping_line=tube('Mapping / camera footprint',[(.1,-1.6,.06),(2.75,-1.6,.06),(2.75,.5,.06),(.1,.5,.06),(.1,-1.6,.06)],.018,mapmat)
    mapping.append(mapping_line)
    scan=tube('Mapping / image scan',[(.12,-1.6,.1),(.12,.5,.1)],.035,mapmat)
    scan_cam=connector('Mapping / downward camera',CHILD+Vector((-.47,-.43,-.43)),(.6,-.45,.15),.018,mapmat,True)
    mapping.extend(scan_cam)
    route=tube('Mapping / tracked path',[(.6,-.4,1.42),(1.0,-.1,1.42),(1.4,-.1,1.42),(1.8,-.35,1.42)],.014,teal,bezier=True)
    mapping.append(route)

    cam_data=bpy.data.cameras.new('Explanation / orthographic camera')
    cam=bpy.data.objects.new('Explanation / orthographic camera',cam_data)
    scene.collection.objects.link(cam)
    cam.location=(10,-16,11)
    cam.rotation_euler=(Vector((0,0,2.85))-cam.location).to_track_quat('-Z','Y').to_euler()
    cam_data.type='ORTHO'; cam_data.ortho_scale=10.8
    scene.camera=cam
    refs={'scene':scene,'boat':boat,'child':child,'satellite':satellite,'cable':cable,'gps':gps_line+[gps_dot], 'gps_dot':gps_dot,'sound':sound_rings+sound_axis,'rings':sound_rings,'light':light_axis+[beam,light_dot],'light_dot':light_dot,'position':position_objects,'mapping':mapping+[scan],'scan':scan,'target':target}
    return refs


def update(refs, mode, t, bake_frame=None):
    active = {
        'overview':{'gps','sound','light'},
        'gps':{'gps'},
        'sound':{'sound'},
        'light':{'light'},
        'position':{'gps','sound','light','position'},
        'mapping':{'mapping','position'},
    }[mode]
    for group in ('gps','sound','light','position','mapping'):
        for ob in refs[group]:
            ob.hide_render = group not in active
            ob.hide_viewport = group not in active
            if bake_frame:
                ob.keyframe_insert('hide_render',frame=bake_frame)
                ob.keyframe_insert('hide_viewport',frame=bake_frame)
    refs['boat'].rotation_euler = (.015*math.sin(t*math.tau/4), .01*math.cos(t*math.tau/4),0)
    refs['child'].location = CHILD+Vector((0,0,.03*math.sin(t*math.tau/4)))
    refs['target'].location=refs['child'].location
    for n,ring in enumerate(refs['rings']):
        p=((t/2.4)+n/3)%1
        end=CHILD+Vector((.23,.16,.59))
        vector=end-SOUND_ORIGIN
        ring.location=SOUND_ORIGIN+vector*p
        ring.rotation_euler=vector.to_track_quat('Z','Y').to_euler()
        r=.10+.36*p
        ring.scale=(r,r,r)
    p=(t/1.6)%1
    start=CHILD+Vector((.02,-.1,.63))
    refs['light_dot'].location=start+(LIGHT_TARGET-start)*p
    refs['light_dot'].scale=(.7+.3*math.sin(t*math.tau/1.6),)*3
    sat_start=Vector((-1.2,1,6.36)); sat_end=PARENT+Vector((-.65,.17,1.4))
    refs['gps_dot'].location=sat_start+(sat_end-sat_start)*((t/2.4)%1)
    refs['scan'].location.x=2.60*((t/4)%1)
    if bake_frame:
        for ob in [refs['boat'],refs['child'],refs['target'],refs['gps_dot'],refs['light_dot'],refs['scan']]+refs['rings']:
            for prop in ('location','rotation_euler','scale'):
                ob.keyframe_insert(prop,frame=bake_frame)


def mode_at(t):
    if t<5:return 'overview'
    if t<10:return 'gps'
    if t<17:return 'sound'
    if t<24:return 'light'
    if t<30:return 'position'
    if t<36:return 'mapping'
    return 'overview'


def projections(scene):
    points={'parent':PARENT+Vector((0,0,.6)),'child':CHILD,'satellite':Vector((-1.2,1,6.6)), 'parent_camera':LIGHT_TARGET,'child_light':CHILD+Vector((.02,-.1,.63)), 'seabed':Vector((1.2,-1.2,0)), 'waterline':Vector((2.8,.9,4.10))}
    result={}
    for key,point in points.items():
        v=world_to_camera_view(scene,scene.camera,point)
        result[key]=[round(v.x*W,2),round((1-v.y)*H,2)]
    (OUT/'projection.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')


def main():
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    p=argparse.ArgumentParser();p.add_argument('--render',choices=['preview','all','build'],default='preview');opts=p.parse_args(args)
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'render').mkdir(exist_ok=True)
    refs=build();scene=refs['scene']
    for frame in range(1,40*FPS+1):
        t=(frame-1)/FPS
        update(refs,mode_at(t),t,frame)
    scene.timeline_markers.new('全体像',frame=1)
    for time,name in [(5,'GPS'),(10,'音 = 距離'),(17,'光 = 方向'),(24,'位置推定'),(30,'3Dマッピング'),(36,'AquaBeacon')]:
        scene.timeline_markers.new(name,frame=time*FPS+1)
    scene.frame_set(25)
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                area.spaces.active.region_3d.view_perspective='CAMERA'
                area.spaces.active.shading.type='MATERIAL'
                area.spaces.active.shading.use_scene_world=True
                area.spaces.active.shading.use_scene_lights=True
                area.spaces.active.overlay.show_overlays=False
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'aquabeacon_explainer.blend'))
    bpy.context.view_layer.update();projections(scene)
    if opts.render=='build':return
    # The saved file retains the complete 40-second timeline. Clip rendering
    # uses explicit per-frame controls, so remove the baked actions in memory
    # to prevent dependency-graph evaluation from restoring timeline values.
    for ob in scene.objects:
        if ob.animation_data:
            ob.animation_data_clear()
    for mode in ['overview','gps','sound','light','position','mapping']:
        scene.frame_set(1);update(refs,mode,1.2)
        scene.render.filepath=str(OUT/'render'/f'{mode}_still.png')
        print('RENDER_STILL',mode,flush=True)
        bpy.ops.render.render(write_still=True)
        if opts.render=='preview':continue
        folder=OUT/'render'/mode;folder.mkdir(exist_ok=True)
        count=48 if mode in ('overview','mapping') else 29
        for frame in range(count):
            destination=folder/f'{frame+1:04d}.png'
            scene.frame_set(1);update(refs,mode,frame/RENDER_FPS)
            scene.render.filepath=str(destination)
            bpy.ops.render.render(write_still=True)
        print('CLIP_COMPLETE',mode,count,flush=True)
    (OUT/'scene_info.json').write_text(json.dumps({'blender':bpy.app.version_string,'scene_fps':FPS,'clip_render_fps':RENDER_FPS,'duration':40,'diagram_dimensions':[W,H]},ensure_ascii=False,indent=2),encoding='utf-8')


if __name__=='__main__':main()
