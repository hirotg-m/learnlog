---
applyTo: "**"
---

# learnlog プロジェクト共通ルール

## プロジェクト概要
勉強管理アプリ。フロントエンド(React) + バックエンド(FastAPI) 構成。

## インフラ構成 (AWS)
- フロントエンド: S3 静的ホスティング + CloudFront (HTTPS)
- バックエンド: API Gateway + Lambda (FastAPI + Mangum)
- データベース: DynamoDB

## ディレクトリ構成
- `web/` — Node.js 24 / TypeScript / React
- `api/` — Python 3.12 / FastAPI
- `docs/` — ドキュメント
- `infra/` — インフラ構成 (CloudFormation YAML)

## 共通ルール
- コメントは日本語で書く
- 変数名・関数名は英語で書く
- 不要なコードやコメントは残さない
- 環境変数は `.env` で管理し、ハードコードしない
