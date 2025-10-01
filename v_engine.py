#
# project: CSV Validator
#
# Vaidation Rule Engine
#
# georgios mountzouris 2025 (gmountzouris@efka.gov.gr)
#

import pandas as pd
import threading
import functools


class RuleEngine():
    def __init__(self):
        self.rules = []
        self.columns_to_check = []
        self.acceptable_values = []
        self.anomalies = {}
        self.cross_validation = []
        #self.process_flag = False
        #self.cv = threading.Condition()
        self.lock = threading.RLock()
        self.result_cursor = 0
        self.data_cursor = 0
        self.rows = -1
        self.logical_operator = None
        self.outlier_detection_time = 0.0
        self.df = None
    
    def add_rule(self, rule, column, value_range):
        if column == "<<ALL>>":
            all_columns = list(self.df)
            for c in all_columns:
                self.add_rule(rule, c, value_range)
        else:
            self.rules.append(rule)
            self.columns_to_check.append(column)
            self.acceptable_values.append(value_range)

    def add_cross_validation(self, i_when, i_then):
        self.cross_validation.append((i_when, i_then))

    def delete_rule(self, index):
        del self.rules[index]
        del self.columns_to_check[index]
        del self.acceptable_values[index]

    def modify_rule(self, index, rule, column, value_range):
        self.rules[index] = rule
        self.columns_to_check[index] = column
        self.acceptable_values[index] = value_range

    def anomaly_detection(self, column, result, is_dictionary=False):
        #print('--> start anomaly detection', 'Thread ID', threading.current_thread().ident)
        if is_dictionary:
            #self.cv.acquire()
            #while self.process_flag:
            #    self.cv.wait()
            #self.process_flag = True
            with self.lock:
                for k, v in result.items():
                    invalid_list = [tuple(val) for val in v]
                    #print('Invalid values for column', k, invalid_list)
                    if not k in self.anomalies:
                        self.anomalies[k] = invalid_list
                    else:
                        self.anomalies[k] += invalid_list
            #self.process_flag = False
            #self.cv.notify_all()
            #self.cv.release()
        else:
            invalid_list = [(i+1+self.result_cursor, t[0]) for i, t in enumerate(result) if t[1] == False]
            if invalid_list:
                #self.cv.acquire()
                #while self.process_flag:
                #    self.cv.wait()
                #self.process_flag = True
                with self.lock:
                    if not column in self.anomalies:
                        self.anomalies[column] = invalid_list
                    else:
                        self.anomalies[column] += invalid_list
                #self.process_flag = False
                #self.cv.notify_all()
                #self.cv.release()

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
        self.cross_validation.clear()
        self.clear_outliers()
        self.parallel_init()
        self.logical_operator = None

    def clear_outliers(self):
        with self.lock:
            self.anomalies.clear()
        self.outlier_detection_time = 0.0

    def parallel_init(self):
        self.clear_outliers()
        #self.process_flag = False
        self.result_cursor = 0
        self.data_cursor = 0
        self.rows = -1

    def fire_all_rules(self):

        def fire_without_op(i, column):
            column_values = (self.df[column][self.data_cursor:self.rows]).tolist()
            result = list(map(functools.partial(self.rules[i].apply, value_range=self.acceptable_values[i]), column_values))
            # Alternative version
            """
            result = []
            for v in column_values:
                result.append(self.rules[i].apply(value=v, value_range=self.acceptable_values[i]))
            """
            self.anomaly_detection(column, result)

        self.clear_outliers()
        if self.rows == -1:
            self.rows = self.df.shape[0]

        # Get the invalid values from cross validation
        if self.cross_validation and len(self.rules) >= 2:
            shift = 1
            for row in self.df[self.data_cursor:self.rows].itertuples():
                for i_when, i_then in self.cross_validation:
                    when_col_idx = self.df.columns.get_loc(self.columns_to_check[i_when]) + shift
                    then_col_idx = self.df.columns.get_loc(self.columns_to_check[i_then]) + shift
                    if self.rules[i_when].apply(row[when_col_idx], self.acceptable_values[i_when])[1] == True and self.rules[i_then].apply(row[then_col_idx], self.acceptable_values[i_then])[1] == False:
                        invalid_list = [(row.Index + shift, row[then_col_idx])]
                        with self.lock:
                            if not self.columns_to_check[i_then] in self.anomalies:
                                self.anomalies[self.columns_to_check[i_then]] = invalid_list
                            else:
                                self.anomalies[self.columns_to_check[i_then]] += invalid_list

        # Simple rule set
        if not self.logical_operator:
            # Iterate over columns_to_check and apply the corresponding rule function
            for i, c in enumerate(self.columns_to_check):
                # If the column is in the cross validation, ignore it
                if self.cross_validation:
                    for j, k in self.cross_validation:
                        if i != j and i != k:
                            fire_without_op(i, c)
                else:
                    fire_without_op(i, c)
        # Rule set with logical operator
        else:
            op = None
            aggregation_result = None
            # Get unique set of columns to check
            colset = set(self.columns_to_check)
            # Remove the cross validation columns from column set
            if self.cross_validation:
                colset_without_cv = set()
                for col in colset:
                    for j, k in self.cross_validation:
                        if col != self.columns_to_check[j] and col != self.columns_to_check[k]:
                            colset_without_cv.add(col)
                colset = colset_without_cv
            # Iterate over column set and apply the corresponding rule function, group the results by column
            total_results = [[list(map(functools.partial(self.rules[i].apply, value_range=self.acceptable_values[i]), self.df[c][self.data_cursor:self.rows].tolist())) for i, c in enumerate(self.columns_to_check) if c == x] for x in colset]
            # Alternative version
            """
            print('*** start apply the rules')
            total_results = []
            for x in colset:
                column_results = []
                for i, c in enumerate(self.columns_to_check):
                    if c == x:
                        #rule_results = list(map(functools.partial(self.rules[i].apply, value_range=self.acceptable_values[i]), self.df[c][self.data_cursor:self.rows].tolist()))
                        rule_results = []
                        for v in self.df[c][self.data_cursor:self.rows].tolist():
                            rule_results.append(self.rules[i].apply(v, self.acceptable_values[i]))
                        column_results.append(rule_results)
                if column_results:
                    total_results.append(column_results)
            print('*** end apply the rules')
            """
            # Set the logical operator function
            if self.logical_operator == "AND":
                op = self.op_and
            elif self.logical_operator =="OR":
                op = self.op_or
            elif self.logical_operator =="XOR":
                op = self.op_xor

            if op:
                # Apply logical operator function and reduce the results
                aggregation_result = list(map(lambda x: self.logical_operator_apply(op, *x), total_results)) # Unpack the function arguments using the asterisk
                # Alternative version
                """
                aggregation_result = []
                for n in total_results:
                    aggregation_result.append(self.logical_operator_apply(op, *n))
                """
            if aggregation_result:
                # Finally get the invalid values
                for col, res in zip(colset, aggregation_result):
                    self.anomaly_detection(col, res)
                        