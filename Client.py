#!/usr/bin/env python
"""
Pymodbus Synchronous Client Examples
--------------------------------------------------------------------------

The following is an example of how to use the synchronous modbus client
implementation from pymodbus.

It should be noted that the client can also be used with
the guard construct that is available in python 2.5 and up::

    with ModbusClient('127.0.0.1') as client:
        result = client.read_coils(1,10)
        print result

Client Is the Master device in this case
"""

# --------------------------------------------------------------------------- #
# import the various client implementations
# --------------------------------------------------------------------------- #
from numpy import unicode_
from pymodbus.client.sync import ModbusTcpClient as ModbusClient
# from pymodbus.client.sync import ModbusUdpClient as ModbusClient
# from pymodbus.client.sync import ModbusSerialClient as ModbusClient
import sys

# --------------------------------------------------------------------------- #
# configure the client #logging
# --------------------------------------------------------------------------- #
import logging
# FORMAT = ('%(asctime)-15s %(threadName)-15s '
#           '%(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s')
# #logging.basicConfig(format=FORMAT)
# #log = #logging.get#Logger()
# #log.setLevel(#logging.DEBUG)

'''
Predefined list of slave devices

0x01 smart meter 1
0x02 smart meter 2
0x03 smart meter 3
0x04 load 1
'''
slaves = [0x01,0x02,0x03,0x04]
slave_sm = [0x01, 0x02,0x03]
SM_1 = 0x01
SM_2 = 0x02
SM_3 = 0x03
LD_1 = 0x04


def run_sync_client():
    client = ModbusClient('localhost', port=5020)
    # from pymodbus.transaction import ModbusRtuFramer
    # client = ModbusClient('localhost', port=5020, framer=ModbusRtuFramer)
    # client = ModbusClient(method='binary', port='/dev/ptyp0', timeout=1)
    # client = ModbusClient(method='ascii', port='/dev/ptyp0', timeout=1)
    # client = ModbusClient(method='rtu', port='/dev/ptyp0', timeout=1,
    #                       baudrate=9600)
    client.connect()

    '''
    Live system
    '''
    try:
        power_required = 0
        while(True):
            if(client.read_coils(0,1,unit=LD_1).bits[0]):
                power_required = client.read_holding_registers(0, 1, unit=LD_1).registers[0]
                client.write_coils(0, [False], unit=LD_1)

                print('Power required by load: ' + str(power_required) + 'KW')

                temp = power_required
                for i in slave_sm:
                    lim = client.read_holding_registers(1, 1, unit=i).registers[0]
                    if temp - lim > 0:
                        client.write_register(0, lim, unit=i)
                        client.write_coil(0, True, unit=i)
                        print('Changed SM' + str(i) + ' Production to: ' + str(lim) + 'KW')
                        temp = temp - lim
                    else:
                        client.write_register(0, temp, unit=i)
                        client.write_coil(0, True, unit=i)
                        print('Changed SM' + str(i) + ' Production to: ' + str(temp) + 'KW')
                        temp = 0
    except:
        print('Killing Master device')
        client.close()




if __name__ == "__main__":
    run_sync_client()