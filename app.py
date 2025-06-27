#
# project: CSV Validator
#
# GUI
#
# georgios mountzouris 2025 (gmountzouris@efka.gov.gr)
#

import os
import time
import tkinter as tk
import tkinter.font
import v_utilities as util
import v_config as cfg
import v_pgdev as pgdev
import v_rule_library as vlib
import pyperclip
import numpy as np
from v_engine import RuleEngine
from tkinter import Tk
from tkinter import ttk
from tkinter import filedialog as fd
from tkinter import messagebox as mb
from tkinter import scrolledtext
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
import functools
fp = functools.partial

class App(Tk):
    def __init__(self):
        Tk.__init__(self)
        self.version="2.3.3"
        self.release = "beta"
        self.title("CSV File Validator v" + self.version + ' (' + self.release + ')')
        self.developer = "Georgios Mountzouris (gmountzouris@efka.gov.gr)"
        self.geometry("1024x640")
        self.resizable(False, False)

        self.df = None
        self.engine = None

        # Create the application variables
        self.csv_file = tk.StringVar()
        self.csv_file.trace_add("write", callback=self.run_process)

        # Create the widgets
        #Menubar
        self.menubar = tk.Menu(master=self)

        self.filemenu = tk.Menu(self.menubar, tearoff=0)
        self.filemenu.add_command(label="CSV Configuration", command=self.open_csv_config_window)
        self.filemenu.add_command(label="DB Configuration", command=self.open_db_config_window)
        self.filemenu.add_separator()
        self.filemenu.add_command(label="Export to Excel", command=self.export_to_excel)
        self.filemenu.add_separator()
        self.filemenu.add_command(label="Exit", command=self.quit)
        self.menubar.add_cascade(label="File", menu=self.filemenu)

        self.editmenu = tk.Menu(self.menubar, tearoff=0)
        self.editmenu.add_command(label="Copy to clipboard", command=self.copy_to_clipboard)
        self.menubar.add_cascade(label="Edit", menu=self.editmenu)

        self.utilitiesmenu = tk.Menu(self.menubar, tearoff=0)
        self.utilitiesmenu.add_command(label="RuleDB", command=self.open_ruledb_window)
        self.utilitiesmenu.add_command(label="Data visualization", command=self.open_dv_window)
        self.menubar.add_cascade(label="Utilities", menu=self.utilitiesmenu)

        self.helpmenu = tk.Menu(self.menubar, tearoff=0)
        self.helpmenu.add_command(label="Help")
        self.helpmenu.add_command(label="Check for updates", command=self.check_for_updates)
        self.helpmenu.add_separator()
        self.helpmenu.add_command(label="About", command=self.about_window)
        self.menubar.add_cascade(label="Help", menu=self.helpmenu)

        self.config(menu=self.menubar)

        #csv file panel
        self.browse_frame = tk.Frame(self)
        self.browse_frame.pack(side=tk.TOP, fill=tk.X)
        self.csv_label = ttk.Label(self.browse_frame, text='CSV / XLSX file:').pack(anchor=tk.W, padx=5, pady=5, fill=tk.X)
        self.csv_entry = tk.Entry(self.browse_frame, textvariable=self.csv_file, bd=3)
        self.csv_entry.pack(side='left', expand=True, fill=tk.X)
        self.csv_button = ttk.Button(self.browse_frame, text='...', command=self.open_csv_file)
        self.csv_button.pack(side='right', expand=False)

        #rule panel
        self.rule_frame = tk.Frame(self)
        self.rule_frame.pack()
        self.rulebtn = ttk.Button(self.rule_frame, text='Rules panel')
        self.rulebtn.pack(side=tk.BOTTOM, pady=5)
        self.rulebtn.bind('<Button-1>', self.open_rules_window)

        #fire panel
        self.fire_frame = tk.Frame(self, background='red')
        self.fire_frame.pack(fill=tk.X)
        self.firebtn = ttk.Button(self.fire_frame, text='Fire all Rules')
        self.firebtn.pack(fill=tk.X, expand=tk.TRUE, padx=3, pady=3)
        self.firebtn.bind('<Button-1>', self.fire_all_rules)

        #execution panel
        self.exec_frame = tk.Frame(self)
        self.exec_frame.pack(fill=tk.X)
        self.exec_label = ttk.Label(self.exec_frame, text='')
        self.exec_label.pack(anchor=tk.W, padx=5, pady=5)
        self.total_label = ttk.Label(self.exec_frame, text='')
        self.total_label.pack(anchor=tk.W, padx=5)

        self.holder_frame = tk.Frame(self)
        self.holder_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=tk.TRUE)

        self.text_area = scrolledtext.ScrolledText(self.holder_frame, bg='white', fg='blue', font=("Courier", 11, "normal"), width=1024, heigh=640)
        self.text_area.pack(fill=tk.BOTH, expand=tk.TRUE)
        self.disable_text_area()

        self.bind('<FocusIn>', self.focus_event_handler)

        self.init_state()
        self.check_for_updates(infomsg=False)

    def run_process(self, var, index, mode):
        self.text_area['bg'] = 'white'
        self.text_area['fg'] = 'blue'
        if self.csv_file.get():
            if os.path.exists(self.csv_file.get()) and (self.csv_file.get().endswith('.csv') or self.csv_file.get().endswith('.xlsx')):
                #sep = util.get_delimiter(self.csv_file.get())
                self.init_state()
                config = cfg.load_config()
                sep = config['delimiter']
                hdr = 'infer' if config['header'] == 'True' else None
                enc = config['encoding']
                self.df = util.get_dataframe(self.csv_file.get(), delimiter=sep, header=hdr, encoding=enc, type=object)
                self.df = util.get_df_as_type_string(self.df)
                self.engine = RuleEngine(self.df)
                txt_content = ''
                bar = '========================================\n'
                info = util.csv_data_structure(df=self.df, method='info')
                info = info[info.index('>')+2:]
                #info += util.csv_data_structure(df=self.df, method='describe')
                txt_content += bar 
                txt_content += '=            Data structure            =\n'
                txt_content += bar
                txt_content += info
                txt_content += bar
                self.enable_text_area()
                self.clear_text_area()
                self.text_area.insert(tk.END, txt_content)
                self.disable_text_area()
                self.show_rule_panel()
                self.enable_export_to_excel()
                self.enable_data_visualization()
            else:
                self.init_state()
                mb.showwarning(title="Warning!", message="Invalid csv file!", parent=self)
        else:
            self.init_state() 

    def open_csv_file(self):
        self.csv_file.set(fd.askopenfilename(defaultextension=".csv", filetypes=[("CSV Comma Separatad Values","*.csv"), ("XLSX Spreadsheets","*.xlsx")]))

    def open_csv_config_window(self):
        self.config_window = ConfigWindow(self)

    def open_db_config_window(self):
        self.dbconfig_window = DBConfigWindow(self)

    def open_ruledb_window(self):
        self.ruledb_window = RuleDBWindow(self)

    def open_dv_window(self):
        self.dv_window = DataVisualizationWindow(self, df=self.df)

    def open_rules_window(self, event):
        self.rules_window = RulesManagementWindow(self, engine=self.engine, columns=util.get_df_columns(self.df))

    def export_to_excel(self):
        filename = fd.SaveAs(initialfile='output.xlsx', defaultextension=".xlsx", filetypes=[("XLSX Spreadsheets","*.xlsx")])
        if filename:
            util.df_to_xlsx(filename.show(), self.df, self.engine.anomalies)

    def about_window(self):
        def close_window():
            self.dialog.grab_release()
            self.dialog.destroy()
        self.dialog = tk.Toplevel(self)
        self.dialog.geometry("350x150")
        self.dialog.title('About')
        tk.Label(self.dialog, text="Project: CSV Validator", font=("Helvetica", 11, "bold"), bg="lightblue", justify=tk.CENTER, relief=tk.RAISED, pady=5,).pack(fill=tk.X)
        tk.Label(self.dialog, text="Csv Validation Tool " + self.version, font=("Times", 11), bg="lightgrey", fg="black", justify=tk.CENTER, relief=tk.FLAT, wraplength=175, pady=5).pack(fill=tk.X)
        self.about_label = tk.Label(self.dialog, text=self.developer, fg="blue", wraplength=175)
        self.close = tk.Button(self.dialog, text="Close", command=close_window)
        self.close.pack(side=tk.BOTTOM, pady=5)
        self.about_label.pack(side=tk.BOTTOM)
        self.dialog.grab_set()

    def check_for_updates(self, infomsg=True):
        config = cfg.load_config(section="general")
        version_info = util.get_version_info(config['api_url'])
        web_version = int(version_info['version'].replace('.', ''))
        my_version = int(self.version.replace('.', ''))
        if (web_version > my_version) or (web_version == my_version and version_info['release'] != self.release):
            mb.showwarning(title="Warning!", message="A new version is available (" + version_info['version'] + " " + version_info['release'] + "), get it from " + config['download_url'], parent=self)
        else:
            if infomsg:
                mb.showinfo(title="No newer version", message="You are running the latest vesion of Validator!", parent=self)

    def init_state(self):
        self.df = None
        self.engine = None
        self.disable_export_to_excel()
        self.disable_data_visualization()
        self.hide_rule_panel()
        self.hide_fire_panel()
        self.hide_exec_panel()

    def enable_export_to_excel(self):
        self.filemenu.entryconfig("Export to Excel", state="normal")

    def disable_export_to_excel(self):
        self.filemenu.entryconfig("Export to Excel", state="disabled")

    def enable_data_visualization(self):
        self.utilitiesmenu.entryconfig("Data visualization", state="normal")

    def disable_data_visualization(self):
        self.utilitiesmenu.entryconfig("Data visualization", state="disabled")

    def disable_text_area(self):
        self.text_area.configure(state='disabled')

    def enable_text_area(self):
        self.text_area.configure(state='normal')

    def clear_text_area(self):
        self.text_area.delete(1.0, tk.END)

    def hide_rule_panel(self):
        self.rule_frame.forget()
        self.enable_text_area()
        self.clear_text_area()
        self.disable_text_area()

    def hide_fire_panel(self):
        self.fire_frame.forget()

    def hide_exec_panel(self):
        self.exec_frame.forget()

    def show_rule_panel(self):
        self.rule_frame.pack(after=self.browse_frame, anchor=tk.W)

    def show_fire_panel(self):
        self.fire_frame.pack(after=self.rule_frame, anchor=tk.W, fill=tk.X)

    def show_exec_panel(self):
        self.exec_frame.pack(after=self.fire_frame, anchor=tk.W)

    def focus_event_handler(self, event):
        if self.engine and len(self.engine.rules) > 0:
            self.show_fire_panel()
        else:
            self.hide_fire_panel()

    def fire_all_rules(self, event):
        if self.engine and len(self.engine.rules) > 0:
            start = time.time()
            self.engine.fire_all_rules()
            end = time.time()
            self.enable_text_area()
            self.clear_text_area()
            total, txt_content = util.get_result(self.engine.anomalies)
            self.text_area['bg'] = 'black'
            self.text_area['fg'] = 'white'
            self.show_exec_panel()
            self.exec_label['text'] = "Execution time: " + str(end - start) + " seconds"
            self.total_label['text'] = "Total invalid values: " + str(total)
            self.text_area.insert(tk.END, txt_content)
            self.disable_text_area()

    def copy_to_clipboard(self):
        content = self.text_area.get("1.0", tk.END)
        pyperclip.copy(content)

class RulesManagementWindow(tk.Toplevel):
    def __init__(self, *args, engine=None, columns=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry("560x280")
        self.title("Rules panel")

        def _event_handler(event):
            _listbox_clear()
            _listbox_fill()

        def _listbox_clear():
            self.listbox_clear()

        def _listbox_fill():
            self.listbox_fill(engine)

        def delete_selected_rule():
            selectied_rule = self.listbox.curselection()
            if selectied_rule:
                engine.delete_rule(selectied_rule[0])
                _listbox_clear()
                _listbox_fill()

        def clear_all():
            engine.clear()
            _listbox_clear()

        def _import():
            filename = fd.askopenfilename(defaultextension=".xml", filetypes=[("XML Documents","*.xml")])
            if filename:
                clear_all()
                xml_rules = util.import_from_xml(filename)
                for r in vlib.get_rule_library():
                    for x in xml_rules:
                        if r.name == x[1]:
                            engine.add_rule(rule=r, column=x[0], value_range=x[2])
                _listbox_fill()

        def _export():
            if self.listbox.index("end") > 0:
                filename = fd.SaveAs(initialfile='rule_panel_template.xml', defaultextension=".xml", filetypes=[("XML Documents","*.xml")])
                if filename:
                    util.export_to_xml(filename.show(), engine)

        def open_new_rule_window():
            self.new_rule_window = NewRuleWindow(self, parent=self, engine=engine, columns=columns)

        def open_rule_amendment_window():
            selected_rule = self.listbox.curselection()
            if selected_rule:
                self.new_rule_window = NewRuleWindow(self, parent=self, engine=engine, columns=columns, amendment=(selected_rule[0], self.listbox.get(selected_rule)))

        #rules frame
        self.rules_frame = tk.Frame(self)
        self.rules_frame.pack(fill=tk.BOTH, side=tk.LEFT, expand=True)

        #control_frame
        self.control_frame = tk.Frame(self)
        self.control_frame.pack(fill=tk.BOTH, side=tk.RIGHT)

        self.scrollbar = tk.Scrollbar(self.rules_frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.BOTH)

        self.listbox = tk.Listbox(self.rules_frame, activestyle=tk.NONE, selectmode=tk.SINGLE)
        self.listbox.pack(fill=tk.BOTH, expand=True)

        _listbox_fill()

        self.listbox.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.listbox.yview)

        self.addbtn = tk.Button(self.control_frame, text="Add", width=10, command=open_new_rule_window)
        self.addbtn.pack()
        self.edtbtn = tk.Button(self.control_frame, text="Edit", width=10, command=open_rule_amendment_window)
        self.edtbtn.pack()
        self.delbtn = tk.Button(self.control_frame, text="Delete", width=10, command=delete_selected_rule)
        self.delbtn.pack()
        self.delbtn = tk.Button(self.control_frame, text="Clear all", width=10, command=clear_all)
        self.delbtn.pack()
        self.impbtn = tk.Button(self.control_frame, text="Import", width=10, command=_import)
        self.impbtn.pack()
        self.expbtn = tk.Button(self.control_frame, text="Export", width=10, command=_export)
        self.expbtn.pack()

        #self.bind('<FocusIn>', _event_handler)

        #self.focus()
        self.wait_visibility()
        self.grab_set()

    def event_handler(self, engine):
        self.listbox_clear()
        self.listbox_fill(engine)

    def listbox_clear(self):
        self.listbox.delete(0, tk.END)

    def listbox_fill(self, engine):
        for i, r in enumerate(engine.rules):
            vr = ','.join(engine.acceptable_values[i])
            vr = ': ' + vr if vr else ''
            self.listbox.insert(tk.END, str(i+1) + ') ' + engine.columns_to_check[i] + ' -> ' + r.name + vr)

class NewRuleWindow(tk.Toplevel):
    def __init__(self, *args, parent=None, engine=None, columns=None, amendment=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry("460x180")
        self.title_text = "New Rule"

        self.rule_name = tk.StringVar()
        self.col = tk.StringVar()
        self.vr = tk.StringVar()

        self.rule_name.trace_add("write", callback=self.display_description)

        def add_rule_to_engine(event):
            for r in vlib.get_rule_library():
                if r.name == self.rule_name.get():
                    if amendment:
                        engine.modify_rule(index=amendment[0], rule=r, column=self.col.get(), value_range=util.get_value_range(self.vr.get()))
                        parent.event_handler(engine)
                        self.destroy()
                    else:
                        engine.add_rule(rule=r, column=self.col.get(), value_range=util.get_value_range(self.vr.get()))
                        parent.event_handler(engine)
                        self.rule_name.set('')
                        self.col.set('')
                        self.vr.set('')
                        self.descr_label['text'] = ''
                        
        self.control_frame = tk.Frame(self, background='grey', relief=tk.GROOVE)
        self.control_frame.pack(fill=tk.X, side=tk.TOP, pady=5)

        self.column_label = ttk.Label(self.control_frame, text='Column:', background='grey', foreground='white')
        self.rule_label = ttk.Label(self.control_frame, text='Rule:', background='grey', foreground='white')
        self.vr_label = ttk.Label(self.control_frame, text='Value range:', background='grey', foreground='white')

        self.column_label.grid(row=0, column=0, sticky=tk.W)
        self.rule_label.grid(row=0, column=1, sticky=tk.W)
        self.vr_label.grid(row=0, column=2, sticky=tk.W)

        self.column_chooser = ttk.Combobox(self.control_frame, textvariable=self.col, state="readonly")
        self.column_chooser['values'] = columns
        self.rule_chooser = ttk.Combobox(self.control_frame, textvariable=self.rule_name, state="readonly", width=25)
        self.rule_chooser['values'] = [r.name for r in vlib.get_rule_library()]
        self.vr_entry = tk.Entry(self.control_frame, textvariable=self.vr, bd=3)

        self.column_chooser.grid(row=1, column=0)
        self.rule_chooser.grid(row=1, column=1)
        self.vr_entry.grid(row=1, column=2)
                               
        self.control_frame.columnconfigure((0,1,2), weight=1)

        self.descr_frame = tk.Frame(self, background='lightgrey', relief=tk.GROOVE, padx=5, pady=25)
        self.descr_frame.pack(fill=tk.X)
        self.descr_label = ttk.Label(self.descr_frame, text='', background='lightgrey', foreground='blue')
        self.descr_label.pack(fill=tk.X)

        self.addbtn = ttk.Button(self, text='Add rule')
        self.addbtn.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
        self.addbtn.bind('<Button-1>', add_rule_to_engine)

        if amendment:
            self.addbtn['text'] = "Modify rule"
            self.title_text = "Rule Amendment"
            amendment_info = util.get_selected_rule_info(amendment[1])
            self.col.set(amendment_info[0])
            self.rule_name.set(amendment_info[1])
            self.vr.set(amendment_info[2])

        self.title(self.title_text)
        #self.focus()
        self.wait_visibility()
        self.grab_set()

    def display_description(self, var, index, mode):
        for r in vlib.get_rule_library():
            if r.name == self.rule_name.get():
                self.descr_label['text'] = r.descr

class ConfigWindow(tk.Toplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry("460x180")
        self.title("CSV Configuration")

        self.delimiter = tk.StringVar()
        self.header = tk.BooleanVar()
        self.encoding = tk.StringVar()

        config = cfg.load_config()
        self.delimiter.set(config['delimiter'])
        self.header.set(config['header'])
        self.encoding.set(config['encoding'])

        self.delimiter_label = ttk.Label(self, text='Delimiter:')
        self.delimiter_label.pack(anchor=tk.W, padx=5, fill=tk.X)
        self.delimiter_entry = tk.Entry(self, textvariable=self.delimiter, width=21, bd=3)
        self.delimiter_entry.pack(anchor=tk.W, padx=5)

        self.encoding_label = ttk.Label(self, text='Encoding:')
        self.encoding_label.pack(anchor=tk.W, padx=5, pady=5, fill=tk.X)
        self.encoding_chooser = ttk.Combobox(self, textvariable=self.encoding, state="readonly")
        self.encoding_chooser['values'] = ['utf-8', 'ansi', 'windows-1253', 'iso-8859-1', 'iso-8859-7', 'macgreek', 'IBM869']
        self.encoding_chooser.pack(anchor=tk.W, padx=5)

        self.header_check = tk.Checkbutton(self, text="CSV file contains header with column names", variable=self.header, onvalue=True, offvalue=False)
        self.header_check.pack(anchor=tk.W, pady=15)

        self.savebtn = ttk.Button(self, text='Save')
        self.savebtn.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
        self.savebtn.bind('<Button-1>', self.save_and_exit)

    def save_and_exit(self, event):
        config = {}
        config['delimiter'] = self.delimiter.get()
        config['header'] = self.header.get()
        config['encoding'] = self.encoding.get()
        cfg.write_config(config=config)
        self.destroy()

class DBConfigWindow(tk.Toplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #self.config(width=300, height=200)
        self.geometry("300x390")
        self.title("DB configuration")

        self.dbconfig = cfg.load_config(section='postgresql')

        # Create the application variables
        self.dbname = tk.StringVar()
        self.dbschm = tk.StringVar()
        self.dbuser = tk.StringVar()
        self.dbpass = tk.StringVar()
        self.dbhost = tk.StringVar()
        self.dbport = tk.StringVar()

        # Initialize the application variables
        self.dbname.set(self.dbconfig['dbname'])
        self.dbschm.set(self.dbconfig['dbschema'])
        self.dbuser.set(self.dbconfig['user'])
        self.dbpass.set(self.dbconfig['password'])
        self.dbhost.set(self.dbconfig['host'])
        self.dbport.set(self.dbconfig['port'])

        self.cf = tkinter.font.Font(family="Arial", size=12, weight="bold")

        #dbname
        self.dbname_frame = tk.Frame(self, padx=5, pady=5)
        self.dbname_frame.pack(fill=tk.X)
        self.dbname_label = ttk.Label(self.dbname_frame, text='DB Name:').pack(anchor=tk.W, fill=tk.X)
        self.dbname_entry = tk.Entry(self.dbname_frame, textvariable=self.dbname, bd=3)
        self.dbname_entry.pack(side='left', expand=True, fill=tk.X)

        #dbschema
        self.dbschema_frame = tk.Frame(self, padx=5, pady=5)
        self.dbschema_frame.pack(fill=tk.X)
        self.dbschema_label = ttk.Label(self.dbschema_frame, text='DB Schema:').pack(anchor=tk.W, fill=tk.X)
        self.dbschema_entry = tk.Entry(self.dbschema_frame, textvariable=self.dbschm, bd=3)
        self.dbschema_entry.pack(side='left', expand=True, fill=tk.X)

        #dbuser
        self.dbuser_frame = tk.Frame(self, padx=5, pady=5)
        self.dbuser_frame.pack(fill=tk.X)
        self.dbuser_label = ttk.Label(self.dbuser_frame, text='DB User:').pack(anchor=tk.W, fill=tk.X)
        self.dbuser_entry = tk.Entry(self.dbuser_frame, textvariable=self.dbuser, bd=3)
        self.dbuser_entry.pack(side='left', expand=True, fill=tk.X)

        #dbpass
        self.dbpass_frame = tk.Frame(self, padx=5, pady=5)
        self.dbpass_frame.pack(fill=tk.X)
        self.dbname_label = ttk.Label(self.dbpass_frame, text='DB Password:').pack(anchor=tk.W, fill=tk.X)
        self.dbpass_entry = tk.Entry(self.dbpass_frame, textvariable=self.dbpass, bd=3)
        self.dbpass_entry.pack(side='left', expand=True, fill=tk.X)

        #dbhost
        self.dbhost_frame = tk.Frame(self, padx=5, pady=5)
        self.dbhost_frame.pack(fill=tk.X)
        self.dbname_label = ttk.Label(self.dbhost_frame, text='DB Host:').pack(anchor=tk.W, fill=tk.X)
        self.dbhost_entry = tk.Entry(self.dbhost_frame, textvariable=self.dbhost, bd=3)
        self.dbhost_entry.pack(side='left', expand=True, fill=tk.X)

        #dbport
        self.dbport_frame = tk.Frame(self, padx=5, pady=5)
        self.dbport_frame.pack(fill=tk.X)
        self.dbname_label = ttk.Label(self.dbport_frame, text='DB Port:').pack(anchor=tk.W, fill=tk.X)
        self.dbport_entry = tk.Entry(self.dbport_frame, textvariable=self.dbport, bd=3)
        self.dbport_entry.pack(side='left', expand=True, fill=tk.X)

        #connection test button
        self.test_frame = tk.Frame(self)
        self.test_frame.pack(fill=tk.X, pady=5)
        self.testbtn = ttk.Button(self.test_frame, text='Test connection')
        self.testbtn.pack()
        self.testbtn.bind('<Button-1>', self.conn_test)

        #save button
        self.save_frame = tk.Frame(self)
        self.save_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
        self.savebtn = ttk.Button(self.save_frame, text='Save configuration')
        self.savebtn.pack(fill=tk.X)
        self.savebtn.bind('<Button-1>', self.save_dbconfig)

        self.focus()
        self.grab_set()

    def get_new_dbconfig(self):
        self.new_dbconfig = dict({'dbname': self.dbname.get(), 'dbschema': self.dbschm.get(), 'user': self.dbuser.get(),'password': self.dbpass.get(), 'host': self.dbhost.get(), 'port': self.dbport.get()})

    def save_dbconfig(self, event):
        self.get_new_dbconfig()
        cfg.write_config(section='postgresql', config=self.new_dbconfig)
        self.destroy()

    def conn_test(self, event):
        self.get_new_dbconfig()
        if pgdev.connection_test(self.new_dbconfig):
            mb.showinfo(title="Success!", message="Connected to Database successfully!!", parent=self)
        else:
            mb.showerror(title="Fail", message="DB Connection failed!!", parent=self)

class RuleDBWindow(tk.Toplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry("560x280")
        self.title("Rule DB")

        self.dbconfig = cfg.load_config(section='postgresql')

        def _event_handler(event):
            _listbox_clear()
            _listbox_fill()

        def _listbox_clear():
            self.listbox_clear()

        def _listbox_fill():
            self.listbox_fill()

        def delete_selected_rule():
            selectied_rule = self.listbox.curselection()
            if selectied_rule:
                util.delete_rule_from_db(self.dbconfig, self.listbox.get(selectied_rule))
                _listbox_clear()
                _listbox_fill()

        def edit_selected_rule():
            selected_rule = self.listbox.curselection()
            if selected_rule:
                rule = util.get_rule_from_db(self.dbconfig, self.listbox.get(selected_rule))
                self.new_rule_window = NewDBRuleWindow(self, parent=self, rule=rule)

        def open_new_rule_window():
            self.new_rule_window = NewDBRuleWindow(self, parent=self)

        #rules frame
        self.rules_frame = tk.Frame(self)
        self.rules_frame.pack(fill=tk.BOTH, side=tk.LEFT, expand=True)

        #control_frame
        self.control_frame = tk.Frame(self)
        self.control_frame.pack(fill=tk.BOTH, side=tk.RIGHT)

        self.scrollbar = tk.Scrollbar(self.rules_frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.BOTH)

        self.listbox = tk.Listbox(self.rules_frame, activestyle=tk.NONE, selectmode=tk.SINGLE)
        self.listbox.pack(fill=tk.BOTH, expand=True)

        _listbox_fill()

        self.listbox.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.listbox.yview)

        self.addbtn = tk.Button(self.control_frame, text="Add", width=10, command=open_new_rule_window)
        self.addbtn.pack()
        self.edtbtn = tk.Button(self.control_frame, text="Edit", width=10, command=edit_selected_rule)
        self.edtbtn.pack()
        self.delbtn = tk.Button(self.control_frame, text="Delete", width=10, command=delete_selected_rule)
        self.delbtn.pack()

        self.edtbtn["state"] = "disabled"
        self.delbtn["state"] = "disabled"

        #self.bind('<FocusIn>', _event_handler)

        #self.focus()
        self.wait_visibility()
        self.grab_set()

    def event_handler(self):
        self.listbox_clear()
        self.listbox_fill()

    def listbox_fill(self):
        if pgdev.connection_test(self.dbconfig):
             rules = util.get_db_rules(self.dbconfig)
             for i, r in enumerate(rules):
                 self.listbox.insert(tk.END, str(i+1) + ') ' + r[1])
        else:
            mb.showerror(title="Fail", message="DB Connection failed!!", parent=self)

    def listbox_clear(self):
        self.listbox.delete(0, tk.END)

class NewDBRuleWindow(tk.Toplevel):
    def __init__(self, *args, parent=None, rule=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry("640x640")
        self.title("New Rule in RuleDB")

        self.amendment = 0

        self.rule_name = tk.StringVar()
        self.rule_description = tk.StringVar()
        self.function_name = tk.StringVar()
        self.function_body = tk.StringVar()

        self.main_frame = tk.Frame(self)
        self.main_frame.pack(side=tk.TOP, fill=tk.X, padx=5)

        self.name_frame = tk.Frame(self.main_frame)
        self.name_frame.pack(fill=tk.X, pady=5)
        self.name_label = ttk.Label(self.name_frame, text='Rule name:').pack(fill=tk.X)
        self.name_entry = tk.Entry(self.name_frame, textvariable=self.rule_name, bd=3)
        self.name_entry.pack(expand=True, fill=tk.X)

        self.descr_frame = tk.Frame(self.main_frame)
        self.descr_frame.pack(fill=tk.X, pady=5)
        self.descr_label = ttk.Label(self.descr_frame, text='Rule description:').pack(fill=tk.X)
        self.descr_entry = tk.Entry(self.descr_frame, textvariable=self.rule_description, bd=3)
        self.descr_entry.pack(expand=True, fill=tk.X)

        self.fname_frame = tk.Frame(self.main_frame)
        self.fname_frame.pack(fill=tk.X, pady=5)
        self.fname_label = ttk.Label(self.fname_frame, text='Function name:').pack(fill=tk.X)
        self.fname_entry = tk.Entry(self.fname_frame, textvariable=self.function_name, bd=3)
        self.fname_entry.pack(expand=True, fill=tk.X)

        self.holder_frame = tk.Frame(self.main_frame)
        self.holder_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.fbody_label = ttk.Label(self.holder_frame, text='Function body:').pack(fill=tk.X)
        self.fbody = scrolledtext.ScrolledText(self.holder_frame, bg='white', fg='blue', font=("Courier", 11, "normal"))
        self.fbody.pack(fill=tk.BOTH, expand=True)

        def _save_rule_to_db(event):
            self.function_body.set(self.fbody.get("1.0", tk.END))
            self.save_rule_to_db(parent)

        self.save_frame = tk.Frame(self)
        self.save_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
        self.savebtn = ttk.Button(self.save_frame, text='Save Rule to RuleDB')
        self.savebtn.pack(fill=tk.X)
        self.savebtn.bind('<Button-1>', _save_rule_to_db)

        self.init(rule)

    def save_rule_to_db(self, parent):
        if self.rule_name.get() and self.rule_description.get() and self.function_name.get() and self.function_body.get():
            if self.amendment <= 0:
                try:
                    util.add_rule_to_db(pgconf=parent.dbconfig, data=(self.rule_name.get(), self.rule_description.get(), self.function_name.get(), self.function_body.get()))
                    parent.listbox_clear()
                    parent.listbox_fill()
                    self.destroy()
                except:
                    mb.showerror(title="Fail", message="Something went wrong", parent=self)
            else:
                try:
                    util.edit_rule_in_db(pgconf=parent.dbconfig, data=(self.rule_name.get(), self.rule_description.get(), self.function_name.get(), self.function_body.get(), self.amendment))
                    parent.listbox_clear()
                    parent.listbox_fill()
                    self.destroy()
                except:
                    mb.showerror(title="Fail", message="Something went wrong", parent=self)

    def init(self, rule):
        if rule != None:
            self.amendment = rule[0]
            self.rule_name.set(rule[1])
            self.rule_description.set(rule[2])
            self.function_name.set(rule[3])
            self.function_body.set(rule[4])
            self.fbody.insert(tk.END, self.function_body.get())

class DataVisualizationWindow(tk.Toplevel):
    def __init__(self, *args, df=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry("860x580")
        self.title("Data Visualization")

        def plot(var, index, mode):
            self.plot(df)

        self.columns = util.get_df_columns(df)

        self.col = tk.StringVar()
        self.col.trace_add("write", callback=plot)

        self.control_frame = tk.Frame(self, borderwidth=2, relief="groove")
        self.control_frame.pack(fill=tk.X)
        self.column_chooser = ttk.Combobox(self.control_frame, textvariable=self.col, state="readonly")
        self.column_chooser.pack(fill=tk.X)
        self.column_chooser['values'] = self.columns

        self.focus()
        self.grab_set()

    def plot(self, df):

        self.destroy_plot_widgets()

        self.fig = Figure(figsize = (5, 5), dpi = 100)
        self.plt = self.fig.add_subplot(111)
        """
        try:
            #data_min_y = data_min_x = 0
            data = [float(v.replace(',', '.')) for v in df[self.col.get()]]
            #data_max_x = max(data)
            #data_max_y = data.count(util.most_frequent_item(data))
        except ValueError:
            data = df[self.col.get()]
            #data_max_y = data_max_x = 10
        #data = df[self.col.get()].value_counts()
        self.plt.hist(data, bins=np.arange(min(data), max(data)+1), align='mid', color='skyblue', edgecolor='black')

        
        #self.plt.set_xticks(np.arange(data_min_x, data_max_x+1, 1.0))
        #self.plt.set_yticks(np.arange(data_min_y, data_max_y+1, 1.0))
        """

        data = df[self.col.get()].value_counts()
        values = data.index.to_list()
        frequency = data.to_list()

        self.plt.bar(values, frequency)

        self.plt.set_xlabel('Values')
        self.plt.set_ylabel('Frequency')
        self.plt.set_title(self.col.get())
        
        self.canvas = FigureCanvasTkAgg(self.fig, self)  
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(anchor=tk.W, fill=tk.X)

        self.toolbar = NavigationToolbar2Tk(self.canvas, self, pack_toolbar=False)
        self.toolbar.update()

        self.canvas.get_tk_widget().pack(anchor=tk.W, fill=tk.X)
        self.toolbar.pack(side=tk.BOTTOM, fill=tk.X)

    def destroy_plot_widgets(self):
        for widget in self.winfo_children():
            if isinstance(widget, tk.Canvas) or isinstance(widget, NavigationToolbar2Tk):
                widget.destroy()

if __name__ == "__main__":
    myapp = App()
    myapp.mainloop()
