from pathlib import Path
import json, wave, math
import numpy as np

OUT=Path(__file__).resolve().parent
SR=48000
N=60*SR
rng=np.random.default_rng(20260927)
def write_wav(path,a):
    a=np.asarray(a)
    if a.ndim==1: a=a[:,None]
    assert np.isfinite(a).all()
    assert np.max(np.abs(a))<1
    pcm=np.round(a*32767).astype('<i2')
    with wave.open(str(path),'wb') as f:
        f.setnchannels(a.shape[1]); f.setsampwidth(2); f.setframerate(SR); f.writeframes(pcm.tobytes())
def envelope(n,attack,release):
    env=np.ones(n)
    a=min(int(attack*SR),n);r=min(int(release*SR),n)
    if a:env[:a]*=np.sin(np.linspace(0,np.pi/2,a))**2
    if r:env[-r:]*=np.cos(np.linspace(0,np.pi/2,r))**2
    return env
def note(freq,dur,kind='pad',phase=0):
    t=np.arange(round(dur*SR))/SR
    if kind=='pad':
        y=np.sin(2*np.pi*freq*t+phase)+.18*np.sin(2*np.pi*2*freq*t+phase*.6)+.06*np.sin(2*np.pi*3*freq*t)
        y*=envelope(len(t),2.1,3.2)
    else:
        y=np.sin(2*np.pi*freq*t)+.18*np.sin(2*np.pi*2*freq*t)*np.exp(-t*5)
        y*=np.exp(-t*2.5)*envelope(len(t),.03,.7)
    return y
music=np.zeros((N,2),dtype=np.float64)
def add(arr,signal,start,amp,pan=0):
    i=round(start*SR);m=min(len(signal),len(arr)-i)
    if m<=0:return
    left=np.sqrt((1-pan)/2);right=np.sqrt((1+pan)/2)
    arr[i:i+m,0]+=signal[:m]*amp*left
    arr[i:i+m,1]+=signal[:m]*amp*right
# Each progression is original procedural instrumentation; no recorded assets.
chords=[([48,55,59,64],0),([45,52,60,67],8),([41,53,57,64],16),([43,55,60,62],24),([48,55,59,64],32),([45,52,60,67],40),([41,53,57,64],48),([48,55,60,64],54)]
for chord,start in chords:
    dur=min(11.0,60-start)
    for j,midi in enumerate(chord):
        hz=440*2**((midi-69)/12)
        add(music,note(hz,dur,phase=rng.uniform(0,2*np.pi)),start,.008*(.9 if j else 1),[-.35,.3,-.1,.45][j])
for i,midi in enumerate([72,67,76,74,72,67,69,76,74,67,72,76,74,72]):
    start=3.2+i*4
    add(music,note(440*2**((midi-69)/12),3,'mallet'),start,.005,(-.35 if i%2 else .35))
# Low, breath-like underwater texture generated from a seeded smooth signal.
t=np.arange(N)/SR
for c in range(2):
    anchors=rng.normal(0,1,12002)
    low=np.interp(t,np.linspace(0,60,len(anchors)),anchors)
    music[:,c]+=low*.0004
music*=envelope(N,1.8,2.7)[:,None]
music*=2.4
write_wav(OUT/'bgm_original_60s.wav',music)

sfx=np.zeros_like(music)
def ping(dur,freq,amp):
    ts=np.arange(round(dur*SR))/SR
    return amp*(np.sin(2*np.pi*freq*ts)+.13*np.sin(2*np.pi*freq*1.5*ts))*np.exp(-ts*5)*envelope(len(ts),.012,.3)
events=[('sound_transmit',20.0,.9,660,.04,-.1),('sound_arrival',25.0,.9,880,.035,.15),('light_on',29.0,1.1,1174.66,.026,.1),('map_record',40.5,.9,1046.5,.023,0)]
for label,start,dur,freq,amp,pan in events:
    mono=ping(dur,freq,amp)*1.3
    stereo=np.zeros((len(mono),2));add(stereo,mono,0,1,pan)
    write_wav(OUT/f'sfx_{label}.wav',stereo)
    add(sfx,mono,start,1,pan)
write_wav(OUT/'sfx_60s.wav',sfx)
write_wav(OUT/'music_and_sfx_60s.wav',music+sfx)
manifest={
 'sample_rate':SR,'duration':60,'channels':2,'bits_per_sample':16,
 'bgm':'bgm_original_60s.wav','sfx':'sfx_60s.wav','combined':'music_and_sfx_60s.wav',
 'sfx_events':[{'name':a,'start':b,'duration':c,'file':f'sfx_{a}.wav'} for a,b,c,*_ in events],
 'provenance':'Original procedural synthesis created for AquaBeacon; no third-party music, samples or recordings.',
 'checks':{}
}
for path in [OUT/x for x in ['bgm_original_60s.wav','sfx_60s.wav','music_and_sfx_60s.wav']]+sorted(OUT.glob('sfx_*.wav')):
    try:
        with wave.open(str(path),'rb') as f:
            a=np.frombuffer(f.readframes(f.getnframes()),dtype='<i2').astype(float)/32768
            manifest['checks'][path.name]={'duration_s':f.getnframes()/f.getframerate(),'sample_rate':f.getframerate(),'channels':f.getnchannels(),'peak_dbfs':round(20*np.log10(max(abs(a).max(),1e-12)),3),'clipped_samples':int((abs(a)>=1).sum())}
    except (EOFError,wave.Error):pass
(OUT/'music_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(manifest['checks'],ensure_ascii=False,indent=2))
