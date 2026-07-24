---
applyTo: "**"
---

# learnlog プロジェクト共通ルール

## プロジェクト概要
勉強管理アプリ。フロントエンド(React) + バックエンド(FastAPI) 構成。

## インフラ構成 (AWS)
- フロントエンド: S3 静的ホスティング + CloudFront (HTTPS)
- バックエンド: API Gateway + Lambda (FastAPI)
- データベース: DynamoDB

## ディレクトリ構成
- `web/` — React フロントエンド
- `api/` — FastAPI バックエンド
- `docs/` — ドキュメント
- `infra/` — インフラ構成 (CloudFormation YAML)

## 共通ルール
- コメントは日本語で書く
- 変数名・関数名は英語で書く
- 不要なコードやコメントは残さない
- 環境変数は `.env` で管理し、ハードコードしない
