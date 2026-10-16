from pathlib import Path
import subprocess,json,wave
import numpy as np
OUT=Path(__file__).resolve().parent
FF='C:/Users/ryupc/anaconda3/Library/bin/ffmpeg.exe'
SR=48000
script=json.loads((OUT/'narration_script.json').read_text(encoding='utf-8'))
def cmd(args):return subprocess.run([FF,'-hide_banner','-nostdin','-y',*args],capture_output=True,text=True,check=True)
def read(p):
    with wave.open(str(p),'rb') as f:
        assert f.getframerate()==SR
        ch=f.getnchannels()
        a=np.frombuffer(f.readframes(f.getnframes()),dtype='<i2').astype(np.float64)/32768
        return a if ch==1 else a.reshape(-1,ch)
def write(p,a):
    assert np.max(abs(a))<1
    with wave.open(str(p),'wb') as f:
        f.setnchannels(1 if a.ndim==1 else a.shape[1]); f.setsampwidth(2);f.setframerate(SR)
        f.writeframes(np.round(a*32767).astype('<i2').tobytes())
master=np.zeros(60*SR)
meta={'duration':60,'sample_rate':SR,'voice':'ja-JP-NanamiNeural','provider':'Microsoft Edge online TTS via edge-tts 7.2.8','synthetic_voice':True,'cuts':[]}
for m in script:
    i=m['cut']; raw=OUT/f'cut_{i:02}_raw.wav'
    cmd(['-v','error','-i',str(OUT/m['raw_file']),'-ar',str(SR),'-ac','1',str(raw)])
    a=read(raw)
    active=np.flatnonzero(abs(a)>.0008)
    assert len(active)>100
    lo=max(0,int(active[0]) - int(.06*SR))
    hi=min(len(a),int(active[-1]) + int(.14*SR))
    a=a[lo:hi]
    duration=len(a)/SR
    available=m['end']-m['start']-.8
    speed=max(1.,duration/available)
    if speed>1.08:raise ValueError(f'Cut {i} needs text shortening: {duration=} {available=}')
    write(OUT/f'cut_{i:02}_trim.wav',a)
    filters=(f'atempo={speed:.8f},' if speed>1 else '')+'loudnorm=I=-19:TP=-2:LRA=9'
    cmd(['-v','error','-i',str(OUT/f'cut_{i:02}_trim.wav'),'-af',filters,'-ar',str(SR),'-ac','1',str(OUT/f'cut_{i:02}_voice.wav')])
    a=read(OUT/f'cut_{i:02}_voice.wav')
    # Exact scene stem includes room before the first word and after the last.
    n=int((m['end']-m['start'])*SR)
    stem=np.zeros(n)
    lead=.4
    offset=int(lead*SR)
    assert offset+len(a)<=n-int(.399*SR),(i,len(a)/SR,n/SR)
    stem[offset:offset+len(a)]=a
    write(OUT/f'cut_{i:02}.wav',stem)
    master[int(m['start']*SR):int(m['end']*SR)]=stem
    voiced=np.flatnonzero(abs(a)>.001)
    start=m['start']+lead
    boundaries=[]
    for b in m['boundaries']:
        bs=start+max(0,b['offset']/1e7-lo/SR)/speed
        be=start+min(duration,(b['offset']+b['duration'])/1e7-lo/SR)/speed
        boundaries.append({'start':round(bs,3),'end':round(be,3),'spoken_text':b['text']})
    meta['cuts'].append({
        'cut':i,'start':m['start'],'end':m['end'],'duration':m['end']-m['start'],
        'text':m['text'],'spoken_text':m['spoken_text'],'file':f'cut_{i:02}.wav','voice_file':f'cut_{i:02}_voice.wav',
        'voice_start':round(start,4),'voice_end':round(start+len(a)/SR,4),'speech_start':round(start+voiced[0]/SR,4),'speech_end':round(start+voiced[-1]/SR,4),
        'leading_padding':lead,'trailing_padding':round(n/SR-lead-len(a)/SR,4),'tempo_factor':round(speed,5),'tts_rate':m['rate'],'sentences':boundaries
    })
write(OUT/'narration_60s.wav',master)
background=read(OUT/'music_and_sfx_60s.wav')
stereo=np.repeat(master[:,None],2,axis=1)
mix=stereo+background
write(OUT/'mix_60s.wav',mix)
meta['files']={'narration':'narration_60s.wav','mix':'mix_60s.wav','bgm':'bgm_original_60s.wav','sfx':'sfx_60s.wav','background':'music_and_sfx_60s.wav'}
meta['endcard_subtitle_note']='仕組みの公開を目指す — final narration omits the publication aspiration to leave space for the closing logo.'
meta['checks']={}
for name in ['narration_60s.wav','bgm_original_60s.wav','sfx_60s.wav','music_and_sfx_60s.wav','mix_60s.wav']:
    a=read(OUT/name)
    meta['checks'][name]={'duration_s':len(a)/SR,'sample_rate':SR,'channels':1 if a.ndim==1 else a.shape[1],'peak_dbfs':round(20*np.log10(max(abs(a).max(),1e-12)),3),'clipped_samples':int((abs(a)>=1).sum())}
(OUT/'timings.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'cuts':[{k:c[k] for k in ['cut','voice_start','voice_end','leading_padding','trailing_padding','tempo_factor']} for c in meta['cuts']],'checks':meta['checks']},indent=2))
