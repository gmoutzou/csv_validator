#
# project: CSV Validator
#
# Vaidation Rule Engine
#
# georgios mountzouris 2025 (gmountzouris@efka.gov.gr)
#

import pandas as pd
import functools

class RuleEngine():
    def __init__(self, df):
        self.rules = []
        self.columns_to_check = []
        self.acceptable_values = []
        self.anomalies = {}
        self.df = df
    
    def add_rule(self, rule, column, value_range):
        self.rules.append(rule)
        self.columns_to_check.append(column)
        self.acceptable_values.append(value_range)

    def delete_rule(self, index):
        del self.rules[index]
        del self.columns_to_check[index]
        del self.acceptable_values[index]

    def anomaly_detection(self, column, result):
        invalid_list = []
        for i, t in enumerate(result):
            if t[0] == False:
                v = t[1]
                invalid_list.append((i+1, v))
        if invalid_list:
            self.anomalies[column] = invalid_list

    def clear(self):
        self.rules.clear()
        self.columns_to_check.clear()
        self.acceptable_values.clear()
        self.anomalies.clear()

    def fire_all_rules(self):
        self.anomalies.clear()
        """ Iterate over Rows in DataFrame
        self.df = self.df.reset_index()
        for i, row in self.df.iterrows():
            for j, column in enumerate(self.columns_to_check):
                print(row[column])
        """
        """ Iterate over columns in DataFrame
        for series_name, series in self.df.items():
            if series_name == 
            for v in series:
                print(v)
        """
        """ Iterate over columns_to_check and apply the corresponding rule function """
        for i, column in enumerate(self.columns_to_check):
            column_values = self.df[column].tolist()
            #result = list(map(self.rules[i].apply, column_values))
            result = list(map(functools.partial(self.rules[i].apply, value_range=self.acceptable_values[i]), column_values))
            self.anomaly_detection(column, result)
            