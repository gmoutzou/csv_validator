#!/home/dev/anaconda3/envs/tensorflow/bin/python3
"""#!/bin/python3"""
#
# project: CSV Validator
#
# debugging script
#
# georgios mountzouris 2025 (gmountzouris@efka.gov.gr)
#

import pandas as pd
import v_local_library as vlib
import v_utilities as util
from v_engine import RuleEngine

"""
#sep = util.get_delimiter('./test.csv')
sep = ';'
df = util.get_dataframe('./test1.csv', delimiter=sep, type=object)
#print(util.csv_data_structure(df, "info"))
df = util.get_df_as_type_string(df)
#print(util.get_df_columns(df))
#print(util.csv_data_structure(df, "info"))
#df = pd.DataFrame({'amka': ['0', '12345678901', '05098102790', ''], 'afm': ['070359257', '100000001', '0', '']})
engine = RuleEngine(df)
engine.add_rule(rule=vlib.rule_library[9], column='SUM(NVL(PENSION,0))', value_range=util.get_value_range('0'))
engine.fire_all_rules()
util.print_result(engine.anomalies)
"""

print(vlib.amka_check('29027000032', []))