# Copilot Instructions for Modbus Server

## Project Overview

This is a **Modbus TCP Server** written in Python that serves as a mock Modbus slave system for testing Modbus master implementations. It allows predefined register values via JSON configuration files and supports both TCP and UDP protocols, with optional TLS encryption.

## Build, Test, and Lint Commands

### Python Version
- **Required**: Python 3.10, 3.11, or 3.12 (see `.tool-versions` for pinned version)
- **Pre-commit hooks**: Python 4.0.1

### Install Dependencies
```bash
cd src/
pip install -r requirements.txt
```

### Run All Tests
```bash
pytest
```

### Run Single Test
```bash
pytest tests/test_server.py::test_prepare_register -v
```

### Linting
The repository uses multiple linting tools configured in `.pre-commit-config.yaml`:
```bash
# Lint with ruff (syntax errors, style)
ruff check --target-version=py37 .

# Format with black
black --line-length=120 .

# Sort imports with isort
isort --profile black --filter-files .

# Remove unused imports/variables
autoflake --in-place --remove-unused-variables --remove-all-unused-imports <file>

# Lint Dockerfile
hadolint Dockerfile
```

### Pre-commit Hook
```bash
pre-commit run --all-files
```

## Architecture

### Key Components

1. **`src/app/modbus_server.py`** - Main application
   - Server initialization and startup logic
   - Register preparation and data block management
   - Support for TCP, UDP, and TLS protocols
   - Logging configuration

2. **`tests/`** - Test suite
   - `test_server.py` - Core server functionality tests
   - `test_utils.py` - Utility function tests
   - Run against Python 3.10, 3.11, and 3.12 via GitHub Actions

3. **Configuration**
   - `src/app/modbus_server.json` - Default server configuration (embedded in container)
   - `examples/` - Additional configuration examples for different use cases

### Data Stores

The server manages four types of Modbus registers:
- **Discrete Inputs** - Read-only single-bit registers
- **Coils** - Read-write single-bit registers
- **Input Registers** - Read-only 16-bit registers
- **Holding Registers** - Read-write 16-bit registers

Register initialization uses `ModbusSparseDataBlock` (sparse registers) or `ModbusSequentialDataBlock` (full 0-65535 range).

## Key Conventions

### Configuration Files

Register values are defined in JSON with these conventions:
- **Bit registers** (Discrete Inputs, Coils): Use `true`/`false` values
- **Word registers** (Input/Holding): Use hex notation (`"0xAA00"`) or integers (0-65535)
- Register numbers must be strings in JSON, converted to integers at runtime
- Example: `"42": true` or `"9": "0xAA00"`

### Function Naming

- `prepare_register()` - Takes register config dict and returns Modbus data block
- Server startup functions accept `config_file` parameter (defaults to `/app/modbus_server.json`)
- Functions include docstrings with parameter descriptions and return types

### Docker Builds

- **Dockerfile**: Alpine-based (3.23.2), Python 3.12.12, deterministic version pinning
- **Exposed ports**: 5020/tcp, 5020/udp (default Modbus port)
- **Entry point**: `python -u /app/modbus_server.py` (unbuffered output for logging)
- **User**: Non-root UID 1434 for security

### CI/CD Workflow

- **Test workflow** (`.github/workflows/test.yaml`):
  - Runs on pull requests and pushes to `main`
  - Tests against Python 3.10, 3.11, 3.12
  - Runs `ruff check` for linting, then `pytest`
  - Install deps in `src/` directory before running tests
- **Pre-commit hooks** enforce code quality before commits
- Bitbucket Pipelines config available for legacy CI/CD

### Code Style

- Line length: 120 characters
- Formatter: Black (via pre-commit)
- Import sorting: isort with Black profile
- Code quality: Ruff with default rules
- Unused imports/variables: auto-removed by autoflake

## MCP Server Configuration

### Python Language Server

For improved code navigation, type checking, and intelligent code completion, configure a Python language server:

**Recommended**: Pylance or Pyright via MCP
- Provides real-time type checking across the codebase
- Supports Python 3.10, 3.11, 3.12
- Helps catch issues with Modbus data types and register handling
