---
name: Pull Request Review

description: |
  コードレビュー、Pull Requestレビュー、
  レビューコメント作成、
  品質評価を行う場合に適用する。

alwaysApply: false
---

# Pull Request Review

レビューでは次の観点を確認する。

## Correctness

- バグがないか
- 境界値
- Null安全
- 非同期処理

## Readability

- 名前は適切か
- 関数は長すぎないか

## Maintainability

- 重複コードはないか
- 将来変更しやすいか
- 責務は単一か
- 可能な限り冪等か

## Security

- 秘密情報
- SQL Injection
- XSS
- 権限

## Performance

- 不要な再レンダリング
- 不要なDBアクセス
- N+1問題

## Review Style

レビューコメントは

- 問題点
- 理由
- 改善案

をセットで説明する。

重大度を

- Critical
- High
- Medium
- Low
- Suggestion

で分類する。
