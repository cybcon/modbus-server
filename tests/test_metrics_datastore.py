from src.app.lib.telemetry.metrics_datastore import MetricsTrackingDataBlock
from src.app.lib.telemetry.prometheus_metrics import PrometheusMetrics


class DummyBlock:
    def __init__(self):
        self.store = {}

    def validate(self, address, count=1):
        return True

    def getValues(self, address, count=1):
        return [address + i for i in range(count)]

    def setValues(self, address, values):
        if isinstance(values, list):
            for i, v in enumerate(values):
                self.store[address + i] = v
        else:
            self.store[address] = values


def test_metrics_tracking_datablock_records_reads_and_writes():
    prom = PrometheusMetrics()
    dummy = DummyBlock()
    # test holding registers ('h') mapping to read function code 3
    wrapped = MetricsTrackingDataBlock(dummy, prom, register_type="h")

    vals = wrapped.getValues(5, 3)
    assert vals == [5, 6, 7]

    # check that a read request for function code 3 was recorded
    assert prom._requests_by_function[3] == 1

    # each address should have been recorded as read once
    assert prom._register_reads["h"][5] == 1
    assert prom._register_reads["h"][6] == 1
    assert prom._register_reads["h"][7] == 1

    # single write -> function code 6 for holding registers
    wrapped.setValues(8, [42])
    assert prom._requests_by_function[6] == 1
    assert prom._register_writes["h"][8] == 1

    # multiple write -> function code 16
    wrapped.setValues(10, [1, 2, 3])
    assert prom._requests_by_function[16] == 1
    assert prom._register_writes["h"][10] == 1
    assert prom._register_writes["h"][11] == 1
    assert prom._register_writes["h"][12] == 1
