"""Package the editable project without the heavy temporary render cache."""
import json
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parent
files=[]

def add(name):
    path=ROOT/name
    if not path.is_file():raise FileNotFoundError(path)
    files.append((path,Path('aquabeacon-film60')/name))

for name in ['AquaBeacon_60s.mp4','AquaBeacon_60s.srt','AquaBeacon_cover.jpg','AquaBeacon_60s_edit.blend','AquaBeacon_60s_scene.blend','README.md','edit_timeline.json','caption_timeline.json','validation.json','build_edit_project.py','compose_film.py','finalize_film.py','package_film.py','background.png','scene/build_film_scene.py','scene/source_scene.py','scene/projection.json','scene/scene_info.json']:
    add(name)
for shot in json.loads((ROOT/'edit_timeline.json').read_text(encoding='utf-8')):
    add('clips/'+shot['id']+'.mp4')
    add('overlays/'+shot['id']+'.png')
for cap in json.loads((ROOT/'caption_timeline.json').read_text(encoding='utf-8')):
    add(cap['image'])
for path in (ROOT/'audio').iterdir():
    if path.is_file() and path.suffix in ('.py','.md','.json','.mp3','.wav'):
        add(path.relative_to(ROOT).as_posix())
for name in ['media/README.md','media/source_index.json','media/selected_clips/assembly_24-32_sdr.mp4','media/selected_clips/harbor_full_sdr.mp4','media/photos/IMG_7986.jpg','media/photos/IMG_8027.jpg','media/thumbs/IMG_8014_hable.jpg']:
    add(name)
for name in ['aquabeacon_logo_transparent.png','DESIGN.md']:
    files.append((ROOT.parent/'aquabeacon-brand'/name,Path('aquabeacon-brand')/name))
output=ROOT/'AquaBeacon_editable.zip'
with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for source,relative in files:z.write(source,relative.as_posix())
with zipfile.ZipFile(output) as z:
    assert z.testzip() is None
    names=set(z.namelist())
    for s in json.loads((ROOT/'edit_timeline.json').read_text(encoding='utf-8')):
        assert 'aquabeacon-film60/clips/'+s['id']+'.mp4' in names
    for c in json.loads((ROOT/'caption_timeline.json').read_text(encoding='utf-8')):
        assert 'aquabeacon-film60/'+c['image'] in names
print(json.dumps({'package':str(output),'files':len(files),'bytes':output.stat().st_size,'crc_verified':True}))
