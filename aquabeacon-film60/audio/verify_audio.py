from pathlib import Path
import json,re,subprocess,wave
import numpy as np
P=Path(__file__).resolve().parent
F='C:/Users/ryupc/anaconda3/Library/bin/ffmpeg.exe'
m=json.loads((P/'timings.json').read_text(encoding='utf-8'))
report={'status':'PASS','checks':[],'listening_review':'Not performed: this agent environment cannot ingest audio. Waveform, TTS sentence metadata, pronunciation spellings and measured levels were verified.'}
for c in m['cuts']:
    with wave.open(str(P/c['file']),'rb') as w:
        assert w.getframerate()==48000 and w.getnchannels()==1 and w.getsampwidth()==2
        assert w.getnframes()==(c['end']-c['start'])*48000
        a=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2')
        assert max(abs(a.astype(np.int32)))<32767
        assert not a[:int(.4*48000)].any()
        assert not a[-int(.39*48000):].any()
    assert c['tempo_factor']==1.0
    assert c['voice_start']>=c['start']+.39
    assert c['voice_end']<=c['end']-.39
    report['checks'].append(f"Cut {c['cut']:02}: exact duration, 48 kHz PCM, leading/trailing silence, no clipping, original TTS rate PASS")
for name in ['mix_60s.wav','narration_60s.wav','bgm_original_60s.wav','sfx_60s.wav']:
    with wave.open(str(P/name),'rb') as w:
        assert w.getframerate()==48000 and w.getnframes()==60*48000
    r=subprocess.run([F,'-hide_banner','-nostdin','-i',str(P/name),'-af','loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json','-f','null','NUL'],capture_output=True,text=True,check=True)
    data=json.loads(re.findall(r'\{[^{}]+\}',r.stderr,re.S)[-1])
    loudness={'integrated_lufs':float(data['input_i']),'true_peak_dbtp':float(data['input_tp']),'loudness_range_lu':float(data['input_lra'])}
    m['checks'][name].update(loudness)
    assert loudness['true_peak_dbtp']<=-2
    report['checks'].append({name:loudness})
assert -18<=m['checks']['mix_60s.wav']['integrated_lufs']<=-14
m['quality_notes']=report['listening_review']
(P/'timings.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8')
(P/'audio_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
