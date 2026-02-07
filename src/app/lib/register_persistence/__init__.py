# -*- coding: utf-8 -*-
"""
###############################################################################
# Library to make register writes persistent across restarts of the modbus server.
# seeAlso: https://github.com/cybcon/modbus-server/issues/28
#------------------------------------------------------------------------------
# Author: Michael Oberdorf
# Date: 2026-02-07
# Last modified by: Michael Oberdorf
# Last modified at: 2026-02-07
###############################################################################\n
"""

__author__ = "Michael Oberdorf <info@oberdorf-itc.de>"
__status__ = "production"
__date__ = "2026-02-07"
__version_info__ = ("1", "0", "0")
__version__ = ".".join(__version_info__)

__all__ = ["RegisterPersistence"]

import json
import logging
import os
import threading
from typing import Optional

from pymodbus.datastore import (
    ModbusSequentialDataBlock,
    ModbusServerContext,
    ModbusSparseDataBlock,
)


class RegisterPersistence:
    """
    Handles saving and loading of register data to/from disk
    """

    def __init__(self, persistence_file: str, context: ModbusServerContext, save_interval: int = 30):
        """
        Initialize the persistence layer

        :param persistence_file: path to the JSON file for storing register data
        :type persistence_file: str
        :param context: the ModbusServerContext to monitor
        :type context: ModbusServerContext
        :param save_interval: how often to save data in seconds (default: 30)
        :type save_interval: int
        """
        self.logger = logging.getLogger(__name__)
        self.persistence_file = persistence_file
        self.context = context
        self.save_interval = save_interval
        self._stop_event = threading.Event()
        self._save_thread = None
        self._last_data = None
        if not os.path.exists(os.path.dirname(self.persistence_file)):
            self.logger.info(f"Persistence file directory does not exist: {os.path.dirname(self.persistence_file)}")
            os.makedirs(os.path.dirname(self.persistence_file), exist_ok=True)
            self.logger.info(f"Created directory for persistence file: {os.path.dirname(self.persistence_file)}")

    def load_registers(self) -> Optional[dict]:
        """
        Load register data from persistence file

        :return: Register data or None if file doesn't exist
        :rtype: Optional[dict]
        :raises: RuntimeError if file exists but cannot be read or parsed
        """
        if not os.path.isfile(self.persistence_file):
            self.logger.info(f"No persistence file found at {self.persistence_file}, using initial configuration")
            return None

        try:
            with open(self.persistence_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.logger.info(f"Successfully loaded register data from {self.persistence_file}")
            return data
        except Exception as e:
            self.logger.error(f"Failed to load persistence file: {e}")
            raise RuntimeError("Error loading persistence file") from e

    def save_registers(self) -> bool:
        """
        Save current register data to persistence file

        :return: True if successful, False otherwise
        :rtype: bool
        :raises: RuntimeError if saving fails but does not raise exceptions (errors are logged and False is returned)
        """
        try:
            # Get the slave context (we use single=True, so slaves is the context directly)
            slave_context = self.context[0]  # Unit ID 0 for single context

            # Extract current register values
            data = {
                "discrete_inputs": self._extract_register_values(slave_context, "d"),
                "coils": self._extract_register_values(slave_context, "c"),
                "holding_registers": self._extract_register_values(slave_context, "h"),
                "input_registers": self._extract_register_values(slave_context, "i"),
            }

            # Only save if data has changed
            if data == self._last_data:
                return True

            # Save to file with atomic write (write to temp file, then rename)
            temp_file = self.persistence_file + ".tmp"
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Atomic rename
            os.replace(temp_file, self.persistence_file)

            self._last_data = data
            self.logger.debug(f"Register data saved to {self.persistence_file}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to save register data: {e}")
            return False

    def _extract_register_values(self, slave_context: ModbusServerContext, register_type: str) -> dict:
        """
        Extract register values from the datastore

        :param slave_context: the slave context
        :type slave_context: ModbusServerContext
        :param register_type: 'd' (discrete inputs), 'c' (coils), 'h' (holding), 'i' (input)
        :type register_type: str
        :return: dict with address: value mappings
        :rtype: dict
        :raises: Exception if register type is invalid or datastore access fails but does not raise exceptions (errors are logged and empty dict is returned)
        """
        result = {}
        try:
            # Get the appropriate datastore
            if register_type == "d":
                store = slave_context.store["d"]
            elif register_type == "c":
                store = slave_context.store["c"]
            elif register_type == "h":
                store = slave_context.store["h"]
            elif register_type == "i":
                store = slave_context.store["i"]
            else:
                return result

            # Check if it's a sparse or sequential block
            if isinstance(store, ModbusSparseDataBlock):
                # Sparse blocks have a values dict
                result = dict(store.values)
            elif isinstance(store, ModbusSequentialDataBlock):
                # Sequential blocks: iterate and save non-zero values
                # This saves space in the JSON file
                for addr in range(0, 65536):
                    values = store.getValues(addr, 1)
                    if values and values[0] != 0:
                        result[addr] = values[0]

            return result

        except Exception as e:
            self.logger.error(f"Error extracting {register_type} register values: {e}")
            return result

    def start_auto_save(self):
        """
        Start background thread for automatic periodic saving
        """
        if self._save_thread is not None:
            self.logger.warning("Auto-save thread already running")
            return

        def save_loop():
            self.logger.info(f"Auto-save thread started (interval: {self.save_interval}s)")
            while not self._stop_event.wait(self.save_interval):
                self.save_registers()
            # Final save on shutdown
            self.logger.info("Performing final save before shutdown...")
            self.save_registers()
            self.logger.info("Auto-save thread stopped")

        self._save_thread = threading.Thread(target=save_loop, daemon=True)
        self._save_thread.start()

    def stop_auto_save(self):
        """
        Stop the background save thread
        """
        if self._save_thread is None:
            return

        self.logger.info("Stopping auto-save thread...")
        self._stop_event.set()
        self._save_thread.join(timeout=5)
        self._save_thread = None
