#
# project: CSV Validator
#
# Vaidation Utilities
#
# georgios mountzouris 2026 (gmountzouris@efka.gov.gr)
#

import os, io, re
import csv
import requests
import webbrowser
import pandas as pd
import pandasql as ps
import numpy as np
import datetime as dt
import netifaces as ni
import v_common as common
import v_client as client
import xml.etree.ElementTree as ET
from fpdf import FPDF
from fpdf.fonts import FontFace
from datetime import datetime
from v_pgdev import Pgdev
from pathlib import Path
from v_dxhub import Dxhub
from xlsxwriter.color import Color
from dateutil.parser import parse
from v_outlier_detector import OutlierDetector


LINE_BREAK = '\r\n'

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

def get_result(anomalies, actual_row_number=True):
    add_header = 0
    if not actual_row_number:
        add_header = 1
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
            for row, val in v:
                data += '-> Row: ' + str(row+add_header) + ', Value: ' + str(val) + '\n'
        result += header + data + '-------\n'
    return total, result

def get_delimiter(filename):
    #read the first line of csv and identify the delimiter
    with open(filename, 'r') as f:
        sniffer = csv.Sniffer()
        dialect = sniffer.sniff(f.readline())
        return dialect.delimiter

def get_dataframe(filename, delimiter=',', header='infer', encoding='utf-8', type=None, jlx_spec=None, fwf_spec=None, nrows=None):
    df = None
    above_threshold = False
    tr_ell = False
    err_msg = ""
    try:
        if filename.lower().endswith('.csv'):
            df = pd.read_csv(filename, sep=delimiter, header=header, encoding=encoding, dtype=type, nrows=nrows)
        elif filename.lower().endswith('.xlsx'):
            df = pd.read_excel(filename, dtype=str)
        elif filename.lower().endswith('.json'):
            df = pd.read_json(filename, dtype=str)
        elif filename.lower().endswith('.jlx'):
            df = jlx2df(filename, jlx_spec)
        else:
            df = fwf2df(filename, fwf_spec)
    except Exception as e:
        print(repr(e))
        err_msg = str(e)
        pass
    if df is not None and filename.lower().endswith('tr.ell.csv') and 'FIELD_R' in df and nrows is None:
        try:
            tr_ell = True
            t = 0.08
            v = get_col_val_frq(df, 'FIELD_R', percentage=False)['1'] + get_col_val_frq(df, 'FIELD_R', percentage=False)['2'] + get_col_val_frq(df, 'FIELD_R', percentage=False)['3']
            above_threshold = v > t
        except Exception as e:
            print(repr(e))
            pass
    return df, tr_ell, above_threshold, err_msg

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
            header_format = {"bold":True, "font_color":"#000000", "align":"center", "bg_color":"#F2F2F2", "border":1}
            h_format = workbook.add_format(header_format)
            for col_num, col_val in enumerate(df.columns.values):
                worksheet.write(0, col_num, col_val, h_format)
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
        with open(filename, "w", encoding='utf-8') as f:
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
    root = ET.Element("template")
    rules = ET.SubElement(root, "rules")
    rules.set('logical_operator', str(engine.logical_operator))
    for i, r in enumerate(engine.rules):
        rule = ET.SubElement(rules, "rule")
        rule.set('id', str(i))
        ET.SubElement(rule, "column_to_check").text = engine.columns_to_check[i]
        ET.SubElement(rule, "rule_name").text = r.name
        vr = ET.SubElement(rule, "value_range")
        for v in engine.acceptable_values[i]:
            ET.SubElement(vr, "value").text = v
    cv = ET.SubElement(root, "cross_validation")
    for i, (j, k) in enumerate(engine.cross_validation):
        cvi = ET.SubElement(cv, "check")
        cvi.set('id', str(i))
        ET.SubElement(cvi, "when").text = str(j)
        ET.SubElement(cvi, "then").text = str(k)
    tree = ET.ElementTree(root)
    if to_string:
        xmlstr = ET.tostring(root, encoding='utf8')
        return xmlstr.decode("utf-8")
    else:
        ET.indent(tree, space="\t", level=0)
        tree.write(filename, encoding='utf-8', xml_declaration=True)

def import_from_xml_template(source_xml, from_string=False):
    logical_operator = None
    xml_rules = []
    cross_validation = []
    if from_string:
        tree = ET.ElementTree(ET.fromstring(source_xml))
    else:
        tree = ET.parse(source_xml)
    root = tree.getroot()
    for rules in root.findall('rules'):
        logical_operator = rules.attrib
        for rule in rules.findall('rule'):
            rule_id = int(rule.attrib['id'])
            column_to_check = rule.find('column_to_check').text
            rule_name = rule.find('rule_name').text
            vr = rule.find('value_range')
            values = []
            for v in vr:
                values.append(v.text)
            xml_rules.append((column_to_check, rule_name, values))
            if xml_rules[rule_id] != (column_to_check, rule_name, values):
                xml_rules[rule_id] = (column_to_check, rule_name, values)
    for cv in root.findall('cross_validation'):
        for check in cv.findall('check'):
            when = check.find('when').text
            then = check.find('then').text
            cross_validation.append((int(when), int(then)))
    return logical_operator, xml_rules, cross_validation

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
                        colname = 'Column_' + str(i)
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
    ignored_list = fwf_spec['ignore'].split(',')
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
                        colname = 'Column_' + str(i)
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
    
def rule_in_cv(rule_index, cross_validation):
  flag = False
  for j, k in cross_validation:
    if rule_index == j or rule_index == k:
      flag = True
      break
  return flag

def change_rule_index_in_cv(i, cv):
    for c, (j, k) in enumerate(cv):
        if i < j:
            j -= 1
        if i < k:
            k -= 1
        cv[c] = (j, k)

def get_col_val_frq(df, col, percentage=False):
    if percentage:
        return df[col].value_counts(normalize=True) * 100
    return df[col].value_counts(normalize=True)

def get_dxhub_result(engine, service, parameter, column, callback_function):
    try:
        dxhub = Dxhub(service, parameter)
        total = engine.df.shape[0]
        data = []
        col_idx = engine.df.columns.get_loc(column)
        for i, row in enumerate(engine.df.itertuples(index=False)):
            status_code, response = dxhub.service_call(row[col_idx])
            if status_code == 999:
                callback_function(-1)
                break
            # Handling record(s) in response
            for record in response:
                combined_dict = {**row._asdict(), **record}
                data.append(combined_dict)
            prog = ((i + 1) * 100) / total
            callback_function(int(prog))
        result_df = get_df_as_type_string(pd.DataFrame(data))
        result_df_columns_list = engine.df.columns.tolist() + [col for col in result_df.columns.tolist()[len(engine.df.columns):]]
        result_df.columns = result_df_columns_list
        Path("./export/dxhub/").mkdir(parents=True, exist_ok=True)
        df2xlsx(filename="./export/dxhub/results.xlsx", df=result_df, anomalies=None)
    except Exception as e:
        print(f"Error: {repr(e)}")
        callback_function(-1)

def execute_sql_query(df, sql, output="CONSOLE"):
    try:
        if output == "CONSOLE":
            print(ps.sqldf(sql))
        else:
            Path("./export/sql/").mkdir(parents=True, exist_ok=True)
            filename = f"./export/sql/results.{output.lower()}"
            if output == "HTML":
                df2html(filename=filename, df=ps.sqldf(sql))
                webbrowser.open('file://' + os.path.realpath(filename))
            elif output == "XLSX":
                df2xlsx(filename=filename, df=ps.sqldf(sql), anomalies=None)
            elif output == "CSV":
                df2csv(filename=filename, df=ps.sqldf(sql))
            elif output == "JSON":
                df2json(filename=filename, df=ps.sqldf(sql))
            elif output == "XML":
                df2xml(filename=filename, df=ps.sqldf(sql))
            elif output == "SQL":
                df2sql(filename=filename, df=ps.sqldf(sql))
        return True
    except Exception as e:
        print(f"Error: {repr(e)}")
        return False

def get_credit_date():
    today_date = dt.date.today()
    next_monday_date = today_date + dt.timedelta(days=-today_date.weekday(), weeks=1)
    dates = (today_date + dt.timedelta(idx + 1) for idx in range((next_monday_date - today_date).days))
    business_dates = sum(1 for day in dates if day.weekday() < 5)
    if business_dates < 3:
        next_monday_date = today_date + dt.timedelta(days=-today_date.weekday(), weeks=2)
    next_monday = next_monday_date.strftime('%Y%m%d')
    month = next_monday_date.strftime('%m')
    year = next_monday_date.strftime('%Y')
    return next_monday, month, year

def get_credit_date_v2(days=3):
    next_credit_date = dt.date.today()
    if days > 0:
        for d in range(1, days+1):
            next_credit_date += dt.timedelta(days=1)
            if next_credit_date.weekday() >= 5:
                diff = 7 - next_credit_date.weekday()
                next_credit_date += dt.timedelta(days=diff)
    credit_date = next_credit_date.strftime('%Y%m%d')
    month = next_credit_date.strftime('%m')
    year = next_credit_date.strftime('%Y')
    return credit_date, month, year

def compute_credit_date():
    now_time = datetime.strptime(str(datetime.now().time().strftime("%H:%M:%S")), "%H:%M:%S")
    deadline = datetime.strptime("11:00:00", "%H:%M:%S")
    diff = deadline - now_time
    minutes_to_deadline = diff.total_seconds() / 60
    if minutes_to_deadline >= 0:
        cdate = get_credit_date_v2(days=1)
    else:
        cdate = get_credit_date_v2(days=2)
    return cdate

def space_fill(n):
    return "".center(n, " ")

def zero_fill(n):
    return "".zfill(n)

def get_bank_code(iban):
    return iban[4:7]

def get_bank_descr(bank_code):
    bank_dict = {"011":"ΕΘΝΙΚΗ ΤΡΑΠΕΖΑ ΤΗΣ ΕΛΛΑΔΟΣ",
                   "012":"ΕΜΠΟΡΙΚΗ ΤΡΑΠΕΖΑ ΤΗΣ ΕΛΛΑΔΟΣ",
                   "014":"ΤΡΑΠΕΖΑ ΠΙΣΤΕΩΣ",
                   "015":"ΓΕΝΙΚΗ ΤΡΑΠΕΖΑ ΤΗΣ ΕΛΛΑΔΟΣ",
                   "016":"ΤΡΑΠΕΖΑ ΑΤΤΙΚΗΣ",
                   "017":"ΤΡΑΠΕΖΑ ΠΕΙΡΑΙΩΣ",
                   "026":"EFG ΕUROBANK",
                   "028":"ΕΓΝΑΤΙΑ ΤΡΑΠΕΖΑ",
                   "031":"ΛΑΪΚΗ ΤΡΑΠΕΖΑ",
                   "032":"ΕΛΛΗΝΙΚΗ ΤΡΑΠΕΖΑ",
                   "037":"ΩΜΕΓΑ ΤΡΑΠΕΖΑ",
                   "038":"NOVA BANK",
                   "043":"ΑΓΡΟΤΙΚΗ ΤΡΑΠΕΖΑ ΤΗΣ ΕΛΛΑΔΟΣ",
                   "047":"ASPIS BANK",
                   "054":"PROBANK",
                   "055":"FIRST BUSINESS BANK (FBB)",
                   "069":"ΣΥΝΕΤΑΙΡΙΣΤΙΚΗ ΤΡΑΠΕΖΑ ΧΑΝΙΩΝ",
                   "071":"HSBC",
                   "073":"ΤΡΑΠΕΖΑ ΚΥΠΡΟΥ",
                   "079":"ΣΥΝΕΤΑΙΡΙΣΤΙΚΗ ΔΩΔΕΚΑΝΗΣΟΥ",
                   "080":"AMERICAN EXPRESS",
                   "084":"CITIBANK",
                   "087":"ΠΑΓΚΡΗΤΙΑ ΣΥΝΕΤΑΙΡΙΣΤΙΚΗ",
                   "096":"ΤΑΧΥΔΡΟΜΙΚΟ ΤΑΜΙΕΥΤΗΡΙΟ",
                   "097":"ΤΑΜΕΙΟ ΠΑΡΑΚΑΤΑΘΗΚΩΝ ΚΑΙ ΔΑΝΕΙΩΝ"}
    return bank_dict[bank_code]

def get_file_header_record(code, afm):
    cdate = compute_credit_date()
    return "1P" + code.rjust(4, "0") + afm[:-1] + zero_fill(3) + cdate[0] + cdate[1] + cdate[2] + space_fill(129) + LINE_BREAK

def get_file_trailer_record(total_records, hash_total):
    return "7" + space_fill(4) + str(total_records).rjust(8, "0") + space_fill(4) + str(round(hash_total, 2)).replace('.', '').rjust(11, "0") + space_fill(2) + zero_fill(11) + space_fill(119) + LINE_BREAK

def get_float_amount(amount):
    amount = amount[:-2] + '.' + amount[-2:]
    return round(float(amount), 2)

def record_process(record, record_dict):
    if record is not None:
        #print(record['AA'], record['REGISTER_NUMBER'], record['SURNAME'], record['NAME'], record['FATHERNAME'], record['AMOUNT'], record['IBAN'])
        detail_record = "4" + zero_fill(3) + zero_fill(13) + record['AMOUNT'].replace(',', '').rjust(8, "0") + record['SURNAME'].ljust(20, " ")[:20] + record['NAME'].ljust(6, " ")[:6] + record['FATHERNAME'].ljust(4, " ")[:4] + record['REGISTER_NUMBER'].rjust(10, "0")[:10] + space_fill(20) + space_fill(16) + space_fill(3) + zero_fill(8) + record['IBAN'] + space_fill(21)
        bcode = get_bank_code(record['IBAN'])
        if bcode in record_dict:
            bgroup = record_dict.get(bcode)
            bgroup.append(detail_record)
            record_dict[bcode] = bgroup
        else:
            bgroup = []
            bgroup.append(detail_record)
            record_dict[bcode] = bgroup

def get_record_dictionary(type, df):
    detail_record_dict = {}
    if type == 5:
        df = df.reset_index()
        proc_row = None
        for index, row in df.iterrows():
            if int(row['COUNT']) > 1:
                if row['REGISTER_NUMBER'] == proc_row['REGISTER_NUMBER'] and row['IBAN'] == proc_row['IBAN']:
                    proc_row['AMOUNT'] = ("%.2f" % (round(round(float(row['AMOUNT'].replace(',', '.')), 2) + round(float(proc_row['AMOUNT'].replace(',', '.')), 2), 2))).replace('.', ',')
                else:
                    record_process(proc_row, detail_record_dict)
                    proc_row = row
            else:
                record_process(proc_row, detail_record_dict)
                proc_row = row
        record_process(proc_row, detail_record_dict)
    return detail_record_dict 

def get_file_detail_record(type, df):
    if type == 5:
        pdf_data_table = [("BANK_CODE", "BANK_DESCR", "CNT", "AMNT")]
        hash_total = 0
        total_records = 0
        detail_record = ""
        detail_record_dict = get_record_dictionary(type, df)
        for key, val in detail_record_dict.items():
            bank_total = 0
            group_header_record = "2" + key + "30" + space_fill(154) + LINE_BREAK
            details = ""
            total_amount = 0
            for rec in val:
                details += rec + LINE_BREAK
                total_amount += get_float_amount(rec[17:25])
                total_amount = round(total_amount, 2)
                bank_total += 1
            total_records += bank_total
            hash_total += total_amount
            hash_total = round(hash_total, 2)
            group_summary_record = "6" + space_fill(4) + str(len(val)).rjust(8, "0") + space_fill(4) + ("%.2f" % (total_amount)).replace('.', '').rjust(11, "0") + space_fill(2) + zero_fill(11) + space_fill(119) + LINE_BREAK
            detail_record += group_header_record + details + group_summary_record
            bank_row = (key, get_bank_descr(key), str(bank_total), ("%.2f" % (total_amount)).replace('.', ','))
            pdf_data_table.append(bank_row)
            totals_row = ("", "ΣΥΝΟΛΟ", str(total_records), ("%.2f" % (hash_total)).replace('.', ','))
        pdf_data_table.append(totals_row)
    return detail_record, total_records, hash_total, pdf_data_table

def generate_file(type, code, header, details, trailer, pdf_data_table):
    filename = ""
    try:
        if type == 5:
            cdate = compute_credit_date()
            Path("./export/diaspay/").mkdir(parents=True, exist_ok=True)
            filename = f"./export/diaspay/MS{code.rjust(4, '0')}IF.{cdate[0]}"
        content = header + details + trailer
        with open(filename, "wb") as f:
            f.write(content.encode('windows-1253'))
        generate_pdf(pdf_data_table)
    except Exception as e:
        print(e)
        return False, ""
    return True, filename

def generate_pdf(pdf_data_table):
    pdf = FPDF(orientation="portrait", format="A4")
    pdf.set_display_mode(zoom=100)
    pdf.set_top_margin(20)
    pdf.set_text_shaping(True)
    pdf.add_font("dejavu-sans", style="", fname="./font/DejaVuSans.ttf")
    pdf.add_font("dejavu-sans", style="b", fname="./font/DejaVuSans-Bold.ttf")
    pdf.add_font("dejavu-sans", style="i", fname="./font/DejaVuSans-Oblique.ttf")
    pdf.add_font("dejavu-sans", style="bi", fname="./font/DejaVuSans-BoldOblique.ttf")
    pdf.set_font('dejavu-sans', size=10)
    pdf.add_page()
    lightgrey = (211, 211, 211)
    headings_style = FontFace(emphasis="BOLD", fill_color=lightgrey)
    with pdf.table(width=150, headings_style=headings_style, col_widths=(23, 55, 10, 30), text_align=("LEFT", "LEFT", "CENTER", "RIGHT")) as table:
        for data_row in pdf_data_table:
            row = table.row()
            for data_cell in data_row:
                row.cell(data_cell)
    Path("./export/diaspay/").mkdir(parents=True, exist_ok=True)
    pdf.output('./export/diaspay/summary.pdf')
