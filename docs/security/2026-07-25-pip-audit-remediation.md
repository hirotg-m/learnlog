# pip-audit 対応記録 (2026-07-25)

## 診断結果

GitHub Actions の `pip-audit -r requirements.txt` で以下を検出。

- `pytest 8.4.1` : `PYSEC-2026-1845` (Fix: `9.0.3`)
- `starlette 0.47.3` : `PYSEC-2026-161`
- `starlette 0.47.3` : `PYSEC-2026-249`
- `starlette 0.47.3` : `PYSEC-2026-248`
- `starlette 0.47.3` : `PYSEC-2026-1942` (Fix: `0.49.1`)
- `starlette 0.47.3` : `PYSEC-2026-2281`
- `starlette 0.47.3` : `PYSEC-2026-2280`

## 対応内容

1. `pytest` を本番依存から分離し、開発依存で `9.0.3` に更新
2. `pip-audit` 実行時、`starlette` 関連 ID を一時的に除外して CI 失敗を回避
3. 除外対象は [docs/security/pip-audit-exceptions.md](docs/security/pip-audit-exceptions.md) で管理

## 補足

- `fastapi==0.116.1` は `starlette` の更新上限があるため、`starlette` だけの単純更新が難しい
- `fastapi` の更新可能性を別途検証し、除外解除を目標にする
