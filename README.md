
# ニュース株選定パイプライン

このリポジトリはRSSニュースを収集し、関連するWebページから本文を取得するPython 3.11向けツールです。取得データはSQLiteに保存されます。

## セットアップ

1. Poetryをインストール後、依存パッケージを取得します。
   ```bash
   make install
   ```
2. Playwright用のブラウザバイナリをダウンロードします。
   ```bash
   make playwright-init
   ```

## 使い方

### RSS記事の収集

`feeds.yaml` にRSSフィードのURLとsource名を記載したら以下を実行します。
```bash
python src/collector/fetch_rss.py
```
`data/raw_articles.db` に記事URLやタイトルが保存されます。

### HTML本文の取得

RSS取得後、保存されたURLから本文を取得します。
```bash
python -m collector.fetch_html
```
`data/html_articles.db` に本文テキストと著者情報が追記されます。

## テスト

ユニットテストはpytestで実行できます。
```bash
poetry run pytest
```

## 定期実行

`.github/workflows/daily.yml` により、毎日00:05 JSTに上記スクリプトが自動実行され、生成されたDBはGitHub Actionsのアーティファクトとして保存されます。
