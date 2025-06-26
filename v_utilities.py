#
# project: CSV Validator
#
# Vaidation Utilities
#
# georgios mountzouris 2025 (gmountzouris@efka.gov.gr)
#

import io, os
import csv
import pandas as pd
import numpy as np
import requests
import xml.etree.ElementTree as ET
from v_pgdev import Pgdev
from xlsxwriter.color import Color

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
    return box
    
def print_result(anomalies):
    print_msg_box('Validation check result')
    for k, v in anomalies.items():
        print(k)
        for val in v:
            print('\t-> Row: ' + str(val[0]) + '\tValue: ' + str(val[1]))

def get_result(anomalies):
    total = 0
    result = '=======================\nValidation check result\n=======================\n'
    result += '\n-----------------------'
    for k, v in anomalies.items():
        inv = len(v)
        total += inv
        result += '\n[' + k + '] invalid values: ' + str(inv)
    result += '\n-----------------------'
    for k, v in anomalies.items():
        result += '\n' + k + '\n'
        for val in v:
            result += '-> Row: ' + str(val[0]) + ', Value: ' + str(val[1]) + '\n'
    result += '-----------------------\n'
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
    
def df_to_xlsx(filename, df, anomalies):
    if filename:
        columns = get_df_columns(df)
        with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Sheet1')
            workbook = writer.book
            worksheet = writer.sheets["Sheet1"]
            (max_row, max_col) = df.shape
            cell_format = workbook.add_format({"bg_color": Color("#FFFF00")})
            cell_format.set_bold(True)
            for k, v in anomalies.items():
                col = columns.index(k)
                for val in v:
                    row = val[0]
                    value = val[1]
                    worksheet.write(row, col, value, cell_format)
            worksheet.set_column(0, max_col - 1, 15)

def get_db_import_statements(pgconf):
    rows = []
    with Pgdev(pgconf) as pgdev:
        sql = "SELECT * FROM %s.modules ORDER BY id asc;" % (pgconf["dbschema"])
        rows = pgdev.fetch_data_all(sql)
    return rows
    
def get_db_rules(pgconf):
    rows = []
    with Pgdev(pgconf) as pgdev:
        sql = "SELECT * FROM %s.rules ORDER BY name asc;" % (pgconf["dbschema"])
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

def get_version_info(url):
    version_info = None
    try:
        r = requests.get(url)
        version_info = r.json()
    except:
        pass
    return version_info

def get_selected_rule_info(rule):
    if rule:
        column = ""
        name = ""
        vr = ""
        info = rule.split(") ", 1)[1]
        info = info.split(" -> ", 1)
        column = info[0]
        info = info[1].split(": ", 1)
        name = info[0]
        if len(info) > 1:
            vr = info[1]
        return column, name, vr
    else:
        return ()

def export_to_xml(filename, engine):
    root = ET.Element("rules")
    for i, r in enumerate(engine.rules):
        rule = ET.SubElement(root, "rule")
        ET.SubElement(rule, "column_to_check").text = engine.columns_to_check[i]
        ET.SubElement(rule, "rule_name").text = r.name
        vr = ET.SubElement(rule, "value_range")
        for v in engine.acceptable_values[i]:
            ET.SubElement(vr, "value").text = v

    tree = ET.ElementTree(root)
    #xmlstr = ET.tostring(root, encoding='utf8')
    #print(xmlstr)
    ET.indent(tree, space="\t", level=0)
    tree.write(filename, encoding='utf-8', xml_declaration=True)

def import_from_xml(filename):
    xml_rules = []
    tree = ET.parse(filename)
    root = tree.getroot()
    for rule in root.findall('rule'):
        column_to_check = rule.find('column_to_check').text
        rule_name = rule.find('rule_name').text
        vr = rule.find('value_range')
        values = []
        for v in vr:
            values.append(v.text)
        xml_rules.append((column_to_check, rule_name, values))
    return xml_rules
