# npm audit 対応記録 (2026-07-25)

## 診断結果

GitHub Actions の npm audit --audit-level=high で以下を検出。

- esbuild <=0.24.2 (GHSA-67mh-4wv8-2f99)
- vite <=6.4.2 が脆弱な esbuild に依存
- 2 vulnerabilities (1 moderate, 1 high)

## 対応内容

1. web/package.json の開発依存を更新
   - vite: ^5.4.10 -> ^8.1.5
   - @vitejs/plugin-react: ^4.3.2 -> ^6.0.4
2. web/package-lock.json を再生成
3. ローカル検証を実施
   - npm audit --audit-level=high
   - npm run typecheck
   - npm test -- --passWithNoTests

## 検証結果

- npm audit: found 0 vulnerabilities
- typecheck: 成功
- test: 成功 (No test files found, code 0)
