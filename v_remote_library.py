#!/home/dev/anaconda3/envs/tensorflow/bin/python3
"""#!/bin/python3"""
#
# project: CSV Validator
#
# Create rules drom remote rule library
#
# georgios mountzouris 2025 (gmountzouris@efka.gov.gr)
#

import v_config as cfg
import v_pgdev as pgd
from v_pgdev import Pgdev

#################################################################
# ......................:: RULE LIBRARY ::......................#
#################################################################

pgconf = cfg.load_config(section='postgresql')
connection = pgd.connection_test(pgconf)

if connection:
    with Pgdev(pgconf) as pgdev:
        sql = "SELECT * FROM validator.modules;"
        rows = pgdev.fetch_data_all(sql)
        for row in rows:
            exec(row[1])

def get_rule_library():
    rule_library = list()
    #check the connection to DB
    #if connection fails then load the local rule library
    #else build rule libray from DB Rules
    if not connection:
        import v_library
        rule_library = v_library.rule_library
    else:
        with Pgdev(pgconf) as pgdev:
            sql = "SELECT * FROM validator.rules;"
            rows = pgdev.fetch_data_all(sql)
            for row in rows:
                exec(row[4])
                exec(f"rule = Rule(name='{row[1]}', descr='{row[2]}', func={row[3]})")
                exec("rule_library.append(rule)")
    return rule_library

#################################################################

