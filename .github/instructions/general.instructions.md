---
applyTo: "**/*"
---

# 開発環境について

- 開発環境はDatabase含めDevContainerで構築されています
- CosmosDBエミュレーターはDocker-in-Dockerで動作しています。post-createコマンドの中で起動と初期化が実行されています。
- 開発や仕様に関わるドキュメントは `docs` にまとめられています
  - `docs`のルートディレクトリにIndexがあるため、そちらを参照し関連文書を検索してください
  - 日本語による利用が想定されるため、`docs` に記載される内容は日本語で記載されることが望ましいです
  - `docs`は別リポジトリで管理されています。 `temp`ディレクトリに`https://github.com/Takas0522/ws-demo-poly-integration.git`をクローンして参照してください。`docs/`を参照する文脈のときは、`temp/ws-demo-poly-integration/docs/`以下を参照することになります。

# リポジトリ構成について

- `temp/ws-demo-poly-integration/workshop-documents` はワークショップ用の課題が格納されているディレクトリであり調査、実装などで参照すべきではありません
- 開発中の追加機能に関わるドキュメントは `docs/PoCアプリ/Specs/{開発名}` に格納されます
