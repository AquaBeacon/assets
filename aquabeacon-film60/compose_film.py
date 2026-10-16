"""Compose Blender sequences, supplied footage, typography and original audio."""
import argparse
import json
import math
import re
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

OUT=Path(__file__).resolve().parent
FF=Path('C:/Users/ryupc/anaconda3/Library/bin/ffmpeg.exe')
FP=FF.with_name('ffprobe.exe')
FONT=Path('C:/Windows/Fonts/NotoSansJP-VF.ttf')
W,H=1920,1080
FPS=30
AQUA='#20D9D2'; AMBER='#F3B44E'; GREEN='#8ED8A5'; WHITE='#F0F7F8'; MUTED='#AAC6CD'
DX,DY,DS=700,35,.88
SZ=(int(1300*DS),int(1080*DS))

SHOTS=[
 {'id':'00_coast','start':0,'duration':2,'type':'photo','source':'IMG_7986','title':['海の中の、どこ？'],'detail':['藻場の広がりを、知るために。']},
 {'id':'01_meadow','start':2,'duration':5,'type':'diagram','mode':'meadow','eyebrow':'海を調べるために','title':['海草や海藻が','育つ「藻場」'],'detail':['撮った場所が分かれば、','調査の手がかりになる。'],'color':GREEN},
 {'id':'02_gps','start':7,'duration':7,'type':'diagram','mode':'gps','eyebrow':'水中の位置情報','title':['水中では、','位置が','分かりにくい。'],'detail':['GPSが使いにくい。','海藻の目印も揺れる。'],'color':WHITE},
 {'id':'03_intro','start':14,'duration':5,'type':'diagram','mode':'overview','eyebrow':'AQUABEACON','title':['光と音を、','組み合わせる。'],'detail':['水上の装置と','水中の装置をつなぐ。'],'color':AQUA},
 {'id':'04_sound','start':19,'duration':9,'type':'diagram','mode':'sound','eyebrow':'ふたつの手がかり  01','title':['音で、','距離を測る。'],'detail':['音が届くまでの時間から、','どれだけ離れたかを知る。'],'color':AMBER},
 {'id':'05_light','start':28,'duration':8,'type':'diagram','mode':'light','eyebrow':'ふたつの手がかり  02','title':['光で、','方向を測る。'],'detail':['水中のライトを、','水上のカメラで捉える。'],'color':AQUA},
 {'id':'06_position','start':36,'duration':6,'type':'diagram','mode':'position','eyebrow':'位置を推定する','title':['距離と方向。','水中の位置へ。'],'detail':['水上のGPSも組み合わせる。'],'color':AQUA},
 {'id':'07_mapping','start':42,'duration':4,'type':'diagram','mode':'mapping','eyebrow':'地図づくりへ','title':['映像と位置を、','結びつける。'],'detail':['撮影したデータを記録。','後処理で、3Dの地図へ。'],'color':GREEN},
 {'id':'08_assembly','start':46,'duration':3,'type':'video','source':'assembly_24-32_sdr.mp4','ss':5,'title':['つくって、確かめる。'],'detail':['機体の組立']},
 {'id':'09_hardware','start':49,'duration':2,'type':'photo','source':'IMG_8027','title':['つくって、確かめる。'],'detail':['試作機の準備']},
 {'id':'10_field','start':51,'duration':3,'type':'portrait','source':'harbor_full_sdr.mp4','ss':.2,'title':['地図づくりへ。','開発は、続く。'],'detail':['水上での機体の様子','位置推定・マッピングを開発中']},
 {'id':'11_end','start':54,'duration':6,'type':'end','source':'IMG_7986','title':['藻場を調べる人たちへ。'],'detail':['光と音で、水中の位置を知る。']},
]


def font(size,bold=False):
    f=ImageFont.truetype(str(FONT),size)
    try:f.set_variation_by_axes([700 if bold else 450])
    except (ValueError,OSError):pass
    return f


def text(d,xy,s,size=40,color=WHITE,bold=False):
    d.text(xy,s,font=font(size,bold),fill=color,anchor='lt')


def run(args):
    normalized=[a.as_posix() if isinstance(a,Path) else str(a) for a in args]
    cmd=[str(FF),'-y','-hide_banner','-loglevel','warning','-filter_complex_threads','4',*normalized]
    subprocess.run(cmd,check=True)


def logo(im,pos=(86,66),width=375):
    x=Image.open(OUT.parent/'aquabeacon-brand'/'aquabeacon_logo_transparent.png').convert('RGBA')
    x=x.crop(x.getchannel('A').getbbox())
    x.thumbnail((width,int(width*.32)),Image.Resampling.LANCZOS)
    im.alpha_composite(x,pos)
    return x.size


def gradient_background():
    yy,xx=np.mgrid[:H,:W]
    glow=np.clip(1-np.sqrt(((xx-1440)/1530)**2+((yy-450)/1200)**2),0,1)[...,None]
    rgb=np.array([5,17,29])+glow*np.array([8,29,34])
    return Image.fromarray(rgb.astype('uint8')).convert('RGBA')


def dark_mask(top=.06,bottom=.80,left=.08):
    yy,xx=np.mgrid[:H,:W]
    a=top+(bottom-top)*(yy/H)**2+left*(1-xx/W)
    rgba=np.zeros((H,W,4),dtype=np.uint8)
    rgba[:,:,:3]=[2,14,24]
    rgba[:,:,3]=(np.clip(a,0,.9)*255).astype('uint8')
    return Image.fromarray(rgba,'RGBA')


def photo_background(name):
    im=Image.open(OUT/'media'/'photos'/f'{name}.jpg').convert('RGB')
    return ImageOps.fit(im,(W,H),Image.Resampling.LANCZOS,centering=(.5,.48)).convert('RGBA')


def label_leader(im,key,label,endpoint,xy,color=MUTED):
    coords=json.loads((OUT/'scene'/'projection.json').read_text(encoding='utf-8'))
    p=coords[key]; p=(DX+p[0]*DS,DY+p[1]*DS)
    d=ImageDraw.Draw(im)
    d.line([p,endpoint],fill=color,width=2)
    d.ellipse((p[0]-4,p[1]-4,p[0]+4,p[1]+4),fill=color)
    text(d,xy,label,30,color,True)


def overlay(shot):
    im=Image.new('RGBA',(W,H))
    d=ImageDraw.Draw(im)
    kind=shot['type']
    if kind=='diagram':
        logo(im)
        text(d,(90,245),shot['eyebrow'],28,MUTED)
        d.line((90,302,162,302),fill=shot['color'],width=5)
        for i,line in enumerate(shot['title']):
            text(d,(82,345+i*100),line,70,shot['color'] if i==0 else WHITE,True)
        y=max(620,345+len(shot['title'])*100+35)
        for i,line in enumerate(shot['detail']):text(d,(88,y+i*53),line,35,MUTED)
        mode=shot['mode']
        text(d,(88,855),'仕組みのイメージ' if mode!='meadow' else '藻場のイメージ',26,MUTED)
        if mode!='meadow':
            label_leader(im,'parent','水上の装置',(1508,267),(1520,248))
            label_leader(im,'child','水中の装置',(1580,720),(1592,701))
            text(d,(1560,90),'GPS',32,WHITE,True)
            label_leader(im,'satellite','',(1550,113),(1550,113))
            text(d,(1610,420),'水面',27,MUTED)
        if mode=='sound':
            text(d,(1218,497),'音',43,AMBER,True)
            text(d,(1170,549),'水上から水中へ',27,AMBER)
            text(d,(88,770),'ケーブルで測定時刻を合わせる',25,MUTED)
        if mode=='light':
            label_leader(im,'parent_camera','カメラ',(1020,445),(880,428),AQUA)
            label_leader(im,'child_light','ライト',(1570,595),(1580,578),AQUA)
            text(d,(1214,500),'光',43,AQUA,True)
        if mode=='position':
            d.rounded_rectangle((1080,809,1798,890),radius=12,fill=(5,21,32,235))
            text(d,(1190,832),'距離 ＋ 方向 ＋ 水上の位置',30,AQUA,True)
        if mode=='mapping':
            d.rounded_rectangle((1000,800,1498,880),radius=12,fill=(5,21,32,235))
            text(d,(1030,820),'撮影',28,GREEN,True)
            text(d,(1175,820),'記録',28,GREEN,True)
            text(d,(1320,820),'後処理',28,GREEN,True)
            d.line((1100,836,1145,836),fill=GREEN,width=2)
            d.line((1245,836,1290,836),fill=GREEN,width=2)
            text(d,(88,772),'地図化を目指して開発中',27,MUTED)
    elif kind=='end':
        im.alpha_composite(dark_mask(.40,.78,.10))
        logo(im,(560,240),800)
        d=ImageDraw.Draw(im)
        s=shot['title'][0];fw=d.textlength(s,font=font(64,True))
        text(d,((W-fw)/2,545),s,64,WHITE,True)
        s=shot['detail'][0];fw=d.textlength(s,font=font(39))
        text(d,((W-fw)/2,650),s,39,WHITE)
        s='研究開発中　・　仕組みの公開を目指して';fw=d.textlength(s,font=font(30))
        text(d,((W-fw)/2,805),s,30,MUTED)
    elif kind=='portrait':
        logo(im)
        text(d,(92,248),'実機の開発',28,AQUA)
        for i,line in enumerate(shot['title']):text(d,(84,345+i*110),line,78,WHITE,True)
        for i,line in enumerate(shot['detail']):text(d,(90,655+i*58),line,36,MUTED)
        text(d,(90,830),'提供素材より',25,MUTED)
    else:
        im.alpha_composite(dark_mask(.03,.87,.08))
        logo(im,(83,63),330)
        d=ImageDraw.Draw(im)
        if shot['start']==0:
            text(d,(88,420),shot['title'][0],98,WHITE,True)
            text(d,(96,560),shot['detail'][0],45,WHITE)
        else:
            text(d,(85,720),shot['title'][0],70,WHITE,True)
            text(d,(92,824),shot['detail'][0],33,MUTED)
            text(d,(1580,80),'開発中',31,WHITE,True)
    # Reserved lower margin for captions, shared by all shots.
    strip=Image.new('RGBA',(W,H))
    a=np.zeros((H,W,4),dtype=np.uint8);a[:,:,:3]=[3,14,23]
    a[940:,:,3]=np.linspace(0,230,H-940,dtype=np.uint8)[:,None]
    im.alpha_composite(Image.fromarray(a,'RGBA'))
    im.save(OUT/'overlays'/f"{shot['id']}.png")
    return im


def prepare():
    for p in ('overlays','clips','preview'): (OUT/p).mkdir(exist_ok=True)
    gradient_background().convert('RGB').save(OUT/'background.png')
    for shot in SHOTS:
        over=overlay(shot)
        if shot['type']=='diagram':
            mode=shot['mode'];file=OUT/'scene'/'render'/mode/'0031.png'
            if not file.exists():file=OUT/'scene'/'render'/f'{mode}_still.png'
            if not file.exists():continue
            canvas=gradient_background()
            visual=Image.open(file).convert('RGBA').resize(SZ,Image.Resampling.LANCZOS)
            canvas.alpha_composite(visual,(DX,DY))
        elif shot['type'] in ('photo','end'):
            canvas=photo_background(shot['source'])
            canvas.convert('RGB').save(OUT/'clips'/f"{shot['id']}_bg.jpg",quality=96)
        elif shot['type']=='portrait':
            canvas=gradient_background()
            pic=Image.open(OUT/'media'/'thumbs'/'IMG_8014_hable.jpg').convert('RGBA')
            pic=ImageOps.fit(pic,(510,906),Image.Resampling.LANCZOS)
            canvas.alpha_composite(pic,(1278,50))
        else:
            src=OUT/'media'/'selected_clips'/shot['source']
            pic=OUT/'preview'/f"{shot['id']}_source.jpg"
            if src.exists():run(['-ss',shot['ss'],'-i',src,'-frames:v',1,'-vf','scale=1920:1080','-q:v',2,pic])
            if not pic.exists():continue
            canvas=Image.open(pic).convert('RGBA')
        canvas.alpha_composite(over)
        canvas.convert('RGB').save(OUT/'preview'/f"{shot['id']}.jpg",quality=92)
    files=[OUT/'preview'/f"{s['id']}.jpg" for s in SHOTS]
    contact=Image.new('RGB',(1920,1080),'#071727')
    for i,p in enumerate(files):
        if p.exists():contact.paste(Image.open(p).resize((480,270)),((i%4)*480,(i//4)*270))
    contact.save(OUT/'preview'/'contact_sheet.jpg',quality=92)
    (OUT/'edit_timeline.json').write_text(json.dumps(SHOTS,ensure_ascii=False,indent=2),encoding='utf-8')


def encode():
    modes=list(dict.fromkeys(s['mode'] for s in SHOTS if s['type']=='diagram'))
    for mode in modes:
        target=OUT/'clips'/f'{mode}.mov'
        frames=list((OUT/'scene'/'render'/mode).glob('*.png'))
        if not frames:raise RuntimeError('No rendered frames for '+mode)
        expected=json.loads((OUT/'scene'/'scene_info.json').read_text())['modes'][mode]
        if len(frames)!=expected:raise RuntimeError(f'{mode}: expected {expected} frames, found {len(frames)}')
        if not target.exists() or max(p.stat().st_mtime for p in frames)>target.stat().st_mtime:
            run(['-framerate',30,'-start_number',1,'-i',OUT/'scene'/'render'/mode/'%04d.png','-vf',f'scale={SZ[0]}:{SZ[1]}:flags=lanczos','-c:v','qtrle','-pix_fmt','argb','-an',target])
    for s in SHOTS:
        dest=OUT/'clips'/f"{s['id']}.mp4"
        args=[];typ=s['type'];duration=s['duration']
        if typ=='diagram':
            args=['-loop',1,'-framerate',30,'-i',OUT/'background.png','-stream_loop',-1,'-i',OUT/'clips'/f"{s['mode']}.mov",'-loop',1,'-framerate',30,'-i',OUT/'overlays'/f"{s['id']}.png"]
            filt=f'[0:v]format=rgba[b];[1:v]format=rgba[m];[b][m]overlay={DX}:{DY}:format=auto[v];[2:v]format=rgba,fade=t=in:st=0:d=0.22:alpha=1[o];[v][o]overlay=0:0:format=auto,format=yuv420p[out]'
        elif typ in ('photo','end'):
            args=['-loop',1,'-framerate',30,'-i',OUT/'clips'/f"{s['id']}_bg.jpg",'-loop',1,'-framerate',30,'-i',OUT/'overlays'/f"{s['id']}.png"]
            filt=f"[0:v]scale=3840:2160,zoompan=z='1+on*0.00013':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d=1:s=1920x1080:fps=30,format=rgba[v];[1:v]format=rgba,fade=t=in:st=0:d=0.35:alpha=1[o];[v][o]overlay=0:0:format=auto,format=yuv420p[out]"
        elif typ=='video':
            args=['-ss',s['ss'],'-i',OUT/'media'/'selected_clips'/s['source'],'-loop',1,'-framerate',30,'-i',OUT/'overlays'/f"{s['id']}.png"]
            filt='[0:v]scale=1920:1080,setsar=1,format=rgba[v];[1:v]format=rgba[o];[v][o]overlay=0:0:format=auto,format=yuv420p[out]'
        else:
            args=['-loop',1,'-framerate',30,'-i',OUT/'background.png','-ss',s['ss'],'-i',OUT/'media'/'selected_clips'/s['source'],'-loop',1,'-framerate',30,'-i',OUT/'overlays'/f"{s['id']}.png"]
            filt='[0:v]format=rgba[b];[1:v]scale=510:906,setsar=1,format=rgba[m];[b][m]overlay=1278:50:format=auto[v];[2:v]format=rgba[o];[v][o]overlay=0:0:format=auto,format=yuv420p[out]'
        run([*args,'-filter_complex',filt,'-map','[out]','-t',duration,'-r',30,'-c:v','libx264','-preset','fast','-crf',18,'-threads',8,'-an',dest])
        print('SHOT_ENCODED',s['id'],flush=True)
    concat()


def concat():
    listing=OUT/'clips'/'concat.txt'
    listing.write_text('\n'.join(f"file '{s['id']}.mp4'" for s in SHOTS),encoding='utf-8')
    run(['-f','concat','-safe',0,'-i',listing,'-c','copy','-movflags','+faststart',OUT/'clips'/'picture_60s.mp4'])


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--preview',action='store_true');ap.add_argument('--concat-only',action='store_true');args=ap.parse_args()
    if args.concat_only:concat();return
    prepare()
    if not args.preview:encode()


if __name__=='__main__':main()
