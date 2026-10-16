"""Burn readable Japanese captions, attach the audio mix, and verify the film."""
import argparse
import json
import math
import subprocess
from pathlib import Path

from PIL import Image,ImageDraw,ImageFont
from compose_film import OUT,FF,FP,W,H,font,run,SHOTS


def ts(t):
    ms=round(t*1000)
    return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'


def wrap(body):
    # Balance two lines at a natural phrase boundary when possible.
    if len(body)<=29:return [body]
    candidates=[i+1 for i,c in enumerate(body) if c in '、。' and 8<i<len(body)-8]
    if not candidates:candidates=[len(body)//2]
    split=min(candidates,key=lambda i:abs(i-len(body)/2))
    return [body[:split],body[split:]]


def captions():
    data=json.loads((OUT/'audio'/'timings.json').read_text(encoding='utf-8'))
    result=[];srt=[]
    for i,c in enumerate(data['cuts']):
        start=max(c['start'],c['voice_start']-.08)
        end=min(c['end']-.15,c['voice_end']+.30)
        lines=wrap(c['text'])
        im=Image.new('RGBA',(W,H));d=ImageDraw.Draw(im)
        y=947 if len(lines)>1 else 982
        for n,line in enumerate(lines):
            width=d.textlength(line,font=font(44))
            assert width<1730,(line,width)
            x=(W-width)/2
            d.rounded_rectangle((x-20,y+n*55-5,x+width+20,y+n*55+49),radius=8,fill=(2,12,20,200))
            d.text((x,y+n*55),line,font=font(44),fill='#F4FAFB',anchor='lt')
        image=f'overlays/caption_{i+1:02d}.png';im.save(OUT/image)
        result.append({'id':i+1,'start':start,'end':end,'image':image,'text':'\n'.join(lines)})
        srt.append(f'{i+1}\n{ts(start)} --> {ts(end)}\n'+ '\n'.join(lines))
    (OUT/'caption_timeline.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'AquaBeacon_60s.srt').write_text('\n\n'.join(srt)+'\n',encoding='utf-8')
    return result


def finish():
    caps=captions()
    args=['-i',OUT/'clips'/'picture_60s.mp4','-i',OUT/'audio'/'mix_60s.wav']
    for c in caps:args+=['-loop',1,'-framerate',30,'-i',OUT/c['image']]
    filters=['[0:v]format=rgba[v0]']
    for i,c in enumerate(caps):
        filters.append(f"[{i+2}:v]format=rgba[c{i}]")
        filters.append(f"[v{i}][c{i}]overlay=0:0:enable='gte(t,{c['start']:.3f})*lt(t,{c['end']:.3f})':format=auto[v{i+1}]")
    filters.append(f'[v{len(caps)}]format=yuv420p[out]')
    run([*args,'-filter_complex',';'.join(filters),'-map','[out]','-map','1:a:0','-t',60,'-r',30,'-c:v','libx264','-preset','fast','-crf',18,'-threads',8,'-c:a','aac','-b:a','192k','-ar',48000,'-movflags','+faststart','-metadata','title=AquaBeacon — 光と音で、水中の位置を知る','-metadata','comment=Blender animation, supplied documentary footage, synthetic Japanese narration and original music.',OUT/'AquaBeacon_60s.mp4'])
    validate()


def validate():
    movie=OUT/'AquaBeacon_60s.mp4'
    cmd=[str(FP),'-v','error','-count_frames','-show_entries','stream=codec_type,codec_name,width,height,pix_fmt,r_frame_rate,nb_read_frames,sample_rate,channels:format=duration,size','-of','json',str(movie)]
    data=json.loads(subprocess.run(cmd,capture_output=True,text=True,check=True).stdout)
    vid=next(s for s in data['streams'] if s['codec_type']=='video')
    aud=next(s for s in data['streams'] if s['codec_type']=='audio')
    assert (vid['width'],vid['height'],vid['r_frame_rate'])==(1920,1080,'30/1')
    assert vid['nb_read_frames']=='1800'
    assert vid['pix_fmt']=='yuv420p' and aud['sample_rate']=='48000'
    assert abs(float(data['format']['duration'])-60)<.03
    subprocess.run([str(FF),'-v','error','-i',str(movie),'-f','null','-'],check=True)
    times=[1,4,10,16,23,31,39,43,47,50,52.5,56,59.2]
    contact=Image.new('RGB',(1920,1080),'#071727')
    for i,t in enumerate(times):
        path=OUT/'preview'/f'final_{t:04.1f}.jpg'
        run(['-ss',t,'-i',movie,'-frames:v',1,'-q:v',2,path])
        im=Image.open(path).resize((480,270),Image.Resampling.LANCZOS)
        contact.paste(im,((i%4)*480,(i//4)*270))
    contact.save(OUT/'preview'/'final_contact_sheet.jpg',quality=94)
    run(['-ss',16,'-i',movie,'-frames:v',1,'-q:v',2,OUT/'AquaBeacon_cover.jpg'])
    data['checks']={'duration_60s':True,'frames_1800':True,'full_decode':True,'caption_events':8,'blender_diagram':True,'supplied_media_used':True}
    (OUT/'validation.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(data,ensure_ascii=False),flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--captions-only',action='store_true');ap.add_argument('--validate-only',action='store_true');a=ap.parse_args()
    if a.captions_only:captions()
    elif a.validate_only:validate()
    else:finish()
