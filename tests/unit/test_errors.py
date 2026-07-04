from src.app.exceptions.errors import (
    CRAWL_EXCEPTION_TO_RESULT_VALUE,
    CrawlTimeoutError,
    NetworkError,
    NotFoundError,
    RobotsDeniedError,
    ServerError,
    TooManyRequestsError,
)


def test_all_six_crawl_exceptions_mapped_to_expected_crawl_results():
    # TestID: ERR-001
    expected = {
        NotFoundError: "NOT_FOUND",
        RobotsDeniedError: "ROBOTS_DENIED",
        NetworkError: "NETWORK_ERROR",
        CrawlTimeoutError: "TIMEOUT",
        ServerError: "SERVER_ERROR",
        TooManyRequestsError: "TOO_MANY_REQUESTS",
    }

    assert CRAWL_EXCEPTION_TO_RESULT_VALUE == expected


def test_robots_denied_error_maps_to_robots_denied_value():
    # TestID: ERR-002
    assert CRAWL_EXCEPTION_TO_RESULT_VALUE[RobotsDeniedError] == "ROBOTS_DENIED"
