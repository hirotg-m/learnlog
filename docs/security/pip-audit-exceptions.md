# pip-audit 例外管理

## 一時除外している脆弱性 ID

- `PYSEC-2026-161`
- `PYSEC-2026-249`
- `PYSEC-2026-248`
- `PYSEC-2026-1942`
- `PYSEC-2026-2281`
- `PYSEC-2026-2280`

## 除外理由

現行の `fastapi==0.116.1` では `starlette` の更新制約があり、`pip-audit` が提示する修正バージョンへ直接更新できないため。

## 解除条件

- `fastapi` 更新により、`starlette` の安全なバージョンへ更新可能になること
- 解除時に `security.yml` の `--ignore-vuln` 指定を削除すること
