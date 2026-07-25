# curl でAPIサーバーを試す方法

`api/`(FastAPI)を起動した状態で、`curl` から一連のエンドポイントを試す手順。APIサーバーの起動方法は `docs/api/api-run.md`、仕様の詳細は `docs/api/api-spec.md` を参照。

## 前提

- APIサーバーが `http://localhost:8000` で起動していること(`docs/api/api-run.md` の「1. メモリストア」が最も手軽)
- 認証はCookie(`session_token`)で行うため、`curl` は `-c`(Cookie保存)/`-b`(Cookie送信)でCookie jarを使う
- レスポンスのJSONから `id` 等を取り出すのに [`jq`](https://jqlang.org/) を使う(なければ手動でレスポンスの `id` を読み取って以降のコマンドに埋め込む)
- `-D /dev/stderr` を付けて、ステータス行を含むレスポンスヘッダーを標準エラー出力に表示する。ボディ(標準出力)には影響しないため、`| jq .` でのボディ整形や `$(...)` での変数への取り込みと同時に使える

`.env` に `COOKIE_SECURE=false` を設定しておくこと。デフォルト(`true`)のままだと `session_token` Cookieに `Secure` 属性が付き、`http://`(TLSなし)の `curl`/ブラウザではCookieが送り返されず、ログイン後のリクエストが軒並み `401` になる(`api/tests/unit/conftest.py` のテスト設定と同様)。

```bash
BASE=http://localhost:8000/api/v1
JAR=/tmp/learnlog-cookies.txt
rm -f "$JAR"
```

## 1. 認証

### ログイン(PIN)

PINは `api/.env` の `LEARNLOG_PIN`(既定 `12345678`)。

```bash
curl -s -D /dev/stderr -X POST "$BASE/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"pin": "12345678"}' \
  -c "$JAR"
```

```
HTTP/1.1 200 OK
content-type: application/json

{"session":{"expiresAt":"2026-07-25T08:19:38Z"}}
```

以降のリクエストは `-b "$JAR"` を付けてCookieを送る。PINを既定の8桁の数字以外の形式で送ると `422`、間違ったPINを一定回数送るとロックされる(`docs/api/api-spec.md` の認証仕様を参照)。

### セッション確認

```bash
curl -s -D /dev/stderr "$BASE/auth/session" -b "$JAR"
```

未ログイン(Cookieなし/期限切れ)だと `401` が返る。

```bash
curl -s -o /dev/null -w "%{http_code}\n" "$BASE/auth/session"
```

### ログアウト

```bash
curl -s -o /dev/null -w "%{http_code}\n" -X POST "$BASE/auth/logout" -b "$JAR" -c "$JAR"
```

## 2. 資格 (qualifications)

`color` は任意のカラーコードではなく、以下のパレット名のいずれか(`api/app/services/qualification_service.py` の `COLOR_PALETTE`)。

`red` / `orange` / `yellow` / `green` / `teal` / `blue` / `indigo` / `pink` / `brown` / `gray`

### 作成

```bash
QUAL=$(curl -s -D /dev/stderr -X POST "$BASE/qualifications" \
  -H "Content-Type: application/json" \
  -b "$JAR" \
  -d '{"name":"応用情報技術者","abbreviation":"AP","color":"blue","status":"open"}')
echo "$QUAL" | jq .

QID=$(echo "$QUAL" | jq -r .id)
```

### 一覧・詳細取得

```bash
curl -s -D /dev/stderr "$BASE/qualifications" -b "$JAR" | jq .

# includeStats=true で学習時間の合計などの集計も返す
curl -s -D /dev/stderr "$BASE/qualifications/$QID?includeStats=true" -b "$JAR" | jq .
```

### 更新・削除

```bash
curl -s -D /dev/stderr -X PATCH "$BASE/qualifications/$QID" \
  -H "Content-Type: application/json" \
  -b "$JAR" \
  -d '{"status":"close"}' | jq .

curl -s -o /dev/null -w "%{http_code}\n" -X DELETE "$BASE/qualifications/$QID" -b "$JAR"
```

資格を削除すると、紐づく学習記録・マイルストーンも合わせて削除される。

## 3. 学習記録 (study-logs)

`hours` は0.25刻み(15分単位)でなければならず、それ以外(例: `1.1`)は `422` になる。

```bash
LOG=$(curl -s -D /dev/stderr -X POST "$BASE/study-logs" \
  -H "Content-Type: application/json" \
  -b "$JAR" \
  -d "{\"qualificationId\":\"$QID\",\"date\":\"2026-07-24\",\"hours\":1.5,\"content\":\"過去問演習\",\"memo\":\"午前問題\"}")
echo "$LOG" | jq .

LID=$(echo "$LOG" | jq -r .id)
```

```bash
# 一覧(資格・期間で絞り込み可能)
curl -s -D /dev/stderr "$BASE/study-logs?qualificationId=$QID&dateFrom=2026-07-01&dateTo=2026-07-31" -b "$JAR" | jq .

# 詳細
curl -s -D /dev/stderr "$BASE/study-logs/$LID" -b "$JAR" | jq .

# 更新
curl -s -D /dev/stderr -X PATCH "$BASE/study-logs/$LID" \
  -H "Content-Type: application/json" \
  -b "$JAR" \
  -d '{"hours":2.0}' | jq .

# 削除
curl -s -o /dev/null -w "%{http_code}\n" -X DELETE "$BASE/study-logs/$LID" -b "$JAR"
```

## 4. マイルストーン (milestones)

```bash
MS=$(curl -s -D /dev/stderr -X POST "$BASE/milestones" \
  -H "Content-Type: application/json" \
  -b "$JAR" \
  -d "{\"qualificationId\":\"$QID\",\"title\":\"午前問題 過去問道場\",\"plannedDate\":\"2026-08-31\"}")
echo "$MS" | jq .

MID=$(echo "$MS" | jq -r .id)
```

```bash
# 一覧(status=open / close で絞り込み可能)
curl -s -D /dev/stderr "$BASE/milestones?qualificationId=$QID" -b "$JAR" | jq .

# 完了にする (completedDate を指定しなければ当日の日付が自動設定される)
curl -s -D /dev/stderr -X PATCH "$BASE/milestones/$MID" \
  -H "Content-Type: application/json" \
  -b "$JAR" \
  -d '{"status":"close"}' | jq .

# 削除
curl -s -o /dev/null -w "%{http_code}\n" -X DELETE "$BASE/milestones/$MID" -b "$JAR"
```

## 5. カレンダー (calendar)

学習記録を登録した状態で確認する(上の「3. 学習記録」で作成したものが残っていればOK)。

```bash
# 月間集計(資格ごとの日別合計時間)
curl -s -D /dev/stderr "$BASE/calendar/month?year=2026&month=7" -b "$JAR" | jq .

# 日別の学習記録一覧
curl -s -D /dev/stderr "$BASE/calendar/day?date=2026-07-24" -b "$JAR" | jq .
```

## 6. エラーレスポンスの確認

```bash
# 未ログイン -> 401
curl -s -o /dev/null -w "%{http_code}\n" "$BASE/qualifications"

# 存在しないID -> 404
curl -s -o /dev/null -w "%{http_code}\n" "$BASE/qualifications/q_notfound" -b "$JAR"

# バリデーションエラー -> 422 (colorがパレット外)
curl -s -D /dev/stderr -X POST "$BASE/qualifications" \
  -H "Content-Type: application/json" \
  -b "$JAR" \
  -d '{"name":"test","color":"#ff0000","status":"open"}' | jq .

# バリデーションエラー -> 422 (hoursが0.25刻みでない)
curl -s -D /dev/stderr -X POST "$BASE/study-logs" \
  -H "Content-Type: application/json" \
  -b "$JAR" \
  -d "{\"qualificationId\":\"$QID\",\"date\":\"2026-07-24\",\"hours\":1.1,\"content\":\"test\"}" | jq .
```

## 関連ドキュメント

- APIサーバーの起動方法: `docs/api/api-run.md`
- APIの仕様: `docs/api/api-spec.md`
- テストの実行方法: `docs/api/api-testing.md`
