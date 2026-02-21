from src.app.modbus_server import _prepare_register


def test_prepare_register():
    register_example_data = {
        "0": "0x84D9",
        "1": "0x41ED",
        "3": "0xC24C",
        "5": "0xBF80",
        "6": "0x0068",
        "7": "0x006C",
        "8": "0x0074",
        "9": "0x0032",
    }
    register = _prepare_register(register=register_example_data, init_type="word", initialize_undefined_registers=False)
    assert len(register) == 8
    assert register[9] == 0x0032

    # full register should contain all entries as normal registered, but all other memory addresses set to 0
    full_register = _prepare_register(
        register=register_example_data, init_type="word", initialize_undefined_registers=True
    )
    for key in register:
        assert register[key] == full_register[key]
    assert full_register[10] == 0
    assert len(full_register) == 65536


# def test_server():
#     run_server()
