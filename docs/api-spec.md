# バックエンド API 仕様

## 1. 目的

スマートフォンからの素早い記録を前提に、資格ごとの学習記録、マイルストーン、カレンダー集計を管理する REST API を定義する。

## 2. 前提

- ベースパスは `/api/v1` とする
- 認証は 8 桁 PIN による単一ユーザー運用とする
- ログイン後のセッション有効期限は 12 時間とする
- 認証情報は HTTP only のセッションクッキーで管理する
- データストアは DynamoDB とする(テーブル設計は 10 章を参照)
- すべての日時は ISO 8601 形式の UTC を返す
- フロントエンド(CloudFront)とバックエンド(API Gateway)は別オリジンのため、CORS では `Access-Control-Allow-Origin` にフロントエンドのオリジンを明示し、`Access-Control-Allow-Credentials: true` を設定する
- セッションクッキーには `Secure; HttpOnly; SameSite=None` を付与し、クロスオリジンでも送信されるようにする

## 3. 共通ルール

### 3.1 ステータスコード

| コード | 意味 |
|---|---|
| 200 | 成功 |
| 201 | 作成成功 |
| 204 | 削除成功、本文なし |
| 400 | 入力不正 |
| 401 | 未認証 |
| 403 | 認可不可 |
| 404 | 対象なし |
| 409 | 競合 |
| 422 | バリデーションエラー |
| 429 | レート制限(PIN ログイン試行のロック中を含む) |
| 500 | 想定外エラー |

### 3.2 エラーレスポンス

```json
{
  "error": {
    "code": "validation_error",
    "message": "hours must be in 0.25 increments",
    "details": []
  }
}
```

### 3.3 ページネーション

一覧系 API は必要に応じて以下のクエリをサポートする。

| パラメータ | 説明 |
|---|---|
| limit | 取得件数。未指定時の既定値は 20 |
| cursor | 次ページ取得用カーソル |

レスポンスには次ページがある場合のみ `nextCursor` を返す。

## 4. 認証 API

### 4.1 PIN ログイン

`POST /auth/login`

リクエスト:

```json
{
  "pin": "12345678"
}
```

レスポンス 200:

```json
{
  "session": {
    "expiresAt": "2026-07-24T15:00:00Z"
  }
}
```

仕様:

- PIN は 8 桁数字のみ
- 5 回連続失敗で 5 分間ロックする
- ロック中は 429 を返し、`Retry-After` ヘッダーでロック解除までの秒数を返す
- 失敗回数・ロック状態は DynamoDB に保持する(10.4 参照)。Lambda はリクエストごとに独立した実行環境になりうるため、メモリ内カウンタは使用しない

### 4.2 セッション確認

`GET /auth/session`

レスポンス 200:

```json
{
  "authenticated": true,
  "expiresAt": "2026-07-24T15:00:00Z"
}
```

未認証時は 401 を返す。

### 4.3 ログアウト

`POST /auth/logout`

レスポンス 204。

## 5. 資格 API

### 5.1 資格一覧取得

`GET /qualifications`

クエリ:

| パラメータ | 説明 |
|---|---|
| status | `active` または `closed` を絞り込み可能 |
| includeStats | `true` の場合は学習時間などの集計を含める |

レスポンス 200:

```json
{
  "items": [
    {
      "id": "q_001",
      "name": "AWS ソリューションアーキテクトプロフェッショナル",
      "abbreviation": "AWS SAP",
      "color": "blue",
      "status": "active",
      "totalHours": 32.5,
      "studyLogCount": 18,
      "lastStudiedAt": "2026-07-24T12:00:00Z",
      "overdueMilestoneCount": 1,
      "createdAt": "2026-07-01T10:00:00Z",
      "updatedAt": "2026-07-20T08:00:00Z"
    }
  ]
}
```

上記は `includeStats=true` の場合の例。`totalHours` / `studyLogCount` / `lastStudiedAt` / `overdueMilestoneCount` は `includeStats=true` のときのみ含め、指定なしの場合はこれらのフィールド自体を返さない。

### 5.2 資格作成

`POST /qualifications`

リクエスト:

```json
{
  "name": "GitHub Copilot",
  "abbreviation": "GH-300",
  "color": "green",
  "status": "active"
}
```

制約:

- `name` は必須
- `color` は 10 色のプリセットから選択する。資格間での重複は許可する(一意性は保証しない)
- `status` は `active` か `closed`
- `abbreviation` は任意

### 5.3 資格詳細取得

`GET /qualifications/{qualificationId}`

### 5.4 資格更新

`PATCH /qualifications/{qualificationId}`

更新可能項目は `name`, `abbreviation`, `color`, `status` とする。

### 5.5 資格削除

`DELETE /qualifications/{qualificationId}`

仕様:

- 学習記録、メモ、マイルストーンを含めて完全削除する
- 元に戻せないため、フロント側で確認ダイアログを出す前提とする

## 6. 学習記録 API

### 6.1 学習記録一覧取得

`GET /study-logs`

クエリ:

| パラメータ | 説明 |
|---|---|
| qualificationId | 資格で絞り込み |
| dateFrom | 開始日 |
| dateTo | 終了日 |
| sort | `date_desc` または `date_asc`。既定値は `date_desc` |

制約:

- 同一日付内に複数件ある場合、`date` が同じ項目同士は `createdAt`(`sort` と同じ向き)で並べ替える
- `qualificationId` を指定しない場合、`dateFrom`〜`dateTo` の範囲は 12 か月以内とする。超過時は 400 を返す

レスポンス 200:

```json
{
  "items": [
    {
      "id": "l_001",
      "qualificationId": "q_001",
      "date": "2026-07-24",
      "hours": 1.5,
      "content": "AWS の IAM ポリシーを復習",
      "memo": "条件キーを整理した",
      "createdAt": "2026-07-24T12:00:00Z",
      "updatedAt": "2026-07-24T12:30:00Z"
    }
  ]
}
```

### 6.2 学習記録作成

`POST /study-logs`

リクエスト:

```json
{
  "qualificationId": "q_001",
  "date": "2026-07-24",
  "hours": 1.5,
  "content": "AWS の IAM ポリシーを復習",
  "memo": "条件キーを整理した"
}
```

制約:

- `hours` は 0.25 刻みの正の数とする
- `content` は必須
- `memo` は任意
- 同日同資格の複数登録を許可する

### 6.3 学習記録詳細取得

`GET /study-logs/{studyLogId}`

### 6.4 学習記録更新

`PATCH /study-logs/{studyLogId}`

更新可能項目は `qualificationId`, `date`, `hours`, `content`, `memo` とする。

### 6.5 学習記録削除

`DELETE /study-logs/{studyLogId}`

## 7. マイルストーン API

マイルストーンは 1 つの資格に対して複数件登録できる。

### 7.1 マイルストーン一覧取得

`GET /milestones`

クエリ:

| パラメータ | 説明 |
|---|---|
| qualificationId | 資格で絞り込み |
| status | `achieved` / `unachieved` を想定 |

レスポンス 200:

```json
{
  "items": [
    {
      "id": "m_001",
      "qualificationId": "q_001",
      "title": "模擬試験 1 回目で 80 点以上",
      "dueDate": "2026-08-31",
      "isAchieved": false,
      "isOverdue": true,
      "createdAt": "2026-07-10T09:00:00Z",
      "updatedAt": "2026-07-20T09:00:00Z"
    }
  ]
}
```

### 7.2 マイルストーン作成

`POST /milestones`

リクエスト:

```json
{
  "qualificationId": "q_001",
  "title": "模擬試験 1 回目で 80 点以上",
  "dueDate": "2026-08-31",
  "isAchieved": false
}
```

### 7.3 マイルストーン更新

`PATCH /milestones/{milestoneId}`

更新可能項目は `qualificationId`, `title`, `dueDate`, `isAchieved` とする。

### 7.4 マイルストーン削除

`DELETE /milestones/{milestoneId}`

## 8. カレンダー API

### 8.1 月間カレンダー集計

`GET /calendar/month?year=2026&month=7`

レスポンス 200:

```json
{
  "year": 2026,
  "month": 7,
  "days": [
    {
      "date": "2026-07-24",
      "items": [
        {
          "qualificationId": "q_001",
          "qualificationName": "AWS ソリューションアーキテクトプロフェッショナル",
          "abbreviation": "AWS SAP",
          "color": "blue",
          "hours": 1.5
        }
      ]
    }
  ]
}
```

用途:

- 月表示カレンダーのセルに色ドットまたはバーを描画する
- 同日に複数資格がある場合は `items` を複数返す

### 8.2 日別詳細取得

`GET /calendar/day?date=2026-07-24`

`items` は `createdAt` の昇順(記録した順)で返す。

レスポンス 200:

```json
{
  "date": "2026-07-24",
  "items": [
    {
      "studyLogId": "l_001",
      "qualificationId": "q_001",
      "qualificationName": "AWS ソリューションアーキテクトプロフェッショナル",
      "abbreviation": "AWS SAP",
      "color": "blue",
      "hours": 1.5,
      "content": "AWS の IAM ポリシーを復習",
      "memo": "条件キーを整理した",
      "createdAt": "2026-07-24T12:00:00Z"
    }
  ]
}
```

## 9. ドメインモデル

### 9.1 Qualification

| 項目 | 型 | 必須 | 説明 |
|---|---|---|---|
| id | string | yes | 識別子 |
| name | string | yes | 資格名 |
| abbreviation | string | no | 略称 |
| color | string | yes | 10 色パレットの識別子。他の資格との重複可 |
| status | string | yes | `active` / `closed` |
| createdAt | string | yes | 作成日時 |
| updatedAt | string | yes | 更新日時 |

### 9.2 StudyLog

| 項目 | 型 | 必須 | 説明 |
|---|---|---|---|
| id | string | yes | 識別子 |
| qualificationId | string | yes | 紐づく資格 |
| date | string | yes | 記録日 |
| hours | number | yes | 勉強時間 |
| content | string | yes | やったこと |
| memo | string | no | メモ |
| createdAt | string | yes | 作成日時 |
| updatedAt | string | yes | 更新日時 |

### 9.3 Milestone

| 項目 | 型 | 必須 | 説明 |
|---|---|---|---|
| id | string | yes | 識別子 |
| qualificationId | string | yes | 紐づく資格。1 資格に対して複数のマイルストーンを持つ |
| title | string | yes | 目標名 |
| dueDate | string | no | 期限 |
| isAchieved | boolean | yes | 達成済みか |
| createdAt | string | yes | 作成日時 |
| updatedAt | string | yes | 更新日時 |

## 10. データストア設計 (DynamoDB)

エンティティごとにテーブルを分ける(infra/dynamodb.yaml 参照)。単一テーブル設計は行わない。

| テーブル | 用途 |
|---|---|
| `learnlog-qualifications` | 資格 |
| `learnlog-study-logs` | 学習記録 |
| `learnlog-milestones` | マイルストーン |
| `learnlog-login-attempts` | ログイン失敗カウンタ |

### 10.1 learnlog-qualifications

- プライマリキー: `id`(HASH)
- GSI なし。資格の件数は個人利用規模で少数のため、`status` によるフィルタは Scan + FilterExpression で許容する

### 10.2 learnlog-study-logs

- プライマリキー: `id`(HASH)
- GSI `ByQualification`: `qualificationId`(HASH) / `date`(RANGE) — 資格ごとの一覧・日付範囲検索(5.1 の `qualificationId` 指定時、9.x の集計)に使用
- GSI `ByMonth`: `month`(HASH、`yyyy-mm` 形式) / `date`(RANGE) — 資格をまたいだ日付検索に使用
  - `GET /calendar/month`: `month` で Query する
  - `GET /calendar/day`: `month` で Query し、アプリ側で `date` を絞り込む(1 か月分のみが対象のため許容する)
  - `qualificationId` 未指定の `GET /study-logs`: `dateFrom`〜`dateTo` にまたがる月ごとに `ByMonth` を Query し、アプリ側で日付範囲にフィルタする。範囲は 12 か月以内に制限する(6.1 参照)
- `month` は `date` から導出する属性(例: `date = "2026-07-24"` → `month = "2026-07"`)であり、DynamoDB が自動で追従するわけではない。学習記録の作成時・および `PATCH /study-logs/{id}` で `date` を更新する際は、書き込みのたびに `month` を必ず再計算して同時に書き込む。更新し忘れると `ByMonth` インデックス上でその記録が古い月に残り、カレンダー表示がずれる
- 同一の `date`(同日複数セッション)を持つ項目同士の順序は GSI 上では保証されない。一覧・カレンダー表示ではアプリ側で `createdAt` により並べ替えてから返す(6.1, 8.2 参照)

### 10.3 learnlog-milestones

- プライマリキー: `id`(HASH)
- GSI `ByQualification`: `qualificationId`(HASH) — 資格ごとのマイルストーン一覧に使用。件数が少ないため、期限順の並び替えはアプリ側で行う

### 10.4 learnlog-login-attempts

- プライマリキー: `id`(HASH)。`id = "singleton"` の 1 レコードのみを保持し、`failCount`、`lockedUntil` を保持する
- Lambda はステートレスなため、この値を DynamoDB 上で管理し、リクエストごとに読み書きする。ロック解除後は `failCount` を 0 にリセットする

### 10.5 集計値の扱い

`totalHours` / `studyLogCount` / `lastStudiedAt` / `overdueMilestoneCount`(5.1, 7.1)は、`learnlog-qualifications` に非正規化カウンタとして持たず、`learnlog-study-logs` / `learnlog-milestones` の `ByQualification` GSI への Query 結果からその都度計算する。個人利用規模のデータ量であれば、書き込みのたびにカウンタを更新する方式(競合対策が必要)より単純で安全なため。

## 11. 実装メモ

- 資格削除は関連レコードの一括削除を前提にする
- `status=closed` の資格は新規作成フォームの候補から除外するが、参照系 API では返す
- マイルストーンの期限超過判定は API 側で `isOverdue` を付与して返す
