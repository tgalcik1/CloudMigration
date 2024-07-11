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
import struct
import sys
import csv
import time
import serial
from datetime import datetime
import socket
import json
import threading

# Global variables
COMPUTER_NAME = None
TASK_NAME = None
SUB_ID = None
SERVER_ADDRESS = ('localhost', 50500)
CONTROL_SERVER_ADDRESS = ('localhost', 50501)
START_TIME_UNIX = {}
START_TIME_SENSOR = {}

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
        self.array = array
        self.bytes_per_element = 1

    def __get_binary(self, start_index, byte_count, signed=False):
        integers = [self.array[start_index + x] for x in range(byte_count)]
        _bytes = [integer.to_bytes(self.bytes_per_element, byteorder='little', signed=signed) for integer in integers]
        binary_result = b''.join(_bytes)
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
    logger.info('You pressed Ctrl+C! exiting...')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def create_socket():
    while True:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(SERVER_ADDRESS)
            print(f"Connected to {SERVER_ADDRESS}")
            return sock
        except socket.error as e:
            print(f"Connection failed: {e}. Retrying in 5 seconds...")
            time.sleep(5)


async def run_queue_consumer(client_socket, queue: asyncio.Queue):
    global COMPUTER_NAME, TASK_NAME, SUB_ID, START_TIME_UNIX, START_TIME_SENSOR

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

                if data_type not in START_TIME_UNIX:
                    # Write the first time
                    START_TIME_UNIX[data_type] = round(time.time() * 1000)
                    START_TIME_SENSOR[data_type] = parsed_row[0]

                    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
                    header = f"'Computer_name','Subject_id','Game_type','Timestamp','acc_x','acc_y','acc_z','gyro_x','gyro_y','gyro_z','magn_x','magn_y','magn_z'".encode('utf-8')
                    client_socket.sendall(header)

                # Writing data
                base_timestamp = parsed_row[0] - START_TIME_SENSOR[data_type] + START_TIME_UNIX[data_type]  # Convert from sensor clock to Unix timestamp in milliseconds
                row_data = [COMPUTER_NAME, SUB_ID, TASK_NAME, base_timestamp] + parsed_row[1:]

                # Sending data to websocket
                json_data = {
                    'Computer_name': COMPUTER_NAME,
                    'data_type': "IMU9",
                    'Subject_id': SUB_ID,
                    'Game_type': TASK_NAME,
                    'Timestamp': base_timestamp,
                    'acc_x': row_data[4],
                    'acc_y': row_data[5],
                    'acc_z': row_data[6],
                    'gyro_x': row_data[7],
                    'gyro_y': row_data[8],
                    'gyro_z': row_data[9],
                    'magn_x': row_data[10],
                    'magn_y': row_data[11],
                    'magn_z': row_data[12]
                }
                json_data = json.dumps(json_data).encode('utf-8')

                try:
                    client_socket.sendall(json_data)
                except socket.error as e:
                    print(f"Connection lost: {e}. Reconnecting...")
                    client_socket.close()
                    client_socket = create_socket()
                    client_socket.sendall(json_data)

            elif isinstance(data, dict):
                # Assuming it's ECG data
                data_type = data.pop('type')
                if data_type not in START_TIME_UNIX:
                    # Write data first time
                    START_TIME_UNIX[data_type] = round(time.time() * 1000)
                    START_TIME_SENSOR[data_type] = data['timestamp']

                    header = "'Computer_name','Subject_id','Game_type','Timestamp','ecg_data'".encode('utf-8')
                    client_socket.sendall(header)

                # Writing data
                base_timestamp = data['timestamp'] - START_TIME_SENSOR[data_type] + START_TIME_UNIX[data_type]  # Convert from sensor clock to Unix timestamp in milliseconds
                for index, value in enumerate(data['samples']):
                    current_timestamp = base_timestamp + index * 4

                    # Sending data to websocket
                    json_data = {
                        'Computer_name': COMPUTER_NAME,
                        'data_type': "Heart_Data",
                        'Subject_id': SUB_ID,
                        'Game_type': TASK_NAME,
                        'Timestamp': current_timestamp,
                        'ecg_data': value
                    }
                    json_data = json.dumps(json_data).encode('utf-8')

                    try:
                        client_socket.sendall(json_data)
                    except socket.error as e:
                        print(f"Connection lost: {e}. Reconnecting...")
                        client_socket.close()
                        client_socket = create_socket()
                        client_socket.sendall(json_data)


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

        # Data is 16 samples of uint32
        data = {
            "type": "ECG",
            "timestamp": ts,
            "samples": [payload.get_int_32(4 + i * 4) for i in range(16)]
        }
        # Queue message for later consumption
        await queue.put(data)

    async def handle_default_data_notification(payload):
        msg = "Unknown data: {} bytes".format(payload.length())
        await queue.put(msg)

    async def handle_command_response(payload):
        print("Command response:", payload.array)

    async def notification_handler(sender, data):
        """Simple notification handler which prints the data received."""
        d = DataView(data)

        packet_type = d.get_uint_8(0)
        reference_id = d.get_uint_8(1)

        global ongoing_data_update

        if reference_id == 99:  # IMU9 Data
            if packet_type == PACKET_TYPE_DATA:
                ongoing_data_update = d

            elif packet_type == PACKET_TYPE_DATA_PART2:
                d = DataView(ongoing_data_update.array + data[2:])
                ongoing_data_update = None

                timestamp = d.get_uint_32(2)
                for i in range(0, 8):
                    row_timestamp = timestamp + int(i * 1000 / 104)
                    offset = 6 + i * 3 * 4
                    skip = 3 * 8 * 4

                    msg_row = "{},{:.2f},{:.2f},{:.2f},{:.2f},{:.2f},{:.2f},{:.2f},{:.2f},{:.2f}".format(
                        row_timestamp,
                        d.get_float_32(offset),
                        d.get_float_32(offset + 4),
                        d.get_float_32(offset + 8),
                        d.get_float_32(offset + skip + 0),
                        d.get_float_32(offset + skip + 4),
                        d.get_float_32(offset + skip + 8),
                        d.get_float_32(offset + 2 * skip + 0),
                        d.get_float_32(offset + 2 * skip + 4),
                        d.get_float_32(offset + 2 * skip + 8)
                    )

                    # Queue message for later consumption (output)
                    await queue.put(msg_row)

        if reference_id == 100:  # ECG Data
            payload = DataView(d.array[2:])
            if packet_type == 1:
                await handle_command_response(payload)
            elif packet_type == 2:
                if payload.length() == 68:
                    await handle_ecg_data_notification(payload)
                else:
                    await handle_default_data_notification(payload)
            else:
                print("unknown response code:", packet_type)

    if found:
        async with BleakClient(address, disconnected_callback=disconnect_callback) as client:
            signal.signal(signal.SIGINT, raise_graceful_exit)
            signal.signal(signal.SIGTERM, raise_graceful_exit)

            logger.info("Enabling notifications")
            await client.start_notify(NOTIFY_CHARACTERISTIC_UUID, notification_handler)
            logger.info("Subscribing datastream")
            await client.write_gatt_char(WRITE_CHARACTERISTIC_UUID, bytearray([1, 99]) + bytearray("/Meas/IMU9/104", "utf-8"), response=True)
            await client.write_gatt_char(WRITE_CHARACTERISTIC_UUID, bytearray([1, 100]) + bytearray("/Meas/ECG/250", "utf-8"), response=True)

            await disconnected_event.wait()
            logger.info("Disconnect set by ctrl+c or real disconnect event. Check Status:")

            status = client.is_connected
            logger.info("Connected: {}".format(status))

            if status:
                logger.info("Unsubscribe")
                await client.write_gatt_char(WRITE_CHARACTERISTIC_UUID, bytearray([2, 99]), response=True)
                logger.info("Stop notifications")
                await client.stop_notify(NOTIFY_CHARACTERISTIC_UUID)

            await queue.put(None)
            await asyncio.sleep(1.0)

    else:
        await queue.put(None)
        print("Sensor end with:" + end_of_serial, "not found!\nExiting")
        return


async def main(end_of_serial: str):
    global COMPUTER_NAME, TASK_NAME, SUB_ID

    COMPUTER_NAME = sys.argv[2]
    TASK_NAME = sys.argv[3]
    SUB_ID = sys.argv[4]

    client_socket = create_socket()

    queue = asyncio.Queue()
    client_task = run_ble_client(end_of_serial, queue)
    consumer_task = run_queue_consumer(client_socket, queue)

    try:
        await asyncio.gather(client_task, consumer_task)
    except KeyboardInterrupt:
        print("KeyboardInterrupt received. Exiting...")
    finally:
        client_socket.close()
        logger.info("Main method done.")
        input("Press Enter to exit...")


def control_server():
    global TASK_NAME

    control_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    control_sock.bind(CONTROL_SERVER_ADDRESS)
    control_sock.listen(1)
    print(f"Control server listening on {CONTROL_SERVER_ADDRESS}")

    while True:
        conn, addr = control_sock.accept()
        with conn:
            print(f"Connected by {addr}")
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                new_task = data.decode('utf-8')
                print(f"Updating TASK_NAME to {new_task}")
                TASK_NAME = new_task


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python script.py <end_of_sensor_series> <COMPUTER_NAME> <TASK_NAME> <USERNAME>")
        input("Press Enter to exit...")
        sys.exit(1)

    END_OF_SERIAL = sys.argv[1]
    logging.basicConfig(level=logging.INFO)

    control_thread = threading.Thread(target=control_server)
    control_thread.daemon = True
    control_thread.start()

    asyncio.run(main(END_OF_SERIAL))
