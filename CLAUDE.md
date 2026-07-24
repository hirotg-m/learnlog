# learnlog

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

## フロントエンド (web/)
- TypeScript の strict モードを有効にする
- `any` 型は使用しない
- コンポーネントは関数コンポーネント + Hooks を使用
- ファイル名はコンポーネントは PascalCase、それ以外は camelCase
- Props には型定義を必ず付ける
- APIエンドポイントは環境変数で管理しハードコードしない

## バックエンド (api/)
- 型ヒントを必ず付ける
- Ruff でリント・フォーマットを実行する
- ルーターは機能単位でファイルを分割する
- リクエスト/レスポンスは Pydantic モデルで定義する
- DB 操作はルーターに直接書かず、サービス層に分離する
- 例外は `HTTPException` を使用し、適切なステータスコードを返す
- AWS リソースへのアクセスは boto3 で行う
