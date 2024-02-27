# -*- coding: utf-8 -*-
from src.app.modbus_server import get_ip_address


def test_ip_address():
    ip = get_ip_address()
    assert isinstance(ip, str)
