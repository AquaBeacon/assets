"""Create editing proxies while preserving source media and provenance."""
from pathlib import Path
import json, subprocess
BASE=Path(__file__).resolve().parent
FFMPEG=r'C:\Users\ryupc\anaconda3\Library\bin\ffmpeg.exe'
FFPROBE=r'C:\Users\ryupc\anaconda3\Library\bin\ffprobe.exe'
HDR='zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p'
SDR='zscale=p=bt709:t=bt709:m=bt709:r=tv,format=yuv420p'
def run(args):
    p=subprocess.run(args,capture_output=True,text=True,encoding='utf-8',errors='replace')
    if p.returncode:raise RuntimeError(p.stderr[-4000:])
    return p.stdout
def main():
    dst=BASE/'selected_clips';dst.mkdir(exist_ok=True)
    jobs=[
      ('IMG_7976.MP4',0,2.94,'electronics_full_sdr.mp4',SDR+',scale=810:1080',False),
      ('IMG_7980.MOV',24,8,'assembly_24-32_sdr.mp4',HDR+',scale=1920:1080',True),
      ('IMG_8014.MOV',0,3.665,'harbor_full_sdr.mp4',HDR+',scale=1080:1920',True),
    ]
    idxpath=BASE/'source_index.json';index=json.loads(idxpath.read_text(encoding='utf-8'))
    for name,start,length,out,vf,was_hdr in jobs:
        target=dst/out
        args=[FFMPEG,'-hide_banner','-loglevel','error','-y','-ss',str(start),'-i',str(BASE/'source'/name),'-t',str(length),'-map','0:v:0','-map','0:a:0?','-vf',vf+',fps=30,setsar=1','-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-color_range','tv','-c:a','aac','-b:a','160k','-map_metadata','-1','-metadata:s:v:0','rotate=0','-movflags','+faststart',str(target)]
        run(args)
        probe=json.loads(run([FFPROBE,'-v','error','-show_format','-show_streams','-of','json',str(target)]))
        entry=next(f for f in index['files'] if f['source']=='source/'+name)
        entry['selected_clip']={'path':target.relative_to(BASE).as_posix(),'source_start':start,'source_end':start+length,'tonemap':'Hable, linear npl=100, no desaturation, BT.709' if was_hdr else None,'format':'H.264 8-bit yuv420p BT.709 SDR, 30 fps, AAC','probe':probe}
        print(out,flush=True)
    idxpath.write_text(json.dumps(index,ensure_ascii=False,indent=2),encoding='utf-8')
if __name__=='__main__':main()
