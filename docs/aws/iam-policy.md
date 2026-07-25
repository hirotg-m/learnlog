# IAM 構成

## リソース一覧

| リソース | 名前 | 用途 |
|---|---|---|
| IAM ユーザー | `learnlog-user` | GitHub Actions からの AWS 操作 |
| IAM ポリシー | `learnlog-policy` | `learnlog-user` に付与する権限 |
| IAM ロール | `learnlog-lambda-role` | Lambda の実行ロール |

---

## learnlog-user / learnlog-policy

### 作成手順

1. AWS コンソール > IAM > ポリシー > ポリシーを作成
2. ポリシー名: `learnlog-policy`、以下の権限を付与
3. AWS コンソール > IAM > ユーザー > ユーザーを作成
4. ユーザー名: `learnlog-user`、AWS マネジメントコンソールへのアクセスは不要
5. `learnlog-policy` をアタッチ
6. アクセスキーを発行し、GitHub Secrets に登録する

### learnlog-policy の権限

#### S3

```json
{
  "Effect": "Allow",
  "Action": [
    "s3:PutObject",
    "s3:DeleteObject",
    "s3:ListBucket"
  ],
  "Resource": [
    "arn:aws:s3:::<バケット名>",
    "arn:aws:s3:::<バケット名>/*"
  ]
}
```

#### CloudFront

```json
{
  "Effect": "Allow",
  "Action": [
    "cloudfront:CreateInvalidation"
  ],
  "Resource": "arn:aws:cloudfront::<アカウントID>:distribution/<ディストリビューションID>"
}
```

#### Lambda

```json
{
  "Effect": "Allow",
  "Action": [
    "lambda:UpdateFunctionCode"
  ],
  "Resource": "arn:aws:lambda:<リージョン>:<アカウントID>:function:<関数名>"
}
```

---

## learnlog-lambda-role

### 作成手順

1. AWS コンソール > IAM > ロール > ロールを作成
2. 信頼されたエンティティ: AWS のサービス > Lambda
3. ロール名: `learnlog-lambda-role`
4. 以下の権限をアタッチ

### 権限

#### DynamoDB

テーブルはエンティティごとに分割している(infra/dynamodb.yaml、docs/api-spec.md 10 章参照)。GSI に対する `Query` も行うため、各テーブルの `index/*` も Resource に含める。

```json
{
  "Effect": "Allow",
  "Action": [
    "dynamodb:GetItem",
    "dynamodb:PutItem",
    "dynamodb:UpdateItem",
    "dynamodb:DeleteItem",
    "dynamodb:Query",
    "dynamodb:Scan"
  ],
  "Resource": [
    "arn:aws:dynamodb:<リージョン>:<アカウントID>:table/learnlog-qualifications",
    "arn:aws:dynamodb:<リージョン>:<アカウントID>:table/learnlog-study-logs",
    "arn:aws:dynamodb:<リージョン>:<アカウントID>:table/learnlog-study-logs/index/*",
    "arn:aws:dynamodb:<リージョン>:<アカウントID>:table/learnlog-milestones",
    "arn:aws:dynamodb:<リージョン>:<アカウントID>:table/learnlog-milestones/index/*",
    "arn:aws:dynamodb:<リージョン>:<アカウントID>:table/learnlog-login-attempts",
    "arn:aws:dynamodb:<リージョン>:<アカウントID>:table/learnlog-sessions"
  ]
}
```

#### CloudWatch Logs（Lambda の基本実行権限）

AWS 管理ポリシー `AWSLambdaBasicExecutionRole` をアタッチする。

---

## 注意事項
- dev / prod でリソースが異なる場合、それぞれのリソース ARN を Resource に追加する
- `"Resource": "*"` は使用しない（最小権限の原則）
- アクセスキーは定期的にローテーションする
