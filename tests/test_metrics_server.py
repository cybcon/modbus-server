import time
import urllib.request

from src.app.lib.telemetry.metrics_server import MetricsServer
from src.app.lib.telemetry.prometheus_metrics import PrometheusMetrics


def test_metrics_server_start_stop_and_endpoints():
    prom = PrometheusMetrics()
    prom.record_request(3)

    server = MetricsServer(prom, address="127.0.0.1", port=0)
    server.start()

    # wait briefly for server to start
    time.sleep(0.05)

    assert server.is_running() is True
    assert server.server is not None

    host, port = server.server.server_address

    # request metrics endpoint
    with urllib.request.urlopen(f"http://{host}:{port}/metrics", timeout=2) as resp:
        body = resp.read().decode("utf-8")
        assert resp.getcode() == 200
        # metrics output should include the modbus_requests_total header
        assert "modbus_requests_total" in body

    # request health endpoint
    with urllib.request.urlopen(f"http://{host}:{port}/health", timeout=2) as resp:
        health = resp.read().decode("utf-8")
        assert resp.getcode() == 200
        assert health == "OK\n"

    server.stop()
    # allow a moment for shutdown to complete
    time.sleep(0.05)
    assert server.is_running() is False
