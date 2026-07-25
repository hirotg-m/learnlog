# Webサーバーのビルド・起動方法

`web/`(React + TypeScript + Vite)のローカル開発・ビルド手順。本番は S3 静的ホスティング + CloudFront(`CLAUDE.md` 参照)。

## 前提

- Node.js 24 / npm
- バックエンド(`api/`)を先に起動しておく(`docs/api/api-run.md` 参照)。既定では `http://localhost:8000` を想定

## セットアップ

```bash
cd web
npm install
```

## 環境変数 (`web/.env`)

| 変数名 | 用途 | 既定値(`.env.example`) |
|---|---|---|
| `VITE_API_ENDPOINT` | APIサーバーのエンドポイント(`src/lib/apiClient.ts` が参照。未設定だと実行時エラー) | `http://localhost:8000/api/v1` |

`web/.env` は `.env.example` と同じ内容で既に用意されている。バックエンドを別ポート・別ホストで動かす場合はここを書き換える。

## 開発サーバーの起動

```bash
cd web
npm run dev
```

`http://localhost:5173` で起動する(Viteの既定ポート)。ファイル変更はHMRで即座に反映される。

> APIサーバー側のCORS許可オリジン(`FRONTEND_ORIGIN`、既定 `http://localhost:5173`)と、この開発サーバーのオリジンを一致させること。ポートを変える場合(`npm run dev -- --port <PORT>`)は `api/.env` の `FRONTEND_ORIGIN` も合わせて変更する(`docs/api/api-run.md` 参照)。

### EC2上などリモート環境で、ブラウザ(手元のPC)からアクセスしたい場合

以下の3点をすべて満たす必要がある。片方だけだと画面自体は表示されても、ログイン(PIN入力)時に `Failed to fetch` になる。

1. **開発サーバーを全インターフェースにバインドする**

   `npm run dev` は既定でループバックアドレス(`localhost`)にのみバインドするため、EC2のパブリックIP等、ローカルホスト以外からは接続できない。`--host` を付ける。

   ```bash
   npm run dev -- --host
   ```

2. **`VITE_API_ENDPOINT` をEC2のパブリックIP/ドメインに向ける**

   `web/.env` の `VITE_API_ENDPOINT=http://localhost:8000/api/v1` のままだと、ビルドされたJSに `localhost` が埋め込まれる。この `localhost` はブラウザを実行している手元のPC自身を指すため、EC2上のAPIサーバーには到達できない(`Failed to fetch` の典型原因)。EC2のパブリックIP/ドメインに書き換える。

   ```
   VITE_API_ENDPOINT=http://<EC2のパブリックIP>:8000/api/v1
   ```

   Viteは起動時に環境変数を読み込むため、変更後は開発サーバーを再起動する。

3. **APIサーバー側も外部からの接続を受け付け、CORSを許可する**

   `docs/api/api-run.md` の起動コマンドはデフォルトで `127.0.0.1` にのみバインドするため、`--host 0.0.0.0` を付けて起動する。また、ブラウザからアクセスするオリジン(`http://<EC2のパブリックIP>:5173`)を `api/.env` の `FRONTEND_ORIGIN` に設定してCORSを許可する。

   ```bash
   cd api
   ./.venv/bin/uvicorn app.main:app --reload --env-file .env --host 0.0.0.0
   ```

   ```
   # api/.env
   FRONTEND_ORIGIN=http://<EC2のパブリックIP>:5173
   ```

それでも繋がらない場合は、EC2のセキュリティグループでポート `5173`(APIサーバーは `8000`、ビルド結果を確認する場合は `4173`)のインバウンドが許可されているか確認する。

## 型チェック

```bash
npm run typecheck
```

`tsc -b --pretty false` で型チェックのみ行う(ビルド成果物は出力しない)。

## ビルド

```bash
npm run build
```

`tsc -b`(型チェック)→ `vite build` の順に実行され、`web/dist/` に静的ファイル一式が出力される。型エラーがあるとビルドは失敗する。本番では、この `dist/` の中身をS3バケットにアップロードし、CloudFrontで配信する。

## ビルド結果のプレビュー

ビルドした `dist/` の中身をローカルで確認したい場合。

```bash
npm run preview
```

`http://localhost:4173` で `dist/` の内容を配信する(開発サーバーとは別物。HMRなし、本番ビルドそのものの動作確認用)。

## 関連ドキュメント

- APIサーバーの起動方法: `docs/api/api-run.md`
- APIの仕様: `docs/api/api-spec.md`
