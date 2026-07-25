# ブランチ戦略

## ブランチ構成

| ブランチ | 環境 | 説明 |
|---|---|---|
| `main` | prod | 本番環境。直接コミット禁止 |
| `develop` | dev | 開発統合ブランチ。直接コミット禁止 |
| `feature/*` | — | 機能開発 |
| `fix/*` | — | バグ修正 |

## フロー

```
feature/* , fix/*
  └─ push → CI (lint, typecheck)
       └─ PR → develop
            └─ CD → dev 環境 (S3, Lambda)
                 └─ PR → main
                      └─ CD → prod 環境 (S3, Lambda)
```

## 運用ルール

- `feature/*`, `fix/*` から直接 `main` へのマージは禁止
- PR はレビュー必須
- ブランチ名の例: `feature/add-study-log`, `fix/login-error`
