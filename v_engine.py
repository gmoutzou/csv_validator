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
        self.logical_operator = None
        self.df = df
    
    def add_rule(self, rule, column, value_range):
        self.rules.append(rule)
        self.columns_to_check.append(column)
        self.acceptable_values.append(value_range)

    def delete_rule(self, index):
        del self.rules[index]
        del self.columns_to_check[index]
        del self.acceptable_values[index]

    def modify_rule(self, index, rule, column, value_range):
        self.rules[index] = rule
        self.columns_to_check[index] = column
        self.acceptable_values[index] = value_range

    def anomaly_detection(self, column, result):
        invalid_list = [(i+1, t[0]) for i, t in enumerate(result) if t[1] == False]
        if invalid_list:
            if not column in self.anomalies:
                self.anomalies[column] = invalid_list
            else:
                self.anomalies[column] += invalid_list

    def op_and(self, x, y):
        #res = [(lambda f, s: (f[0], f[1] and s[1]))(j, k) for j, k in zip(x, y)] #lambda function in list comprehension#
        res = [(j[0], j[1] and k[1]) for j, k in zip(x, y)]
        return res
    
    def op_or(self, x, y):
        #res = [(lambda f, s: (f[0], f[1] or s[1]))(j, k) for j, k in zip(x, y)] #lambda function in list comprehension#
        res = [(j[0], j[1] or k[1]) for j, k in zip(x, y)]
        return res
    
    def op_xor(self, x, y):
        #res = [(lambda f, s: (f[0], f[1] != s[1]))(j, k) for j, k in zip(x, y)] #lambda function in list comprehension#
        res = [(j[0], j[1] != k[1]) for j, k in zip(x, y)]
        return res

    def logical_operator_apply(self, op, *argv):
        res = functools.reduce(op, argv)
        return res

    def clear(self):
        self.rules.clear()
        self.columns_to_check.clear()
        self.acceptable_values.clear()
        self.anomalies.clear()
        self.logical_operator = None

    def fire_all_rules(self):
        self.anomalies.clear()
        """ Iterate over columns_to_check and apply the corresponding rule function """
        if not self.logical_operator:
            for i, column in enumerate(self.columns_to_check):
                column_values = self.df[column].tolist()
                result = list(map(functools.partial(self.rules[i].apply, value_range=self.acceptable_values[i]), column_values))
                self.anomaly_detection(column, result)
        else:
            op = None
            aggregation_result = None
            # Get unique set of columns to check
            colset = set(self.columns_to_check)
            # Iterate over columns set and apply the corresponding rule function, group the result by column
            results = [[list(map(functools.partial(self.rules[i].apply, value_range=self.acceptable_values[i]), self.df[c].tolist())) for i, c in enumerate(self.columns_to_check) if c == x] for x in colset]

            if self.logical_operator == "AND":
                op = self.op_and
            elif self.logical_operator =="OR":
                op = self.op_or
            elif self.logical_operator =="XOR":
                op = self.op_xor

            if op:
                # Apply logical operator and reduce the results
                aggregation_result = list(map(lambda x: self.logical_operator_apply(op, *x), results)) #unpack the function arguments using the asterisk
            if aggregation_result:
                # Get the invalid values
                for col, res in zip(colset, aggregation_result):
                    self.anomaly_detection(col, res)
