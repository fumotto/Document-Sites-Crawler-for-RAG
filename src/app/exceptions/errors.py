"""
ドメイン例外の定義。

CrawlResult（05_データ構造設計.md）との対応関係は本モジュール末尾の
CRAWL_EXCEPTION_TO_RESULT を参照。CrawlerService はここで定義された例外を
捕捉し、対応する CrawlResult へマッピングして manifest 更新・ログ出力を行う。
"""
from __future__ import annotations


class AppError(Exception):
    """本アプリケーションの基底例外。"""


class ConfigError(AppError):
    """設定の読み込み・検証エラー（07_CLI仕様.md 5節）。"""


class LockAcquisitionError(AppError):
    """サイト単位のロック取得に失敗した場合の例外（06_処理シーケンス.md 9節）。"""


class BuilderError(AppError):
    """ビルド処理中に回復不能な状態が発生した場合の例外
    （例: metadata に対応する pages/{page_hash}.md が見つからない）。
    06_処理シーケンス.md 5節に基づき、サイレントスキップせず処理を中断する。
    """


# --- クロール関連例外（CrawlResult と 1:1 対応する） -----------------------

class CrawlError(AppError):
    """クロール関連例外の基底クラス。"""


class NotFoundError(CrawlError):
    """HTTP 404。CrawlResult.NOT_FOUND に対応する。"""


class RobotsDeniedError(CrawlError):
    """robots.txt により取得が禁止されている。CrawlResult.ROBOTS_DENIED に対応する。"""


class NetworkError(CrawlError):
    """接続エラー・DNSエラー等。CrawlResult.NETWORK_ERROR に対応する。"""


class CrawlTimeoutError(CrawlError):
    """タイムアウト。CrawlResult.TIMEOUT に対応する。"""


class ServerError(CrawlError):
    """5xx系エラー。CrawlResult.SERVER_ERROR に対応する。"""


class TooManyRequestsError(CrawlError):
    """HTTP 429。CrawlResult.TOO_MANY_REQUESTS に対応する。"""


# CrawlResult（Enum）は models/crawl_result.py に定義する。
# ここでは循環importを避けるため、文字列値でマッピングを表現する。
CRAWL_EXCEPTION_TO_RESULT_VALUE = {
    NotFoundError: "NOT_FOUND",
    RobotsDeniedError: "ROBOTS_DENIED",
    NetworkError: "NETWORK_ERROR",
    CrawlTimeoutError: "TIMEOUT",
    ServerError: "SERVER_ERROR",
    TooManyRequestsError: "TOO_MANY_REQUESTS",
}
