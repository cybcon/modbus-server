import re

from src.app.lib.telemetry.prometheus_metrics import PrometheusMetrics


def test_record_and_generate_metrics_contains_expected_lines():
    m = PrometheusMetrics()

    # record some requests, reads, writes and errors
    m.record_request(3)
    m.record_request(3)
    m.record_request(5)

    m.record_register_read("h", 10, count=2)
    m.record_register_write("h", 10, count=1)

    m.record_error(2)

    m.set_connected_clients(4)

    out = m.generate_metrics()

    # basic expected metric labels/sections
    assert "# HELP modbus_requests_total" in out
    assert "# TYPE modbus_requests_total counter" in out

    # function code 3 should appear with count 2
    assert re.search(r'modbus_requests_total\{.*function_code="03".*\} 2', out)

    # function code 5 should appear with count 1
    assert re.search(r'modbus_requests_total\{.*function_code="05".*\} 1', out)

    # register reads/writes entries should be present
    assert "modbus_register_reads_total" in out
    assert "modbus_register_writes_total" in out

    # error should be present
    assert re.search(r'modbus_errors_total\{.*exception_code="02".*\} 1', out)

    # uptime metric present
    assert "modbus_server_uptime_seconds" in out


def test_reset_metrics_resets_counters():
    m = PrometheusMetrics()
    m.record_request(1)
    m.record_register_read("c", 1)
    m.record_error(3)

    # ensure metrics show up
    assert "modbus_requests_total" in m.generate_metrics()

    # reset
    m.reset_metrics()

    # after reset there should be no request entries
    out = m.generate_metrics()
    assert "modbus_requests_total" in out
    # but there should be no recorded function labels (only header lines)
    # check that function entries are absent
    assert not re.search(r"modbus_requests_total\{", out.split("# HELP modbus_requests_total")[1])
