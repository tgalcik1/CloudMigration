#!/usr/bin/env python
# coding: utf-8

import csv
import sys
import tobii_research as tr
import time
import datetime
import serial
import socket
import json

COMPUTER_NAME = sys.argv[1]
TASK_NAME = sys.argv[2]
user_name = sys.argv[3]
SERVER_ADDRESS = ('localhost', 50500)
CONTROL_SERVER_ADDRESS = ('localhost', 50501)
prev_timestamp = None
client_socket = None
isConnectionlost = False

def gaze_data_callback(gaze_data):
    global prev_timestamp, client_socket, isConnectionlost

    timestamp = tr.get_system_time_stamp()
    date_time1 = round(time.time()*1000)
    if prev_timestamp is not None:
        time_diff = (timestamp - prev_timestamp) / 1000
    prev_timestamp = timestamp
    date_time2 = date_time1 + time_diff
    x, y = gaze_data['left_gaze_point_on_display_area']
    a = gaze_data['left_pupil_diameter']
    b = gaze_data['right_pupil_diameter']

    json_data = {
        'Computer_name': COMPUTER_NAME,
        'data_type': "Pupil_Data",
        'Subject_id': user_name,
        'Game_type': TASK_NAME,
        'Timestamp': date_time2,
        'Gaze_X': x,
        'Gaze_Y': y,
        'Pupil_left': a,
        'Pupil_right': b
    }
    json_data = json.dumps(json_data).encode('utf-8')
    try:
        client_socket.sendall(json_data)
    except:
        isConnectionlost = True

def create_socket():
    while True:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(SERVER_ADDRESS)
            print(f"Connected to {SERVER_ADDRESS}")
            return sock
        except socket.error as e:
            try:
                print(f"Connection failed: {e}. Retrying in 5 seconds...")
                time.sleep(5)
            except KeyboardInterrupt:
                print("Exiting ...")
                sys.exit(1)
        except KeyboardInterrupt:
            print("Exiting ...")
            sys.exit(1)

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

def main():
    global prev_timestamp, client_socket, isConnectionlost

    client_socket = create_socket()
    while True:
        try:
            eyetrackers = tr.find_all_eyetrackers()
            eyetracker = eyetrackers[0]
            print(eyetracker)

            timestamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')

            string = f"Computer_name,Subject_id,Game_type,Timestamp,Gaze_X,Gaze_Y,Pupil_left,Pupil_right".encode('utf-8')
            client_socket.sendall(string)
            isConnectionlost = False
            eyetracker.subscribe_to(tr.EYETRACKER_GAZE_DATA, gaze_data_callback, as_dictionary=True)
            
            import threading
            control_thread = threading.Thread(target=control_server)
            control_thread.daemon = True
            control_thread.start()

            while True:
                try:
                    time.sleep(1)
                    if isConnectionlost:
                        break
                except KeyboardInterrupt:
                    client_socket.close()
                    eyetracker.unsubscribe_from(tr.EYETRACKER_GAZE_DATA, gaze_data_callback)
                    input("Press Enter to exit...")
                    return

            client_socket.close()
            eyetracker.unsubscribe_from(tr.EYETRACKER_GAZE_DATA, gaze_data_callback)
        except socket.error as e:
            print(f"Connection lost: {e}. Reconnecting...")
            client_socket.close()
            client_socket = create_socket()

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python final_eye_tracking.py <COMPUTER_NAME> <TASK_NAME> <USERNAME>")
        input("Press Enter to exit...")
        sys.exit(1)
    main()
