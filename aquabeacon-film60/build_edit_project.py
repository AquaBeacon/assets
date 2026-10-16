"""Build the editable 60-second Blender VSE project from finished shot clips.

Run with Blender 5.2: blender -b --factory-startup -P build_edit_project.py
Preflight without Blender: python build_edit_project.py --check-only
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
import wave

ROOT = Path(__file__).resolve().parent
FPS = 30
TOTAL_FRAMES = 1800


def frame_at(seconds: float) -> int:
    """Map a seconds boundary to Blender's one-based, end-exclusive timeline."""
    if not math.isfinite(float(seconds)):
        raise ValueError(f"Non-finite timeline value: {seconds!r}")
    return 1 + round(float(seconds) * FPS)


def load_inputs(root: Path) -> tuple[list[dict], list[dict], Path]:
    shots = json.loads((root / "edit_timeline.json").read_text(encoding="utf-8"))
    captions = json.loads((root / "caption_timeline.json").read_text(encoding="utf-8"))
    if not isinstance(shots, list) or len(shots) != 12:
        raise ValueError("edit_timeline.json must contain the 12 finished shots.")
    if not isinstance(captions, list) or not captions:
        raise ValueError("caption_timeline.json must be a non-empty caption list.")
    missing = []
    seen = set()
    expected = 1
    for shot in shots:
        ident = str(shot["id"])
        if ident in seen or Path(ident).name != ident or "/" in ident or "\\" in ident:
            raise ValueError(f"Duplicate or invalid shot id: {ident!r}")
        seen.add(ident)
        start = frame_at(shot["start"])
        end = frame_at(float(shot["start"]) + float(shot["duration"]))
        if start != expected or end <= start:
            raise ValueError(f"Shot {ident} is not contiguous or has no duration.")
        expected = end
        shot["_start"], shot["_end"] = start, end
        shot["_path"] = root / "clips" / f"{ident}.mp4"
        if not shot["_path"].is_file() or shot["_path"].stat().st_size == 0:
            missing.append(shot["_path"])
    if expected != TOTAL_FRAMES + 1:
        raise ValueError(f"Shots must cover exactly 60 seconds; final boundary is {expected}.")
    previous_end = 1
    for caption in sorted(captions, key=lambda c: float(c["start"])):
        start, end = frame_at(caption["start"]), frame_at(caption["end"])
        if not 1 <= start < end <= TOTAL_FRAMES + 1 or start < previous_end:
            raise ValueError(f"Caption timing is invalid or overlaps: {caption.get('id')}")
        previous_end = end
        path = Path(caption["image"])
        if not path.is_absolute():
            path = root / path
            if not path.exists() and Path(caption["image"]).parent == Path("."):
                path = root / "overlays" / caption["image"]
        path = path.resolve()
        if not path.is_relative_to(root):
            raise ValueError(f"Caption image must be inside the project: {path}")
        caption["_start"], caption["_end"], caption["_path"] = start, end, path
        if not path.is_file() or path.stat().st_size == 0:
            missing.append(path)
    audio = root / "audio" / "mix_60s.wav"
    if not audio.is_file():
        missing.append(audio)
    if missing:
        raise FileNotFoundError("Finish these media files before building the project:\n" + "\n".join(str(p) for p in missing))
    with wave.open(str(audio), "rb") as wav:
        if abs(wav.getnframes() - 60 * wav.getframerate()) > 1:
            raise ValueError("audio/mix_60s.wav must have a duration of 60 seconds.")
    return shots, captions, audio


def build(root: Path, output: Path, shots: list[dict], captions: list[dict], audio: Path) -> None:
    import bpy

    if bpy.app.version < (5, 2, 0):
        raise RuntimeError("This script uses Blender 5.2's VSE strips API.")
    if output.name == "AquaBeacon_60s_scene.blend":
        raise ValueError("The separately owned 3D scene must not be overwritten.")
    output.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.name = "AquaBeacon 60s — 映像編集"
    scene.render.resolution_x, scene.render.resolution_y = 1920, 1080
    scene.render.resolution_percentage = 100
    scene.render.pixel_aspect_x = scene.render.pixel_aspect_y = 1.0
    scene.render.fps, scene.render.fps_base = FPS, 1.0
    scene.frame_start, scene.frame_end = 1, TOTAL_FRAMES
    scene.render.use_sequencer = True
    scene.render.use_compositing = False
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.view_settings.exposure = 0
    scene.view_settings.gamma = 1
    scene.sequencer_colorspace_settings.name = "sRGB"
    scene.render.image_settings.media_type = "VIDEO"
    scene.render.image_settings.file_format = "FFMPEG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"
    scene.render.ffmpeg.constant_rate_factor = "HIGH"
    scene.render.ffmpeg.ffmpeg_preset = "GOOD"
    scene.render.ffmpeg.audio_codec = "AAC"
    scene.render.ffmpeg.audio_bitrate = 192
    scene.render.ffmpeg.audio_mixrate = 48000
    scene.render.ffmpeg.audio_channels = "STEREO"
    scene.render.filepath = "//AquaBeacon_60s_from_edit.mp4"
    editor = scene.sequence_editor_create()

    def relative(path: Path) -> str:
        return bpy.path.relpath(str(path), start=str(output.parent))

    for shot in shots:
        # new_movie creates only video; it does not add a second sound strip.
        strip = editor.strips.new_movie(shot["id"], str(shot["_path"]), channel=1, frame_start=shot["_start"], fit_method="FIT")
        expected_duration = shot["_end"] - shot["_start"]
        if strip.content_duration != expected_duration:
            raise ValueError(f"{shot['id']} contains {strip.content_duration} frames, expected {expected_duration}. Finish or re-encode the clip first.")
        if abs(strip.fps - FPS) > 0.01:
            raise ValueError(f"{shot['id']} is {strip.fps} fps; expected 30 fps.")
        strip.right_handle = shot["_end"]
        strip.filepath = relative(shot["_path"])
        strip.colorspace_settings.name = "sRGB"
        strip.blend_type = "REPLACE"
        strip.select = False
        title = " / ".join(shot.get("title", []))
        scene.timeline_markers.new(f"{shot['id']}  {title}", frame=shot["_start"])

    for caption in captions:
        strip = editor.strips.new_image(f"字幕 {caption['id']}: {caption.get('text', '')}", str(caption["_path"]), channel=2, frame_start=caption["_start"], fit_method="FIT")
        strip.right_handle = caption["_end"]
        strip.directory = relative(caption["_path"].parent).rstrip("/\\") + "/"
        strip.colorspace_settings.name = "sRGB"
        strip.alpha_mode = "STRAIGHT"
        strip.blend_type = "ALPHA_OVER"
        strip.select = False

    sound = editor.strips.new_sound("完成ミックス — ナレーション・BGM・効果音", str(audio), channel=3, frame_start=1)
    sound.right_handle = TOTAL_FRAMES + 1
    sound.sound.filepath = relative(audio)
    sound.volume = 1.0
    sound.show_waveform = True
    sound.select = False
    channel_names = {1: "映像・図解・タイトル（12カット）", 2: "字幕 PNG", 3: "完成ミックス（音声はこの1本のみ）"}
    for channel in editor.channels:
        if channel.number in channel_names:
            channel.name = channel_names[channel.number]
    counts = {kind: sum(s.type == kind for s in editor.strips) for kind in ("MOVIE", "IMAGE", "SOUND")}
    if counts != {"MOVIE": 12, "IMAGE": len(captions), "SOUND": 1}:
        raise AssertionError(f"Unexpected strip counts: {counts}")

    scene["description"] = "完成カットの順序・長さ、字幕の表示時刻、完成ミックスを編集する60秒のプロジェクト。3Dの再編集は別ファイル AquaBeacon_60s_scene.blend。"
    scene["source_timeline"] = relative(root / "edit_timeline.json")
    scene["caption_timeline"] = relative(root / "caption_timeline.json")
    scene["synthetic_narration"] = "ja-JP-NanamiNeural; see audio/audio_notes.md"
    note = bpy.data.texts.new("編集について.txt")
    note.write("AquaBeacon / 60秒編集\n\nチャンネル1: 図・タイトルを合成済みの12本の無音クリップ\nチャンネル2: 透明PNG字幕。文面の変更は字幕PNGを再生成してください。\nチャンネル3: ナレーション・BGM・効果音の完成ミックス1本\n\n素材は.blendからの相対パスです。フォルダ構成を保って移動してください。\n3D形状・アニメーションの再編集は別の AquaBeacon_60s_scene.blend を使用します。\n音声は合成音声を含みます。音源の詳細は audio/audio_notes.md を参照してください。\n")
    scene.frame_set(1)
    # Open directly in the combined preview/timeline view when loaded in the UI.
    if bpy.context.screen:
        areas = [a for a in bpy.context.screen.areas if a.type == "VIEW_3D"]
        if areas:
            area = max(areas, key=lambda a: a.width * a.height)
            area.type = "SEQUENCE_EDITOR"
            area.spaces.active.view_type = "SEQUENCER_PREVIEW"
            area.spaces.active.show_region_ui = False
    if bpy.context.workspace:
        bpy.context.workspace.name = "AquaBeacon 編集"
    bpy.ops.wm.save_as_mainfile(filepath=str(output))
    print(json.dumps({"saved": str(output), "fps": FPS, "frames": TOTAL_FRAMES, "duration_seconds": 60, "strips": counts, "relative_media_paths": True}, ensure_ascii=False), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="Project folder containing the timelines and media.")
    parser.add_argument("--output", type=Path, help="Default: <root>/AquaBeacon_60s_edit.blend")
    parser.add_argument("--check-only", action="store_true", help="Check input manifests and media without writing a Blender file.")
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    # Blender's own flags precede --; no separator means the script has no flags.
    if "bpy" in sys.modules and "--" not in sys.argv:
        argv = []
    args = parser.parse_args(argv)
    root = args.root.resolve()
    shots, captions, audio = load_inputs(root)
    if args.check_only:
        print(f"INPUTS_OK: {len(shots)} shots, {len(captions)} captions, 60-second audio.")
        return
    output = (args.output or root / "AquaBeacon_60s_edit.blend").resolve()
    build(root, output, shots, captions, audio)


if __name__ == "__main__":
    main()
