import socket 
import json 
import threading 
import matplotlib.pyplot as plt 


SERVER_IP = socket.gethostbyname(socket.gethostname())  # get the server's ip 
SERVER_CONNECTION_PORT = 65430 # get the port we will be connecting from
DATA_SIZE = 2048 # how much data we should read
EXCPECTED_CONNECTIONS = 4 # how many computers will be sending data 
NUM_POINTS_TO_GRAPH = 750 # 3 seconds worth of data

# will track data from clients that connect
client_data_history = {}

def buffer_to_json(data):
    """
        The buffer can be filled with a bunch of json objects.
        This will parse through the buffer and seperate json objects 
        into a list
    """

    # creates list of dictionary like string 
    delimiter = "}" 
    data =  [json.loads(x+delimiter) for x in data.split(delimiter) if x] # creates list of json objects 
    return data 

def handle_client(client_socket, client_address):
    """
        Handles communcation 
        between server and client 

        Servicer 
    """
    try: 
        while True:
            
            # read from socket 
            data = client_socket.recv(DATA_SIZE)
            if not data:
                continue
                
            data = data.decode('utf-8') # decode byte string so we can parse it 
            
            # parse through string (should be formatted as json)
            json_data_list = buffer_to_json(data)

            # loop through all json entries 
            for entry in json_data_list:

                # Check who connected, and setup tracking for this computer  
                comp_name = entry["Computer_name"]

                # add computer name to dictionary so we can store all data that comes in the future  
                if comp_name not in client_data_history.keys():
                    client_data_history[comp_name] = {}
                    client_data_history[comp_name]['ecg_data']  = []
                    client_data_history[comp_name]['eda_data']  = []
                    client_data_history[comp_name]['Pupil_left'] = []


                data_type = entry['data_type'] # Data type tells us what fields we should check for 

                if data_type == "Pupil_Data":

                    # get sent over pupil data 
                    pupil_diam = entry['Pupil_left']

                    # truncate old data 
                    if len(client_data_history[comp_name]['Pupil_left']) > NUM_POINTS_TO_GRAPH* 2:
                        client_data_history[comp_name]['Pupil_left']  = client_data_history[comp_name]['Pupil_left'][-NUM_POINTS_TO_GRAPH:]
                    
                    # add new pupil data to tracking list 
                    client_data_history[comp_name]['Pupil_left'].append(pupil_diam)
                elif data_type == "Heart_Data":

                    # get sent over heart data 
                    ecg_data = entry['ecg_data']
                    eda_data = entry['eda_data']

                    # ensure tracking lists arent taking up too much memory. Once we have double the points we want to display, clear out old half of list 
                    if len(client_data_history[comp_name]['ecg_data']) > NUM_POINTS_TO_GRAPH* 2 or len(client_data_history[comp_name]['eda_data']) > NUM_POINTS_TO_GRAPH * 2:
                        client_data_history[comp_name]['ecg_data']  = client_data_history[comp_name]['ecg_data'][-NUM_POINTS_TO_GRAPH:]
                        client_data_history[comp_name]['eda_data']  = client_data_history[comp_name]['eda_data'][-NUM_POINTS_TO_GRAPH:]

                    # add data to the tracking list 
                    client_data_history[comp_name]['ecg_data'].append(ecg_data)
                    client_data_history[comp_name]['eda_data'].append(eda_data)

    except KeyboardInterrupt:
        return

def plot_function():
    fig, axes = plt.subplots(nrows =EXCPECTED_CONNECTIONS  , ncols = 3, figsize=(10, 10))

    plt.ion()

    while True:
        fig.show()
        fig.canvas.draw()

        # GO THROUGH EACH CONNECTION AND PLOT DATA        
        for i, connection in enumerate(client_data_history.keys()):

            ecg_data = client_data_history[connection]["ecg_data"][-NUM_POINTS_TO_GRAPH:]
            eda_data = client_data_history[connection]["eda_data"][-NUM_POINTS_TO_GRAPH:]
            pupil_data = client_data_history[connection]['Pupil_left'][-NUM_POINTS_TO_GRAPH:]


            
            # plot ecg data
            axes[i, 0].clear()
            axes[i, 0].set_title("{} ECG".format(connection))
            axes[i, 0].plot(ecg_data)
      
            # plot eda data 
            axes[i, 1].clear()
            axes[i, 1].set_title("{} EDA".format(connection))
            axes[i, 1].plot(eda_data)

            # plot pupil data 
            axes[i, 2].clear()
            axes[i, 2].set_title("{} Pupil Diameter".format(connection))
            axes[i, 2].plot(pupil_data)
                     

        fig.canvas.draw()
        fig.tight_layout()
        plt.pause(0.001)
   
def start_server():
    if SERVER_CONNECTION_PORT < 20000:
        print("Port given needs to be greater than 20000")
        return 


    print("Starting Server at {}".format(SERVER_IP))

    # handle plotting 
    plot_handler = threading.Thread(target=plot_function)
    plot_handler.start()


    # create the socket object
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # bind socket object to the actual socket it should listen from 
    server_socket.bind((SERVER_IP, SERVER_CONNECTION_PORT))
    server_socket.listen()


    while True: 
    
        # wait for a connection from a client
        client_socket, client_address = server_socket.accept()
        print("Got connection from client at {}".format(client_address))
        # service this connection 
        listen = threading.Thread(target=handle_client, args=(client_socket, client_address, ))
        listen.start()
        

if __name__ == "__main__":
    start_server()