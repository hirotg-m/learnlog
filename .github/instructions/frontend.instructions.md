---
applyTo: "web/**"
---

# フロントエンド (React) ルール

## 技術スタック
- Node.js 24 / TypeScript
- React (関数コンポーネント + Hooks)

## 静的解析
- TypeScript の strict モードを有効にする
- `any` 型は使用しない

## デプロイ
- S3 に静的ファイルとして配置する
- CloudFront 経由で HTTPS で公開する
- APIエンドポイントは環境変数で管理しハードコードしない

## ルール
- ファイル名はコンポーネントは PascalCase、それ以外は camelCase
- Props には型定義を必ず付ける
- `any` 型は使用しない
- スタイルはコンポーネントと同じディレクトリに配置する
