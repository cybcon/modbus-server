# -*- coding: utf-8 -*-
"""
###############################################################################
# Modbus datastore wrapper with metrics tracking.
# This module wraps the pymodbus datastore to track read and write operations
# for Prometheus metrics.
#------------------------------------------------------------------------------
# Author: Michael Oberdorf
# Date: 2026-02-18
# Last modified by: Michael Oberdorf
# Last modified at: 2026-02-21
###############################################################################\n
"""

__author__ = "Michael Oberdorf <info@oberdorf-itc.de>"
__status__ = "production"
__date__ = "2026-02-21"
__version_info__ = ("1", "0", "2")
__version__ = ".".join(__version_info__)

__all__ = ["MetricsTrackingDataBlock"]

import logging

from pymodbus.datastore.store import BaseModbusDataBlock

from .prometheus_metrics import PrometheusMetrics

log = logging.getLogger(__name__)


class MetricsTrackingDataBlock(BaseModbusDataBlock):
    """
    Wrapper around a Modbus data block that tracks read/write operations.

    This class wraps an existing Modbus data block and intercepts calls to getValues and setValues.
    It uses a PrometheusMetrics instance to record the number of reads and writes for each register
    address. The register type (discrete input, coil, holding register, input register) is also
    tracked to allow for more detailed metrics.
    """

    def __init__(self, wrapped_block: BaseModbusDataBlock, metrics_collector: PrometheusMetrics, register_type: str):
        """
        Initialize the metrics tracking data block.

        :param wrapped_block: The original data block to wrap
        :type wrapped_block: BaseModbusDataBlock
        :param metrics_collector: PrometheusMetrics instance for recording metrics
        :type metrics_collector: PrometheusMetrics
        :param register_type: Type of register ('d' for discrete input, 'c' for coil, 'h' for holding register, 'i' for input register)
        :type register_type: str
        :return: None
        """
        self.wrapped_block = wrapped_block
        self.metrics_collector = metrics_collector
        self.register_type = register_type

        # Initialize parent with same values as wrapped block
        super().__init__()

    def validate(self, address: int, count: int = 1) -> bool:
        """
        Validate the request.

        This method can be used to track validation attempts if needed.

        :param address: Starting address
        :type address: int
        :param count: Number of values to validate (default: 1)
        :type count: int
        :return: Result of validation
        :rtype: bool
        """
        return self.wrapped_block.validate(address, count)

    def getValues(self, address: int, count: int = 1) -> list:
        """
        Get values and track the read operation.

        :param address: Starting address
        :type address: int
        :param count: Number of values to read (default: 1)
        :type count: int
        :return: List of values read from the data block
        :rtype: list
        :raises Exception: If the underlying data block raises an exception during the getValues call
        """
        # Track the read operation for each address
        if self.metrics_collector:
            # infer request function code from register type and record a single request
            if self.register_type == "c":
                self.metrics_collector.record_request(1)  # read coils
            elif self.register_type == "d":
                self.metrics_collector.record_request(2)  # read discrete inputs
            elif self.register_type == "h":
                self.metrics_collector.record_request(3)  # read holding registers
            elif self.register_type == "i":
                self.metrics_collector.record_request(4)  # read input registers
            for addr in range(address, address + count):
                self.metrics_collector.record_register_read(self.register_type, addr, count=1)

        return self.wrapped_block.getValues(address, count)

    def setValues(self, address: int, values: list) -> None:
        """
        Set values and track the write operation.

        :param address: Starting address
        :type address: int
        :param values: List of values to write
        :type values: list
        :return: None
        :raises Exception: If the underlying data block raises an exception during the setValues call
        """
        # Track the write operation for each address and infer request type
        if self.metrics_collector:
            count = len(values) if isinstance(values, list) else 1
            # infer and record a single request for the write
            if self.register_type == "c":
                # coils: single (5) vs multiple (15)
                self.metrics_collector.record_request(5 if count == 1 else 15)
            elif self.register_type == "h":
                # holding registers: single (6) vs multiple (16)
                self.metrics_collector.record_request(6 if count == 1 else 16)
            for i, addr in enumerate(range(address, address + count)):
                self.metrics_collector.record_register_write(self.register_type, addr, count=1)

        return self.wrapped_block.setValues(address, values)
