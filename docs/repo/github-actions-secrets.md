# GitHub Actions Secrets

GitHub リポジトリの Settings > Secrets and variables > Actions に以下を登録する。

## AWS 共通

| Secret | 説明 | 例 |
|---|---|---|
| `AWS_ACCESS_KEY_ID` | AWS アクセスキー | `AKIA...` |
| `AWS_SECRET_ACCESS_KEY` | AWS シークレットアクセスキー | |
| `AWS_REGION` | デプロイ先リージョン | `ap-northeast-1` |

## フロントエンド

| Secret | 環境 | 説明 |
|---|---|---|
| `DEV_API_ENDPOINT` | dev | API Gateway エンドポイント URL |
| `DEV_S3_BUCKET` | dev | S3 バケット名 |
| `DEV_CF_DISTRIBUTION_ID` | dev | CloudFront ディストリビューション ID |
| `PROD_API_ENDPOINT` | prod | API Gateway エンドポイント URL |
| `PROD_S3_BUCKET` | prod | S3 バケット名 |
| `PROD_CF_DISTRIBUTION_ID` | prod | CloudFront ディストリビューション ID |

## バックエンド

| Secret | 環境 | 説明 |
|---|---|---|
| `DEV_LAMBDA_FUNCTION_NAME` | dev | Lambda 関数名 |
| `PROD_LAMBDA_FUNCTION_NAME` | prod | Lambda 関数名 |

## 注意事項
- Secret の値は登録後に参照できない。紛失した場合は再登録する
- AWS アクセスキーは CI/CD 専用の IAM ユーザーを作成し、最小権限を付与する
- 本番環境の Secret は担当者を限定して管理する
