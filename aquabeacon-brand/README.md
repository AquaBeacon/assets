# AquaBeacon ロゴ・アイコン・アニメーション

Blender 5.2.1 LTS / Cycles / NVIDIA OptiXで制作したオリジナルのロゴです。
頭文字A、水・音の波、光ビーコンを一つのシンボルにまとめています。

| ファイル | 用途・仕様 |
| --- | --- |
| `aquabeacon_logo.png` | 背景付きロゴ、1920×1080 |
| `aquabeacon_icon.png` | 角丸のアプリアイコン、1024×1024、角の外側は透過 |
| `aquabeacon_icon_512.png`〜`aquabeacon_icon_32.png` | 小サイズのアイコン |
| `aquabeacon_symbol_transparent.png` | シンボルのみ、1024×1024、透過背景 |
| `aquabeacon_logo_transparent.png` | 名前付きロゴ、2400×900、透過背景 |
| `aquabeacon_symbol_flat.svg` | 立体表現を省いた拡大可能なカラーマーク |
| `aquabeacon_symbol_white.svg` | 白一色のマーク、暗い背景用 |
| `aquabeacon.ico` | Windows／Webのアイコン |
| `aquabeacon_animation.mp4` | 5秒、1920×1080、30fps、H.264、無音 |
| `aquabeacon_animation.gif` | 表示確認用、800×450、15fps、繰り返し再生 |
| `aquabeacon_brand.blend` | 編集可能なBlenderシーン。フォントはファイル内に同梱 |
| `aquabeacon_brand_assets.zip` | 上記素材、スクリプト、説明、フォントライセンスの一式 |

## アニメーション

最初に光点が点灯し、A・波・信号の弧が現れます。
円形の音響パルスが広がり、シンボルが左へ移動して名前が表示されます。
約3.3秒から最後まで完成したロゴを保持します。

## Blenderで編集する

`aquabeacon_brand.blend`を開き、画面上部のシーン切替で選択してください。

1. `01 · AquaBeacon / Animation`：150フレームのアニメーションと背景付きロゴ。
2. `02 · App icon`：角丸アイコン。
3. `03 · Symbol transparent`：背景なしのシンボル。
4. `04 · Logo transparent`：背景なしの名前付きロゴ。

保存時はアニメーションの完成形が見える120フレームを表示しています。
シンボルは名前の付いたカーブ、文字は編集可能なテキストです。
色は各オブジェクトのマテリアルから変更できます。
シンボルの形状は`create_brand.py`の`mark()`でも調整できます。

## 再生成

PowerShellでこのプロジェクトのルートから実行してください。
BlenderおよびFFmpegのパスは必要に応じて変更してください。

```powershell
& 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe' --background --factory-startup --python-exit-code 1 --python 'assets\aquabeacon-brand\create_brand.py' -- --mode stills
& 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe' --background 'assets\aquabeacon-brand\aquabeacon_brand.blend' --python-exit-code 1 --python 'assets\aquabeacon-brand\create_brand.py' -- --mode animation
python 'assets\aquabeacon-brand\package_assets.py'
```

動画の元フレームは`frames/`に出力されます。一式のZIPには元フレームとキャッシュを含めていません。
`validation.json`に画像サイズ・透過・動画形式・フレーム数・再生時間の確認結果を記録します。

書体はInstrument SansおよびDM Monoです。同梱のSIL Open Font Licenseをご確認ください。
フォント以外のシンボル形状とアニメーションは今回新規に制作しています。
