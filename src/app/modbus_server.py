# -*- coding: utf-8 -*-
""" ***************************************************************************
Modbus TCP server script for debugging
Author: Michael Oberdorf IT-Consulting
Datum: 2020-03-30
Last modified by: Michael Oberdorf
Last modified at: 2026-02-07
*************************************************************************** """
import argparse
import json
import logging
import os
import socket
import sys
from typing import Literal, Optional

import pymodbus
from pymodbus.datastore import (
    ModbusDeviceContext,
    ModbusSequentialDataBlock,
    ModbusServerContext,
    ModbusSparseDataBlock,
)
from pymodbus.pdu.device import ModbusDeviceIdentification
from pymodbus.server import StartTcpServer, StartTlsServer, StartUdpServer

# default configuration file path
__script_path__ = os.path.dirname(__file__)
default_config_file = os.path.join(__script_path__, "modbus_server.json")
VERSION = "2.0.0"

log = logging.getLogger()


"""
###############################################################################
# F U N C T I O N S
###############################################################################
"""


def get_ip_address() -> str:
    """
    Small function that determines the IP address of the outbound ethernet interface

    :return IP address
    :rtype: str
    :raises Exception: if the IP address cannot be determined (will be passed silently and empty string will be returned)
    """
    ipaddr = ""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ipaddr = s.getsockname()[0]
    except Exception:
        pass
    return ipaddr


def run_server(
    listener_address: str = "0.0.0.0",
    listener_port: int = 5020,
    protocol: str = "TCP",
    tls_cert: str = None,
    tls_key: str = None,
    zero_mode: bool = False,
    discrete_inputs: Optional[dict] = None,
    coils: Optional[dict] = None,
    holding_registers: Optional[dict] = None,
    input_registers: Optional[dict] = None,
):
    """
    Run the modbus server(s)

    :param listener_address: IP address to bind the listener (default: '0.0.0.0')
    :type listener_address: str
    :param listener_port: TCP port to bin the listener (default: 5020)
    :type listener_port: int
    :param protocol: defines if the server listenes to TCP or UDP (default: 'TCP')
    :type protocol: str
    :param tls_cert: path to certificate to start tcp server with TLS (default: None)
    :type tls_cert: str
    :param tls_key: path to private key to start tcp server with TLS (default: None)
    :type tls_key: str
    :param zero_mode: request to address(0-7) will map to the address (0-7) instead of (1-8) (default: False)
    :type zero_mode: bool
    :param discrete_inputs: initial addresses and their values (default: dict())
    :type discrete_inputs: Optional[dict]
    :param coils: initial addresses and their values (default: dict())
    :type coils: Optional[dict]
    :param holding_registers: initial addresses and their values (default: dict())
    :type holding_registers: Optional[dict]
    :param input_registers: initial addresses and their values (default: dict())
    :type input_registers: Optional[dict]
    """

    # initialize data store
    log.debug("Initialize discrete input")
    if isinstance(discrete_inputs, dict) and discrete_inputs:
        # log.debug('using dictionary from configuration file:')
        # log.debug(discreteInputs)
        di = ModbusSparseDataBlock(discrete_inputs)
    else:
        # log.debug('set all registers to 0xaa')
        # di = ModbusSequentialDataBlock(0x00, [0xaa]*65536)
        log.debug("set all registers to 0x00")
        di = ModbusSequentialDataBlock.create()

    log.debug("Initialize coils")
    if isinstance(coils, dict) and coils:
        # log.debug('using dictionary from configuration file:')
        # log.debug(coils)
        co = ModbusSparseDataBlock(coils)
    else:
        # log.debug('set all registers to 0xbb')
        # co = ModbusSequentialDataBlock(0x00, [0xbb]*65536)
        log.debug("set all registers to 0x00")
        co = ModbusSequentialDataBlock.create()

    log.debug("Initialize holding registers")
    if isinstance(holding_registers, dict) and holding_registers:
        # log.debug('using dictionary from configuration file:')
        # log.debug(holdingRegisters)
        hr = ModbusSparseDataBlock(holding_registers)
    else:
        # log.debug('set all registers to 0xcc')
        # hr = ModbusSequentialDataBlock(0x00, [0xcc]*65536)
        log.debug("set all registers to 0x00")
        hr = ModbusSequentialDataBlock.create()

    log.debug("Initialize input registers")
    if isinstance(input_registers, dict) and input_registers:
        # log.debug('using dictionary from configuration file:')
        # log.debug(inputRegisters)
        ir = ModbusSparseDataBlock(input_registers)
    else:
        # log.debug('set all registers to 0xdd')
        # ir = ModbusSequentialDataBlock(0x00, [0xdd]*65536)
        log.debug("set all registers to 0x00")
        ir = ModbusSequentialDataBlock.create()

    store = ModbusDeviceContext(di=di, co=co, hr=hr, ir=ir)

    log.debug("Define Modbus server context")
    context = ModbusServerContext(devices=store, single=True)

    # ----------------------------------------------------------------------- #
    # initialize the server information
    # ----------------------------------------------------------------------- #
    # If you don't set this or any fields, they are defaulted to empty strings.
    # ----------------------------------------------------------------------- #
    log.debug("Define Modbus server identity")
    identity = ModbusDeviceIdentification()
    identity.VendorName = "Pymodbus"
    log.debug(f"Set VendorName to: {identity.VendorName}")
    identity.ProductCode = "PM"
    log.debug(f"Set ProductCode to: {identity.ProductCode}")
    identity.VendorUrl = "https://github.com/pymodbus-dev/pymodbus/"
    log.debug(f"Set VendorUrl to: {identity.VendorUrl}")
    identity.ProductName = "Pymodbus Server"
    log.debug(f"Set ProductName to: {identity.ProductName}")
    identity.ModelName = "Pymodbus Server"
    log.debug(f"Set ModelName to: {identity.ModelName}")
    identity.MajorMinorRevision = pymodbus.__version__
    log.debug(f"Set MajorMinorRevision to: {identity.MajorMinorRevision}")

    # ----------------------------------------------------------------------- #
    # run the server
    # ----------------------------------------------------------------------- #
    start_tls = False
    if tls_cert and tls_key and os.path.isfile(tls_cert) and os.path.isfile(tls_key):
        start_tls = True

    if start_tls:
        log.info(f"Starting Modbus TCP server with TLS on {listener_address}:{listener_port}")
        StartTlsServer(
            context=context,
            identity=identity,
            certfile=tls_cert,
            keyfile=tls_key,
            address=(listener_address, listener_port),
        )
    else:
        if protocol == "UDP":
            log.info(f"Starting Modbus UDP server on {listener_address}:{listener_port}")
            StartUdpServer(context=context, identity=identity, address=(listener_address, listener_port))
        else:
            log.info(f"Starting Modbus TCP server on {listener_address}:{listener_port}")
            StartTcpServer(context=context, identity=identity, address=(listener_address, listener_port))
            # TCP with different framer
            # StartTcpServer(context=context, identity=identity, framer=ModbusRtuFramer, address=(listener_address, listener_port))


def prepare_register(
    register: dict,
    init_type: Literal["boolean", "word"],
    initialize_undefined_registers: bool = False,
) -> dict:
    """
    Function to prepare the register to have the correct data types

    :param register: the register dictionary, loaded from json file
    :type register: dict
    :param init_type: how to initialize the register values 'boolean' or 'word'
    :type init_type: Literal["boolean", "word"]
    :param initialize_undefined_registers: fill undefined registers with 0x00 (default: False)
    :type initialize_undefined_registers: bool
    :return: register with correct data types
    :rtype: dict
    :raises ValueError: if the input register is not a dictionary
    """
    out_register = dict()
    if not isinstance(register, dict):
        log.error("Unexpected input in function prepareRegister")
        raise ValueError("Unexpected input in function prepareRegister")
    if len(register) == 0:
        return out_register

    for key in register:
        if isinstance(key, str):
            key_out = int(key, 0)
            log.debug(f"  Transform register id: {key} ({type(key)}) to: {key_out} ({type(key_out)})")
        else:
            key_out = key

        val = register[key]
        val_out = val
        if init_type == "word" and isinstance(val, str) and str(val)[0:2] == "0x" and 3 <= len(val) <= 6:
            val_out = int(val, 16)
            log.debug(
                f"  Transform value for register: {key_out} from: {val} ({type(key)}) to: {val_out} ({type(val_out)})"
            )
        elif init_type == "word" and isinstance(val, int) and 0 <= val <= 65535:
            val_out = val
            log.debug("  Use value for register: {}: {}".format(str(key_out), str(val_out)))
        elif init_type == "boolean":
            if isinstance(val, bool):
                val_out = val
                log.debug(f"  Set register: {key_out} to: {val_out} ({type(val_out)})")
            elif isinstance(val, int):
                if val == 0:
                    val_out = False
                else:
                    val_out = True
                log.debug(
                    f"  Transform value for register: {key_out} from: {val} ({type(key)}) to: "
                    f"{val_out} ({type(val_out)})"
                )
        else:
            log.error(
                f"  Malformed input or input is out of range for register: "
                f"{key_out} -> value is {val} - skip this register initialization!"
            )
            continue
        out_register[key_out] = val_out

    if initialize_undefined_registers:
        if init_type == "word":
            log.debug("  Fill undefined registers with 0x00")
        elif init_type == "boolean":
            log.debug("  Fill undefined registers with False")
        for r in range(0, 65536, 1):
            if r not in out_register:
                if init_type == "word":
                    # log.debug('  Initialize address: ' + str(r) + ' with 0')
                    out_register[r] = 0
                elif init_type == "boolean":
                    # log.debug('  Initialize address: ' + str(r) + ' with False')
                    out_register[r] = False

    return out_register


"""
###############################################################################
# M A I N
###############################################################################
"""
if __name__ == "__main__":
    # Parsing command line arguments
    parser = argparse.ArgumentParser(description="Modbus TCP Server")
    group = parser.add_argument_group()
    group.add_argument(
        "-f",
        "--config_file",
        help=f"The configuration file in json format (default: {default_config_file})",
        default=default_config_file,
    )

    args = parser.parse_args()
    if "CONFIG_FILE" in os.environ:
        config_file = os.environ["CONFIG_FILE"]
    else:  # will either use the command line argument or the default value
        config_file = args.config_file
    # check if file actually exists
    if not os.path.isfile(config_file):
        print(f"ERROR: configuration file '{config_file}' does not exist.")
        sys.exit(1)

    # read configuration file
    with open(config_file, encoding="utf-8") as f:
        CONFIG = json.load(f)

    # Initialize logger
    if CONFIG["server"]["logging"]["logLevel"].lower() == "debug":
        log.setLevel(logging.DEBUG)
    elif CONFIG["server"]["logging"]["logLevel"].lower() == "info":
        log.setLevel(logging.INFO)
    elif CONFIG["server"]["logging"]["logLevel"].lower() == "warn":
        log.setLevel(logging.WARN)
    elif CONFIG["server"]["logging"]["logLevel"].lower() == "error":
        log.setLevel(logging.ERROR)
    else:
        log.setLevel(logging.INFO)
    logging.basicConfig(format=CONFIG["server"]["logging"]["format"])

    # start the server
    log.info(f"Starting Modbus Server, v{VERSION}")
    log.debug(f"Loaded successfully the configuration file: {config_file}")

    # be sure the data types within the dictionaries are correct (json will only allow strings as keys)
    configured_discrete_inputs = prepare_register(
        register=CONFIG["registers"]["discreteInput"],
        init_type="boolean",
        initialize_undefined_registers=CONFIG["registers"]["initializeUndefinedRegisters"],
    )
    configured_coils = prepare_register(
        register=CONFIG["registers"]["coils"],
        init_type="boolean",
        initialize_undefined_registers=CONFIG["registers"]["initializeUndefinedRegisters"],
    )
    configured_holding_registers = prepare_register(
        register=CONFIG["registers"]["holdingRegister"],
        init_type="word",
        initialize_undefined_registers=CONFIG["registers"]["initializeUndefinedRegisters"],
    )
    configured_input_registers = prepare_register(
        register=CONFIG["registers"]["inputRegister"],
        init_type="word",
        initialize_undefined_registers=CONFIG["registers"]["initializeUndefinedRegisters"],
    )

    # add TCP protocol to configuration if not defined
    if "protocol" not in CONFIG["server"]:
        CONFIG["server"]["protocol"] = "TCP"

    # try to get the interface IP address
    local_ip_addr = get_ip_address()
    if local_ip_addr != "":
        log.info(f"Outbound device IP address is: {local_ip_addr}")
    run_server(
        listener_address=CONFIG["server"]["listenerAddress"],
        listener_port=CONFIG["server"]["listenerPort"],
        protocol=CONFIG["server"]["protocol"],
        tls_cert=CONFIG["server"]["tlsParams"]["privateKey"],
        tls_key=CONFIG["server"]["tlsParams"]["certificate"],
        discrete_inputs=configured_discrete_inputs,
        coils=configured_coils,
        holding_registers=configured_holding_registers,
        input_registers=configured_input_registers,
    )
