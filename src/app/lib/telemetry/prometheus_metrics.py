# -*- coding: utf-8 -*-
"""
###############################################################################
# Prometheus metrics collector for Modbus Server.
# This module provides a Prometheus-compatible metrics endpoint that exposes
# real-time counters and gauges for Modbus activity.
#------------------------------------------------------------------------------
# Author: Michael Oberdorf
# Date: 2026-02-18
# Last modified by: Michael Oberdorf
# Last modified at: 2026-02-18
###############################################################################\n
"""

__author__ = "Michael Oberdorf <info@oberdorf-itc.de>"
__status__ = "production"
__date__ = "2026-02-18"
__version_info__ = ("1", "0", "0")
__version__ = ".".join(__version_info__)

__all__ = ["PrometheusMetrics"]

import threading
import time
from collections import defaultdict
from typing import Dict, Optional


class PrometheusMetrics:
    """
    Collects and exposes Prometheus metrics for Modbus server activity.

    Metrics collected:
    - modbus_requests_total: Counter of requests by function code
    - modbus_register_reads_total: Counter of read operations per register
    - modbus_register_writes_total: Counter of write operations per register
    - modbus_errors_total: Counter of errors by exception code
    - modbus_connected_clients: Gauge of currently connected clients
    - modbus_server_uptime_seconds: Counter of server uptime
    """

    # Modbus function code names for better readability
    FUNCTION_CODE_NAMES = {
        1: "read_coils",
        2: "read_discrete_inputs",
        3: "read_holding_registers",
        4: "read_input_registers",
        5: "write_single_coil",
        6: "write_single_register",
        15: "write_multiple_coils",
        16: "write_multiple_registers",
    }

    # Modbus exception code names
    EXCEPTION_CODE_NAMES = {
        1: "illegal_function",
        2: "illegal_data_address",
        3: "illegal_data_value",
        4: "slave_device_failure",
        5: "acknowledge",
        6: "slave_device_busy",
        8: "memory_parity_error",
        10: "gateway_path_unavailable",
        11: "gateway_target_device_failed_to_respond",
    }

    # Register type names
    REGISTER_TYPE_NAMES = {
        "d": "discrete_input",
        "c": "coil",
        "h": "holding",
        "i": "input",
    }

    def __init__(self):
        """
        Initialize the metrics collector.

        :return: None
        """
        self._lock = threading.Lock()
        self._start_time = time.time()

        # Counters
        self._requests_by_function = defaultdict(int)
        self._register_reads = defaultdict(lambda: defaultdict(int))  # {type: {address: count}}
        self._register_writes = defaultdict(lambda: defaultdict(int))  # {type: {address: count}}
        self._errors_by_exception = defaultdict(int)

        # Gauges
        self._connected_clients = 0

    def record_request(self, function_code: int):
        """
        Record a Modbus request.

        :param function_code: The Modbus function code of the request
        :type function_code: int
        :return: None
        """
        with self._lock:
            self._requests_by_function[function_code] += 1

    def record_register_read(self, register_type: str, address: int, count: int = 1):
        """
        Record register read operations.

        :param register_type: Type of register ('d', 'c', 'h', 'i')
        :type register_type: str
        :param address: Register address
        :type address: int
        :param count: Number of registers read (default: 1)
        :type count: int
        :return: None
        """
        with self._lock:
            self._register_reads[register_type][address] += count

    def record_register_write(self, register_type: str, address: int, count: int = 1):
        """
        Record register write operations.

        :param register_type: Type of register ('c' for coils, 'h' for holding)
        :type register_type: str
        :param address: Register address
        :type address: int
        :param count: Number of registers written (default: 1)
        :type count: int
        :return: None
        """
        with self._lock:
            self._register_writes[register_type][address] += count

    def record_error(self, exception_code: int):
        """
        Record a Modbus exception.

        :param exception_code: The Modbus exception code
        :type exception_code: int
        :return: None
        """
        with self._lock:
            self._errors_by_exception[exception_code] += 1

    def set_connected_clients(self, count: int):
        """
        Set the current number of connected clients.

        :param count: Number of currently connected clients
        :type count: int
        :return: None
        """
        with self._lock:
            self._connected_clients = count

    def increment_connected_clients(self):
        """
        Increment the connected clients counter.
        """
        with self._lock:
            self._connected_clients += 1

    def decrement_connected_clients(self):
        """
        Decrement the connected clients counter.
        """
        with self._lock:
            self._connected_clients = max(0, self._connected_clients - 1)

    def get_uptime(self) -> float:
        """
        Get the server uptime in seconds.

        :return: Server uptime in seconds
        :rtype: float
        """
        return time.time() - self._start_time

    def _format_metric_line(
        self, name: str, value, labels: Optional[Dict[str, str]] = None, metric_type: Optional[str] = None
    ) -> str:
        """
        Format a single metric line in Prometheus format.

        :param name: Metric name
        :type name: str
        :param value: Metric value
        :type value: int, float, or str
        :param labels: Optional dict of label key-value pairs
        :type labels: dict, optional
        :param metric_type: Optional metric type for HELP/TYPE comments
        :type metric_type: str, optional
        :return: Formatted metric line
        :rtype: str
        """
        if labels:
            label_str = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
            return f"{name}{{{label_str}}} {value}"
        return f"{name} {value}"

    def generate_metrics(self) -> str:
        """
        Generate Prometheus metrics in text exposition format.

        :return: Metrics in Prometheus text format
        :rtype: str
        """
        lines = []

        with self._lock:
            # modbus_requests_total
            lines.append("# HELP modbus_requests_total Total number of Modbus requests received, by function code")
            lines.append("# TYPE modbus_requests_total counter")
            for func_code, count in sorted(self._requests_by_function.items()):
                func_name = self.FUNCTION_CODE_NAMES.get(func_code, f"function_{func_code}")
                labels = {"function_code": str(func_code).zfill(2), "function_name": func_name}
                lines.append(self._format_metric_line("modbus_requests_total", count, labels))

            # modbus_register_reads_total
            lines.append("")
            lines.append("# HELP modbus_register_reads_total Total number of read operations per register")
            lines.append("# TYPE modbus_register_reads_total counter")
            for reg_type, addresses in sorted(self._register_reads.items()):
                type_name = self.REGISTER_TYPE_NAMES.get(reg_type, reg_type)
                for address, count in sorted(addresses.items()):
                    labels = {"type": type_name, "address": str(address)}
                    lines.append(self._format_metric_line("modbus_register_reads_total", count, labels))

            # modbus_register_writes_total
            lines.append("")
            lines.append("# HELP modbus_register_writes_total Total number of write operations per register")
            lines.append("# TYPE modbus_register_writes_total counter")
            for reg_type, addresses in sorted(self._register_writes.items()):
                type_name = self.REGISTER_TYPE_NAMES.get(reg_type, reg_type)
                for address, count in sorted(addresses.items()):
                    labels = {"type": type_name, "address": str(address)}
                    lines.append(self._format_metric_line("modbus_register_writes_total", count, labels))

            # modbus_errors_total
            lines.append("")
            lines.append("# HELP modbus_errors_total Total number of Modbus errors returned, by exception code")
            lines.append("# TYPE modbus_errors_total counter")
            for exc_code, count in sorted(self._errors_by_exception.items()):
                exc_name = self.EXCEPTION_CODE_NAMES.get(exc_code, f"exception_{exc_code}")
                labels = {"exception_code": str(exc_code).zfill(2), "exception_name": exc_name}
                lines.append(self._format_metric_line("modbus_errors_total", count, labels))

            # modbus_connected_clients
            lines.append("")
            lines.append("# HELP modbus_connected_clients Current number of active Modbus TCP client connections")
            lines.append("# TYPE modbus_connected_clients gauge")
            lines.append(self._format_metric_line("modbus_connected_clients", self._connected_clients))

            # modbus_server_uptime_seconds
            lines.append("")
            lines.append("# HELP modbus_server_uptime_seconds Total uptime of the mock server in seconds")
            lines.append("# TYPE modbus_server_uptime_seconds counter")
            uptime = self.get_uptime()
            lines.append(self._format_metric_line("modbus_server_uptime_seconds", f"{uptime:.2f}"))

        return "\n".join(lines) + "\n"

    def reset_metrics(self):
        """
        Reset all metrics (for testing purposes).
        """
        with self._lock:
            self._requests_by_function.clear()
            self._register_reads.clear()
            self._register_writes.clear()
            self._errors_by_exception.clear()
            self._connected_clients = 0
            self._start_time = time.time()
