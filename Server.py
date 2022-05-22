#!/usr/bin/env python
"""
Pymodbus Synchronous Server Example
--------------------------------------------------------------------------

The synchronous server is implemented in pure python without any third
party libraries (unless you need to use the serial protocols which require
pyserial). This is helpful in constrained or old environments where using
twisted is just not feasible. What follows is an example of its use:

This is the Slave device in this case
"""
# --------------------------------------------------------------------------- #
# import the various server implementations
# --------------------------------------------------------------------------- #
from pymodbus.version import version
from pymodbus.server.sync import StartTcpServer
from pymodbus.server.sync import StartTlsServer
from pymodbus.server.sync import StartUdpServer
from pymodbus.server.sync import StartSerialServer

from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSparseDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext

from pymodbus.transaction import ModbusRtuFramer, ModbusBinaryFramer
from threading import Thread
import random
import time


'''

Simulation for DER smart meter device using modbus communication

Power output of device between 0 - 20KW

Varies output depending on request from master device

'''
class DER_Smart_meter(Thread):
    def __init__(self, data_block, slave_id, limit):
        Thread.__init__(self)
        self.data_block = data_block
        self.slave_id = slave_id
        self.power_produced = 0
        self.status = True
        self.limit = limit #KW
        print('Smart Meter ' + str(self.slave_id) + ' Max load:' + str(self.limit) + 'KW')
        self.data_block.setValues(3,0,[0])
        self.data_block.setValues(1,0,[False])

    def run(self):
        print('Starting Smart Meter')
        #Establishing MAX limit
        self.data_block.setValues(3,1,[self.limit])

        while(self.status):
            time.sleep(1)
            self.producing_power()
            self.change_power_produced()
        print('Killing smart Meter')

    def turn_off(self):
        self.status = False

    def producing_power(self):
        print('Smart meter ' + str(self.slave_id) + ' is producing: ' + str(self.power_produced) + 'KW') 

    def check_coil_change(self):
        return self.data_block.getValues(1,0,1)[0]

    def change_power_produced(self):
        if(self.check_coil_change()):
            temp = self.data_block.getValues(3,0,1)[0]
            if temp > self.limit:
                print('Smart Meter ERROR: LIMIT REACHED')
            else:
                self.power_produced = temp

'''
Simulation of a load in the network

Requests random amounts of power from the Master device, which has to change

registers of the Smart_meters in order to request more or less power into the network

Power request can be between:

0 - 50 KW of power
'''

class DER_Load(Thread):
    def __init__(self, data_block, slave_id, max_load):
        Thread.__init__(self)
        self.data_block = data_block
        self.slave_id = slave_id
        self.status = True
        self.max_load = max_load
        print('Load Max: ' + str(self.max_load) + 'KW')

    def run(self):
        print('Starting Load')
        while(self.status):
            time.sleep(2)
            val = random.randint(0,self.max_load)
            self.change_val()
            self.data_block.setValues(3,0,[val])
            self.print_load(val)
        print('Killing Load')

    def turn_off(self):
        self.status = False

    '''
    Changes first coil value to true to establish that the load value has changed
    '''
    def change_val(self):
        self.data_block.setValues(1,0,[True])

    def print_load(self, load):
        print('Load Required in system: ' + str(load))

def run_server():
    # ----------------------------------------------------------------------- #
    # initialize your data store
    # ----------------------------------------------------------------------- #
    # The datastores only respond to the addresses that they are initialized to
    # Therefore, if you initialize a DataBlock to addresses of 0x00 to 0xFF, a
    # request to 0x100 will respond with an invalid address exception. This is
    # because many devices exhibit this kind of behavior (but not all)::
    #
    #     block = ModbusSequentialDataBlock(0x00, [0]*0xff)
    #
    # Continuing, you can choose to use a sequential or a sparse DataBlock in
    # your data context.  The difference is that the sequential has no gaps in
    # the data while the sparse can. Once again, there are devices that exhibit
    # both forms of behavior::
    #
    #     block = ModbusSparseDataBlock({0x00: 0, 0x05: 1})
    #     block = ModbusSequentialDataBlock(0x00, [0]*5)
    #
    # Alternately, you can use the factory methods to initialize the DataBlocks
    # or simply do not pass them to have them initialized to 0x00 on the full
    # address range::
    #
    #     store = ModbusSlaveContext(di = ModbusSequentialDataBlock.create())
    #     store = ModbusSlaveContext()
    #
    # Finally, you are allowed to use the same DataBlock reference for every
    # table or you may use a separate DataBlock for each table.
    # This depends if you would like functions to be able to access and modify
    # the same data or not::
    #
    #     block = ModbusSequentialDataBlock(0x00, [0]*0xff)
    #     store = ModbusSlaveContext(di=block, co=block, hr=block, ir=block)
    #
    # The server then makes use of a server context that allows the server to
    # respond with different slave contexts for different unit ids. By default
    # it will return the same context for every unit id supplied (broadcast
    # mode).
    # However, this can be overloaded by setting the single flag to False and
    # then supplying a dictionary of unit id to context mapping::
    #
    #     slaves  = {
    #         0x01: ModbusSlaveContext(...),
    #         0x02: ModbusSlaveContext(...),
    #         0x03: ModbusSlaveContext(...),
    #     }
    #     context = ModbusServerContext(slaves=slaves, single=False)
    #
    # The slave context can also be initialized in zero_mode which means that a
    # request to address(0-7) will map to the address (0-7). The default is
    # False which is based on section 4.4 of the specification, so address(0-7)
    # will map to (1-8)::
    #
    #     store = ModbusSlaveContext(..., zero_mode=True)
    # ----------------------------------------------------------------------- #
    store = ModbusSlaveContext(
        di=ModbusSequentialDataBlock(0, [17]*100),
        co=ModbusSequentialDataBlock(0, [17]*100),
        hr=ModbusSequentialDataBlock(0, [17]*100),
        ir=ModbusSequentialDataBlock(0, [17]*100))

    store1 = ModbusSlaveContext(
        di=ModbusSequentialDataBlock(0, [17]*100),
        co=ModbusSequentialDataBlock(0, [17]*100),
        hr=ModbusSequentialDataBlock(0, [17]*100),
        ir=ModbusSequentialDataBlock(0, [17]*100))

    store2 = ModbusSlaveContext(
        di=ModbusSequentialDataBlock(0, [17]*100),
        co=ModbusSequentialDataBlock(0, [17]*100),
        hr=ModbusSequentialDataBlock(0, [17]*100),
        ir=ModbusSequentialDataBlock(0, [17]*100))

    store3 = ModbusSlaveContext(
        di=ModbusSequentialDataBlock(0, [17]*100),
        co=ModbusSequentialDataBlock(0, [17]*100),
        hr=ModbusSequentialDataBlock(0, [17]*100),
        ir=ModbusSequentialDataBlock(0, [17]*100))

    #Malicious
    store4 = ModbusSlaveContext(
        di=ModbusSequentialDataBlock(0, [17]*100),
        co=ModbusSequentialDataBlock(0, [17]*100),
        hr=ModbusSequentialDataBlock(0, [17]*100),
        ir=ModbusSequentialDataBlock(0, [17]*100))

    slaves = {
        0x01: store,
        0x02: store1,
        0x03: store2,
        0x04: store3,
        #0x01: store4,
    }

    max_load = random.randint(30,50)
    sm_1_max = random.randint(15, 20)
    sm_2_max = random.randint(15, 20)
    sm_3_max = random.randint(15, 20)

    smart_meter = DER_Smart_meter(store, 0x01, sm_1_max)
    smart_meter1 = DER_Smart_meter(store1, 0x02, sm_2_max)
    smart_meter2 = DER_Smart_meter(store2, 0x03, sm_3_max)
    load = DER_Load(store3, 0x04, max_load)
    smart_meter.start()
    smart_meter1.start()
    smart_meter2.start()
    load.start()
    context = ModbusServerContext(slaves=slaves, single=False)
    
    # ----------------------------------------------------------------------- #
    # initialize the server information
    # ----------------------------------------------------------------------- #
    # If you don't set this or any fields, they are defaulted to empty strings.
    # ----------------------------------------------------------------------- #
    identity = ModbusDeviceIdentification()
    identity.VendorName = 'Calvin Code'
    identity.ProductCode = 'DER SL Sim'
    identity.ProductName = 'DER slave simulator'
    identity.ModelName = 'DER slave simulator'

    # ----------------------------------------------------------------------- #
    # run the server you want
    # ----------------------------------------------------------------------- #
    # Tcp:
    try:
        print('Starting TCP Modbus slave server')
        StartTcpServer(context, identity=identity, address=("", 5020))
    except:
        print('Closing Modbus slave server')
        smart_meter.turn_off()
        smart_meter1.turn_off()
        smart_meter2.turn_off()
        load.turn_off()

    #
    # TCP with different framer
    # StartTcpServer(context, identity=identity,
    #                framer=ModbusRtuFramer, address=("0.0.0.0", 5020))

    # TLS
    # StartTlsServer(context, identity=identity, certfile="server.crt",
    #                keyfile="server.key", address=("0.0.0.0", 8020))

    # Udp:
    # StartUdpServer(context, identity=identity, address=("0.0.0.0", 5020))

    # socat -d -d PTY,link=/tmp/ptyp0,raw,echo=0,ispeed=9600 PTY,link=/tmp/ttyp0,raw,echo=0,ospeed=9600
    # Ascii:
    # StartSerialServer(context, identity=identity,
    #                    port='/dev/ttyp0', timeout=1)

    # RTU:
    # StartSerialServer(context, framer=ModbusRtuFramer, identity=identity,
    #                   port='/tmp/ttyp0', timeout=.005, baudrate=9600)

    # Binary
    # StartSerialServer(context,
    #                   identity=identity,
    #                   framer=ModbusBinaryFramer,
    #                   port='/dev/ttyp0',
    #                   timeout=1)


if __name__ == "__main__":
    run_server()
    


