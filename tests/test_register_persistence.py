# -*- coding: utf-8 -*-
"""
Unit tests for the RegisterPersistence library
"""

import json
import os
import shutil
import tempfile
import time
from unittest.mock import MagicMock, patch

import pytest
from pymodbus.datastore import (
    ModbusSequentialDataBlock,
    ModbusServerContext,
    ModbusSparseDataBlock,
)

from src.app.lib.register_persistence import RegisterPersistence


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def temp_persistence_file(temp_dir):
    """Create a temporary persistence file path"""
    return os.path.join(temp_dir, "test_persistence.json")


@pytest.fixture
def mock_modbus_context():
    """Create a mock ModbusServerContext for testing"""
    context = MagicMock(spec=ModbusServerContext)

    # Create mock slave context with register stores
    slave_context = MagicMock()

    # Create mock data stores for each register type
    discrete_inputs = MagicMock(spec=ModbusSparseDataBlock)
    discrete_inputs.values = {0: True, 5: False}

    coils = MagicMock(spec=ModbusSparseDataBlock)
    coils.values = {1: True, 3: True}

    holding_registers = MagicMock(spec=ModbusSparseDataBlock)
    holding_registers.values = {0: 100, 5: 200, 10: 300}

    input_registers = MagicMock(spec=ModbusSparseDataBlock)
    input_registers.values = {2: 50, 7: 75}

    slave_context.store = {"d": discrete_inputs, "c": coils, "h": holding_registers, "i": input_registers}

    context.__getitem__ = MagicMock(return_value=slave_context)

    return context


class TestRegisterPersistenceInit:
    """Test RegisterPersistence initialization"""

    def test_init_with_existing_directory(self, temp_persistence_file, mock_modbus_context):
        """Test initialization when directory already exists"""
        persistence = RegisterPersistence(temp_persistence_file, mock_modbus_context)
        assert persistence.persistence_file == temp_persistence_file
        assert persistence.context == mock_modbus_context
        assert persistence.save_interval == 30
        assert persistence._stop_event is not None
        assert persistence._save_thread is None

    def test_init_with_nonexistent_directory(self, temp_dir, mock_modbus_context):
        """Test initialization creates directory if it doesn't exist"""
        nested_path = os.path.join(temp_dir, "nested", "dir", "persistence.json")
        persistence = RegisterPersistence(nested_path, mock_modbus_context)
        assert persistence.save_interval == 30
        assert os.path.isdir(os.path.dirname(nested_path))

    def test_init_with_custom_save_interval(self, temp_persistence_file, mock_modbus_context):
        """Test initialization with custom save interval"""
        persistence = RegisterPersistence(temp_persistence_file, mock_modbus_context, save_interval=60)
        assert persistence.save_interval == 60


class TestLoadRegisters:
    """Test RegisterPersistence.load_registers() method"""

    def test_load_registers_file_not_exists(self, temp_persistence_file, mock_modbus_context):
        """Test loading when persistence file doesn't exist"""
        persistence = RegisterPersistence(temp_persistence_file, mock_modbus_context)
        result = persistence.load_registers()
        assert result is None

    def test_load_registers_file_exists(self, temp_persistence_file, mock_modbus_context):
        """Test loading when persistence file exists with valid JSON"""
        test_data = {
            "discrete_inputs": {"0": True, "5": False},
            "coils": {"1": True},
            "holding_registers": {"0": 100, "5": 200},
            "input_registers": {"2": 50},
        }

        with open(temp_persistence_file, "w") as f:
            json.dump(test_data, f)

        persistence = RegisterPersistence(temp_persistence_file, mock_modbus_context)
        result = persistence.load_registers()
        assert result == test_data

    def test_load_registers_invalid_json(self, temp_persistence_file, mock_modbus_context):
        """Test loading when persistence file contains invalid JSON"""
        with open(temp_persistence_file, "w") as f:
            f.write("invalid json {{{")

        persistence = RegisterPersistence(temp_persistence_file, mock_modbus_context)
        with pytest.raises(RuntimeError, match="Error loading persistence file"):
            persistence.load_registers()

    def test_load_registers_file_read_error(self, temp_persistence_file, mock_modbus_context):
        """Test loading when file cannot be read (permission denied, etc.)"""
        # Create file
        with open(temp_persistence_file, "w") as f:
            f.write("{}")

        persistence = RegisterPersistence(temp_persistence_file, mock_modbus_context)

        with patch("builtins.open", side_effect=IOError("Permission denied")):
            with pytest.raises(RuntimeError, match="Error loading persistence file"):
                persistence.load_registers()


class TestSaveRegisters:
    """Test RegisterPersistence.save_registers() method"""

    def test_save_registers_success(self, temp_persistence_file, mock_modbus_context):
        """Test successful saving of registers"""
        persistence = RegisterPersistence(temp_persistence_file, mock_modbus_context)
        result = persistence.save_registers()
        assert result is True
        assert os.path.isfile(temp_persistence_file)

        # Verify saved data
        with open(temp_persistence_file, "r") as f:
            saved_data = json.load(f)

        assert "discrete_inputs" in saved_data
        assert "coils" in saved_data
        assert "holding_registers" in saved_data
        assert "input_registers" in saved_data

    def test_save_registers_no_changes(self, temp_persistence_file, mock_modbus_context):
        """Test that repeated saves without changes don't write to file"""
        persistence = RegisterPersistence(temp_persistence_file, mock_modbus_context)

        # First save
        result1 = persistence.save_registers()
        assert result1 is True
        stat1 = os.stat(temp_persistence_file)

        # Wait a bit
        time.sleep(0.1)

        # Second save without changes
        result2 = persistence.save_registers()
        assert result2 is True
        stat2 = os.stat(temp_persistence_file)

        # File should not have been modified (timestamp should be the same)
        assert stat1.st_mtime == stat2.st_mtime

    def test_save_registers_file_write_error(self, temp_persistence_file, mock_modbus_context):
        """Test handling of file write errors"""
        persistence = RegisterPersistence(temp_persistence_file, mock_modbus_context)

        with patch("builtins.open", side_effect=IOError("No space left")):
            result = persistence.save_registers()
            assert result is False

    def test_save_registers_atomic_write(self, temp_persistence_file, mock_modbus_context):
        """Test that atomic write doesn't leave temp files on success"""
        persistence = RegisterPersistence(temp_persistence_file, mock_modbus_context)
        persistence.save_registers()

        temp_file = temp_persistence_file + ".tmp"
        assert not os.path.exists(temp_file)

    def test_save_registers_preserves_data_on_error(self, temp_persistence_file, mock_modbus_context):
        """Test that existing data is preserved if save fails"""
        persistence = RegisterPersistence(temp_persistence_file, mock_modbus_context)

        # Save initial data
        persistence.save_registers()
        with open(temp_persistence_file, "r") as f:
            initial_data = json.load(f)

        # Try to save with error
        with patch("os.replace", side_effect=OSError("Cannot replace")):
            persistence.save_registers()

        # Original file should still exist with original data
        with open(temp_persistence_file, "r") as f:
            current_data = json.load(f)

        assert current_data == initial_data


class TestExtractRegisterValues:
    """Test RegisterPersistence._extract_register_values() method"""

    def test_extract_sparse_discrete_inputs(self, temp_persistence_file, mock_modbus_context):
        """Test extracting discrete input values from sparse block"""
        persistence = RegisterPersistence(temp_persistence_file, mock_modbus_context)
        slave_context = mock_modbus_context[0]

        result = persistence._extract_register_values(slave_context, "d")
        assert result == {0: True}

    def test_extract_sparse_coils(self, temp_persistence_file, mock_modbus_context):
        """Test extracting coil values from sparse block"""
        persistence = RegisterPersistence(temp_persistence_file, mock_modbus_context)
        slave_context = mock_modbus_context[0]

        result = persistence._extract_register_values(slave_context, "c")
        assert result == {1: True, 3: True}

    def test_extract_sparse_holding_registers(self, temp_persistence_file, mock_modbus_context):
        """Test extracting holding register values from sparse block"""
        persistence = RegisterPersistence(temp_persistence_file, mock_modbus_context)
        slave_context = mock_modbus_context[0]

        result = persistence._extract_register_values(slave_context, "h")
        assert result == {0: 100, 5: 200, 10: 300}

    def test_extract_sparse_input_registers(self, temp_persistence_file, mock_modbus_context):
        """Test extracting input register values from sparse block"""
        persistence = RegisterPersistence(temp_persistence_file, mock_modbus_context)
        slave_context = mock_modbus_context[0]

        result = persistence._extract_register_values(slave_context, "i")
        assert result == {2: 50, 7: 75}

    def test_extract_sequential_registers(self, temp_persistence_file):
        """Test extracting values from sequential data block"""
        context = MagicMock(spec=ModbusServerContext)
        slave_context = MagicMock()

        # Create a mock sequential block
        sequential_block = MagicMock(spec=ModbusSequentialDataBlock)
        sequential_block.getValues = MagicMock(side_effect=lambda addr, count: [100] if addr in [5, 10] else [0])

        slave_context.store = {"h": sequential_block}
        context.__getitem__ = MagicMock(return_value=slave_context)

        persistence = RegisterPersistence(temp_persistence_file, context)
        result = persistence._extract_register_values(slave_context, "h")

        # Sequential blocks save non-zero values
        assert isinstance(result, dict)

    def test_extract_invalid_register_type(self, temp_persistence_file, mock_modbus_context):
        """Test extracting with invalid register type"""
        persistence = RegisterPersistence(temp_persistence_file, mock_modbus_context)
        slave_context = mock_modbus_context[0]

        result = persistence._extract_register_values(slave_context, "x")
        assert result == {}

    def test_extract_on_datastore_error(self, temp_persistence_file):
        """Test extraction handles datastore errors gracefully"""
        context = MagicMock(spec=ModbusServerContext)
        slave_context = MagicMock()

        # Create a mock store that raises an error
        error_store = MagicMock(spec=ModbusSparseDataBlock)
        slave_context.store = {"h": error_store}
        context.__getitem__ = MagicMock(return_value=slave_context)

        # Mock the isinstance check to not match, causing an exception
        with patch("src.app.lib.register_persistence.isinstance", side_effect=Exception("Store error")):
            persistence = RegisterPersistence(temp_persistence_file, context)
            result = persistence._extract_register_values(slave_context, "h")

        # Should return empty dict on error
        assert result == {}


class TestAutoSave:
    """Test RegisterPersistence auto-save threading"""

    def test_start_auto_save(self, temp_persistence_file, mock_modbus_context):
        """Test starting auto-save thread"""
        persistence = RegisterPersistence(temp_persistence_file, mock_modbus_context, save_interval=1)
        persistence.start_auto_save()

        assert persistence._save_thread is not None
        assert persistence._save_thread.is_alive()

        # Cleanup
        persistence.stop_auto_save()

    def test_auto_save_doesnt_start_twice(self, temp_persistence_file, mock_modbus_context):
        """Test that starting auto-save twice doesn't create multiple threads"""
        persistence = RegisterPersistence(temp_persistence_file, mock_modbus_context, save_interval=1)
        persistence.start_auto_save()
        thread1 = persistence._save_thread

        persistence.start_auto_save()
        thread2 = persistence._save_thread

        assert thread1 is thread2

        # Cleanup
        persistence.stop_auto_save()

    def test_stop_auto_save(self, temp_persistence_file, mock_modbus_context):
        """Test stopping auto-save thread"""
        persistence = RegisterPersistence(temp_persistence_file, mock_modbus_context, save_interval=1)
        persistence.start_auto_save()

        assert persistence._save_thread is not None
        persistence.stop_auto_save()

        # Thread should be None after stopping
        assert persistence._save_thread is None

    def test_stop_auto_save_when_not_running(self, temp_persistence_file, mock_modbus_context):
        """Test stopping auto-save when it's not running"""
        persistence = RegisterPersistence(temp_persistence_file, mock_modbus_context)
        # Should not raise an error
        persistence.stop_auto_save()
        assert persistence._save_thread is None

    def test_auto_save_periodic_writes(self, temp_persistence_file, mock_modbus_context):
        """Test that auto-save periodically writes data"""
        persistence = RegisterPersistence(temp_persistence_file, mock_modbus_context, save_interval=1)
        persistence.start_auto_save()

        # Wait for at least one save cycle
        time.sleep(1.5)

        assert os.path.isfile(temp_persistence_file)

        # Cleanup
        persistence.stop_auto_save()

    def test_auto_save_final_save_on_shutdown(self, temp_persistence_file, mock_modbus_context):
        """Test that auto-save performs final save on shutdown"""
        persistence = RegisterPersistence(temp_persistence_file, mock_modbus_context, save_interval=100)
        persistence.start_auto_save()
        persistence.stop_auto_save()

        # File should exist after shutdown due to final save
        assert os.path.isfile(temp_persistence_file)


class TestIntegration:
    """Integration tests for RegisterPersistence"""

    def test_full_workflow(self, temp_persistence_file, mock_modbus_context):
        """Test complete workflow: save, load, verify"""
        # Save data
        persistence = RegisterPersistence(temp_persistence_file, mock_modbus_context)
        save_result = persistence.save_registers()
        assert save_result is True

        # Load data
        loaded_data = persistence.load_registers()
        assert loaded_data is not None
        assert "discrete_inputs" in loaded_data
        assert "coils" in loaded_data
        assert "holding_registers" in loaded_data
        assert "input_registers" in loaded_data

    def test_auto_save_with_manual_save(self, temp_persistence_file, mock_modbus_context):
        """Test combining auto-save with manual save"""
        persistence = RegisterPersistence(temp_persistence_file, mock_modbus_context, save_interval=1)

        # Manual save
        persistence.save_registers()
        assert os.path.isfile(temp_persistence_file)

        # Start auto-save
        persistence.start_auto_save()
        time.sleep(1.5)

        # Manual save again
        persistence.save_registers()

        persistence.stop_auto_save()
        assert os.path.isfile(temp_persistence_file)
