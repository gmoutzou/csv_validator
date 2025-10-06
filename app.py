#!/home/dev/anaconda3/envs/tensorflow/bin/python3
"""#!/bin/python3"""
#
# project: CSV Validator
#
# GUI
#
# georgios mountzouris 2025 (gmountzouris@efka.gov.gr)
#

import os, gc, sys
import time
import psutil
import tkinter as tk
import tkinter.font
import v_utilities as util
import v_config as cfg
import v_pgdev as pgdev
import v_server as server
import v_client as client
import pyperclip
import threading
from v_engine import RuleEngine
from tkinter import Tk
from tkinter import ttk
from tkinter import filedialog as fd
from tkinter import messagebox as mb
from tkinter import scrolledtext
from v_rule_library import RuleLibrary
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
import functools
fp = functools.partial


class App(Tk):
    def __init__(self):
        Tk.__init__(self)
        self.version="5.0.4"
        self.release = "beta"
        self.init_title = "CSV File Validator v" + self.version + ' (' + self.release + ')'
        self.developer = "Georgios Mountzouris (gmountzouris@efka.gov.gr)"
        self.geometry("1024x640")
        self.resizable(False, False)

        self.engine = None
        self.server_thread = None
        self.server_list = []
        self.vlib = RuleLibrary()

        # Create the application variables
        self.csv_file = tk.StringVar()
        self.csv_file.trace_add("write", callback=self.run_process)

        # Create the widgets
        #Menubar
        self.menubar = tk.Menu(master=self)

        self.filemenu = tk.Menu(self.menubar, tearoff=0)
        self.filemenu.add_command(label="Enable server mode", command=self.enable_server_mode)
        self.filemenu.add_command(label="Disable server mode", command=self.disable_server_mode)
        self.filemenu.add_separator()
        self.filemenu.add_command(label="CSV Configuration", command=self.open_csv_config_window)
        self.filemenu.add_command(label="JL10 Configuration", command=self.open_jl10_config_window)
        self.filemenu.add_command(label="Fixed Width Format File Configuration", command=self.open_fwf_config_window)
        self.filemenu.add_command(label="DB Configuration", command=self.open_db_config_window)
        self.filemenu.add_separator()
        self.filemenu.add_command(label="Export to Excel", command=self.export_to_excel)
        self.filemenu.add_command(label="Export to Csv", command=self.export_to_csv)
        self.filemenu.add_command(label="Export to Json", command=self.export_to_json)
        self.filemenu.add_command(label="Export to Xml", command=self.export_to_xml)
        self.filemenu.add_command(label="Export to Html", command=self.export_to_html)
        self.filemenu.add_command(label="Export to Sql", command=self.generate_sql)
        self.filemenu.add_separator()
        self.filemenu.add_command(label="Exit", command=self.on_closing)
        self.menubar.add_cascade(label="File", menu=self.filemenu)

        self.editmenu = tk.Menu(self.menubar, tearoff=0)
        self.editmenu.add_command(label="Copy to clipboard", command=self.copy_to_clipboard)
        self.menubar.add_cascade(label="Edit", menu=self.editmenu)

        self.utilitiesmenu = tk.Menu(self.menubar, tearoff=0)
        self.utilitiesmenu.add_command(label="RuleDB", command=self.open_ruledb_window)
        self.utilitiesmenu.add_separator()
        self.utilitiesmenu.add_command(label="Data structure", command=self.data_structure)
        self.utilitiesmenu.add_command(label="Data preview", command=self.data_preview)
        self.utilitiesmenu.add_command(label="Data visualization", command=self.open_dv_window)
        self.utilitiesmenu.add_separator()
        self.utilitiesmenu.add_command(label="Outlier detection (Ensemble model)", command=self.open_od_window)
        self.utilitiesmenu.add_command(label="Value frequency display", command=self.open_vfd_window)
        self.utilitiesmenu.add_separator()
        self.utilitiesmenu.add_command(label="Performance monitor", command=self.open_performance_window)
        self.utilitiesmenu.add_separator()
        self.utilitiesmenu.add_command(label="Parallel processing workers", command=self.open_ppw_window)
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
        self.csv_label = ttk.Label(self.browse_frame, text='CSV / XLSX / JSON / JL10 / Fixed Width Format file:').pack(anchor=tk.W, padx=5, pady=5, fill=tk.X)
        self.csv_entry = tk.Entry(self.browse_frame, textvariable=self.csv_file, bd=3)
        self.csv_entry.pack(side='left', expand=True, fill=tk.X)
        self.csv_button = ttk.Button(self.browse_frame, text='Choose file...', command=self.open_csv_file)
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
        self.proc_label = ttk.Label(self.exec_frame, text='')
        self.proc_label.pack(anchor=tk.W, padx=5, pady=5)
        self.exec_label = ttk.Label(self.exec_frame, text='')
        self.exec_label.pack(anchor=tk.W, padx=5, pady=5)
        self.total_label = ttk.Label(self.exec_frame, text='')
        self.total_label.pack(anchor=tk.W, padx=5, pady=5)

        self.holder_frame = tk.Frame(self)
        self.holder_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=tk.TRUE)

        self.text_area = scrolledtext.ScrolledText(self.holder_frame, bg='white', fg='blue', font=("Courier", 11, "normal"), width=1024, heigh=640)
        self.text_area.pack(fill=tk.BOTH, expand=tk.TRUE)
        self.disable_text_area()

        #self.bind('<FocusIn>', self.focus_event_handler)

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.init_state()
        self.check_for_updates(infomsg=False)

    def run_process(self, var, index, mode):
        self.text_area['bg'] = 'white'
        self.text_area['fg'] = 'blue'
        if self.csv_file.get():
            if os.path.exists(self.csv_file.get()): #and (self.csv_file.get().endswith('.csv') or self.csv_file.get().endswith('.xlsx') or self.csv_file.get().endswith('.json') or self.csv_file.get().endswith('.jlx')):
                #sep = util.get_delimiter(self.csv_file.get())
                self.init_state()
                config = cfg.load_config()
                sep = config['delimiter']
                hdr = 'infer' if config['header'] == 'True' else None
                enc = config['encoding']
                jlx_config = cfg.load_config(section='JL10')
                jlx_spec = jlx_config['specification']
                fwf_config = cfg.load_config(section='FWF')
                self.engine = RuleEngine()
                self.engine.df = util.get_dataframe(self.csv_file.get(), delimiter=sep, header=hdr, encoding=enc, type=object, jlx_spec=jlx_spec, fwf_spec=fwf_config)
                if self.engine is not None and self.engine.df is not None:
                    self.engine.df = util.get_df_as_type_string(self.engine.df)
                    self.data_structure()
                    self.show_rule_panel()
                    self.enable_export_menu()
                    self.enable_data_menu()
                    self.init_server_menu()
                else:
                    self.engine = None
                    mb.showwarning(title="Warning!", message="Something went wrong with file reading!", parent=self)
            else:
                self.init_state()
                mb.showwarning(title="Warning!", message="Invalid file!", parent=self)
        else:
            self.init_state() 

    def open_csv_file(self):
        self.csv_file.set(fd.askopenfilename(defaultextension=".csv", filetypes=[("CSV Comma Separatad Values","*.csv"), ("XLSX Spreadsheets","*.xlsx"), ("JSON Files","*.json"), ("JL10 Files","*.jlx"), ("All Files","*.*")]))

    def open_csv_config_window(self):
        self.config_window = ConfigWindow(self)

    def open_jl10_config_window(self):
        self.jl10_config_window = JL10ConfigWindow(self)

    def open_fwf_config_window(self):
        self.fwf_config_window = FixedWidthConfigWindow(self)

    def open_db_config_window(self):
        self.dbconfig_window = DBConfigWindow(self)

    def open_ruledb_window(self):
        self.ruledb_window = RuleDBWindow(self)

    def open_dv_window(self):
        self.dv_window = DataVisualizationWindow(self, df=self.engine.df)

    def open_od_window(self):
        self.od_window = OutlierDetectionWindow(self, parent=self)

    def open_vfd_window(self):
        self.vfd_window = ValueFrequencyDisplayWindow(self, parent=self)

    def open_performance_window(self):
        self.performance_window = PerformanceDisplayWindow(self)

    def open_ppw_window(self):
        self.ppw_window = WorkersManagementWindow(self, parent=self)

    def open_rules_window(self, event):
        self.rules_window = RulesManagementWindow(self, engine=self.engine, columns=util.get_df_columns(self.engine.df), parent=self)

    def export_to_excel(self):
        filename = fd.SaveAs(initialfile='output.xlsx', defaultextension=".xlsx", filetypes=[("XLSX Spreadsheets","*.xlsx")])
        if filename:
            util.df2xlsx(filename.show(), self.engine.df, self.engine.anomalies)

    def export_to_csv(self):
        filename = fd.SaveAs(initialfile='output.csv', defaultextension=".csv", filetypes=[("CSV Files","*.csv")])
        if filename:
            util.df2csv(filename.show(), self.engine.df)

    def export_to_json(self):
        filename = fd.SaveAs(initialfile='output.json', defaultextension=".json", filetypes=[("JSON Files","*.json")])
        if filename:
            util.df2json(filename.show(), self.engine.df)

    def export_to_xml(self):
        filename = fd.SaveAs(initialfile='output.xml', defaultextension=".xml", filetypes=[("XML Files","*.xml")])
        if filename:
            util.df2xml(filename.show(), self.engine.df)

    def export_to_html(self):
        filename = fd.SaveAs(initialfile='output.html', defaultextension=".html", filetypes=[("HTML Files","*.html")])
        if filename:
            util.df2html(filename.show(), self.engine.df)

    def generate_sql(self):
        filename = fd.SaveAs(initialfile='output.sql', defaultextension=".sql", filetypes=[("SQL Files","*.sql")])
        if filename:
            util.df2sql(filename.show(), self.engine.df)

    def data_structure(self):
        txt_content = ''
        bar = '========================================\n'
        info = util.csv_data_structure(df=self.engine.df, method='info')
        info = info[info.index('>')+2:]
        #info += util.csv_data_structure(df=self.engine.df, method='describe')
        txt_content += bar 
        txt_content += '=            Data structure            =\n'
        txt_content += bar
        txt_content += info
        txt_content += bar
        self.text_area_style('white', 'blue')
        self.enable_text_area()
        self.clear_text_area()
        self.text_area.insert(tk.END, txt_content)
        self.disable_text_area()

    def data_preview(self):
        txt_content = util.df_preview(self.engine.df, 10)
        self.text_area_style('white', 'blue')
        self.enable_text_area()
        self.clear_text_area()
        self.text_area.insert(tk.END, txt_content)
        self.disable_text_area()

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
        if version_info:
            web_version = int(version_info['version'].replace('.', ''))
            web_release = version_info['release']
        else:
            web_version = int(self.version.replace('.', ''))
            web_release = self.release
        my_version = int(self.version.replace('.', ''))
        if (web_version > my_version) or (web_version == my_version and web_release != self.release):
            mb.showwarning(title="Warning!", message="A new version is available (" + str(web_version) + " " + web_release + "), get it from " + config['download_url'], parent=self)
        else:
            if infomsg:
                mb.showinfo(title="No newer version", message="You are running the latest vesion of Validator!", parent=self)

    def init_state(self):
        self.engine = None
        if self.server_thread:
            server.RUNFLAG = False
            self.enable_dummy_client_mode()
            self.server_thread = None

        self.title(self.init_title)
        self.disable_export_menu()
        self.disable_data_menu()
        self.hide_rule_panel()
        self.hide_fire_panel()
        self.hide_exec_panel()
        self.disable_server_menu()

    def enable_export_menu(self):
        self.filemenu.entryconfig("Export to Excel", state="normal")
        self.filemenu.entryconfig("Export to Csv", state="normal")
        self.filemenu.entryconfig("Export to Json", state="normal")
        self.filemenu.entryconfig("Export to Xml", state="normal")
        self.filemenu.entryconfig("Export to Html", state="normal")
        self.filemenu.entryconfig("Export to Sql", state="normal")

    def disable_export_menu(self):
        self.filemenu.entryconfig("Export to Excel", state="disabled")
        self.filemenu.entryconfig("Export to Csv", state="disabled")
        self.filemenu.entryconfig("Export to Json", state="disabled")
        self.filemenu.entryconfig("Export to Xml", state="disabled")
        self.filemenu.entryconfig("Export to Html", state="disabled")
        self.filemenu.entryconfig("Export to Sql", state="disabled")

    def enable_data_menu(self):
        self.utilitiesmenu.entryconfig("Data structure", state="normal")
        self.utilitiesmenu.entryconfig("Data preview", state="normal")
        self.utilitiesmenu.entryconfig("Data visualization", state="normal")
        self.utilitiesmenu.entryconfig("Outlier detection (Ensemble model)", state="normal")
        self.utilitiesmenu.entryconfig("Value frequency display", state="normal")
        self.utilitiesmenu.entryconfig("Parallel processing workers", state="normal")

    def disable_data_menu(self):
        self.utilitiesmenu.entryconfig("Data structure", state="disabled")
        self.utilitiesmenu.entryconfig("Data preview", state="disabled")
        self.utilitiesmenu.entryconfig("Data visualization", state="disabled")
        self.utilitiesmenu.entryconfig("Outlier detection (Ensemble model)", state="disabled")
        self.utilitiesmenu.entryconfig("Value frequency display", state="disabled")
        self.utilitiesmenu.entryconfig("Parallel processing workers", state="disabled")

    def init_server_menu(self):
        self.filemenu.entryconfig("Enable server mode", state="normal")
        self.filemenu.entryconfig("Disable server mode", state="disabled")

    def disable_server_menu(self):
        self.filemenu.entryconfig("Enable server mode", state="disabled")
        self.filemenu.entryconfig("Disable server mode", state="disabled")

    def disable_text_area(self):
        self.text_area.configure(state='disabled')

    def enable_text_area(self):
        self.text_area.configure(state='normal')

    def clear_text_area(self):
        self.text_area.delete(1.0, tk.END)

    def hide_browse_panel(self):
        self.browse_frame.forget()
        self.holder_frame.forget()

    def hide_rule_panel(self):
        self.rule_frame.forget()
        self.enable_text_area()
        self.clear_text_area()
        self.disable_text_area()

    def hide_fire_panel(self):
        self.fire_frame.forget()

    def hide_exec_panel(self):
        self.exec_frame.forget()

    def show_browse_panel(self):
        self.browse_frame.pack(side=tk.TOP, fill=tk.X)
        self.holder_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=tk.TRUE)

    def show_rule_panel(self):
        self.rule_frame.pack(after=self.browse_frame, anchor=tk.W)

    def show_fire_panel(self):
        self.fire_frame.pack(after=self.rule_frame, anchor=tk.W, fill=tk.X)

    def show_exec_panel(self):
        self.exec_frame.pack(after=self.fire_frame, anchor=tk.W)

    def show_exec_panel_without_fire(self):
        self.exec_frame.pack(after=self.rule_frame, anchor=tk.W)

    def show_exec_panel_in_server_mode(self):
        self.show_exec_panel_without_fire()

    def close_actions(self, func):
        """
        if func != self.show_exec_panel_in_server_mode:
            self.engine.clear_outliers()
        """
        # Garbage collector (Free Memory)
        gc.collect()

    def result_display(self, start_row, end_row, exec_time, exec_panel_func):
        self.enable_text_area()
        self.clear_text_area()
        total, txt_content = util.get_result(self.engine.anomalies)
        self.text_area_style('black', 'white')
        exec_panel_func()
        self.proc_label['text'] = "Processed rows: " +  str(start_row) + " - " + str(end_row)
        self.exec_label['text'] = "Execution time: " + str(exec_time) + " seconds"
        self.total_label['text'] = "Total invalid values: " + str(total)
        self.text_area.insert(tk.END, txt_content)
        self.disable_text_area()
        self.close_actions(exec_panel_func)

    def rule_handler(self):
        if self.engine and len(self.engine.rules) > 0:
            self.show_fire_panel()
        else:
            self.hide_fire_panel()
            self.hide_exec_panel()

    def fire_all_rules(self, event):
        self.engine.parallel_init()
        if self.engine and len(self.engine.rules) > 0:
            if len(self.server_list) > 0:
                self.enable_client_mode()
            else:
                start = time.time()
                self.engine.fire_all_rules()
                end = time.time()
                self.result_display(1, self.engine.df.shape[0], end - start, self.show_exec_panel)
            
    def copy_to_clipboard(self):
        content = self.text_area.get("1.0", tk.END)
        pyperclip.copy(content)

    def text_area_style(self, bg_color, fg_color):
        self.text_area['bg'] = bg_color
        self.text_area['fg'] = fg_color

    def gui_callback(self, start_row, end_row, exec_time):
        self.result_display(start_row, end_row, exec_time, self.show_exec_panel_in_server_mode)

    def enable_server_mode(self):
        if self.engine is not None and self.engine.df is not None and self.server_thread is None:
            print(f"*** Server IP4 addresses: {util.ip4_addresses()} ***")
            self.title(self.init_title + " [Server mode]")
            self.filemenu.entryconfig("Enable server mode", state="disabled")
            self.filemenu.entryconfig("Disable server mode", state="normal")
            #self.hide_browse_panel()
            self.text_area_style('lightgrey', 'blue')
            server.RUNFLAG = True
            #self.engine = RuleEngine()
            self.server_thread = threading.Thread(target=server.main, args=(self.engine, self.vlib, self.gui_callback))
            self.server_thread.daemon = True
            self.server_thread.start()
            
    def disable_server_mode(self):
        if self.server_thread:
            server.RUNFLAG = False
            self.enable_dummy_client_mode()
            self.server_thread = None
            self.title(self.init_title)
            self.text_area_style('white', 'blue')
            self.data_structure()
            #self.show_browse_panel()
            #self.init_state()
            self.init_server_menu()

    def enable_client_mode(self):
        if self.engine and len(self.engine.rules) > 0:
            start = time.time()
            self.engine.parallel_init()
            total_rows = self.engine.df.shape[0]
            workers = len(self.server_list) + 1
            chunk = int(total_rows / workers)
            #remain = rows % workers
            self_cursor = len(self.server_list) * chunk
            self.engine.data_cursor = self.engine.result_cursor = self_cursor
            client_thread = threading.Thread(target=client.main, args=(self.engine, self.server_list, chunk))
            self_thread = threading.Thread(target=self.engine.fire_all_rules, args=())
            client_thread.start()
            self_thread.start()
            client_thread.join()
            self_thread.join()
            end = time.time()
            self.result_display(self_cursor + 1, total_rows, end - start, self.show_exec_panel)
    
    def enable_dummy_client_mode(self):
        client.main(engine=None, server_list=None, chunk=None, dummy=True)

    def on_closing(self):
        sys.exit()

class RulesManagementWindow(tk.Toplevel):
    def __init__(self, *args, engine=None, columns=None, parent=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry("560x330")
        self.title("Rules panel")

        self.vlib = parent.vlib

        def destroy_event_handler(event):
            if parent and isinstance(event.widget, RulesManagementWindow):
                parent.rule_handler()

        #def _event_handler(event):
        #    _listbox_clear()
        #    _listbox_fill()

        def _listbox_clear():
            self.listbox_clear()

        def _listbox_fill():
            self.listbox_fill(engine)

        def delete_selected_rule():
            selected_rule = self.listbox.curselection()
            if selected_rule and selected_rule[0] < len(engine.rules) and not util.rule_in_cv(selected_rule[0], engine.cross_validation):
                util.change_rule_index_in_cv(selected_rule[0], engine.cross_validation)
                engine.delete_rule(selected_rule[0])
                _listbox_clear()
                _listbox_fill()

        def clear_all():
            engine.clear()
            _listbox_clear()

        def cross_validation_clear():
            engine.cross_validation.clear()
            _listbox_clear()
            _listbox_fill()

        def _import():
            filename = fd.askopenfilename(defaultextension=".xml", filetypes=[("XML Documents","*.xml")])
            if filename:
                clear_all()
                rules_attrib, xml_rules, cross_validation = util.import_from_xml_template(filename)
                op = str(None)
                df_colums = util.get_df_columns(engine.df)
                success_flag = True
                if "logical_operator" in rules_attrib:
                    op = rules_attrib['logical_operator']
                if op == "AND" or op == "OR" or op == "XOR":
                    engine.logical_operator = op
                for x in xml_rules:
                    if x[0] not in df_colums:
                        success_flag = False
                        break
                    #for r in vlib.get_rule_library():
                    for r in self.vlib.rule_library:
                        if x[1] == r.name:
                            engine.add_rule(rule=r, column=x[0], value_range=x[2])
                for i_when, i_then in cross_validation:
                    engine.add_cross_validation(i_when, i_then)
                if success_flag:
                    _listbox_fill()
                else:
                    clear_all()
                    mb.showwarning(title="Warning!", message="Invalid rules template!", parent=self)

        def _export():
            if self.listbox.index("end") > 0:
                filename = fd.SaveAs(initialfile='template.xml', defaultextension=".xml", filetypes=[("XML Documents","*.xml")])
                if filename:
                    util.export_to_xml_template(filename.show(), engine)

        def open_new_rule_window():
            self.new_rule_window = NewRuleWindow(self, parent=self, engine=engine, columns=columns)

        def open_rule_amendment_window():
            selected_rule = self.listbox.curselection()
            if selected_rule and selected_rule[0] < len(engine.rules):
                self.new_rule_window = NewRuleWindow(self, parent=self, engine=engine, columns=columns, amendment=(selected_rule[0], self.listbox.get(selected_rule)))

        def open_cross_validation_window():
            if engine and len(engine.rules) >=2:
                self.cross_validation_window = CrossValidationWindow(self, parent=self, engine=engine)

        def operator_and_state(var, index, mode):
            if self.operator_and.get() == True:
                self.operator_or.set(False)
                self.operator_xor.set(False)
                engine.logical_operator = "AND"
            else:
                engine.logical_operator = None

        def operator_or_state(var, index, mode):
            if self.operator_or.get() == True:
                self.operator_and.set(False)
                self.operator_xor.set(False)
                engine.logical_operator = "OR"
            else:
                engine.logical_operator = None

        def operator_xor_state(var, index, mode):
            if self.operator_xor.get() == True:
                self.operator_and.set(False)
                self.operator_or.set(False)
                engine.logical_operator = "XOR"
            else:
                engine.logical_operator = None

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
        self.crvbtn = tk.Button(self.control_frame, text="Cross validation", width=10, command=open_cross_validation_window)
        self.crvbtn.pack()
        self.cvcbtn = tk.Button(self.control_frame, text="Clear CV", width=10, command=cross_validation_clear)
        self.cvcbtn.pack()

        self.operator_and = tk.BooleanVar()
        self.operator_or = tk.BooleanVar()
        self.operator_xor = tk.BooleanVar()

        self.operator_and.trace_add("write", callback=operator_and_state)
        self.operator_or.trace_add("write", callback=operator_or_state)
        self.operator_xor.trace_add("write", callback=operator_xor_state)

        self.operator_and_check = tk.Checkbutton(self.control_frame, text="AND", variable=self.operator_and, onvalue=True, offvalue=False)
        self.operator_and_check.pack(anchor=tk.W, pady=5)
        self.operator_or_check = tk.Checkbutton(self.control_frame, text="OR", variable=self.operator_or, onvalue=True, offvalue=False)
        self.operator_or_check.pack(anchor=tk.W, pady=5)
        self.operator_xor_check = tk.Checkbutton(self.control_frame, text="XOR", variable=self.operator_xor, onvalue=True, offvalue=False)
        self.operator_xor_check.pack(anchor=tk.W, pady=5)

        _listbox_fill()

        #self.bind('<FocusIn>', _event_handler)
        self.bind('<Destroy>', destroy_event_handler)

        #self.focus()
        self.wait_visibility()
        self.grab_set()

    def event_handler(self, engine):
        self.listbox_clear()
        self.listbox_fill(engine)

    def listbox_clear(self):
        self.listbox.delete(0, tk.END)
        self.operator_and.set(False)
        self.operator_or.set(False)
        self.operator_xor.set(False)

    def listbox_fill(self, engine):
        shift = 1
        for i, r in enumerate(engine.rules):
            vr = ','.join(engine.acceptable_values[i])
            vr = ': ' + vr if vr else ''
            self.listbox.insert(tk.END, str(i+shift) + ') ' + engine.columns_to_check[i] + ' -> ' + r.name + vr)
        if engine.logical_operator == "AND":
            self.operator_and.set(True)
        elif engine.logical_operator == "OR":
            self.operator_or.set(True)
        elif engine.logical_operator == "XOR":
            self.operator_xor.set(True)
        if engine.cross_validation:
            self.listbox.insert(tk.END, "*** Cross validation checks ***")
            for j, k in engine.cross_validation:
                self.listbox.insert(tk.END, "When Rule #" + str(j+shift) + " Then Rule #" + str(k+shift))

class NewRuleWindow(tk.Toplevel):
    def __init__(self, *args, parent=None, engine=None, columns=None, amendment=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry("460x180")
        self.title_text = "New Rule"

        self.vlib = parent.vlib

        self.rule_name = tk.StringVar()
        self.col = tk.StringVar()
        self.vr = tk.StringVar()

        self.rule_name.trace_add("write", callback=self.display_description)

        def add_rule_to_engine(event):
            #for r in vlib.get_rule_library():
            for r in self.vlib.rule_library:
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
        col = ["<<ALL>>"] + columns
        self.column_chooser['values'] = col
        self.rule_chooser = ttk.Combobox(self.control_frame, textvariable=self.rule_name, state="readonly", width=25)
        #self.rule_chooser['values'] = [r.name for r in vlib.get_rule_library()]
        self.rule_chooser['values'] = sorted([r.name for r in self.vlib.rule_library])
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
        #for r in vlib.get_rule_library():
        for r in self.vlib.rule_library:
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

class JL10ConfigWindow(tk.Toplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry("460x180")
        self.title("JL10 Configuration")

        self.spec_panel = tk.Frame(self)
        self.spec_panel.pack(fill=tk.X)
        self.specification_label = ttk.Label(self.spec_panel, text='JL10 specification:')
        self.specification_label.pack(anchor=tk.W, padx=5, fill=tk.X)
        self.text_widget = tk.Text(self.spec_panel, height=9)
        self.text_widget.insert(tk.END, (cfg.load_config(filename='config.ini', section='JL10')['specification']).replace('|', '\n'))
        self.text_widget.pack(anchor=tk.W, fill=tk.X, padx=5)

        self.save_panel = tk.Frame(self)
        self.save_panel.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
        self.savebtn = ttk.Button(self.save_panel, text='Save')
        self.savebtn.pack(fill=tk.X)
        self.savebtn.bind('<Button-1>', self.save_and_exit)

    def save_and_exit(self, event):
        config = {}
        new_spec = self.text_widget.get(1.0, "end-1c")
        new_spec_list = new_spec.split('\n')
        clean_spec_list = []
        for record in new_spec_list:
            if ':' in record:
                clean_spec_list.append(record)
        new_spec = '|'.join(clean_spec_list)
        config['specification'] = new_spec
        cfg.write_config(filename='config.ini', section='JL10', config=config)
        self.destroy()


class FixedWidthConfigWindow(tk.Toplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry("480x340")
        self.title("Fixed Width File Format Configuration")

        self.spec_panel = tk.Frame(self)
        self.spec_panel.pack(fill=tk.X, pady=5)
        self.specification_label = ttk.Label(self.spec_panel, text='Specification:')
        self.specification_label.pack(anchor=tk.W, padx=5, fill=tk.X)
        self.text_widget = tk.Text(self.spec_panel, height=9)
        self.text_widget.insert(tk.END, (cfg.load_config(filename='config.ini', section='FWF')['specification']))
        self.text_widget.pack(anchor=tk.W, fill=tk.X, padx=5)

        self.ignored_panel = tk.Frame(self)
        self.ignored_panel.pack(fill=tk.X, pady=5)
        self.ignored_label = ttk.Label(self.ignored_panel, text='Ignore lines which start with:')
        self.ignored_label.pack(anchor=tk.W, padx=5, fill=tk.X)
        self.ignored_input = tk.Text(self.ignored_panel, height=9)
        self.ignored_input.insert(tk.END, (cfg.load_config(filename='config.ini', section='FWF')['ignored']))
        self.ignored_input.pack(anchor=tk.W, fill=tk.X, padx=5)

        self.save_panel = tk.Frame(self)
        self.save_panel.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
        self.savebtn = ttk.Button(self.save_panel, text='Save')
        self.savebtn.pack(fill=tk.X)
        self.savebtn.bind('<Button-1>', self.save_and_exit)

    def save_and_exit(self, event):
        config = {}
        new_spec = (self.text_widget.get(1.0, "end-1c")).replace('\n', ',')
        new_ignored = (self.ignored_input.get(1.0, "end-1c")).replace('\n', ',')
        config['specification'] = new_spec
        config['ignored'] = new_ignored
        cfg.write_config(filename='config.ini', section='FWF', config=config)
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

        #self.edtbtn["state"] = "disabled"
        #self.delbtn["state"] = "disabled"

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
        if rule:
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

class OutlierDetectionWindow(tk.Toplevel):
    def __init__(self, *args, parent=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry("460x300")
        self.title("Outlier Detection (Ensemble model)")

        def run_process(var, index, mode):
            parent.engine.clear_outliers()
            start = time.time()
            result = util.detect_outliers(parent.engine.df, self.col.get())
            parent.engine.anomaly_detection(self.col.get(), result)
            end = time.time()
            parent.engine.outlier_detection_time = end - start
            parent.result_display(1, parent.engine.df.shape[0], parent.engine.outlier_detection_time, parent.show_exec_panel_without_fire)
            #self.destroy()

        self.columns = util.get_df_columns(parent.engine.df)

        self.col = tk.StringVar()
        self.col.trace_add("write", callback=run_process)

        self.control_frame = tk.Frame(self, borderwidth=2, relief="groove")
        self.control_frame.pack(fill=tk.X)
        self.column_chooser = ttk.Combobox(self.control_frame, textvariable=self.col, state="readonly")
        self.column_chooser.pack(fill=tk.X)
        self.column_chooser['values'] = self.columns

        self.descr_frame = tk.Frame(self, background='lightgrey', relief=tk.GROOVE, padx=5, pady=5)
        self.descr_frame.pack(fill=tk.BOTH, expand=True)
        self.descr_txt = """
[Model #1] 
The interquartile range (IQR) 
is a measure of the spread of the middle 50% of the data. 
The IQR can be calculated as the difference 
between the 75th percentile and the 25th percentile of the dataset. 
Any data point outside the range of 1.5 times 
the IQR below the 25th percentile or above the 75th percentile 
can be considered an outlier.

[Model #2]
Isolation Forest is an unsupervised machine learning algorithm 
used for anomaly detection. It works by isolating anomalies in data 
through a process of random partitioning using a collection of decision trees. 
Anomalies, being different from the majority of the data, 
are expected to be isolated with fewer partitions (shorter paths in the trees). 
"""
        self.descr_label = ttk.Label(self.descr_frame, text=self.descr_txt, background='lightgrey', foreground='blue')
        self.descr_label.pack(fill=tk.X)

        #self.focus()
        self.grab_set()

class WorkersManagementWindow(tk.Toplevel):
    def __init__(self, *args, parent=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry("560x280")
        self.title("Workers panel")

        def open_new_worker_window():
            self.new_worker_window = NewWorkerWindow(self, parent=self, server_list=parent.server_list)

        def _listbox_clear():
            self.listbox_clear()

        def _listbox_fill():
            self.listbox_fill(parent.server_list)

        def delete_selected_worker():
            selectied_worker = self.listbox.curselection()
            if selectied_worker:
                del parent.server_list[selectied_worker[0]]
                _listbox_clear()
                _listbox_fill()

        def clear_all():
            parent.server_list.clear()
            _listbox_clear()
    
        #workers frame
        self.workers_frame = tk.Frame(self)
        self.workers_frame.pack(fill=tk.BOTH, side=tk.LEFT, expand=True)

        #control_frame
        self.control_frame = tk.Frame(self)
        self.control_frame.pack(fill=tk.BOTH, side=tk.RIGHT)

        self.scrollbar = tk.Scrollbar(self.workers_frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.BOTH)

        self.listbox = tk.Listbox(self.workers_frame, activestyle=tk.NONE, selectmode=tk.SINGLE)
        self.listbox.pack(fill=tk.BOTH, expand=True)

        self.listbox.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.listbox.yview)

        self.addbtn = tk.Button(self.control_frame, text="Add", width=10, command=open_new_worker_window)
        self.addbtn.pack()
        self.delbtn = tk.Button(self.control_frame, text="Delete", width=10, command=delete_selected_worker)
        self.delbtn.pack()
        self.delbtn = tk.Button(self.control_frame, text="Clear all", width=10, command=clear_all)
        self.delbtn.pack()

        _listbox_fill()

        #self.focus()
        #self.wait_visibility()
        self.grab_set()

    def event_handler(self, server_list):
        self.listbox_clear()
        self.listbox_fill(server_list)

    def listbox_clear(self):
        self.listbox.delete(0, tk.END)

    def listbox_fill(self, server_list):
        for i, ip in enumerate(server_list):
            self.listbox.insert(tk.END, str(i+1) + ') ' + ip)

class NewWorkerWindow(tk.Toplevel):
    def __init__(self, *args, parent=None, server_list=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry("460x180")
        self.title_text = "New Worker IP"

        self.worker_ip = tk.StringVar()

        def add_worker(event):
            if self.worker_ip.get() not in server_list:
                if parent and server_list is not None and util.server_status_check(self.worker_ip.get()):
                    server_list.append(self.worker_ip.get())
                    parent.event_handler(server_list)
                else:
                    mb.showwarning(title="Warning!", message="The IP address is incorrect or the server is not activated!", parent=self)
                        
        self.control_frame = tk.Frame(self, background='grey', relief=tk.GROOVE)
        self.control_frame.pack(fill=tk.X, side=tk.TOP, pady=5)

        self.ip_entry = tk.Entry(self.control_frame, textvariable=self.worker_ip, bd=3)
        self.ip_entry.pack(fill=tk.X)

        self.addbtn = ttk.Button(self, text='Add worker')
        self.addbtn.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
        self.addbtn.bind('<Button-1>', add_worker)

        self.title(self.title_text)
        #self.focus()
        #self.wait_visibility()
        self.grab_set()

class CrossValidationWindow(tk.Toplevel):
    def __init__(self, *args, parent=None, engine=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry("460x180")
        self.title("Cross Validation")

        def fill_then_list(var, index, mode):
            self.then_rule['values'] = [str(i+1) + ') ' + engine.columns_to_check[i] + ' -> ' + r.name + (': ' + ','.join(engine.acceptable_values[i]) if engine.acceptable_values[i] else '') for i, r in enumerate(engine.rules)]

        def run_process(var, index, mode):
            if self.when.get() and self.then.get():
                shift = 1
                i_when = int(self.when.get().split(')')[0]) - shift
                i_then = int(self.then.get().split(')')[0]) - shift
                engine.add_cross_validation(i_when, i_then)
                parent.event_handler(engine)
                self.destroy()
        
        self.when = tk.StringVar()
        self.when.trace_add("write", callback=fill_then_list)
        self.then = tk.StringVar()
        self.then.trace_add("write", callback=run_process)

        self.control_frame = tk.Frame(self, borderwidth=2, relief="groove")
        self.control_frame.pack(fill=tk.X)
        self.when_label = ttk.Label(self.control_frame, text='When:')
        self.when_label.pack(anchor=tk.W, padx=5, pady=5)
        self.when_rule = ttk.Combobox(self.control_frame, textvariable=self.when, state="readonly")
        self.when_rule.pack(fill=tk.X)
        self.when_rule['values'] = [str(i+1) + ') ' + engine.columns_to_check[i] + ' -> ' + r.name + (': ' + ','.join(engine.acceptable_values[i]) if engine.acceptable_values[i] else '') for i, r in enumerate(engine.rules)]
        self.then_label = ttk.Label(self.control_frame, text='Then:')
        self.then_label.pack(anchor=tk.W, padx=5, pady=5)
        self.then_rule = ttk.Combobox(self.control_frame, textvariable=self.then, state="readonly")
        self.then_rule.pack(fill=tk.X)
        self.then_rule['values'] = []

        #self.focus()
        self.grab_set()

class ValueFrequencyDisplayWindow(tk.Toplevel):
    def __init__(self, *args, parent=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry("560x280")
        self.title("Value Frequency Display")

        self.columns = util.get_df_columns(parent.engine.df)

        def listbox_clear():
            self.listbox.delete(0, tk.END)

        def listbox_fill():
            val_freq = parent.engine.df[self.col.get()].value_counts(normalize=True) * 100
            for i, v in val_freq.items():
                if i == '':
                    i = 'NULL'
                self.listbox.insert(tk.END, str(i) + ' --> ' + str(round(v, 2)) + '%')

        def run_process(var, index, mode):
            listbox_clear()
            listbox_fill()
            

        self.col = tk.StringVar()
        self.col.trace_add("write", callback=run_process)

        self.control_frame = tk.Frame(self, borderwidth=2, relief="groove")
        self.control_frame.pack(fill=tk.X, side=tk.TOP)
        self.col_label = ttk.Label(self.control_frame, text='Select column:')
        self.col_label.pack(anchor=tk.W, padx=5, pady=5)
        self.col_chooser = ttk.Combobox(self.control_frame, textvariable=self.col, state="readonly")
        self.col_chooser.pack(fill=tk.X)
        self.col_chooser['values'] = self.columns

        #display_frame
        self.display_frame = tk.Frame(self)
        self.display_frame.pack(fill=tk.X, side=tk.BOTTOM, expand=True)

        self.scrollbar = tk.Scrollbar(self.display_frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.BOTH)

        self.listbox = tk.Listbox(self.display_frame, activestyle=tk.NONE, selectmode=tk.SINGLE)
        self.listbox.pack(fill=tk.BOTH, expand=True)

        self.listbox.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.listbox.yview)

        #self.focus()
        self.grab_set()

class PerformanceDisplayWindow(tk.Toplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry("360x130")
        self.title("Performance Monitor")

        self.RUNNING_FLAG = True
        self.RUNNING_COUNTER = 0

        self.style = ttk.Style()
        self.style.configure("custom.TLabel", foreground="blue")

        self.style_2 = ttk.Style()
        self.style_2.configure("custom2.TLabel", foreground="red")

        self.monitor_frame = tk.Frame(self, borderwidth=2, relief="groove")
        self.monitor_frame.pack(fill=tk.BOTH, expand=True, side=tk.TOP)
        self.cpu_text = "CPU Usage: "
        self.cpu_label = ttk.Label(self.monitor_frame, text=self.cpu_text, style='custom.TLabel')
        self.cpu_label.pack(anchor=tk.W, padx=5, fill=tk.X)
        self.ram_text = "Memory Usage: "
        self.ram_label = ttk.Label(self.monitor_frame, text=self.ram_text, style='custom.TLabel')
        self.ram_label.pack(anchor=tk.W, padx=5, fill=tk.X)
        self.proc_mem_text = "Process Memory Usage: "
        self.proc_mem_label = ttk.Label(self.monitor_frame, text=self.proc_mem_text, style='custom.TLabel')
        self.proc_mem_label.pack(anchor=tk.W, padx=5, fill=tk.X)
        self.hdd_text = "Disk Usage: "
        self.hdd_label = ttk.Label(self.monitor_frame, text=self.hdd_text, style='custom.TLabel')
        self.hdd_label.pack(anchor=tk.W, padx=5, fill=tk.X)
        self.eth_text = "Ethernet: "
        self.eth_label = ttk.Label(self.monitor_frame, text=self.eth_text, style='custom.TLabel')
        self.eth_label.pack(anchor=tk.W, padx=5, fill=tk.X)

        self.exitbtn = ttk.Button(self, text='Terminate Performance Monitor')
        self.exitbtn.pack(fill=tk.X, side=tk.BOTTOM)
        self.exitbtn.bind('<Button-1>', self.terminate_monitor)

        self.protocol("WM_DELETE_WINDOW", self.terminate_monitor)

        self.monitor_thread = threading.Thread(target=self.performance_monitor, args=())
        self.monitor_thread.start()

        #self.focus()
        self.grab_set()

    def performance_monitor(self):
        while self.RUNNING_FLAG:
            # CPU usage
            cpu_usage = psutil.cpu_percent(interval=1)
            self.cpu_text = f"CPU Usage: {cpu_usage}%"
            self.cpu_label['text'] = self.cpu_text
            #print(f"CPU Usage: {cpu_usage}%")
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.ram_text = f"Memory Usage: {memory.percent}%"
            self.ram_label['text'] = self.ram_text
            #print(f"Memory Usage: {memory.percent}%")

            # Process memory usage
            self.proc_mem_text = f"Process Memory Usage: {round(psutil.Process(os.getpid()).memory_info().rss / 1024 ** 2, 2)} MB"
            self.proc_mem_label['text'] = self.proc_mem_text
            #print(f"Process Memory Usage: {round(psutil.Process(os.getpid()).memory_info().rss / 1024 ** 2, 2)} MB")
            
            # Disk usage
            disk_usage = psutil.disk_usage('/')
            self.hdd_text = f"Disk Usage: {disk_usage.percent}%"
            self.hdd_label['text'] = self.hdd_text
            #print(f"Disk Usage: {disk_usage.percent}%")
            
            # Network usage
            network = psutil.net_io_counters()
            self.eth_text = f"Ethernet: Bytes Sent: {network.bytes_sent}, Bytes Received: {network.bytes_recv}"
            self.eth_label['text'] = self.eth_text
            #print(f"Ethernet: Bytes Sent: {network.bytes_sent}, Bytes Received: {network.bytes_recv}")
            
            # Adding a separator for readability
            #print("-" * 50)
            
            # Wait for a few seconds before the next update
            self.RUNNING_COUNTER += 1
            time.sleep(5)

    def terminate_monitor(self, event=None):
        if self.RUNNING_COUNTER > 0:
            self.RUNNING_FLAG = False
            #self.monitor_thread.join()
            self.destroy()

if __name__ == "__main__":
    myapp = App()
    myapp.mainloop()
