#!/usr/bin/env python
# coding: utf-8

# In[3]:
import csv
import sys
import tobii_research as tr
import time
import datetime
import serial
import socket
import json
import sys


if len(sys.argv) != 4:
    print("Usage: python final_eye_tracking.py <COMPUTER_NAME> <TASK_NAME> <USERNAME>")
    sys.exit(1)

COMPUTER_NAME = sys.argv[1]
TASK_NAME = sys.argv[2]
user_name = sys.argv[3]
SERVER_ADDRESS = ('10.10.1.2', 65430)

#create socket and send data 
print('Opening Socket ...')
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(SERVER_ADDRESS) 
print('Opened Socket successfully')


# Find and connect to the eye tracker
eyetrackers = tr.find_all_eyetrackers()
eyetracker = eyetrackers[0]
print(eyetracker)


# user_name=input("Enter the subject ID:")
# print(user_name)


timestamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
filename=f"{user_name}_{TASK_NAME}_{timestamp}_eye.csv"
prev_timestamp = None


# Define the callback function for Tobii stream
def gaze_data_callback(gaze_data):
    #print("inside_fucntion")
    global prev_timestamp

    
    timestamp = tr.get_system_time_stamp()
    date_time1 = round(time.time()*1000)
    if prev_timestamp is not None:
        time_diff = (timestamp - prev_timestamp)/1000
    prev_timestamp = timestamp
    date_time2=date_time1+time_diff
    x, y = gaze_data['left_gaze_point_on_display_area']
    a = gaze_data['left_pupil_diameter']
    b = gaze_data['right_pupil_diameter']
    
    json_data = {}
    json_data['Computer_name'] = COMPUTER_NAME 
    json_data['data_type'] = "Pupil_Data"
    json_data['Subject_id'] = user_name
    json_data['Game_type'] = TASK_NAME
    json_data['Timestamp'] = date_time2
    json_data['Gaze_X'] = x
    json_data['Gaze_Y'] = y
    json_data['Pupil_left'] = a
    json_data['Pupil_right'] = b
    print(json_data)
    json_data = json.dumps(json_data).encode('utf-8')
    client_socket.sendall(json_data)
     
    # print('x:{x},y:{y}'.format(x=x,y=y))
    # Write the gaze data to the text file
    gaze_data_file.write(f"{COMPUTER_NAME},{user_name},{TASK_NAME},{date_time2},{x},{y},{a},{b}\n")
    #print("row written")
    
    #print('Computer_name: {pc_name}, Subject_id:{name}, Game_type:{task_name}, Timestamp: {timestamp}, Gaze point: ({x}, {y}) , Pupil Diameter : ({a} , {b})'.format(pc_name = COMPUTER_NAME,name=user_name, task_name=TASK_NAME, timestamp=date_time2 ,x=x, y=y ,a=a ,b=b))



# Open the text file in append mode
with open(filename,'a') as gaze_data_file: 
    gaze_data_file.write(f"Computer_name,Subject_id,Game_type,Timestamp,Gaze_X,Gaze_Y,Pupil_left,Pupil_right\n")
    gaze_data_file.flush()
    
    eyetracker.subscribe_to(tr.EYETRACKER_GAZE_DATA, gaze_data_callback, as_dictionary=True)
    
    is_running = True
    while is_running:
        try:
            input()
        except KeyboardInterrupt:
            break
            
    client_socket.close()
    gaze_data_file.flush()
    eyetracker.unsubscribe_from(tr.EYETRACKER_GAZE_DATA, gaze_data_callback)
