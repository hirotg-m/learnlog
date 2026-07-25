# AWS へのデプロイ手順

`infra/` の CloudFormation テンプレートで配信・実行基盤(S3 / CloudFront / Lambda / API Gateway / DynamoDB)を作成し、
アプリコード(`web/` のビルド成果物、`api/` のソース)は AWS CLI で手動デプロイする手順。

GitHub Actions (`.github/workflows/cd-dev.yml`, `cd-prod.yml`) によるコードデプロイの自動化は現時点では使わず、
インフラ構築・コードデプロイともに手元(またはEC2上)の AWS CLI から行う運用としている。
将来 GitHub Actions 経由の自動デプロイに切り替える場合は、末尾の「GitHub Actions に切り替える場合」を参照。

## 前提

- AWS CLI が使えること、対象アカウントへの管理者相当の権限を持つ認証情報を `aws configure` 等で設定済みであること
  (`aws sts get-caller-identity` で確認できる)
- デプロイ先リージョンを決めておくこと (例: `ap-northeast-1`)
- dev / prod は別々の AWS アカウントを使う想定(`infra/dynamodb.yaml` のテーブル名が環境で分かれていないため、同一アカウントに両方デプロイすると衝突する)

```bash
export AWS_DEFAULT_REGION=ap-northeast-1
```

## 1. インフラを CloudFormation で作成する

依存関係があるため、この順番で作成する。

1. `infra/dynamodb.yaml`(テーブル)
2. `infra/frontend.yaml`(S3 + CloudFront)
3. `infra/backend.yaml`(Lambda + API Gateway、`frontend.yaml` の出力を CORS 許可オリジンとして使う)

### 1-1. DynamoDB

```bash
aws cloudformation deploy \
  --template-file infra/dynamodb.yaml \
  --stack-name learnlog-dynamodb
```

### 1-2. フロントエンド (S3 + CloudFront)

```bash
aws cloudformation deploy \
  --template-file infra/frontend.yaml \
  --stack-name learnlog-frontend-prod \
  --parameter-overrides EnvironmentName=prod
```

CloudFront ディストリビューションの作成には数分〜十数分かかることがある。完了後、出力の
`BucketName` / `DistributionId` / `DistributionDomainName` を控えておく(以降のステップで使う)。

```bash
aws cloudformation describe-stacks \
  --stack-name learnlog-frontend-prod \
  --query "Stacks[0].Outputs" --output table
```

### 1-3. バックエンド (Lambda + API Gateway)

`LearnlogPin` はシェル履歴に残るため、共有端末では対話的に入力するなど扱いに注意する。

```bash
aws cloudformation deploy \
  --template-file infra/backend.yaml \
  --stack-name learnlog-backend-prod \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    EnvironmentName=prod \
    FrontendOrigin=https://<1-2 で控えた DistributionDomainName> \
    LearnlogPin=<8桁PIN> \
    CookieSecure=true
```

出力の `ApiEndpoint` / `LambdaFunctionName` を控えておく。

```bash
aws cloudformation describe-stacks \
  --stack-name learnlog-backend-prod \
  --query "Stacks[0].Outputs" --output table
```

この時点では `backend.yaml` が作成した Lambda はプレースホルダーコード(`503` を返すだけ)なので、
次の手順で実際のアプリコードをデプロイする。

## 2. アプリコードを手動デプロイする

インフラ作成後、コードを変更するたびに以下を実行する。

### 2-1. バックエンド (Lambda)

```bash
cd api

# 依存パッケージをビルド用ディレクトリにインストール
rm -rf /tmp/lambda-build && mkdir -p /tmp/lambda-build/package
./.venv/bin/pip install -r requirements.txt -t /tmp/lambda-build/package

# アプリコードを加えて zip化
cp -r app /tmp/lambda-build/package/
cd /tmp/lambda-build/package
rm -f /tmp/lambda-build/lambda.zip
zip -rq /tmp/lambda-build/lambda.zip . -x "*.pyc" -x "__pycache__/*"

# Lambda のコードを更新
aws lambda update-function-code \
  --function-name learnlog-api-prod \
  --zip-file fileb:///tmp/lambda-build/lambda.zip
```

動作確認:

```bash
curl -i https://<ApiEndpoint>/api/v1/auth/session
# ログインしていなければ 401 が返れば正常

curl -i -X POST https://<ApiEndpoint>/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"pin": "<8桁PIN>"}'
# 200 と Set-Cookie が返れば、Lambda -> DynamoDB の疎通も含めて正常
```

### 2-2. フロントエンド (S3 + CloudFront)

```bash
cd web

# API エンドポイントを指定してビルド (backend.yaml の ApiEndpoint + /api/v1)
VITE_API_ENDPOINT=https://<ApiEndpoint>/api/v1 npm run build

# S3 に同期
aws s3 sync dist/ s3://<frontend.yaml の BucketName> --delete

# CloudFront のキャッシュを削除 (反映まで数十秒〜数分かかることがある)
aws cloudfront create-invalidation \
  --distribution-id <frontend.yaml の DistributionId> \
  --paths "/*"
```

動作確認: `https://<DistributionDomainName>` にブラウザでアクセスし、PIN ログインができることを確認する。

## デプロイ後にやること

- 動作確認: `https://<CloudFrontドメイン>` にアクセスし、PIN ログイン〜資格登録〜学習記録登録が一通りできることを確認する
- (任意) CI/CD 用 IAM ユーザーの作成(`docs/aws/iam-policy.md`)は、GitHub Actions を使わない限り不要

## 削除する場合

`frontend.yaml` の S3 バケットは `DeletionPolicy: Retain`、`dynamodb.yaml` の各テーブルも同様に `Retain` のため、
`aws cloudformation delete-stack` してもデータは残る。完全に削除したい場合はスタック削除後に手動でバケット・テーブルを削除する。

## GitHub Actions に切り替える場合

将来 push 契機の自動デプロイ (`cd-dev.yml` / `cd-prod.yml`) に切り替える場合は、`docs/repo/github-actions-secrets.md`
に従って以下の GitHub Secrets を登録する。値は上記の CloudFormation 出力から取得する。

| Secret | 値の取得元 |
|---|---|
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `AWS_REGION` | `docs/aws/iam-policy.md` の手順で作成する `learnlog-user` のアクセスキー |
| `DEV_S3_BUCKET` / `PROD_S3_BUCKET` | `frontend.yaml` の `BucketName` |
| `DEV_CF_DISTRIBUTION_ID` / `PROD_CF_DISTRIBUTION_ID` | `frontend.yaml` の `DistributionId` |
| `DEV_API_ENDPOINT` / `PROD_API_ENDPOINT` | `backend.yaml` の `ApiEndpoint` + `/api/v1` |
| `DEV_LAMBDA_FUNCTION_NAME` / `PROD_LAMBDA_FUNCTION_NAME` | `backend.yaml` の `LambdaFunctionName` |

登録後、`develop`(dev) または `main`(prod)に push すれば、以降は本ドキュメントの
「2. アプリコードを手動デプロイする」の内容を GitHub Actions が代行する。
