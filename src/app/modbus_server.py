# -*- coding: utf-8 -*-
""" ***************************************************************************
Modbus TCP server script for debugging
Author: Michael Oberdorf IT-Consulting
Datum: 2020-03-30
Last modified by: Michael Oberdorf
Last modified at: 2023-12-06
*************************************************************************** """
import sys
import os
import socket
from pymodbus.server.sync import StartTcpServer
from pymodbus.server.sync import StartTlsServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSparseDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.transaction import ModbusRtuFramer, ModbusBinaryFramer
import logging
import argparse
import json

# default configuration file path
default_config_file='/app/modbus_server.json'
VERSION='1.3.0'
"""
###############################################################################
# F U N C T I O N S
###############################################################################
"""
def get_ip_address():
    """
    get_ip_address is a small function that determines the IP address of the outbound ethernet interface
    @return: string, IP address
    """
    ipaddr = ''
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ipaddr = s.getsockname()[0]
    except:
        pass
    return(ipaddr)

def run_server(listener_address: str = '0.0.0.0', listener_port: int = 5020, tls_cert: str = None, tls_key: str = None, zeroMode: bool = False, discreteInputs: dict = dict(), coils: dict = dict(), holdingRegisters: dict = dict(), inputRegisters: dict = dict()):
    """
    Run the modbus server(s)
    @param listener_address: string, IP address to bind the listener (default: '0.0.0.0')
    @param listener_port: integer, TCP port to bin the listener (default: 5020)
    @param tls_cert: boolean, path to certificate to start tcp server with TLS (default: None)
    @param tls_key: boolean, path to private key to start tcp server with TLS (default: None)
    @param zeroMode: boolean, request to address(0-7) will map to the address (0-7) instead of (1-8) (default: False)
    @param discreteInputs: dict(), initial addresses and their values (default: dict())
    @param coils: dict(), initial addresses and their values (default: dict())
    @param holdingRegisters: dict(), initial addresses and their values (default: dict())
    @param inputRegisters: dict(), initial addresses and their values (default: dict())
    """

    # initialize data store
    log.debug('Initialize discrete input')
    if isinstance(discreteInputs, dict) and len(discreteInputs) > 0:
        #log.debug('using dictionary from configuration file:')
        #log.debug(discreteInputs)
        di = ModbusSparseDataBlock(discreteInputs)
    else:
        #log.debug('set all registers to 0xaa')
        #di = ModbusSequentialDataBlock(0x00, [0xaa]*65536)
        log.debug('set all registers to 0x00')
        di = ModbusSequentialDataBlock.create()

    log.debug('Initialize coils')
    if isinstance(coils, dict) and len(coils) > 0:
        #log.debug('using dictionary from configuration file:')
        #log.debug(coils)
        co = ModbusSparseDataBlock(coils)
    else:
        #log.debug('set all registers to 0xbb')
        #co = ModbusSequentialDataBlock(0x00, [0xbb]*65536)
        log.debug('set all registers to 0x00')
        co = ModbusSequentialDataBlock.create()

    log.debug('Initialize holding registers')
    if isinstance(holdingRegisters, dict) and len(holdingRegisters) > 0:
        #log.debug('using dictionary from configuration file:')
        #log.debug(holdingRegisters)
        hr = ModbusSparseDataBlock(holdingRegisters)
    else:
        #log.debug('set all registers to 0xcc')
        #hr = ModbusSequentialDataBlock(0x00, [0xcc]*65536)
        log.debug('set all registers to 0x00')
        hr = ModbusSequentialDataBlock.create()

    log.debug('Initialize input registers')
    if isinstance(inputRegisters, dict) and len(inputRegisters) > 0:
        #log.debug('using dictionary from configuration file:')
        #log.debug(inputRegisters)
        ir = ModbusSparseDataBlock(inputRegisters)
    else:
        #log.debug('set all registers to 0xdd')
        #ir = ModbusSequentialDataBlock(0x00, [0xdd]*65536)
        log.debug('set all registers to 0x00')
        ir = ModbusSequentialDataBlock.create()

    store = ModbusSlaveContext(
        di=di,
        co=co,
        hr=hr,
        ir=ir,
        zero_mode=zeroMode
        )

    log.debug('Define Modbus server context')
    context = ModbusServerContext(slaves=store, single=True)

    # ----------------------------------------------------------------------- #
    # initialize the server information
    # ----------------------------------------------------------------------- #
    # If you don't set this or any fields, they are defaulted to empty strings.
    # ----------------------------------------------------------------------- #
    log.debug('Define Modbus server identity')
    identity = ModbusDeviceIdentification()
    identity.VendorName = 'Pymodbus'
    identity.ProductCode = 'PM'
    identity.VendorUrl = 'http://github.com/riptideio/pymodbus/'
    identity.ProductName = 'Pymodbus Server'
    identity.ModelName = 'Pymodbus Server'
    identity.MajorMinorRevision = '2.5.3'

    # ----------------------------------------------------------------------- #
    # run the server
    # ----------------------------------------------------------------------- #
    startTLS=False
    if tls_cert and tls_key and os.path.isfile(tls_cert) and os.path.isfile(tls_key): startTLS=True

    if startTLS:
        log.info('Starting Modbus TCP server with TLS on ' + listener_address + ':' + str(listener_port))
        StartTlsServer(context, identity=identity, certfile=tls_cert, keyfile=tls_key, address=(listener_address, listener_port))
    else:
        log.info('Starting Modbus TCP server on ' + listener_address + ':' + str(listener_port))
        StartTcpServer(context, identity=identity, address=(listener_address, listener_port))
        # TCP with different framer
        # StartTcpServer(context, identity=identity, framer=ModbusRtuFramer, address=(listener_address, listener_port))


def prepareRegister(register: dict, initType: str, initializeUndefinedRegisters: bool = False) -> dict:
    """
    Function to prepare the register to have the correct data types
    @param register: dict(), the register dictionary, loaded from json file
    @param initType: str(), how to initialize the register values 'boolean' or 'word'
    @param initializeUndefinedRegisters: boolean, fill undefined registers with 0x00 (default: False)
    @return: dict(), register with correct data types
    """
    outRegister=dict()
    if not isinstance(register, dict):
        log.error('Unexpected input in function prepareRegister')
        return(outRegister)
    if len(register) == 0: return(outRegister)

    for key in register:
      if isinstance(key, str):
        keyOut = int(key, 0)
        log.debug('  Transform register id: ' + str(key) + ' ('+ str(type(key)) + ') to: ' + str(keyOut) + ' (' + str(type(keyOut)) + ')')
      else: keyOut = key

      val = register[key]
      valOut = val
      if initType == 'word' and isinstance(val, str) and str(val)[0:2] == '0x' and len(val) >= 3 and len(val) <= 6:
        valOut = int(val, 16)
        log.debug('  Transform value for register: ' + str(keyOut) + ' from: ' + str(val) + ' ('+ str(type(key)) + ') to: ' + str(valOut) + ' (' + str(type(valOut)) + ')')
      elif initType == 'word' and isinstance(val, int) and val >=0 and val <= 65535:
        valOut = val
        log.debug('  Use value for register: {}: {}'.format(str(keyOut), str(valOut)))
      elif initType == 'boolean':
        if isinstance(val, bool):
          valOut = val
          log.debug('  Set register: ' + str(keyOut) + ' to: ' + str(valOut) + ' (' + str(type(valOut)) + ')')
        elif isinstance(val, int):
          if val == 0:
            valOut = False
          else:
            valOut = True
          log.debug('  Transform value for register: ' + str(keyOut) + ' from: ' + str(val) + ' ('+ str(type(key)) + ') to: ' + str(valOut) + ' (' + str(type(valOut)) + ')')
      else:
        log.error('  Malformed input or input is out of range for register: {} -> value is {} - skip this register initialization!'.format(str(keyOut), str(val)))
        continue
      outRegister[keyOut] = valOut

    if initializeUndefinedRegisters:
        if initType == 'word':
          log.debug('  Fill undefined registers with 0x00')
        elif initType == 'boolean':
          log.debug('  Fill undefined registers with False')
        for r in range(0, 65536, 1):
            if r not in outRegister:
              if initType == 'word':
                #log.debug('  Initialize address: ' + str(r) + ' with 0')
                outRegister[r] = 0
              elif initType == 'boolean':
                #log.debug('  Initialize address: ' + str(r) + ' with False')
                outRegister[r] = False

    return(outRegister)


"""
###############################################################################
# M A I N
###############################################################################
"""
# intialize variable
config_file=None

# Parsing environment variables
if 'CONFIG_FILE' in os.environ:
  if not os.path.isfile(os.environ['CONFIG_FILE']):
    print('ERROR:', 'configuration file not exist:', os.environ['CONFIG_FILE'])
    sys.exit(1)
  else:
    config_file=os.environ['CONFIG_FILE']


# Parsing command line arguments
parser = argparse.ArgumentParser(description='Modbus TCP Server')
group = parser.add_argument_group()
group.add_argument('-f', '--config_file', help='The configuration file in json format (default: ' + default_config_file +')')
args = parser.parse_args()
if args.config_file:
  if not os.path.isfile(args.config_file):
    print('ERROR:', 'configuration file not exist:', args.config_file)
    sys.exit(1)
  else:
    config_file=args.config_file

# define default if no config file path is set
if not config_file:
  config_file=default_config_file

# read configuration file
with open(config_file, encoding='utf-8') as f:
  CONFIG = json.load(f)


# Initialize logger
#FORMAT = ('%(asctime)-15s %(threadName)-15s  %(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s')
FORMAT = CONFIG['server']['logging']['format']
logging.basicConfig(format=FORMAT)
log = logging.getLogger()
if CONFIG['server']['logging']['logLevel'].lower() == 'debug': log.setLevel(logging.DEBUG)
elif CONFIG['server']['logging']['logLevel'].lower() == 'info': log.setLevel(logging.INFO)
elif CONFIG['server']['logging']['logLevel'].lower() == 'warn': log.setLevel(logging.WARN)
elif CONFIG['server']['logging']['logLevel'].lower() == 'error': log.setLevel(logging.ERROR)
else: log.setLevel(logging.INFO)


# start the server
log.info('Starting Modbus TCP Server, v' + str(VERSION))
log.debug('Loaded successfully the configuration file: {}'.format(config_file))

# be sure the data types within the dictionaries are correct (json will only allow strings as keys)
discreteInputs = prepareRegister(register = CONFIG['registers']['discreteInput'], initType='boolean', initializeUndefinedRegisters = CONFIG['registers']['initializeUndefinedRegisters'])
coils=prepareRegister(register = CONFIG['registers']['coils'], initType='boolean', initializeUndefinedRegisters = CONFIG['registers']['initializeUndefinedRegisters'])
holdingRegisters=prepareRegister(register = CONFIG['registers']['holdingRegister'], initType='word', initializeUndefinedRegisters = CONFIG['registers']['initializeUndefinedRegisters'])
inputRegisters=prepareRegister(register = CONFIG['registers']['inputRegister'], initType='word', initializeUndefinedRegisters = CONFIG['registers']['initializeUndefinedRegisters'])

# try to get the interface IP address
localIPAddr = get_ip_address()
if localIPAddr != '': log.info('Outbund device IP address is: ' + localIPAddr)
run_server(
    listener_address=CONFIG['server']['listenerAddress'],
    listener_port=CONFIG['server']['listenerPort'],
    tls_cert=CONFIG['server']['tlsParams']['privateKey'],
    tls_key=CONFIG['server']['tlsParams']['certificate'],
    zeroMode=CONFIG['registers']['zeroMode'],
    discreteInputs=discreteInputs,
    coils=coils,
    holdingRegisters=holdingRegisters,
    inputRegisters=inputRegisters
    )
