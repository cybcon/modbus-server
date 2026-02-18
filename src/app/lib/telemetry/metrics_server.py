# -*- coding: utf-8 -*-
"""
###############################################################################
# HTTP server for Prometheus metrics endpoint.
# This module provides a simple HTTP server that exposes the /metrics endpoint
# for Prometheus/OpenTelemetry scraping.
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

__all__ = ["MetricsRequestHandler", "MetricsServer"]

import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Optional

from prometheus_metrics import PrometheusMetrics

log = logging.getLogger(__name__)


class MetricsRequestHandler(BaseHTTPRequestHandler):
    """
    HTTP request handler for the /metrics endpoint.
    """

    # Class variable to hold the metrics collector instance
    metrics_collector = None
    # Class variable for the metrics path (can be customized if needed)
    metrics_path = "/metrics"

    def log_message(self, format: str, *args: tuple):
        """
        Override to use the standard logging framework.

        :param format: The format string for the log message
        :type format: str
        :param args: Arguments to be formatted into the log message
        :type args: tuple
        :return: None
        """
        log.debug(f"{self.address_string()} - {format % args}")

    def do_GET(self):
        """
        Handle GET requests.

        Routes requests to the appropriate handler based on the path.
        """
        if self.path == "/metrics":
            self._handle_metrics()
        elif self.path == "/health" or self.path == "/":
            self._handle_health()
        else:
            self.send_error(404, "Not Found")

    def _handle_metrics(self):
        """
        Handle requests to the /metrics endpoint.

        This method generates the metrics output and sends it back to the client.
        """
        if self.metrics_collector is None:
            self.send_error(500, "Metrics collector not initialized")
            return

        try:
            metrics_output = self.metrics_collector.generate_metrics()

            self.send_response(200)
            self.send_header("Content-Type", f"text/plain; version={__version__}; charset=utf-8")
            self.send_header("Content-Length", str(len(metrics_output)))
            self.end_headers()
            self.wfile.write(metrics_output.encode("utf-8"))

        except Exception as e:
            log.error(f"Error generating metrics: {e}", exc_info=True)
            self.send_error(500, f"Internal Server Error: {str(e)}")

    def _handle_health(self):
        """
        Handle requests to the /health endpoint.

        This can be used for health checks by load balancers or monitoring systems.
        """
        response = "OK\n"
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response.encode("utf-8"))


class MetricsServer:
    """
    HTTP server for exposing Prometheus metrics.

    Runs in a separate thread to avoid blocking the Modbus server.
    """

    def __init__(
        self, metrics_collector: PrometheusMetrics, address: str = "0.0.0.0", port: int = 9090, path: str = "/metrics"
    ):
        """
        Initialize the metrics server.

        :param metrics_collector: Instance of PrometheusMetrics to generate metrics from
        :type metrics_collector: PrometheusMetrics
        :param address: Address to bind to (default: 0.0.0.0)
        :type address: str
        :param port: Port to listen on (default: 9090)
        :type port: int
        :param path: Path for the metrics endpoint (default: /metrics)
        :type path: str
        :return: None
        """
        self.metrics_collector = metrics_collector
        self.address = address
        self.port = port
        self.path = path
        self.server: Optional[HTTPServer] = None
        self.thread: Optional[threading.Thread] = None
        self._running = False

    def start(self):
        """
        Start the metrics server in a separate thread.

        :return: None
        :raises Exception: If the server fails to start
        """
        if self._running:
            log.warning("Metrics server is already running")
            return

        # Set the class variables so the handler can access the metrics collector and path
        MetricsRequestHandler.metrics_collector = self.metrics_collector
        MetricsRequestHandler.metrics_path = self.path

        try:
            # HTTPServer expects a handler *class*, not an instance.
            # Pass the class itself so the server can instantiate handlers
            # for each incoming request.
            self.server = HTTPServer((self.address, self.port), MetricsRequestHandler)
            self._running = True

            # Start server in a daemon thread
            self.thread = threading.Thread(target=self._serve, daemon=True)
            self.thread.start()

            log.info(f"Prometheus metrics server started on {self.address}:{self.port}")
            log.info(f"Metrics endpoint: http://{self.address}:{self.port}{self.path}")

        except Exception as e:
            log.error(f"Failed to start metrics server: {e}", exc_info=True)
            self._running = False
            raise

    def _serve(self):
        """
        Serve HTTP requests (runs in separate thread).

        :return: None
        :raises Exception: If the server encounters an error while serving
        """
        try:
            log.debug(f"Metrics server thread started, serving on {self.address}:{self.port}")
            self.server.serve_forever()
        except Exception as e:
            log.error(f"Metrics server error: {e}", exc_info=True)
        finally:
            self._running = False
            log.info("Metrics server thread stopped")

    def stop(self):
        """
        Stop the metrics server.

        :return: None
        """
        if not self._running:
            log.debug("Metrics server is not running")
            return

        log.info("Stopping metrics server...")
        self._running = False

        if self.server:
            self.server.shutdown()
            self.server.server_close()

        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)

        log.info("Metrics server stopped")

    def is_running(self) -> bool:
        """
        Check if the metrics server is running.

        :return: True if running, False otherwise
        :rtype: bool
        """
        return self._running
