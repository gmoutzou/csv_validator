#!/home/dev/anaconda3/envs/tensorflow/bin/python3
"""#!/bin/python3"""
#
# project: CSV Validator
#
# Vaidation Utilities
#
# georgios mountzouris 2025 (gmountzouris@efka.gov.gr)
#

import io
import csv
import pandas as pd
import numpy as np
from v_pgdev import Pgdev

def print_msg_box(msg, indent=1, width=None, title=None):
    """Print message-box with optional title."""
    lines = msg.split('\n')
    space = " " * indent
    if not width:
        width = max(map(len, lines))
    box = f'╔{"═" * (width + indent * 2)}╗\n'  #upper_border
    if title:
        box += f'║{space}{title:<{width}}{space}║\n'  # title
        box += f'║{space}{"-" * len(title):<{width}}{space}║\n'  # underscore
    box += ''.join([f'║{space}{line:<{width}}{space}║\n' for line in lines])
    box += f'╚{"═" * (width + indent * 2)}╝'  #lower_border
    print(box)
    
def print_result(anomalies):
    print_msg_box('Validation check result')
    for k, v in anomalies.items():
        print(k)
        for val in v:
            print('\t-> Row: ' + str(val[0]) + '\tValue: ' + str(val[1]))

def get_result(anomalies):
    total = 0
    result = '-----------------------\nValidation check result\n-----------------------\n'
    for k, v in anomalies.items():
        result += '\n' + k + '\n'
        for val in v:
            total += 1
            result += '-> Row: ' + str(val[0]) + ', Value: ' + str(val[1]) + '\n'
    return total, result

def get_delimiter(filename):
    #read the first line of csv and identify the delimiter
    with open(filename, 'r') as f:
        sniffer = csv.Sniffer()
        dialect = sniffer.sniff(f.readline())
        return dialect.delimiter

def get_dataframe(filename, delimiter=',', header='infer', encoding='utf-8', type=None):
    df = pd.read_csv(filename, sep=delimiter, header=header, encoding=encoding, dtype=type)
    return df

def is_digit(n):
    try:
        float(n)
        return True
    except ValueError:
        return  False

def get_value_range(strval):
    value_range = []
    #strval = strval.strip()
    #strval = strval.replace(" ", "")
    if strval:
        if '~' in strval:
            value_range = strval.split('~')
        elif ',' in strval:
            value_range = strval.split(',')
        else:
            value_range.append(strval)
    return value_range

def get_df_columns(df):
    return list(df)

def get_df_as_type_string(df):
    df = df.replace(np.nan, "")
    columns = get_df_columns(df)
    for c in columns:
        if df.dtypes[c] != object:
            df[c] = df[c].astype("string")
    return df

def csv_data_structure(df, method='describe'):
    if method == 'info':
        buf = io.StringIO()
        df.info(buf=buf)
        return buf.getvalue()
    elif method == 'describe':
        s = df.describe()
        return s.to_string()
    
def get_db_import_statements(pgconf):
    rows = []
    with Pgdev(pgconf) as pgdev:
        sql = "SELECT * FROM %s.modules ORDER BY id asc;" % (pgconf["dbschema"])
        rows = pgdev.fetch_data_all(sql)
    return rows
    
def get_db_rules(pgconf):
    rows = []
    with Pgdev(pgconf) as pgdev:
        sql = "SELECT * FROM %s.rules ORDER BY id asc;" % (pgconf["dbschema"])
        rows = pgdev.fetch_data_all(sql)
    return rows

def get_db_rules_number(pgconf):
    result = 0
    with Pgdev(pgconf) as pgdev:
        sql = "SELECT COUNT(1) FROM %s.rules;" % (pgconf["dbschema"])
        rows = pgdev.fetch_data_all(sql)
        for row in rows:
            result = row[0]
    return result

def add_rule_to_db(pgconf, data):
    with Pgdev(pgconf) as pgdev:
        query = "INSERT INTO " + pgconf["dbschema"] + ".rules (name, description, function_name, function_body) VALUES (%s, %s, %s, %s);" 
        pgdev.crud(query, data)

def delete_rule_from_db(pgconf, data):
    name = data.split(") ", 1)[1]
    with Pgdev(pgconf) as pgdev:
        sql = "SELECT id FROM %s.rules WHERE name = '%s';" % (pgconf["dbschema"], name)
        rows = pgdev.fetch_data_all(sql)
        for row in rows:
            id = row[0]
            query = "DELETE FROM " + pgconf["dbschema"] + ".rules WHERE id = %s;"
            pgdev.crud(query, (id,))

def get_rule_from_db(pgconf, data):
    name = data.split(") ", 1)[1]
    with Pgdev(pgconf) as pgdev:
        sql = "SELECT * FROM %s.rules WHERE name = '%s';" % (pgconf["dbschema"], name)
        rows = pgdev.fetch_data_all(sql)
        return rows[0]
    
def edit_rule_in_db(pgconf, data):
    with Pgdev(pgconf) as pgdev:
        query = "UPDATE " + pgconf["dbschema"] + ".rules SET (name, description, function_name, function_body) = (%s, %s, %s, %s) WHERE id = %s;"
        pgdev.crud(query, data)
