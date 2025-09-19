#
# project: CSV Validator
#
# Server
#
# georgios mountzouris 2025 (gmountzouris@efka.gov.gr)
#

import json
import time
import socket
import hashlib
import pandas as pd
import v_utilities as util
import v_rule_library as vlib
#from tqdm import tqdm
from io import StringIO


IP = socket.gethostbyname(socket.gethostname())
PORT = 4456
ADDR = (IP, PORT)
SIZE = 1024
STRINGCHUNKSIZE = 512
FORMAT = "utf-8"
RUNFLAG = True

def handle_rules(client_socket, engine):
    success_flag = True
    xml_rules_string = ""
    try:
        while True:
            client_socket.send("Waiting Rules.".encode(FORMAT))
            data = client_socket.recv(SIZE*4).decode(FORMAT)
            if not data or data == "@RULES-END@":
                break
            xml_rules_string += data
        if xml_rules_string:
            root_attrib, xml_rules_list = util.import_from_xml_template(xml_rules_string, from_string=True)
            op = str(None)
            if "logical_operator" in root_attrib:
                op = root_attrib['logical_operator']
            if op == "AND" or op == "OR" or op == "XOR":
                engine.logical_operator = op
            for r in vlib.get_rule_library():
                for x in xml_rules_list:
                    if r.name == x[1]:
                        engine.add_rule(rule=r, column=x[0], value_range=x[2])    
    except Exception as e:
        print(f" --  Error while handling rules from client: {repr(e)}")
        success_flag = False
    return success_flag

def handle_dataframe(client_socket, engine):
    success_flag = True
    df_string = ""
    try:
        client_socket.send("Waiting dataframe.".encode(FORMAT))
        while True:
            data = client_socket.recv(SIZE).decode(FORMAT)
            if not data or data == "@DATAFRAME-END@":
                break
            df_string += data
            client_socket.send("Dataframe chunk received.".encode(FORMAT))
    except Exception as e:
        print(f" -- Error while handling dataframe from client: {repr(e)}")
        success_flag = False
    if df_string:
        df = pd.read_csv(StringIO(df_string), sep=';', header='infer', encoding='utf-8', dtype=object)
        engine.df = util.get_df_as_type_string(df)
    return success_flag

def fire_all_client_rules(client_socket, engine, callback):
    success_flag = True
    anomalies_json = "{}"
    try:
        if engine and len(engine.rules) > 0:
            try:
                start = time.time()
                engine.fire_all_rules()
                end = time.time()
                if callback:
                    callback(engine.data_cursor + 1, engine.data_cursor + engine.rows, end - start)
                anomalies_json = json.dumps(engine.anomalies)
            except Exception as e:
                print(f" -- Error while fire client rules and get the result in json: {repr(e)}")
        client_socket.send("@ANOMALIES-START@".encode(FORMAT))
        for i in range(0, len(anomalies_json), STRINGCHUNKSIZE*4):
            data = anomalies_json[i:i+(STRINGCHUNKSIZE*4)]
            if not data:
                break
            client_socket.send(data.encode(FORMAT))
            msg = client_socket.recv(SIZE).decode(FORMAT)
        client_socket.send("@ANOMALIES-END@".encode(FORMAT))
    except Exception as e:
        print(f" -- Error while handle anomalies: {repr(e)}")
        success_flag = False
    return success_flag

def handle_client(client_socket, addr, engine, callback):
    try:
        """ Receiving from client. """
        success_flag = True
        while success_flag:
            data = client_socket.recv(SIZE).decode(FORMAT)
            if data == "@STATUS@":
                client_socket.send("200".encode(FORMAT))
            elif data == "@DATAFRAME-HASH@":
                df_hash = hashlib.sha256(engine.df.to_json().encode()).hexdigest()
                client_socket.send(df_hash.encode(FORMAT))
            elif data == "@RULES-START@":
                success_flag = handle_rules(client_socket, engine)
            elif data == "@DATAFRAME-START@":
                success_flag = handle_dataframe(client_socket, engine)
            elif data == "@FIRE@":
                success_flag = fire_all_client_rules(client_socket, engine, callback)
            elif "CURSOR#" in data and "CHUNK#" in data:
                items = data.split('@')
                engine.clear()
                engine.data_cursor = engine.result_cursor = int(items[0].split('#')[1])
                engine.rows = int(items[1].split('#')[1])
                client_socket.send("Cursor & chunk size received.".encode(FORMAT))
            elif data == "@CLOSE@":
                break
    except Exception as e:
        print(f" -- Error while handling client connection: {repr(e)}")
    finally:
        #engine.df = None
        #engine.clear()
        engine.parallel_init()
        client_socket.close()
        print(f" -- Connection to client ({addr[0]}:{addr[1]}) was closed")

def main(engine, callback=None):
    try:
        """ Creating a TCP server socket """
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(ADDR)
        server.listen()
        print(f"[+] Server listening on {IP}:{PORT}")
        while RUNFLAG:
            #print(f"[+] Waiting for client connection...")
            client_socket, addr = server.accept()
            """ Accepting the connection from the client. """
            print(f" -- Client connected from {addr[0]}:{addr[1]}")
            # handle the client
            handle_client(client_socket, addr, engine, callback)
    except Exception as e:
        print(f"An error has occured: {repr(e)}")
    finally:
        """ Server socket termination. """
        #engine.df = None
        #engine.clear()
        engine.parallel_init()
        server.close()
        print(f"[+] Server terminated")
