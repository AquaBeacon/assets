"""Safely extract user media, probe it, and generate review images."""
from pathlib import Path, PurePosixPath
import sys, json, zipfile, hashlib, subprocess, shutil, io

BASE = Path(__file__).resolve().parent
from PIL import Image, ImageOps, ImageDraw, ImageFont, ExifTags, ImageCms
ZIP = Path(r'C:\Users\ryupc\Downloads\Photos-1-001 (3).zip')
FFMPEG = r'C:\Users\ryupc\anaconda3\Library\bin\ffmpeg.exe'
FFPROBE = r'C:\Users\ryupc\anaconda3\Library\bin\ffprobe.exe'

def run(args):
    result = subprocess.run(args, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if result.returncode:
        raise RuntimeError(result.stderr[-6000:])
    return result.stdout

def probe(path):
    return json.loads(run([FFPROBE, '-v','error','-show_format','-show_streams','-of','json',str(path)]))

def sheet(items, dest, columns=4):
    cw,ch=480,390
    out=Image.new('RGB',(cw*columns,ch*((len(items)+columns-1)//columns)), '#15202b')
    draw=ImageDraw.Draw(out)
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18)
    for i,(path,label) in enumerate(items):
        im=Image.open(path).convert('RGB'); im.thumbnail((cw-20,ch-60))
        x=(i%columns)*cw+(cw-im.width)//2; y=(i//columns)*ch+10
        out.paste(im,(x,y))
        draw.text(((i%columns)*cw+10,(i//columns)*ch+ch-44),label,font=font,fill='white')
    out.save(dest,quality=91)

def main():
    source=BASE/'source'; photos=BASE/'photos'; thumbs=BASE/'thumbs'
    for d in [source,photos,thumbs]:d.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(ZIP) as z:
        for item in z.infolist():
            rel=PurePosixPath(item.filename.replace('\\','/'))
            if rel.is_absolute() or '..' in rel.parts or ':' in str(rel) or ((item.external_attr>>16)&0o170000)==0o120000:
                raise ValueError(f'Unsafe archive entry: {item.filename}')
            dest=(source/Path(*rel.parts)).resolve()
            if not dest.is_relative_to(source.resolve()):raise ValueError('Outside source directory')
            if item.is_dir():dest.mkdir(parents=True,exist_ok=True);continue
            dest.parent.mkdir(parents=True,exist_ok=True)
            if not dest.exists():
                with z.open(item) as inp, dest.open('xb') as out: shutil.copyfileobj(inp,out)
            elif dest.stat().st_size != item.file_size:raise ValueError(f'Existing file differs: {dest}')
    index={'archive':str(ZIP),'archive_bytes':ZIP.stat().st_size,'files':[]}
    photo_items=[]
    for path in sorted(source.iterdir()):
        rec={'source':path.relative_to(BASE).as_posix(), 'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
        if path.suffix.lower()=='.heic':
            with Image.open(path) as im:
                exif=im.getexif()
                rec.update({'type':'photo','actual_format':im.format,'source_dimensions':list(im.size),'source_mode':im.mode,
                            'exif':{ExifTags.TAGS.get(k,str(k)):str(v) for k,v in exif.items() if k not in (34853,37500)},
                            'has_mp_auxiliary_metadata':'mp' in im.info,
                            'color_note':'HEIC extension but actual JPEG signature; SDR primary RGB image. Auxiliary gain-map metadata is not used.'})
                upright=ImageOps.exif_transpose(im).convert('RGB')
                srgb=ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB'))
                if im.info.get('icc_profile'):
                    profile=ImageCms.ImageCmsProfile(io.BytesIO(im.info['icc_profile']))
                    rec['source_color_profile']=ImageCms.getProfileName(profile).strip()
                    upright=ImageCms.profileToProfile(upright,profile,srgb,outputMode='RGB')
                dest=photos/(path.stem+'.jpg'); upright.save(dest,quality=96,subsampling=0,icc_profile=srgb.tobytes())
                rec.update({'jpeg':dest.relative_to(BASE).as_posix(),'dimensions':list(upright.size),'output_color':'8-bit SDR sRGB JPEG, converted from embedded Display P3 ICC'})
                photo_items.append((dest,f'{path.stem}   {upright.width} x {upright.height}'))
        else:
            info=probe(path); video=next(s for s in info['streams'] if s['codec_type']=='video'); duration=float(info['format']['duration'])
            rec.update({'type':'video','probe':info,'duration_seconds':duration})
            times=[max(0.2,duration*f) for f in [0.05,0.25,0.5,0.75,0.95]]
            video_items=[]
            hdr=video.get('color_transfer') in ('smpte2084','arib-std-b67')
            vf='scale=960:-2'
            if hdr:
                vf='zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p,scale=960:-2'
            for n,t in enumerate(times):
                dest=thumbs/f'{path.stem}_{n+1:02}.jpg'
                run([FFMPEG,'-hide_banner','-loglevel','error','-y','-ss',str(t),'-i',str(path),'-frames:v','1','-vf',vf,'-q:v','2',str(dest)])
                video_items.append((dest,f'{path.stem}   {t:.2f} s'))
            out=thumbs/f'{path.stem}_sheet.jpg';sheet(video_items,out,columns=3)
            rec.update({'review_times':times,'thumb_sheet':out.relative_to(BASE).as_posix(),'hdr_detected':hdr})
        index['files'].append(rec)
        print(path.name,rec.get('dimensions'),rec.get('duration_seconds'),flush=True)
    sheet(photo_items,BASE/'contact_sheet.jpg')
    (BASE/'source_index.json').write_text(json.dumps(index,ensure_ascii=False,indent=2),encoding='utf-8')

if __name__=='__main__':main()
