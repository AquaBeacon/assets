# 開発ガイド

ロゴ・説明図・紹介映像。

各サブディレクトリのREADMEに制作手順があります。Blender、FFmpeg、Pythonを使い、素材間の相対配置を保って編集します。

## 入口

画像・音声・映像・BlenderファイルはGit LFSで公開しています。Git LFSを導入して `git lfs install`、clone後に必要なら `git lfs pull` を実行してください。LFSデータは約1.5 GiBです。動画の元素材を追加する場合は出典と配布許諾を確認してください。

- [aquabeacon-brand/README.md](aquabeacon-brand/README.md)
- [aquabeacon-film60/README.md](aquabeacon-film60/README.md)

## 検証

ビルド・実機・外部ツールの確認手順はREADMEを参照してください。移行検証だけで実機動作・製造可能性を合格扱いにしません。

## データと関連リポジトリ

このディレクトリがGitリポジトリのルートです。親の AquaBeacon-OSS は複数リポジトリの置き場です。横断開発では各リポジトリを同じ親ディレクトリに配置し、[全体の入口](https://github.com/AquaBeacon/workspace-tools)から関連設計へ進みます。単体checkoutでも本書のローカル入口を使用できます。

生データ・生成物・SDK・仮想環境は手元に保持し、公開対象を.gitignoreで区別します。追跡済みのファイルは.gitignoreだけでは除外されないので、`git status --short`と`git ls-files`を確認します。

ライセンスは[Apache 2.0](LICENSE)、第三者部分は[THIRD_PARTY.md](THIRD_PARTY.md)。

## 公開リポジトリ

GitHub: https://github.com/AquaBeacon/assets

```sh
git clone https://github.com/AquaBeacon/assets.git
```

公開ブランチはmainです。新設リポジトリは公開対象だけを初期履歴にし、過去の開発履歴と実験ログはローカルに保管します。
