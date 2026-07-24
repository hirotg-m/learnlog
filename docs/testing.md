# バックエンドのテスト方法

## ディレクトリ構成

```
api/tests/
  unit/         単体テスト。MemoryStore を使い、TestClient 経由で API を叩く
  integration/  結合テスト
    test_dynamodb_store.py  DynamoDBStore を直接呼び出す (プロセス内 moto)
    test_api_server.py      uvicorn で実際に起動したバックエンドに、実HTTPでアクセスする
```

| 種類 | 対象 | 依存先 |
|---|---|---|
| 単体テスト (`tests/unit`) | ルーター〜サービス層のロジック(バリデーション、認証ロック、並び順など) | `MemoryStore`(インメモリ、実AWS不要) |
| 結合テスト・リポジトリ層 (`test_dynamodb_store.py`) | `DynamoDBStore` のクエリ(GSIの絞り込み、集計)が実際のDynamoDBの挙動として正しいか | `moto`(プロセス内でboto3呼び出しを模擬。サーバー起動なし) |
| 結合テスト・実サーバー (`test_api_server.py`) | バックエンド(FastAPI)を実際に別プロセスで起動し、実HTTPでCookie認証・CORSなどを含めた一連の流れを確認する | `uvicorn`(別プロセス)+ `moto` の standalone サーバーモード(別プロセスからも繋げるHTTPサーバー) |

## セットアップ

```bash
cd api
python3 -m venv .venv
./.venv/bin/pip install -r requirements-dev.txt
```

`requirements-dev.txt` は `requirements.txt`(本番依存)に加えて、結合テスト用の `moto[dynamodb,server]` を含む。

## 実行方法

```bash
# 全テスト
./.venv/bin/pytest -q

# 単体テストのみ
./.venv/bin/pytest -q tests/unit

# 結合テストのみ
./.venv/bin/pytest -q tests/integration
```

## 単体テスト (tests/unit)

- `tests/unit/conftest.py` の `client` フィクスチャが `TestClient` を生成し、ASGI経由でアプリを直接呼び出す(実サーバー起動なし)
- `reset_store`(autouse)がテストごとに `MemoryStore.reset()` とセッションのクリアを行う。サービス層は `app.dependencies` のシングルトンを参照しているため、これがないと前のテストの状態が引き継がれてしまう
- `setup_pin`(autouse)が `LEARNLOG_PIN` を固定し、Cookieの `Secure` 属性をテスト用に無効化する

## 結合テスト・リポジトリ層 (tests/integration/test_dynamodb_store.py)

- `tests/integration/conftest.py` の `dynamodb_resource` フィクスチャが `moto.mock_aws` でDynamoDBを模擬し、`infra/dynamodb.yaml` と同じテーブル名・キー・GSI構成(`ByQualification`, `ByMonth`)でテーブルを作成する
- `dynamodb_store` フィクスチャが、その模擬テーブルに接続した `DynamoDBStore` を返す
- FastAPIのルーターは経由せず、`DynamoDBStore` のメソッドを直接呼び出す。サーバープロセスは起動しない
- 単体テストでは検出できない、DynamoDB特有の挙動を検証する。特に以下は実装時に見落としやすいため、リグレッションテストとして残している
  - `ByQualification` / `ByMonth` GSIが設計通り絞り込めるか(docs/api-spec.md 10章)
  - 学習記録の `date` を更新する際に `month` を再計算し忘れると、レコードが古い月のパーティションに残ったまま、新しい月のカレンダー集計に出てこなくなること(docs/api-spec.md 10.2)
  - ログイン失敗カウンタが、別インスタンスの `DynamoDBStore` からでも参照できること(MemoryStore と異なり、プロセス内の変数ではなくDynamoDB自体に永続化されているか)

## 結合テスト・実サーバー (tests/integration/test_api_server.py)

「バックエンドを実際に動かした状態」を検証する結合テスト。以下の2段階で構成される。

1. `moto_server_endpoint` フィクスチャが `moto.server.ThreadedMotoServer` を起動する。これはプロセス内モック(`mock_aws`)と異なり、実際にソケットで待ち受けるHTTPサーバーなので、**別プロセスからも** `endpoint_url` 経由で接続できる
2. `live_api_base_url` フィクスチャが、`STORE_BACKEND=dynamodb` と `DYNAMODB_ENDPOINT_URL`(上記moto サーバーのURL)を環境変数に設定したうえで、`uvicorn app.main:app` を **`subprocess.Popen` で別プロセスとして起動**する。起動後は `/api/v1/auth/session` にポーリングして起動完了を待つ

テストは `httpx.Client` で実際にHTTPリクエストを送り、PINログイン→Cookie付与→以降のリクエストでの認証→資格登録→学習記録登録→カレンダー参照、という一連の流れを本物のプロセス境界・HTTP境界を越えて検証する。

- `DynamoDBStore` は `DYNAMODB_ENDPOINT_URL` 環境変数が設定されている場合、boto3のエンドポイントをそちらに向ける(未設定時は本番のAWSエンドポイントのまま)
- moto の standalone サーバーはプロセス内でバックエンド状態を共有するため、`moto_server_endpoint` フィクスチャは起動直後に `POST /moto-api/reset` を呼び、テスト間の状態が混ざらないようにしている
- `moto[server]`(Flask依存)が必要なため、`requirements-dev.txt` では `moto[dynamodb,server]` を指定している

この方式は起動・終了のオーバーヘッド(数秒)があるため、本数を絞り、認証・CORS・シリアライズなど「プロセスとHTTPを実際に越えないと気づけない」観点に絞ってテストする。DynamoDBのクエリロジック自体の細かい検証は `test_dynamodb_store.py` 側に任せる。

## テーブル・GSI設計を変更したとき

`infra/dynamodb.yaml` のテーブル定義(属性・キー・GSI)を変更した場合は、`tests/integration/conftest.py` の `_create_tables` も同じ内容に合わせて更新する。ここがズレると、結合テストが実際のAWS環境と異なる前提で「成功」してしまう。

## CI について

現状、`.github/workflows/ci.yml` の `backend` ジョブは `ruff check` / `ruff format --check` のみを実行しており、`pytest` は含まれていない。テストをCIで実行したい場合は別途ワークフローの追加が必要。
