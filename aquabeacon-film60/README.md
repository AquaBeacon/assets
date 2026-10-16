# AquaBeacon 60秒紹介映像

一般の方に向けて、藻場の調査に必要な「撮影した場所」と、光・音を組み合わせて水中の位置を推定するAquaBeaconの仕組みを紹介する映像です。1920×1080、30fps、60秒（1800フレーム）で制作しました。

## 納品ファイル

| ファイル | 用途 |
| --- | --- |
| `AquaBeacon_60s.mp4` | 字幕・ナレーション・BGM・効果音を含む完成映像 |
| `AquaBeacon_60s.srt` | 字幕テキストと表示時刻 |
| `AquaBeacon_cover.jpg` | 映像紹介用の静止画 |
| `AquaBeacon_60s_edit.blend` | Blenderの映像編集用プロジェクト。12カット、字幕PNG、完成ミックスを配置 |
| `AquaBeacon_60s_scene.blend` | 仕組みの説明に使う3Dモデル・アニメーションの編集用シーン |
| `edit_timeline.json` | 全12カットの順番・開始時刻・長さ・画面上の文面 |
| `caption_timeline.json` | 字幕の文面・開始時刻・終了時刻・PNGの対応 |
| `audio/audio_notes.md` | 最終的な音声の種類・生成方法・利用した音源についての注記 |
| `media/source_index.json` | ユーザー提供素材の元ファイル、メタデータ、変換・使用区間の記録 |

映像確認用の静止画一覧は `preview/contact_sheet.jpg`、提供写真の一覧は `media/contact_sheet.jpg` にあります。編集用プロジェクトを保存後に読み直し、相対パス21件（動画12・字幕8・音声1）の素材が見つかることと、代表フレームの画像・字幕表示を確認しています。確認画像は `preview/edit_check_0001.png`、`edit_check_0660.png`、`edit_check_1440.png` です。

## 内容と表現

| 時間 | 内容 |
| --- | --- |
| 0–14秒 | 藻場の調査と、水中で撮影位置を知る難しさ |
| 14–46秒 | 水上・水中の装置、音による距離、光による方向、位置推定、映像と位置を結び付ける考え方 |
| 46–54秒 | 提供された機体の製作・準備・水上での様子 |
| 54–60秒 | 藻場調査への活用を目指す姿勢とロゴ |

3D部分は一般向けの説明用の模式モデルです。形状、寸法、距離、速度、光や音の見え方を理解しやすいように表現しており、実機の設計図や測定結果を再現するものではありません。位置推定・マッピングは開発中として表現し、未完成の機能や精度、環境改善の効果を実証済みと断言していません。

当初の構成にあった「プール実験」は、今回の提供素材に合わせて「機体の製作と実験の記録」に調整しました。映っているのは室内の組立、岸壁での準備、水面の機体です。プール、海中の藻場観測、自律移動の成功を示す映像としては扱っていません。初回の企画資料にある「制作しない」という記載は当時の検討範囲を示すもので、この映像はその後のユーザーによる制作承認に基づいています。

## 素材・音声の出典

写真と実写動画は、ユーザー提供の `Photos-1-001 (3).zip` 内の11ファイル（写真8枚・動画3本）を使用しています。元ZIPは変更せず、元データは `media/source/` に展開しています。写真の色空間変換、動画のHDRからSDRへの変換、採用区間は `media/README.md` と `media/source_index.json` に記録しています。海岸写真は景観として使用し、その場所の藻場の状態や位置を特定する説明は付けていません。

主な採用素材は、海岸写真 `IMG_7986`、機体写真 `IMG_8027`、室内組立の `IMG_7980.MOV`（元29–32秒）、水上の `IMG_8014.MOV` です。AquaBeaconのロゴは既存の `../aquabeacon-brand/` の素材を使用しています。

ナレーションには合成音声 `ja-JP-NanamiNeural` を使用しています。読み上げ用の読み方と字幕用の表記を分け、各場面の前後に間を設けています。BGMと効果音はこの映像用に手続き的に生成した音源で、第三者の楽曲・録音サンプルを取り込んでいません。最終的な音声注記は `audio/audio_notes.md`、台本は `audio/narration_script.json`、配置時刻は `audio/timings.json` を参照してください。

## 編集する

Blender 5.2.1で `AquaBeacon_60s_edit.blend` を開くと、映像のプレビューと編集タイムラインを確認できます。

- チャンネル1：12本の無音クリップ。図解・画面タイトルは各クリップに合成済みです。
- チャンネル2：透明PNGの字幕。表示時刻や順番を調整できます。文面の変更はPNGを再生成します。
- チャンネル3：`audio/mix_60s.wav` 1本。ナレーション・BGM・効果音が合成済みです。

3Dモデルやアニメーションを変える場合は、別の `AquaBeacon_60s_scene.blend` または `scene/build_film_scene.py` を編集し、該当する図解クリップを再生成してください。編集用 `.blend` 内の映像は合成済みなので、図解の部品やタイトルを個別の3Dオブジェクトとして選択する構成にはなっていません。

音声を差し替える場合はチャンネル3のミックスを置き換えます。すでに完成ミックスを配置しているため、同じナレーションやBGMを追加すると二重に再生されます。最終MP4の原音として実写素材の音声は使用していません。

すべての編集用素材は `.blend` からの相対パスで参照します。移動・受け渡しには `aquabeacon-film60` フォルダ全体をコピーし、少なくとも `clips/`、`overlays/`、`audio/` と2つのタイムラインJSONの位置を保ってください。3Dから再生成する場合は `scene/`、`media/`、各Pythonスクリプトと、隣の `aquabeacon-brand/` も必要です。`.blend` だけを移動すると動画・字幕・音声を見失います。

## 再生成

制作環境はWindows、Blender 5.2.1、Python 3.12＋Pillow／NumPy、FFmpeg／ffprobeです。音声の再合成には `edge-tts` とネットワーク接続が必要です。既存のWAVを使って編集プロジェクトを再構築するだけなら、音声を再合成する必要はありません。スクリプト内のツール・フォントの絶対パスは制作環境に合わせているため、別環境では変更してください。

以下はこのフォルダを作業ディレクトリとするPowerShellの例です。動画・字幕・音声が生成途中のときは、完成を待ってから編集プロジェクトを作成します。

```powershell
$blenderExe = 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe'
$pythonExe = 'C:\Users\ryupc\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'

# 必要な場合：3D説明シーンの保存と描画
& $blenderExe --background --factory-startup --python scene/build_film_scene.py -- --mode build
& $blenderExe --background --factory-startup --python scene/build_film_scene.py -- --mode all --force

# 全12カットの映像を生成。--preview を付けると静止画確認のみ
& $pythonExe compose_film.py

# 既存の音声ミックスから字幕PNG・SRTを生成し、完成MP4を出力
# 字幕だけを更新する場合は --captions-only
& $pythonExe finalize_film.py

# 字幕PNG・caption_timeline.json・mix_60s.wavが揃った後に確認
& $pythonExe build_edit_project.py --check-only

# 映像編集用プロジェクトを保存
& $blenderExe --background --factory-startup --python build_edit_project.py
```

`build_edit_project.py` は12カットが隙間なく60秒を構成すること、字幕の範囲・重複、必要素材、ミックス音声の長さを確認します。Blenderへの読み込み時に各クリップのフレーム数と30fpsも確認し、動画12本・字幕PNG・音声1本を配置して `AquaBeacon_60s_edit.blend` を保存します。

編集プロジェクトから別名で映像を書き出す場合は次のコマンドを使います。出力先の初期値は `AquaBeacon_60s_from_edit.mp4` です。

```powershell
& $blenderExe --background AquaBeacon_60s_edit.blend --render-anim
```

音声だけを再生成する場合の順序は `audio/generate_music.py`、`audio/synthesize_narration.py`、`audio/assemble_audio.py`、`audio/verify_audio.py` です。台本の変更後は字幕とその時刻も見直し、完成MP4を実際に再生して確認してください。
