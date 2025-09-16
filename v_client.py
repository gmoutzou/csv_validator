#
# project: CSV Validator
#
# Client
#
# georgios mountzouris 2025 (gmountzouris@efka.gov.gr)
#

import os
import json
import socket
import threading
import pandas as pd
import v_utilities as util
#from tqdm import tqdm


IP = socket.gethostbyname(socket.gethostname())
PORT = 4456
ADDR = (IP, PORT)
SIZE = 1024
STRINGCHUNKSIZE = 512
FORMAT = "utf-8"
anomalies_dict = {}
status_result = []
c = threading.Condition()

def handle_server(addr, engine, df_string, xml_rules, cursor, chunk_size):
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #server_socket.settimeout(3)
        server_socket.connect(addr)

        """ Step #1 """
        # Sending the cursor to server. """
        try:
            server_socket.send(("@CURSOR#" + str(cursor) + "@").encode(FORMAT))
            msg = server_socket.recv(SIZE).decode(FORMAT)
        except Exception as e:
            print(f"Error while sending the cursor to server: {repr(e)}")

        """ Step #2 """
        # Sending the chunk size to server. """
        try:
            server_socket.send(("@CHUNK-SIZE#" + str(chunk_size) + "@").encode(FORMAT))
            msg = server_socket.recv(SIZE).decode(FORMAT)
        except Exception as e:
            print(f"Error while sending the chunk size to server: {repr(e)}")

        """ Step #3 """
        # Sending ruleset to the server.
        try:
            server_socket.send("@RULES-START@".encode(FORMAT))
            msg = server_socket.recv(SIZE).decode(FORMAT)
            #print(f"SERVER: {msg}")
            for i in range(0, len(xml_rules), STRINGCHUNKSIZE):
                data = xml_rules[i:i+STRINGCHUNKSIZE]
                if not data:
                    break
                server_socket.send(data.encode(FORMAT))
                msg = server_socket.recv(SIZE).decode(FORMAT)
            server_socket.send("@RULES-END@".encode(FORMAT))
        except Exception as e:
            print(f"Error while sending ruleset to the server: {repr(e)}")

        """ Step #4 
        # Sending the dataframe to the server.
        try:
            server_socket.send("@DATAFRAME-START@".encode(FORMAT))
            msg = server_socket.recv(SIZE).decode(FORMAT)
            #print(f"SERVER: {msg}")
            for i in range(0, len(df_string), STRINGCHUNKSIZE):
                data = df_string[i:i+STRINGCHUNKSIZE]
                if not data:
                    break
                server_socket.send(data.encode(FORMAT))
                msg = server_socket.recv(SIZE).decode(FORMAT)
            server_socket.send("@DATAFRAME-END@".encode(FORMAT))
        except Exception as e:
            print(f"Error while sending the dataframe to server: {repr(e)}")
        """

        """ Step #5 """
        # Receive anomalies from server.
        try:
            anomalies_json = ""
            server_socket.send("@FIRE@".encode(FORMAT))
            msg = server_socket.recv(SIZE).decode(FORMAT)
            if msg == "@ANOMALIES-START@":
                while True:
                    data = server_socket.recv(SIZE).decode(FORMAT)
                    if not data or data == "@ANOMALIES-END@":
                        break
                    anomalies_json += data
                    server_socket.send("Anomalies chunk received.".encode(FORMAT))
            anomalies_dict = json.loads(anomalies_json)
            try:
                engine.anomaly_detection(column=None, result=anomalies_dict, is_dictionary=True)
            except Exception as e:
                print(f"Error while running anomaly detection: {repr(e)}")
        except Exception as e:
            print(f"Error while receiving anomalies from server: {repr(e)}")

        """ Step #6 """
        # Sending close message to the server and closing the connection.
        server_socket.send("@CLOSE@".encode(FORMAT))
        server_socket.close()
    except Exception as e:
        print(f"Error while handling server connection: {repr(e)}")

def handle_self_server():
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.connect(ADDR)
        server_socket.send("@CLOSE@".encode(FORMAT))
        # Closing the connection
        server_socket.close()
    except Exception as e:
        print(f"Error while handling self server connection: {repr(e)}")

def handle_server_status(addr, status_result):
    success_flag = False
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.settimeout(3)
        server_socket.connect(addr)
        server_socket.send("@STATUS@".encode(FORMAT))
        status = server_socket.recv(SIZE).decode(FORMAT)
        if status == "200":
            success_flag = True
            server_socket.send("@CLOSE@".encode(FORMAT))
        # Closing the connection
        server_socket.close()
    except Exception as e:
        print(f"Error while handling server status: {repr(e)}")
    status_result.append(success_flag)

def main(engine, server_list, chunk, dummy=False, status_check=False):
    if status_check:
        status_result.clear()
        ADDR = (server_list[0], PORT)
        thread = threading.Thread(target=handle_server_status, args=(ADDR, status_result))
        thread.start()
        thread.join()
        return status_result[0]
    else:
        if dummy:
            handle_self_server()
        else:
            xml_rules = util.export_to_xml_template(filename=None, engine=engine, to_string=True)
            for i, server_ip in enumerate(server_list):
                ADDR = (server_ip, PORT)
                #df_string = engine.df[i*chunk:(i*chunk)+chunk].to_csv(sep=';', encoding='utf-8', header=True, index=False)
                thread = threading.Thread(target=handle_server, args=(ADDR, engine, None, xml_rules, i*chunk, chunk))
                thread.start()
                thread.join()
