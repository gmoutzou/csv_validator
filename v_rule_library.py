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
import v_utilities as util
from v_pgdev import Pgdev

#################################################################
# ......................:: RULE LIBRARY ::......................#
#################################################################

pgconf = cfg.load_config(section='postgresql')
connection = pgd.connection_test(pgconf)

if connection:
    rows = util.get_db_import_statements(pgconf)
    for row in rows:
        exec(row[1])

def get_rule_library():
    rule_library = list()
    #check the connection to DB
    #if the connection fails then load the local rule library
    #else build rule libray from DB Rules
    if not connection:
        import v_local_library as local
        rule_library = local.rule_library
    else:
        #if util.get_db_rules_number(pgconf) < 25:
        #    import v_local_library as local
        #    rule_library = local.rule_library
        #else:
            rows = util.get_db_rules(pgconf)
            for row in rows:
                exec(row[4])
                exec(f"rule=Rule(name='{row[1]}', descr='{row[2]}', func={row[3]})")
                exec("rule_library.append(rule)")
    return rule_library

#################################################################
