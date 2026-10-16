# AquaBeacon film60 user media

Source archive: `C:/Users/ryupc/Downloads/Photos-1-001 (3).zip` (166,804,275 bytes, 11 files). The archive and originals remain unchanged. Entries were checked for traversal, absolute paths, drive prefixes, and symbolic links before extraction. Original files are in `source/`, with SHA-256 checksums and ffprobe/EXIF details in `source_index.json`.

## Ready for editing

| Asset | Content visible | Recommended use |
| --- | --- | --- |
| `photos/IMG_7986.jpg` | Sea, shoreline, rock, blue sky; horizontal 5712×4284 | Opening / future imagery. This does not depict a verified seagrass bed or its degradation. |
| `photos/IMG_8027.jpg` | Orange device, transparent circular housing, cameras/lights, cables, a person's arm on a harbor wall; horizontal 5712×4284 | Hardware close-up, about 49–51 s of film |
| `selected_clips/assembly_24-32_sdr.mp4` | Person assembling an orange device indoors; 1920×1080, 8 s | Original `IMG_7980.MOV` 24–32 s. For original 29–32 s, use derivative 5–8 s; about 46–49 s of film |
| `selected_clips/harbor_full_sdr.mp4` | Orange device floating beside harbor wall, yellow cable and tether, moving water; portrait 1080×1920 | Original `IMG_8014.MOV` 0–3.665 s, full video; about 51–54 s of film |
| `selected_clips/electronics_full_sdr.mp4` | Circuit boards and wiring on a workbench; portrait 810×1080 | Original `IMG_7976.MP4` 0–2.94 s, full video; optional hardware insert |

All derivatives: H.264, 8-bit yuv420p, BT.709 SDR limited range, constant 30 fps, orientation baked into pixels, square pixels, fast-start MP4. AAC audio is retained only for reference and can be muted in the final edit. 30 fps rounding gives 2.933 s for electronics and 3.667 s for harbor; assembly is exactly 8.000 s.

The two MOV files were HEVC Main 10, BT.2020/HLG. They were converted to linear light at npl=100, transformed to BT.709, tone-mapped with Hable without desaturation, and encoded as SDR. Final decoded frames were visually checked for orientation, sea-surface detail, orange device color, and highlight handling. The electronics source is 8-bit SDR with P3 primaries and was transformed to BT.709.

The 8 files named `.HEIC` actually contain JPEG data with embedded Display P3 ICC profiles. Their 8-bit primary images were correctly opened as JPEG, oriented, converted to sRGB with the ICC profile, and saved at quality 96. Auxiliary MP/gain-map metadata is not used in the SDR outputs. No HEIF dependency is required by the final preparation scripts.

## Other photos

| Photo | Visible content | EXIF date/time |
| --- | --- | --- |
| `IMG_7976` | PCB and wiring close-up, portrait | 2026-09-20 00:06:12 |
| `IMG_7978` | Person working on orange device indoors, portrait | 2026-09-20 15:33:57 |
| `IMG_7982` | Turquoise sea and distant harbor shoreline, portrait | 2026-09-21 10:13:31 |
| `IMG_7986` | Sea, rock and shoreline, horizontal | 2026-09-21 10:41:48 |
| `IMG_8005` | Orange device on harbor wall, portrait | 2026-09-21 16:42:37 |
| `IMG_8008` | Person handling device and cables beside water, portrait | 2026-09-21 16:42:59 |
| `IMG_8027` | Orange device close-up at harbor, horizontal | 2026-09-22 16:14:27 |
| `IMG_8036` | Person handling line beside water, portrait | 2026-09-22 16:28:19 |

Dates are metadata values, not independently verified event dates. Video creation times in UTC are stored in the index.

## Visual review files

- `contact_sheet.jpg`: all eight photos after sRGB conversion.
- `thumbs/IMG_7976_sheet.jpg`, `IMG_7980_sheet.jpg`, `IMG_8014_sheet.jpg`: five evenly spaced frames per original video, HDR tone-mapped where needed.
- `thumbs/*_sdr_final.jpg`: decoded samples from the final editing derivatives.

## Limits on interpretation

There is no pool scene or underwater seagrass footage in these 11 files. The photographs and clips support descriptions of fabrication, hardware, waterside preparation and a device on the water. They do not by themselves establish autonomous operation, location, successful seagrass mapping, achieved accuracy, durability, or environmental improvement. People and locations were not identified. For a wide frame, preserve the portrait harbor clip in a designed layout or crop around the visible device; an automatic center crop can make the device too small or cut it off.

## Reproduce

Run `prepare_media.py`, wait for completion, then run `encode_selected.py`. Python with Pillow plus the ffmpeg/ffprobe paths in these scripts are required. The source archive must be available at the recorded path.
