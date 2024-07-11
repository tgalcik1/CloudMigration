import csv
import time
import sys
import serial
from datetime import datetime
import time
import socket
import json



first_save = True

# # Get the COM port and filename from the command line arguments
if len(sys.argv) != 5:
    print("Usage: python script.py <COM_PORT> <COMPUTER_NAME> <TASK_NAME> <USERNAME>")
    sys.exit(1)

com_port = sys.argv[1]
COMPUTER_NAME = sys.argv[2]
TASK_NAME = sys.argv[3]
sub_id = sys.argv[4]
SERVER_ADDRESS = ('10.10.1.2', 65430)

#create socket and send data 
print('Opening Socket ...')
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(SERVER_ADDRESS) 
print('Opened Socket successfully')

timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
filename = f"{sub_id}_{TASK_NAME}_{timestamp}_sensor.csv"


# Configure the serial port and set the appropriate baud rate
print("Opening Serial port ...")
ser = serial.Serial(com_port, baudrate=57600, timeout=1)
ser.close()
ser.open()
ser.flush()
print("Opened Serial port successfully")

timestamps = []
ecg_data = []
eda_data = []


starttime = time.time()


def save_to_file():
    global first_save
    
    print('Writing data to file...')
    
    mode = 'w' if first_save else 'a' 
    
    with open(filename, mode=mode, newline='') as file:
        writer = csv.writer(file)
        
        # Write the headers
        if first_save:
            writer.writerow(['Computer_name','Subject_id','Game_type','Timestamp', 'ecg_data', 'eda_data'])
        
        # Write the data
        for timestamp, data1, data2 in zip(timestamps, ecg_data, eda_data):
            writer.writerow([COMPUTER_NAME,sub_id,TASK_NAME,timestamp, data1, data2])
    
    first_save = False
    print('File Written')

try:
    print('Connected and reading') 
    while True:
        # Read a line from the serial port
        line = ser.readline().decode(errors = 'ignore').strip().split(',')
        #print(line)
      
            # If the line is not empty and has three elements (time and data)
        if line and len(line) == 3:
            # try:
                current_time = float(line[0])/1000 + starttime
                current_ecg = float(line[1])
                current_eda = float(line[2])     
                ecg_data.append(current_ecg)
                eda_data.append(current_eda)
                timestamps.append(current_time)
                
                
                json_data = {}
                json_data['Computer_name'] = COMPUTER_NAME
                json_data['data_type'] = "Heart_Data"    
                json_data['Subject_id'] = sub_id
                json_data['Game_type'] = TASK_NAME
                json_data['Timestamp'] = current_time
                json_data['ecg_data'] = current_ecg
                json_data['eda_data'] = current_eda
                print(json_data)
                json_data = json.dumps(json_data).encode('utf-8')
                
                client_socket.sendall(json_data)
            # Periodically save data to file, for instance every 1000 readings
                if len(timestamps) % 1000 == 0:
                    save_to_file()
                    print('temp data saved')
                    timestamps = []
                    ecg_data = []
                    eda_data = []
            # except:
                # print("got error")
                # continue
except KeyboardInterrupt:
    pass

finally:
    save_to_file()  # Ensure the data is saved one last time
    client_socket.close()
    print("Exiting...")
    ser.flush()
    print("Port flushed")
    ser.close()
    print("Port closed")