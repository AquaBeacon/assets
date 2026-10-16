"""Create web-sized icons and encode the rendered Blender animation."""
from pathlib import Path
import json
import math
import shutil
import subprocess
import sys
import zipfile

from PIL import Image

OUT = Path(__file__).resolve().parent
FFMPEG = Path(r'C:\Users\ryupc\anaconda3\Library\bin\ffmpeg.exe')
FFPROBE = FFMPEG.with_name('ffprobe.exe')
FONT_DIR = Path(r'C:\Users\ryupc\.codex\plugins\cache\claude-cowork\anthropic-skills\1.0.0\skills\canvas-design\canvas-fonts')


def svg(mono=False):
    a, b, wave, signal = ('#FFFFFF',) * 4 if mono else ('#20D9D2', '#239FCF', '#69F5E1', '#B9FFFF')
    arcs = []
    for radius, color, width in [(0.45, a, 0.082), (0.76, b, 0.076)]:
        points = [(radius * math.cos(math.radians(28 + 124 * i / 80)), 0.82 + radius * math.sin(math.radians(28 + 124 * i / 80))) for i in range(81)]
        d = 'M ' + ' L '.join(f'{x:.6f},{y:.6f}' for x, y in points)
        arcs.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}"/>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="-1.7 -1.97 3.4 3.4" width="1024" height="1024" role="img" aria-label="AquaBeacon">
  <title>AquaBeacon — A, water wave and beacon</title>
  <g transform="scale(1,-1)">
    <path d="M -1,-1 L -.65,-1 L -.10,.52 L -.40,.52 Z" fill="{a}" stroke="{a}" stroke-width=".04" stroke-linejoin="round"/>
    <path d="M .65,-1 L 1,-1 L .40,.52 L .10,.52 Z" fill="{b}" stroke="{b}" stroke-width=".04" stroke-linejoin="round"/>
    <path d="M -.65,-.40 C -.40,-.17 -.20,-.27 .02,-.37 S .42,-.57 .65,-.36" fill="none" stroke="{wave}" stroke-width=".17"/>
    <circle cx="0" cy=".82" r=".165" fill="{signal}"/>
    {''.join(arcs)}
  </g>
</svg>'''


def run(args):
    subprocess.run(args, check=True)


def main():
    report = {'images': {}, 'animation': {}}
    icon = Image.open(OUT / 'aquabeacon_icon.png').convert('RGBA')
    for size in (512, 256, 128, 64, 32):
        icon.resize((size, size), Image.Resampling.LANCZOS).save(OUT / f'aquabeacon_icon_{size}.png')
    icon.save(OUT / 'aquabeacon.ico', sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    (OUT / 'aquabeacon_symbol_flat.svg').write_text(svg(), encoding='utf-8')
    (OUT / 'aquabeacon_symbol_white.svg').write_text(svg(True), encoding='utf-8')
    for name in ('InstrumentSans-OFL.txt', 'DMMono-OFL.txt'):
        shutil.copyfile(FONT_DIR / name, OUT / name)
    if '--stills-only' in sys.argv:
        return
    frames = list((OUT / 'frames').glob('aquabeacon_*.png'))
    if len(frames) != 150:
        raise RuntimeError(f'Expected 150 animation frames, found {len(frames)}')
    expected = [OUT / 'frames' / f'aquabeacon_{frame:04d}.png' for frame in range(1, 151)]
    if not all(p.exists() for p in expected):
        raise RuntimeError('Animation frame sequence has a gap')
    run([str(FFMPEG), '-y', '-hide_banner', '-loglevel', 'warning', '-framerate', '30', '-start_number', '1', '-i', str(OUT / 'frames' / 'aquabeacon_%04d.png'), '-frames:v', '150', '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(OUT / 'aquabeacon_animation.mp4')])
    run([str(FFMPEG), '-y', '-hide_banner', '-loglevel', 'warning', '-i', str(OUT / 'aquabeacon_animation.mp4'), '-filter_complex', 'fps=15,scale=800:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=192:stats_mode=diff[p];[b][p]paletteuse=dither=sierra2_4a:diff_mode=rectangle', '-loop', '0', str(OUT / 'aquabeacon_animation.gif')])
    for name in ['aquabeacon_logo.png', 'aquabeacon_icon.png', 'aquabeacon_symbol_transparent.png', 'aquabeacon_logo_transparent.png']:
        im = Image.open(OUT / name)
        alpha = im.getchannel('A')
        report['images'][name] = {'size': list(im.size), 'mode': im.mode, 'alpha_extrema': list(alpha.getextrema()), 'visible_bbox': list(alpha.getbbox())}
        if 'transparent' in name and alpha.getextrema() != (0, 255):
            raise RuntimeError(f'Transparency missing in {name}')
    result = subprocess.run([str(FFPROBE), '-v', 'error', '-select_streams', 'v:0', '-count_frames', '-show_entries', 'stream=codec_name,width,height,pix_fmt,r_frame_rate,nb_read_frames:format=duration', '-of', 'json', str(OUT / 'aquabeacon_animation.mp4')], capture_output=True, text=True, check=True)
    report['animation'] = json.loads(result.stdout)
    stream = report['animation']['streams'][0]
    if (stream['width'], stream['height'], stream['nb_read_frames']) != (1920, 1080, '150'):
        raise RuntimeError('Video dimensions or frame count are incorrect')
    if abs(float(report['animation']['format']['duration']) - 5) > 0.01:
        raise RuntimeError('Video duration is incorrect')
    (OUT / 'validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    with zipfile.ZipFile(OUT / 'aquabeacon_brand_assets.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(OUT.iterdir()):
            if path.is_file() and path.suffix.lower() in {'.blend', '.png', '.svg', '.ico', '.mp4', '.gif', '.md', '.py', '.txt', '.json'}:
                archive.write(path, path.name)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
