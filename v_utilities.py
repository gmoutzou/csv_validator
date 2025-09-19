#
# project: CSV Validator
#
# Vaidation Utilities
#
# georgios mountzouris 2025 (gmountzouris@efka.gov.gr)
#

import io, os, re, sys
import csv
import pandas as pd
import numpy as np
import requests
import netifaces as ni
import xml.etree.ElementTree as ET
import v_common as common
import v_client as client
from v_pgdev import Pgdev
from xlsxwriter.color import Color
from dateutil.parser import parse
from v_outlier_detector import OutlierDetector


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

def header_box(msg, width=100, character='=', centered=True):
    box = ''
    msg_ary = msg.split('\n')
    if centered:
        message = ' '.join(msg_ary[len(msg_ary) // 2:]).center(width, ' ')
    else:
        message = ' '.join(msg_ary[len(msg_ary) // 2:])
    box += character * (width + 4) + '\n'
    if centered:
        box += character + f' {message} ' + character + '\n'
    else:
        box += f'{message}' + '\n'
    box += character * (width + 4) + '\n'
    return box

def print_result(anomalies):
    print_msg_box('Validation check result')
    for k, v in anomalies.items():
        print(k)
        for val in v:
            print('\t-> Row: ' + str(val[0]) + '\tValue: ' + str(val[1]))

def get_result(anomalies):
    total = 0
    #result = '=======================\nValidation check result\n=======================\n'
    result = header_box('Validation check result')
    header = '\n'
    data = '\n'
    if len(anomalies) > 0:
        for k, v in anomalies.items():
            inv = len(v)
            total += inv
            header += header_box(msg='[' + k + '] invalid values: ' + str(inv), width=50, character='-')
            #header += '\n-----------------------'
            data += '\n' + k + '\n'
            for val in v:
                data += '-> Row: ' + str(val[0]) + ', Value: ' + str(val[1]) + '\n'
        result += header + data + '-------\n'
    return total, result

def get_delimiter(filename):
    #read the first line of csv and identify the delimiter
    with open(filename, 'r') as f:
        sniffer = csv.Sniffer()
        dialect = sniffer.sniff(f.readline())
        return dialect.delimiter

def get_dataframe(filename, delimiter=',', header='infer', encoding='utf-8', type=None, jlx_spec=None, fwf_spec=None):
    df = None
    if filename.endswith('.csv'):
        df = pd.read_csv(filename, sep=delimiter, header=header, encoding=encoding, dtype=type)
    elif filename.endswith('.xlsx'):
        df = pd.read_excel(filename, dtype=object)
    elif filename.endswith('.json'):
        df = pd.read_json(filename, dtype=object)
    elif filename.endswith('.jlx'):
        df = jlx2df(filename, jlx_spec)
    else:
        df = fwf2df(filename, fwf_spec)
    return df

def is_digit(n):
    try:
        float(n)
        return True
    except ValueError:
        return False
    
def is_date(string, fuzzy=False):
    try: 
        parse(string, fuzzy=fuzzy)
        return True
    except ValueError:
        return False

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
    
def df2csv(filename, df):
    if filename:
        df.to_csv(filename)
    
def df2xlsx(filename, df, anomalies):
    if filename:
        columns = get_df_columns(df)
        with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Sheet1')
            workbook = writer.book
            worksheet = writer.sheets["Sheet1"]
            (max_row, max_col) = df.shape
            if anomalies:
                cell_format = workbook.add_format({"bg_color": Color("#FFFF00")})
                cell_format.set_bold(True)
                for k, v in anomalies.items():
                    col = columns.index(k)
                    for val in v:
                        row = val[0]
                        value = val[1]
                        worksheet.write(row, col, value, cell_format)
            worksheet.set_column(0, max_col - 1, 15)

def df2json(filename, df):
    if filename:
        df.to_json(filename, orient='records', force_ascii=False)

def df2xml(filename, df):
    if filename:
        df.to_xml(filename, parser='lxml')

def df2html(filename, df):
    if filename:
        html = '''<!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="utf-8">
                        <meta http-equiv="X-UA-Compatible" content="IE=edge">
                        <meta name="viewport" content="width=device-width,initial-scale=1">
                        <title>output</title>
                        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
                    </head>
                    <body>
                    <div class="content-body">
                '''
        html_table = df.to_html(classes='table table-striped table-bordered table-hover')
        html += html_table
        html += '''
                </div>
                <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.min.js"></script>
                </body>
                </html>
                '''
        with open(filename, "w") as f:
            f.write(html)

def df2sql(filename, df):
    sql_create_statement = pd.io.sql.get_schema(df.reset_index(), 'data')
    sql_create_statement += ";\n\n"
    sql_insert_statements = []
    for index, row in df.iterrows():       
        sql_insert_statements.append('INSERT INTO '+ 'data' +' ('+ str(', '.join(df.columns))+ ') VALUES '+ str(tuple(row.values)) + ';\n')
    with open(filename, "w") as f:
        f.write(sql_create_statement)
        f.writelines(sql_insert_statements)

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

def export_to_xml_template(filename, engine, to_string=False):
    root = ET.Element("rules")
    root.set('logical_operator', str(engine.logical_operator))
    for i, r in enumerate(engine.rules):
        rule = ET.SubElement(root, "rule")
        ET.SubElement(rule, "column_to_check").text = engine.columns_to_check[i]
        ET.SubElement(rule, "rule_name").text = r.name
        vr = ET.SubElement(rule, "value_range")
        for v in engine.acceptable_values[i]:
            ET.SubElement(vr, "value").text = v
    tree = ET.ElementTree(root)
    if to_string:
        xmlstr = ET.tostring(root, encoding='utf8')
        return xmlstr.decode("utf-8")
    else:
        ET.indent(tree, space="\t", level=0)
        tree.write(filename, encoding='utf-8', xml_declaration=True)

def import_from_xml_template(source_xml, from_string=False):
    xml_rules = []
    if from_string:
        tree = ET.ElementTree(ET.fromstring(source_xml))
    else:
        tree = ET.parse(source_xml)
    root = tree.getroot()
    for rule in root.findall('rule'):
        column_to_check = rule.find('column_to_check').text
        rule_name = rule.find('rule_name').text
        vr = rule.find('value_range')
        values = []
        for v in vr:
            values.append(v.text)
        xml_rules.append((column_to_check, rule_name, values))
    return root.attrib, xml_rules

def most_frequent_item(List):
    return max(set(List), key=List.count)

def df_preview(df, n):
    return df.head(n).to_string()

def detect_outliers(df, column):
    min_val = -999999.999
    data = df[column].map(lambda x: float(x.replace(',', '.')) if common.is_digit(x.replace(',', '.')) else min_val)
    detector = OutlierDetector(data)
    outliers_and_anomalies = detector.detect_outliers_ensemble_model()
    result = list(zip(df[column].to_list(), outliers_and_anomalies))
    return result

def jlx2df(filename, jl10_spec):
    df = None
    try:
        jl10_spec_dict = {}
        jl10_spec_list = jl10_spec.split('|')
        for r_spec in jl10_spec_list:
            r_spec_list = r_spec.split(':')
            if len(r_spec_list) == 2:
                rid = r_spec_list[0]
                rdata = r_spec_list[1]
                jl10_spec_dict[rid] = rdata
        with open(filename, 'r', encoding='utf-8') as file:
            data = []
            for record in file:
                if record[0] in jl10_spec_dict and '-' not in jl10_spec_dict[record[0]]:
                    col_spec_list = jl10_spec_dict[record[0]].split(',')
                    start = 0
                    rdict = {}
                    for i, c in enumerate(col_spec_list):
                        colname = 'Column-' + str(i)
                        end = start + int(c)
                        coldata = record[start:end]
                        rdict[colname] = coldata
                        start = end
                    data.append(rdict)
            df = pd.DataFrame(data)
    except Exception as e:
        print(repr(e))
    return df

def fwf2df(filename, fwf_spec):
    df = None
    col_spec_list = fwf_spec['specification'].split(',')
    ignored_list = fwf_spec['ignored'].split(',')
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            data = []
            for record in file:
                ignored_record = False
                for x in ignored_list:
                    if record.startswith(x):
                        ignored_record = True
                        break
                if not ignored_record:
                    start = 0
                    rdict = {}
                    for i, c in enumerate(col_spec_list):
                        colname = 'Column-' + str(i)
                        end = start + int(c)
                        coldata = record[start:end]
                        rdict[colname] = coldata
                        start = end
                    data.append(rdict)
            df = pd.DataFrame(data)
    except Exception as e:
        print(repr(e))
    return df

def ip4_addresses():
    ip_list = []
    """ Linux only version """
    #for interface in ni.interfaces():
    #    for link in ni.ifaddresses(interface)[ni.AF_INET]:
    #        ip_list.append(link['addr'])
    """ Linux & Windows version """
    for interface in ni.interfaces():
        if interface and ni.AF_INET in ni.ifaddresses(interface):
            ip_list.append(ni.ifaddresses(interface)[ni.AF_INET][0]['addr'])
    return ip_list

def validate_ip_address(ip_address):
    regex = "^((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])$"
    return (re.search(regex, ip_address))


def server_status_check(server_ip):
    if validate_ip_address(server_ip):
        server_list = list()
        server_list.append(server_ip)
        return client.main(engine=None, server_list=server_list, chunk=None, dummy=False, status_check=True)
    else:
        return False
