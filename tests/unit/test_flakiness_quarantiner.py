"""Unit tests for RepoMedic's FlakyTestQuarantiner service."""

from services.flakiness_quarantiner import FlakyTestQuarantiner


def test_quarantines_socket_bind_error():
    quarantiner = FlakyTestQuarantiner()
    test_id = "tests/test_server.py::test_bind_port"
    quarantiner.record_test_run(
        test_id=test_id,
        passed=False,
        error_message="OSError: [Errno 98] Address already in use",
    )

    assert quarantiner.is_quarantined(test_id)
    report = quarantiner.generate_report(total_tests_executed=10)
    assert report.quarantined_count == 1
    assert report.quarantined_tests[0].category == "SOCKET_BINDING"
    assert "test_bind_port" in report.pytest_filter_args


def test_quarantines_network_timeout():
    quarantiner = FlakyTestQuarantiner()
    test_id = "tests/test_api.py::test_fetch_remote"
    quarantiner.record_test_run(
        test_id=test_id,
        passed=False,
        error_message="requests.exceptions.ReadTimeout: HTTPSConnectionPool: Read timed out",
    )

    assert quarantiner.is_quarantined(test_id)
    report = quarantiner.generate_report(total_tests_executed=20)
    assert report.quarantined_count == 1
    assert report.quarantined_tests[0].category == "NETWORK_TIMEOUT"


def test_quarantines_intermittent_flips():
    quarantiner = FlakyTestQuarantiner()
    test_id = "tests/test_worker.py::test_concurrency"

    # Outcome sequence: Pass -> Fail -> Pass (2 flips)
    quarantiner.record_test_run(test_id, passed=True)
    quarantiner.record_test_run(test_id, passed=False, error_message="Value mismatch 4 != 5")
    quarantiner.record_test_run(test_id, passed=True)

    assert quarantiner.is_quarantined(test_id)
    report = quarantiner.generate_report(total_tests_executed=5)
    assert report.quarantined_count == 1
    assert report.quarantined_tests[0].category == "INTERMITTENT_FLIP"
    assert report.quarantined_tests[0].flip_count >= 2


def test_deterministic_confidence_and_serialization():
    quarantiner = FlakyTestQuarantiner()
    quarantiner.record_test_run("tests/test_ok.py::test_1", passed=True)
    quarantiner.record_test_run("tests/test_ok.py::test_2", passed=True)
    quarantiner.record_test_run(
        "tests/test_bad.py::test_port",
        passed=False,
        error_message="port 8080 in use",
    )

    report = quarantiner.generate_report(total_tests_executed=10)
    assert report.quarantined_count == 1
    assert report.deterministic_tests_count == 9
    assert report.deterministic_suite_confidence == 0.9

    d = report.to_dict()
    assert d["quarantined_count"] == 1
    assert d["deterministic_suite_confidence"] == 0.9
    assert "not test_port" in d["pytest_filter_args"]
