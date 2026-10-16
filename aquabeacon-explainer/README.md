# AquaBeacon サムネイル・仕組み説明動画

ユーザー提供の`AquaBeacon.pptx`をもとに制作した紹介素材です。
前回のAquaBeaconロゴを使用し、Blenderで親機・子機・水面・藻場の模式モデルを新規制作しました。

| ファイル | 内容 |
| --- | --- |
| `aquabeacon_thumbnail.png` | 1920×1080。光と音による水中の位置推定と、藻場のマッピングを紹介 |
| `aquabeacon_thumbnail.jpg` | 同じ画像のJPEG版 |
| `aquabeacon_explainer.mp4` | 40秒、1920×1080、24fps、H.264。日本語の説明字幕付き、無音 |
| `aquabeacon_explainer_preview.gif` | 音と光の場面を抜き出した15秒の確認用プレビュー |
| `aquabeacon_explainer.srt` | 説明字幕。MP4にも同じ字幕を焼き込んでいます |
| `aquabeacon_explainer.blend` | 40秒の機構説明用3Dアニメーション。字幕やロゴの組版はPythonの合成工程で追加 |
| `aquabeacon_explainer_assets.zip` | 上記ファイルと構成案・再生成スクリプト |

## 説明の内容

水中ではGPSを直接使えないため、水上の親機を位置の基準にします。
親機から子機に音を送り、その到達時間から距離を求めます。
子機のライトを親機のカメラで追跡し、方向を求めます。
距離と方向を組み合わせ、親機のGPSから子機の位置を推定します。
撮影した映像に位置を対応づけ、藻場の3Dマッピングにつなげる考え方を紹介しています。

親機・子機の形状、信号の速度、空間スケールは説明用です。
機体の実機映像やマッピングの実測成果ではありません。
位置推定や地図の精度が実証済みであるとは表現していません。
光学追跡は水の濁りの影響を受けるため、最後の字幕でも対象範囲を示しています。

## 資料

参照：`C:\Users\ryupc\OneDrive\ドキュメント\高校\探究2年\未踏ジュニア\中間合宿\AquaBeacon.pptx`

主にスライド1、10–13、16、17–19、22、23を使用しています。
各場面と参照内容の対応は`STORYBOARD.md`に記載しています。
元のPowerPointには変更を加えていません。

## 編集・再生成

Blenderファイルには、GPS、音響、光学、位置推定、マッピングの切替を含む40秒のタイムラインがあります。
親機・子機・信号・藻場はオブジェクト名を付けて整理しています。
`build_scene.py`で3D部分、`compose_video.py`で日本語の見出し・字幕と動画を書き出します。
動画の3D部分は短い信号の動きを繰り返し、説明を読める時間を確保しています。

以下をプロジェクトのルートから実行します。Blender・FFmpeg・書体のパスはスクリプト先頭にあります。
合成工程では`../aquabeacon-brand/aquabeacon_logo_transparent.png`を使用します。

```powershell
& 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe' --background --factory-startup --python-exit-code 1 --python 'assets\aquabeacon-explainer\build_scene.py' -- --render all
python 'assets\aquabeacon-explainer\compose_video.py'
```

Python側の依存：Pillow、NumPy。日本語はNoto Sans JP、ロゴは前回のオリジナル素材です。
ZIPには素材の確認用に取り出したPowerPoint内の画像や、大量のレンダリング途中ファイルを含めていません。
