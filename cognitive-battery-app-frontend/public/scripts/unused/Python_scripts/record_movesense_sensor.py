# -*- coding: utf-8 -*-
"""
Python gatt_sensordata_app client example using the Bleak GATT client.

This example is based on the examples in the Bleak repo: https://github.com/hbldh/bleak
"""

import logging
import asyncio
import platform
import signal
from bleak import BleakClient
from bleak import BleakScanner
from bleak import _logger as logger
from bleak import discover
#from functools import reduce
import struct
import sys
import csv
import time
import serial
from datetime import datetime
import socket
import json

#global variable 
COMPUTER_NAME = None
TASK_NAME = None
SUB_ID = None
START_TIME_UNIX = {}   #time at openfile in milisecond(to convert timeline to unix timestamp)
START_TIME_SENSOR = {} #time at openfile (sensor_clock)

# Dictionary to keep track of open files and writers
open_files = {}
writers = {}
 

WRITE_CHARACTERISTIC_UUID = (
    "34800001-7185-4d5d-b431-630e7050e8f0"
)

NOTIFY_CHARACTERISTIC_UUID = (
    "34800002-7185-4d5d-b431-630e7050e8f0"
)


PACKET_TYPE_DATA = 2
PACKET_TYPE_DATA_PART2 = 3
ongoing_data_update = None



# https://stackoverflow.com/a/56243296
class DataView:
    def __init__(self, array, bytes_per_element=1):
        """
        bytes_per_element is the size of each element in bytes.
        By default we are assume the array is one byte per element.
        """
        self.array = array
        self.bytes_per_element = 1

    def __get_binary(self, start_index, byte_count, signed=False):
        integers = [self.array[start_index + x] for x in range(byte_count)]
        _bytes = [integer.to_bytes(
            self.bytes_per_element, byteorder='little', signed=signed) for integer in integers]
        #return reduce(lambda a, b: a + b, _bytes)
        binary_result = b''
        for b in _bytes:
            binary_result += b
        return binary_result

    def get_uint_16(self, start_index):
        bytes_to_read = 2
        return int.from_bytes(self.__get_binary(start_index, bytes_to_read), byteorder='little')

    def get_uint_8(self, start_index):
        bytes_to_read = 1
        return int.from_bytes(self.__get_binary(start_index, bytes_to_read), byteorder='little')

    def get_uint_32(self, start_index):
        bytes_to_read = 4
        binary = self.__get_binary(start_index, bytes_to_read)
        return struct.unpack('<I', binary)[0]  # <f for little endian

    def get_int_32(self, start_index):
        bytes_to_read = 4
        binary = self.__get_binary(start_index, bytes_to_read)
        return struct.unpack('<i', binary)[0]  # < for little endian

    def get_float_32(self, start_index):
        bytes_to_read = 4
        binary = self.__get_binary(start_index, bytes_to_read)
        return struct.unpack('<f', binary)[0]  # <f for little endian

    def length(self):
        return len(self.array)



# Handle graceful exit on program termination
def signal_handler(sig, frame):
    logger.info('You pressed Ctrl+C! Closing files and exiting...')
    for file in open_files.values():
        file.close()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)


async def run_queue_consumer(client_socket, queue: asyncio.Queue):
    global open_files, writers, COMPUTER_NAME, TASK_NAME, SUB_ID, START_TIME_UNIX, START_TIME_SENSOR

    while True:
        data = await queue.get()
        if data is None:
            logger.info(
                "Got message from client about disconnection. Exiting consumer loop..."
            )
            break
        else:
            if isinstance(data, str):
                # Assuming it's a single string of IMU9 data
                data_type = 'IMU9'
                # Parse the string data into the appropriate columns
                parsed_row = list(map(float, data.split(',')))
                
                if data_type not in open_files:
                    START_TIME_UNIX[data_type] = round(time.time()*1000)
                    START_TIME_SENSOR[data_type] = parsed_row[0]
                    
                    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
                    filename = f"{SUB_ID}_{TASK_NAME}_{timestamp}_{data_type.lower()}.csv"
                    file = open(filename, mode='w', newline='')
                    open_files[data_type] = file

                    # Initialize the CSV writer with fieldnames
                    fieldnames = ['Computer_name','Subject_id','Game_type','Timestamp', 'acc_x', 'acc_y', 'acc_z', 'gyro_x', 'gyro_y', 'gyro_z', 'magn_x',
                                  'magn_y', 'magn_z']
                    writer = csv.writer(file)
                    writer.writerow(fieldnames)
                    writers[data_type] = writer

                writer = writers[data_type]
                
                #writing data
                base_timestamp = parsed_row[0] - START_TIME_SENSOR[data_type] + START_TIME_UNIX[data_type] #convert from sensor clock to unix timestamp in milisecond
                row_data = [COMPUTER_NAME,SUB_ID,TASK_NAME,base_timestamp] + parsed_row[1:]
                print("IMU9: ",row_data)
                writer.writerow(row_data)
                
                #sending data to websocket (put the code in here)
                #print(parsed_row)
                
                
            elif isinstance(data, dict):
                # Assuming it's ECG data
                data_type = data.pop('type')
                if data_type not in open_files:
                    START_TIME_UNIX[data_type] = round(time.time()*1000)
                    START_TIME_SENSOR[data_type] = data['timestamp']
                    
                    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
                    filename = f"{SUB_ID}_{TASK_NAME}_{timestamp}_{data_type.lower()}.csv"
                    file = open(filename, mode='w', newline='')
                    open_files[data_type] = file

                    # Initialize the CSV writer with fieldnames
                    fieldnames = ['Computer_name','Subject_id','Game_type','Timestamp','ecg_data']
                    writer = csv.writer(file)
                    writer.writerow(fieldnames)
                    writers[data_type] = writer

                writer = writers[data_type]
                
                
                
                #writing data
                print("ECG: ",data)
                base_timestamp = data['timestamp'] - START_TIME_SENSOR[data_type] + START_TIME_UNIX[data_type] #convert from sensor clock to unix timestamp in milisecond
                for index, value in enumerate(data['samples']):
                    current_timestamp = base_timestamp + index * 4
                    writer.writerow([COMPUTER_NAME,SUB_ID,TASK_NAME,current_timestamp, value])
                    #print([COMPUTER_NAME,SUB_ID,TASK_NAME,current_timestamp, value])

                    #sending data to web socket
                    json_data = {}
                    json_data['Computer_name'] = COMPUTER_NAME
                    json_data['data_type'] = "Heart_Data"    
                    json_data['Subject_id'] = SUB_ID
                    json_data['Game_type'] = TASK_NAME
                    json_data['Timestamp'] = current_timestamp
                    json_data['ecg_data'] = value
                    json_data = json.dumps(json_data).encode('utf-8')
                    client_socket.sendall(json_data)

                
            # Flush to ensure data is written to disk
            open_files[data_type].flush()

            # Print to stdout (for debugging purposes)
            # print(data)

    # Close all open files when done
    for file in open_files.values():
        file.close()


async def run_ble_client(end_of_serial: str, queue: asyncio.Queue):

    # Check the device is available
    devices = await BleakScanner.discover()
    found = False
    address = None
    for d in devices:
        logger.debug("device:", d)
        if d.name and d.name.endswith(end_of_serial):
            logger.info("device found")
            address = d.address
            found = True
            break

    # This event is set if device disconnects or ctrl+c is pressed
    disconnected_event = asyncio.Event()

    def raise_graceful_exit(*args):
        disconnected_event.set()

    def disconnect_callback(client):
        logger.info("Disconnected callback called!")
        disconnected_event.set()

    async def handle_ecg_data_notification(payload):
        # Dig data from the binary
        ts = payload.get_uint_32(0)

        # data is 16 samples of uint32
        data = {}
        data["type"] = "ECG"
        data["timestamp"] = ts
        data["samples"] = []
        for i in range(16):
            sample = payload.get_int_32(4 + i * 4)
            data["samples"].append(sample)
        # queue message for later consumption

        await queue.put(data)

    async def handle_default_data_notification(payload):
        msg = "Unknown data: {} bytes".format(payload.length())
        await queue.put(msg)

    async def handle_command_response(payload):
        print("Command response:", payload.array)

    async def notification_handler(sender, data):
        """Simple notification handler which prints the data received."""
        d = DataView(data)

        packet_type= d.get_uint_8(0)
        reference_id = d.get_uint_8(1)

        global ongoing_data_update
        # print("packet ", packet_type, ", ongoing:",ongoing_data_update)
        # print("#######################################")
        # print("packet type:", packet_type, "reference_id:", reference_id, "ongoing_data_update:", ongoing_data_update)
        # print("#######################################")

        if reference_id == 99: # IMU9 Data
            if packet_type == PACKET_TYPE_DATA:
                # print("PACKET_TYPE_DATA")
                # Store 1st part of the incoming data
                ongoing_data_update = d

            elif packet_type == PACKET_TYPE_DATA_PART2:
                # print("PACKET_TYPE_DATA_PART2. len:",len(data))

                # Create combined DataView that contains the whole data packet
                # (skip type_id + ref num of the data_part2)
                d = DataView( ongoing_data_update.array + data[2:])
                ongoing_data_update = None

                # Dig data from the binary
                # msg = "Data: offset: {}, len: {}".format(d.get_uint_32(2), len(d.array))
                timestamp = d.get_uint_32(2)
                msg_row = {}

                for i in range(0,8):
                    # Interpolate timestamp within the data notification
                    row_timestamp = timestamp + int(i*1000/104)
                    ## IMU9 package starts with timestamp and then three arrays (len 8*4 bytes) of xyz's
                    ## Each "row" therefore starts (3*4 bytes after each other interleaving to acc, gyro and magn)
                    offset = 6 + i * 3* 4
                    skip = 3*8*4

                    msg_row = "{},{:.2f},{:.2f},{:.2f},{:.2f},{:.2f},{:.2f},{:.2f},{:.2f},{:.2f}".format(row_timestamp
                                                                ,  d.get_float_32(offset)
                                                                ,  d.get_float_32(offset+4)
                                                                ,  d.get_float_32(offset+8)
                                                                ,  d.get_float_32(offset+skip+0)
                                                                ,  d.get_float_32(offset+skip+4)
                                                                ,  d.get_float_32(offset+skip+8)
                                                                ,  d.get_float_32(offset+2*skip+0)
                                                                ,  d.get_float_32(offset+2*skip+4)
                                                                ,  d.get_float_32(offset+2*skip+8))

                    # queue message for later consumption (output)
                    await queue.put(msg_row)

        if reference_id == 100: # ECG Data
            payload = DataView(d.array[2:])
            if packet_type == 1:
                # COMMAND_RESPONSE
                await handle_command_response(payload)
            elif packet_type == 2:
                # DATA
                if payload.length() == 68:
                    await handle_ecg_data_notification(payload)
                else:
                    await handle_default_data_notification(payload)
            else:
                print("unknown response code:", packet_type)

    if found:
        async with BleakClient(address, disconnected_callback=disconnect_callback) as client:

            # Add signal handler for ctrl+c
            signal.signal(signal.SIGINT, raise_graceful_exit)
            signal.signal(signal.SIGTERM, raise_graceful_exit)
           
            # Start notifications and subscribe to acceleration @ 13Hz
            logger.info("Enabling notifications")
            await client.start_notify(NOTIFY_CHARACTERISTIC_UUID, notification_handler)
            logger.info("Subscribing datastream")
            await client.write_gatt_char(WRITE_CHARACTERISTIC_UUID, bytearray([1, 99])+bytearray("/Meas/IMU9/104", "utf-8"), response=True)
            ###############################
            await client.write_gatt_char(WRITE_CHARACTERISTIC_UUID,bytearray([1, 100]) + bytearray("/Meas/ECG/250", "utf-8"), response=True)
            ###############################
            # Run until disconnect event is set
            await disconnected_event.wait()
            logger.info(
                "Disconnect set by ctrl+c or real disconnect event. Check Status:")

            # Check the conection status to infer if the device disconnected or crtl+c was pressed
            status = client.is_connected
            logger.info("Connected: {}".format(status))

            # If status is connected, unsubscribe and stop notifications
            if status:
                logger.info("Unsubscribe")
                await client.write_gatt_char(WRITE_CHARACTERISTIC_UUID, bytearray([2, 99]), response=True)
                logger.info("Stop notifications")
                await client.stop_notify(NOTIFY_CHARACTERISTIC_UUID)
            
            # Signal consumer to exit
            await queue.put(None)
            
            await asyncio.sleep(1.0)

    else:
        # Signal consumer to exit
        await queue.put(None)
        print("Sensor end with:" + end_of_serial, "not found!\nExiting")
        return




async def main(end_of_serial: str):
    global COMPUTER_NAME, TASK_NAME, SUB_ID
    
    
    COMPUTER_NAME = sys.argv[2]
    TASK_NAME = sys.argv[3]
    SUB_ID = sys.argv[4]
    SERVER_ADDRESS = ('10.10.1.2', 65430)
    print('Opening Socket ...')
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(SERVER_ADDRESS) 
    print('Opened Socket successfully')
    
    queue = asyncio.Queue()
    client_task = run_ble_client(end_of_serial, queue)
    consumer_task = run_queue_consumer(client_socket, queue)
    
    await asyncio.gather(client_task, consumer_task)   
    
    client_socket.close()
    logger.info("Main method done.")

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python script.py <end_of_sensor_series> <COMPUTER_NAME> <TASK_NAME> <USERNAME>")
        sys.exit(1)
    
    END_OF_SERIAL = sys.argv[1]
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main(END_OF_SERIAL))