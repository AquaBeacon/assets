"""Typeset the thumbnail and silent Japanese explanation film.

Illustrative assets are Blender renders. Pillow is used for typography,
flat background colors, label leaders and QA contact sheets.
"""
import argparse
import json
import math
from pathlib import Path
import subprocess
import zipfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont

OUT=Path(__file__).resolve().parent
BRAND=OUT.parent/'aquabeacon-brand'
FFMPEG=Path(r'C:\Users\ryupc\anaconda3\Library\bin\ffmpeg.exe')
FFPROBE=FFMPEG.with_name('ffprobe.exe')
JP=Path(r'C:\Windows\Fonts\NotoSansJP-VF.ttf')
EN=Path(r'C:\Users\ryupc\.codex\plugins\cache\claude-cowork\anthropic-skills\1.0.0\skills\canvas-design\canvas-fonts\InstrumentSans-Regular.ttf')
SIZE=(1920,1080)
DIAGRAM_X=720
WHITE='#EAF9FF'; MUTED='#9BB7C5'; AQUA='#55EFDE'; AMBER='#FFCA71'

CHAPTERS=[
 {'start':0,'duration':5,'mode':'overview','title':['光と音で','水中の位置を測る'],'detail':['水中の位置推定と','藻場の3Dマッピング'],'caption':'水上の親機と水中の子機を、光と音でつなぎます。','accent':AQUA},
 {'start':5,'duration':5,'mode':'gps','title':['水上の親機が','位置の基準'],'detail':['親機のGPSで','水上の位置を取得'],'caption':'水中ではGPSを直接使えないため、水上の親機を基準にします。','accent':WHITE},
 {'start':10,'duration':7,'mode':'sound','title':['音で、','距離を測る'],'detail':['距離 = 音速 × 到達時間','有線で送信時刻を共有'],'caption':'親機からの音が子機へ届くまでの時間から、距離を求めます。','accent':AMBER},
 {'start':17,'duration':7,'mode':'light','title':['光で、','方向を測る'],'detail':['子機のライトを','親機のカメラで捉える'],'caption':'親機のカメラが子機のライトを捉え、子機の方向を推定します。','accent':AQUA},
 {'start':24,'duration':6,'mode':'position','title':['距離と方向から','位置を求める'],'detail':['音の距離 + 光の方向','親機のGPSと組み合わせる'],'caption':'距離と方向を合わせ、親機のGPSを基に子機の位置を求めます。','accent':AQUA},
 {'start':30,'duration':6,'mode':'mapping','title':['撮影した映像を','正しい位置へ'],'detail':['位置情報と映像を結びつけ','藻場の3Dマッピングへ'],'caption':'撮影した映像を位置情報に結びつけ、藻場の3Dマッピングへ。','accent':'#8DFACB'},
 {'start':36,'duration':4,'mode':'overview','title':['光と音で、','藻場のマッピングへ'],'detail':['AquaBeacon','浅い海の観測を支える'],'caption':'浅い海を想定。濁りでライトを見失う場合があります。','accent':AQUA},
]


def font(size,bold=False,english=False):
    f=ImageFont.truetype(str(EN if english else JP),size)
    if not english:
        try:f.set_variation_by_axes([700 if bold else 420])
        except (OSError,ValueError):pass
    return f


def text(draw,xy,body,size,color=WHITE,bold=False,english=False):
    f=font(size,bold,english)
    # Anchor on ascender keeps line placement consistent across Japanese text.
    draw.text(xy,body,font=f,fill=color,anchor='lt',stroke_width=0)
    return draw.textlength(body,font=f)


def background():
    y,x=np.mgrid[0:1080,0:1920]
    r=np.sqrt(((x-1480)/1380)**2+((y-420)/1120)**2)
    glow=np.clip(1-r,0,1)[...,None]
    base=np.array([5,16,31]);high=np.array([14,46,61])
    rgb=base+(high-base)*glow
    # Quiet bottom strip gives subtitles a consistent contrast across shots.
    shade=np.clip((y-940)/110,0,1)[...,None]
    rgb=rgb*(1-shade*.38)
    return Image.fromarray(rgb.astype('uint8'),'RGB').convert('RGBA')


def brand(canvas):
    im=Image.open(BRAND/'aquabeacon_logo_transparent.png').convert('RGBA')
    im=im.crop(im.getchannel('A').getbbox())
    im.thumbnail((530,140),Image.Resampling.LANCZOS)
    canvas.alpha_composite(im,(82,65))


def diagram_labels(canvas, mode, thumbnail=False):
    d=ImageDraw.Draw(canvas)
    points=json.loads((OUT/'projection.json').read_text(encoding='utf-8'))
    size=32 if not thumbnail else 35
    def leader(key,label,end,pos,color=WHITE):
        p=points[key]; p=(p[0]+DIAGRAM_X,p[1])
        d.line([p,end],fill='#86AEBD',width=2)
        d.ellipse((p[0]-3,p[1]-3,p[0]+3,p[1]+3),fill=color)
        text(d,pos,label,size,color,True)
    leader('parent','親機（水上）',(1450,279),(1468,252))
    leader('child','子機（水中）',(1635,743),(1652,717))
    leader('satellite','GPS衛星',(1480,97),(1497,75),MUTED)
    text(d,(1785,453),'水面',29,MUTED)
    text(d,(1060,853),'藻場',30,'#A1E4C9')
    if mode in ('light','overview','position'):
        text(d,(1112,410),'カメラ',29,AQUA,True)
        text(d,(1500,636),'ライト',29,AQUA,True)
    if mode=='sound':
        text(d,(1390,506),'音',42,AMBER,True)
    if mode=='mapping':
        text(d,(1640,853),'撮影する範囲',28,'#8DFACB',True)


def thumbnail():
    canvas=background()
    visual=Image.open(OUT/'render'/'overview_still.png').convert('RGBA')
    canvas.alpha_composite(visual,(DIAGRAM_X,0))
    brand(canvas)
    d=ImageDraw.Draw(canvas)
    x=84
    for word,color in [('光',AQUA),('と',WHITE),('音',AMBER),('で',WHITE)]:
        x+=text(d,(x,297),word,104,color,True)
    text(d,(84,427),'水中の位置を',94,WHITE,True)
    text(d,(84,550),'測る',104,WHITE,True)
    text(d,(88,750),'水中の位置推定と',42,MUTED)
    text(d,(88,816),'藻場の3Dマッピング',42,MUTED)
    text(d,(88,970),'音 = 距離',41,AMBER,True)
    text(d,(385,970),'光 = 方向',41,AQUA,True)
    diagram_labels(canvas,'overview',True)
    canvas.convert('RGB').save(OUT/'aquabeacon_thumbnail.png')
    canvas.convert('RGB').save(OUT/'aquabeacon_thumbnail.jpg',quality=95,subsampling=0)
    small=canvas.convert('RGB');small.thumbnail((480,270),Image.Resampling.LANCZOS)
    small.save(OUT/'preview'/'thumbnail_480.png')


def overlay(chapter,index):
    canvas=Image.new('RGBA',SIZE,(0,0,0,0))
    brand(canvas)
    d=ImageDraw.Draw(canvas)
    # A single composition and generous line spacing keep the diagram dominant.
    longest=max(len(t) for t in chapter['title'])
    title_size=76 if longest>=9 else 86
    for i,line in enumerate(chapter['title']):
        text(d,(84,307+i*116),line,title_size,chapter['accent'] if i==0 else WHITE,True)
    for i,line in enumerate(chapter['detail']):
        s=41 if chapter['mode']!='sound' or i else 45
        color=chapter['accent'] if chapter['mode']=='sound' and i==0 else MUTED
        text(d,(88,655+i*69),line,s,color,False,english=line=='AquaBeacon')
    caption=chapter['caption']
    size=42
    width=d.textlength(caption,font=font(size))
    text(d,((1920-width)/2,976),caption,size,WHITE)
    # Labels persist with the diagram while each chapter's text fades in/out.
    diagram_labels(canvas,chapter['mode'])
    path=OUT/'overlays'/f'chapter_{index:02d}.png'
    canvas.save(path)
    preview=background()
    preview.alpha_composite(Image.open(OUT/'render'/f"{chapter['mode']}_still.png").convert('RGBA'),(DIAGRAM_X,0))
    preview.alpha_composite(canvas)
    preview.convert('RGB').save(OUT/'preview'/f'chapter_{index:02d}.png')
    return path


def run(args,cwd=None):
    subprocess.run([str(FFMPEG),'-y','-hide_banner','-loglevel','warning',*map(str,args)],check=True,cwd=cwd)


def timestamp(t):
    return f'{int(t)//3600:02}:{int(t)//60%60:02}:{int(t)%60:02},{round((t%1)*1000):03}'


def make_video():
    for mode in ('overview','gps','sound','light','position','mapping'):
        folder=OUT/'render'/mode
        if not list(folder.glob('*.png')):raise RuntimeError('Missing rendered clip: '+mode)
        run(['-framerate','12','-start_number','1','-i',folder/'%04d.png','-c:v','qtrle','-pix_fmt','argb','-an',OUT/'clips'/f'{mode}.mov'])
    segments=[]
    for i,ch in enumerate(CHAPTERS):
        duration=ch['duration'];output=OUT/'clips'/f'chapter_{i:02d}.mp4'
        filters=f'[0:v]format=rgba[b];[1:v]fps=24,format=rgba[d];[b][d]overlay=x={DIAGRAM_X}:y=0:format=auto[v];[2:v]format=rgba,fade=t=in:st=0:d=0.30:alpha=1,fade=t=out:st={duration-.2}:d=0.2:alpha=1[t];[v][t]overlay=format=auto,format=yuv420p[out]'
        run(['-loop','1','-framerate','24','-i',OUT/'background.png','-stream_loop','-1','-i',OUT/'clips'/f"{ch['mode']}.mov",'-loop','1','-framerate','24','-i',OUT/'overlays'/f'chapter_{i:02d}.png','-filter_complex',filters,'-map','[out]','-t',duration,'-r','24','-c:v','libx264','-preset','medium','-crf','18','-an',output])
        segments.append(output)
        print('CHAPTER_ENCODED',i,flush=True)
    finish_video()


def finish_video():
    listing=OUT/'clips'/'concat.txt'
    listing.write_text('\n'.join("file 'chapter_"+f'{i:02d}'+".mp4'" for i in range(len(CHAPTERS))),encoding='utf-8')
    run(['-f','concat','-safe','0','-i',listing.name,'-c','copy','-movflags','+faststart',OUT/'aquabeacon_explainer.mp4'],cwd=listing.parent)
    # Short preview only; the full film is supplied in MP4.
    run(['-ss','9.5','-i',OUT/'aquabeacon_explainer.mp4','-t','15','-filter_complex','fps=10,scale=768:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=160[p];[b][p]paletteuse=dither=sierra2_4a','-loop','0',OUT/'aquabeacon_explainer_preview.gif'])
    subtitles='\n\n'.join(f'{i+1}\n{timestamp(ch["start"])} --> {timestamp(ch["start"]+ch["duration"]-.05)}\n{ch["caption"]}' for i,ch in enumerate(CHAPTERS))
    (OUT/'aquabeacon_explainer.srt').write_text(subtitles+'\n',encoding='utf-8')


def validate_and_package():
    cmd=[str(FFPROBE),'-v','error','-count_frames','-show_entries','stream=codec_type,codec_name,width,height,pix_fmt,r_frame_rate,nb_read_frames:format=duration','-of','json',str(OUT/'aquabeacon_explainer.mp4')]
    report=json.loads(subprocess.run(cmd,capture_output=True,text=True,check=True).stdout)
    streams=report['streams'];assert len(streams)==1 and streams[0]['codec_type']=='video'
    assert streams[0]['width']==1920 and streams[0]['height']==1080
    assert streams[0]['nb_read_frames']=='960'
    assert abs(float(report['format']['duration'])-40)<.02
    report['thumbnail']={'dimensions':list(Image.open(OUT/'aquabeacon_thumbnail.png').size)}
    report['silent']=True
    (OUT/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    with zipfile.ZipFile(OUT/'aquabeacon_explainer_assets.zip','w',zipfile.ZIP_DEFLATED) as z:
        for name in ['aquabeacon_thumbnail.png','aquabeacon_thumbnail.jpg','aquabeacon_explainer.mp4','aquabeacon_explainer_preview.gif','aquabeacon_explainer.srt','aquabeacon_explainer.blend','STORYBOARD.md','README.md','build_scene.py','compose_video.py','projection.json','scene_info.json']:
            z.write(OUT/name,name)
    print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)


def main():
    p=argparse.ArgumentParser();p.add_argument('--preview-only',action='store_true');p.add_argument('--finish-only',action='store_true');opts=p.parse_args()
    if opts.finish_only:
        finish_video();validate_and_package();return
    for directory in ('preview','overlays','clips'):(OUT/directory).mkdir(exist_ok=True)
    background().convert('RGB').save(OUT/'background.png')
    thumbnail()
    for i,ch in enumerate(CHAPTERS):overlay(ch,i)
    montage=Image.new('RGB',(1440,810),'#071727')
    for i in range(7):
        im=Image.open(OUT/'preview'/f'chapter_{i:02d}.png').resize((480,270),Image.Resampling.LANCZOS)
        montage.paste(im,((i%3)*480,(i//3)*270))
    montage.save(OUT/'preview'/'chapter_contact_sheet.png')
    if opts.preview_only:return
    make_video();validate_and_package()


if __name__=='__main__':main()
