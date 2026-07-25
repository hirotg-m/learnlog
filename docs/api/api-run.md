# APIサーバーの実行方法

ローカル環境で `api/`(FastAPI)を起動する手順。本番は Lambda + API Gateway だが、開発時は `uvicorn` でローカル起動する。

## 前提

- Python 3.12
- ストア実装は `STORE_BACKEND` で切り替わる(既定は `memory`)。DynamoDB実機に繋ぐ場合のみ AWS 認証情報が必要

## セットアップ

```bash
cd api
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
```

`docs/testing.md` にあるとおり、テストも実行する場合は `requirements-dev.txt` を使う。

## 環境変数 (`api/.env`)

| 変数名 | 用途 | 既定値 |
|---|---|---|
| `LEARNLOG_PIN` | ログインPIN | `12345678` |
| `COOKIE_SECURE` | セッションCookieの `Secure` 属性 | `true` |
| `FRONTEND_ORIGIN` | CORS許可オリジン | `http://localhost:5173` |
| `STORE_BACKEND` | `memory` または `dynamodb` | `memory` |

`STORE_BACKEND=dynamodb` のときのみ以下も参照する(未設定時は `infra/dynamodb.yaml` と同じテーブル名を使う)。

| 変数名 | 用途 | 既定値 |
|---|---|---|
| `QUALIFICATIONS_TABLE` | 資格テーブル名 | `learnlog-qualifications` |
| `STUDY_LOGS_TABLE` | 学習記録テーブル名 | `learnlog-study-logs` |
| `MILESTONES_TABLE` | マイルストーンテーブル名 | `learnlog-milestones` |
| `LOGIN_ATTEMPTS_TABLE` | ログイン失敗カウンタテーブル名 | `learnlog-login-attempts` |
| `SESSIONS_TABLE` | セッションテーブル名 | `learnlog-sessions` |
| `DYNAMODB_ENDPOINT_URL` | DynamoDBのエンドポイント差し替え(DynamoDB Local等)。未設定時はAWS実エンドポイント | なし |

`api/.env` には `LEARNLOG_PIN` のみ設定済み。ハードコードせず、必要な値は `.env` に追記する。

## 起動方法

### 1. メモリストア(既定・AWS不要)

資格・学習記録などをプロセス内メモリに保持する。動作確認用の最も手軽な起動方法。

```bash
cd api
./.venv/bin/uvicorn app.main:app --reload --env-file .env
```

起動後、`http://localhost:8000/api/v1/auth/session` などにアクセスできる。`web/` から使う場合は `web/.env` の `VITE_API_ENDPOINT`(既定 `http://localhost:8000/api/v1`)と向き先を合わせる。

### 2. DynamoDBストア

`STORE_BACKEND=dynamodb` を指定すると `DynamoDBStore`(`api/app/repositories/dynamodb_store.py`)を使う。接続先は `DYNAMODB_ENDPOINT_URL` の有無で切り替わる。

- 設定あり: `DYNAMODB_ENDPOINT_URL` が指すエンドポイント(DynamoDB Local等)に接続する
- 未設定: AWS実機のDynamoDBに接続する

いずれの場合も、テーブルは `infra/dynamodb.yaml` と同じ名前・キー・GSI構成で事前に作成しておく必要がある(アプリ側はテーブル作成を行わない)。

#### 2-1. DynamoDB Local を使う場合

AWS実機に繋がずローカルだけで動作確認したい場合。Dockerが必要。

> APIサーバー自身がポート8000で起動する(下記「1. メモリストア」・「動作確認」参照)ため、DynamoDB Localのホスト側ポートは別にする必要がある。以下ではホスト側 `8001` → コンテナ側 `8000` にマッピングする(`-p 8001:8000`)。

1. DynamoDB Local を起動する

   コンテナを止めるとデータが消えて良い場合(`-inMemory`):

   ```bash
   docker run -d --rm --name learnlog-ddb-local -p 8001:8000 \
     amazon/dynamodb-local:latest -jar DynamoDBLocal.jar -inMemory -sharedDb
   ```

   コンテナを再作成してもデータを残したい場合は、Dockerボリュームに `-dbPath` でデータを永続化する。イメージ内のプロセスは非rootユーザーで動くため、ボリュームへの書き込み権限を持たせるのに `--user root` が必要(付けないと `unable to open database file` で起動に失敗する)。

   ```bash
   docker volume create learnlog-ddb-data

   docker run -d --rm --name learnlog-ddb-local -p 8001:8000 \
     --user root \
     -v learnlog-ddb-data:/home/dynamodblocal/data \
     amazon/dynamodb-local:latest \
     -jar DynamoDBLocal.jar -sharedDb -dbPath /home/dynamodblocal/data
   ```

   2回目以降も同じ `docker run` コマンドで起動すれば、`learnlog-ddb-data` ボリュームに保存されたデータ(テーブル・レコード)を引き継げる。データを完全に消したい場合は `docker volume rm learnlog-ddb-data` で削除する。

2. `infra/dynamodb.yaml` と同じ構成でテーブルを作成する(`tests/integration/conftest.py` の `_create_tables` も同内容)

   ```bash
   ENDPOINT=http://localhost:8001

   aws dynamodb create-table --endpoint-url $ENDPOINT \
     --table-name learnlog-qualifications \
     --attribute-definitions AttributeName=id,AttributeType=S \
     --key-schema AttributeName=id,KeyType=HASH \
     --billing-mode PAY_PER_REQUEST

   aws dynamodb create-table --endpoint-url $ENDPOINT \
     --table-name learnlog-study-logs \
     --attribute-definitions AttributeName=id,AttributeType=S AttributeName=qualificationId,AttributeType=S AttributeName=date,AttributeType=S AttributeName=month,AttributeType=S \
     --key-schema AttributeName=id,KeyType=HASH \
     --global-secondary-indexes \
       'IndexName=ByQualification,KeySchema=[{AttributeName=qualificationId,KeyType=HASH},{AttributeName=date,KeyType=RANGE}],Projection={ProjectionType=ALL}' \
       'IndexName=ByMonth,KeySchema=[{AttributeName=month,KeyType=HASH},{AttributeName=date,KeyType=RANGE}],Projection={ProjectionType=ALL}' \
     --billing-mode PAY_PER_REQUEST

   aws dynamodb create-table --endpoint-url $ENDPOINT \
     --table-name learnlog-milestones \
     --attribute-definitions AttributeName=id,AttributeType=S AttributeName=qualificationId,AttributeType=S \
     --key-schema AttributeName=id,KeyType=HASH \
     --global-secondary-indexes \
       'IndexName=ByQualification,KeySchema=[{AttributeName=qualificationId,KeyType=HASH}],Projection={ProjectionType=ALL}' \
     --billing-mode PAY_PER_REQUEST

   aws dynamodb create-table --endpoint-url $ENDPOINT \
     --table-name learnlog-login-attempts \
     --attribute-definitions AttributeName=id,AttributeType=S \
     --key-schema AttributeName=id,KeyType=HASH \
     --billing-mode PAY_PER_REQUEST

   aws dynamodb create-table --endpoint-url $ENDPOINT \
     --table-name learnlog-sessions \
     --attribute-definitions AttributeName=token,AttributeType=S \
     --key-schema AttributeName=token,KeyType=HASH \
     --billing-mode PAY_PER_REQUEST
   ```

   DynamoDB Localは認証情報の中身を検証しないが、AWS CLI/boto3はリージョン・認証情報が未設定だとエラーになるため、ダミー値を渡す(既に `~/.aws/credentials` を設定済みなら不要)。

   ```bash
   export AWS_ACCESS_KEY_ID=dummy
   export AWS_SECRET_ACCESS_KEY=dummy
   export AWS_DEFAULT_REGION=ap-northeast-1
   ```

3. `DYNAMODB_ENDPOINT_URL` を指定してAPIサーバーを起動する

   APIサーバー内部の `DynamoDBStore`(`api/app/repositories/dynamodb_store.py`)も内部でboto3を使っているため、サーバープロセス自身にもリージョン・認証情報が必要(値の中身はDynamoDB Localには渡らないので何でもよい)。手順2で `export` したのと同じシェルセッションでそのまま起動すれば環境変数は引き継がれるが、別セッションで起動する場合や `~/.aws/credentials` が未設定の場合は `NoRegionError` / `NoCredentialsError` で起動時に失敗する。確実なのは `api/.env` にダミー値を追記しておく方法(`--env-file .env` で読み込まれる)。

   ```bash
   # api/.env に追記
   AWS_ACCESS_KEY_ID=dummy
   AWS_SECRET_ACCESS_KEY=dummy
   AWS_DEFAULT_REGION=ap-northeast-1
   ```

   ```bash
   cd api
   STORE_BACKEND=dynamodb DYNAMODB_ENDPOINT_URL=http://localhost:8001 \
     ./.venv/bin/uvicorn app.main:app --reload --env-file .env --host 0.0.0.0
   ```

   > EC2上などで動かし、手元のPCのブラウザからアクセスする場合は `--host 0.0.0.0` を付けて全インターフェースにバインドし、`api/.env` の `FRONTEND_ORIGIN` にブラウザ側のオリジン(例: `http://<EC2のパブリックIP>:5173`)を設定する。詳細は `docs/web/web-run.md` の「EC2上などリモート環境で、ブラウザ(手元のPC)からアクセスしたい場合」を参照。

4. 動作確認(テーブル一覧・データ確認)

   ```bash
   aws dynamodb scan --endpoint-url http://localhost:8001 --table-name learnlog-qualifications
   ```

5. 終了時はコンテナを止める(`--rm` 付きなので停止と同時に削除される)

   ```bash
   docker stop learnlog-ddb-local
   ```

> Cookieに `Secure` 属性が付いていると、`http://` 経由のブラウザ/curlではブラウザ・curlがCookieを送り返さないことがある。ローカルでログイン込みの動作確認をする場合は `.env` に `COOKIE_SECURE=false` を追加する(`api/tests/unit/conftest.py` のテスト設定と同様)。

#### 2-2. AWS実機のDynamoDBを使う場合

開発環境(dev)や本番相当のDynamoDBに接続して動作確認したい場合。

1. `infra/dynamodb.yaml` からテーブルを作成する(未作成の場合)

   ```bash
   aws cloudformation deploy \
     --template-file infra/dynamodb.yaml \
     --stack-name learnlog-dynamodb
   ```

2. AWS認証情報を設定する。`learnlog-user`(`docs/iam-policy.md` 参照)相当の、DynamoDBへの `GetItem`/`PutItem`/`UpdateItem`/`DeleteItem`/`Query`/`Scan` 権限を持つ認証情報が必要

   ```bash
   aws configure --profile learnlog
   # または環境変数で指定
   export AWS_ACCESS_KEY_ID=...
   export AWS_SECRET_ACCESS_KEY=...
   export AWS_DEFAULT_REGION=ap-northeast-1
   ```

   `AWS_PROFILE` を使う場合:

   ```bash
   export AWS_PROFILE=learnlog
   ```

3. `DYNAMODB_ENDPOINT_URL` を設定せずに起動する(未設定時はAWSの実エンドポイントに向く)

   ```bash
   cd api
   STORE_BACKEND=dynamodb ./.venv/bin/uvicorn app.main:app --reload --env-file .env
   ```

4. テーブル名がデフォルト(`learnlog-qualifications` 等)と異なる場合は、`QUALIFICATIONS_TABLE` 等の環境変数で個別に上書きする(`api/app/repositories/dynamodb_store.py` 参照)

> **注意**: この方法は実際のAWSリソースに対して読み書きする。開発用アカウント・開発用テーブル以外(特に本番)には接続しないこと。誤って本番データを変更・削除しないよう、接続先(リージョン・アカウント・テーブル名)を必ず確認してから実行する。

## 動作確認

```bash
curl -i http://localhost:8000/api/v1/auth/session
```

未ログイン状態では `401` が返る。

```
HTTP/1.1 401 Unauthorized
content-type: application/json

{"detail":"unauthorized"}
```

PINログインは以下で確認できる。

```bash
curl -i -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"pin": "12345678"}'
```

## 関連ドキュメント

- テストの実行方法: `docs/testing.md`
- APIの仕様: `docs/api-spec.md`
- IAM権限: `docs/iam-policy.md`
