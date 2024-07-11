import csv
import json
import pandas as pd
import numpy as np
import psycopg2
import os
import shutil


CURRENT_DIR = os.getcwd()
DATA_DIR = CURRENT_DIR + '\..\..\Data'

SAVE_DATA_DIR = DATA_DIR + '\\Backup'
if not os.path.exists(SAVE_DATA_DIR):
    os.makedirs(SAVE_DATA_DIR)


list_file = []
list_file_save = []
for file in os.listdir(DATA_DIR):
    file_path = os.path.abspath(os.path.join(DATA_DIR,file))
    file_save_path = os.path.abspath(os.path.join(SAVE_DATA_DIR,file))
    if '_eye.csv' in file_path:
        list_file.append(file_path)
        list_file_save.append(file_save_path)
    

    
DATABASE = {
    'dbname': 'cognitive_battery',
    'user': 'postgres',
    'password': 'postgres',
    'host': '10.10.1.2',
    'port': '5432'
}
conn = psycopg2.connect(**DATABASE)



for index,file_path in enumerate(list_file):
    print(file_path)
    #user_id = filename[:4]  # Extract the first four characters from the filename as the user ID
    #data_dict = {'user_id': user_id}  # Initialize a dictionary with user ID
    cursor = conn.cursor()
    df = pd.read_csv(file_path)
    df['Gaze_X']=df['Gaze_X'].fillna("None")
    df['Gaze_Y']=df['Gaze_Y'].fillna("None")
    df['Pupil_right']=df['Pupil_right'].fillna("None")
    df['Pupil_left']=df['Pupil_left'].fillna("None")

    data_dict = df.to_dict(orient = 'list')

    subject_id = data_dict['Subject_id'][0]
    game_type = data_dict['Game_type'][0]

    data_dict['Computer_name'] = data_dict['Computer_name'][0]
    data_dict['Game_type']=data_dict['Game_type'][0]

    del(data_dict['Computer_name'])
    del(data_dict['Subject_id'])
    del(data_dict['Game_type'])

    # Convert dictionary to JSON
    json_data = json.dumps(data_dict, indent=4)
    # Print the JSON data
    cursor.execute("""INSERT INTO eyes_data (subject_id,eye_data,game_type)VALUES (%s, %s,%s);""", (subject_id,json_data,game_type))
    shutil.move(file_path, list_file_save[index])
    print("written to database")

    conn.commit()
    cursor.close()
conn.close()