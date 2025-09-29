#
# project: CSV Validator
#
# Create rules drom remote rule library
#
# georgios mountzouris 2025 (gmountzouris@efka.gov.gr)
#

import re
import math
import time
import v_config as cfg
import v_pgdev as pgd
import v_utilities as util
import v_common as common
from v_rule import Rule
from v_pgdev import Pgdev
from datetime import datetime
from string import whitespace


#################################################################
# ......................:: RULE LIBRARY ::......................#
#################################################################

class RuleLibrary():
    def __init__(self):
        self.rule_library = list()
        self.pgconf = cfg.load_config(section='postgresql')
        self.connection = pgd.connection_test(self.pgconf)
        #self.import_modules()
        self.build_rule_library()

    def import_modules(self):
        if self.connection:
            rows = util.get_db_import_statements(self.pgconf)
            for row in rows:
                exec(row[1])

    def build_rule_library(self):
        #check the connection to DB
        #if the connection fails then load the local rule library
        #else build rule libray from DB Rules
        if not self.connection:
            import v_local_library as local
            self.rule_library = local.rule_library
        else:
            #if util.get_db_rules_number(pgconf) < 25:
            #    import v_local_library as local
            #    rule_library = local.rule_library
            #else:
                rows = util.get_db_rules(self.pgconf)
                for row in rows:
                    """ Linux only version """
                    #exec(row[4])
                    #exec(f"rule=Rule(name='{row[1]}', descr='{row[2]}', func={row[3]})")
                    #exec("self.rule_library.append(rule)")
                    """ Linux & Windows version"""
                    exec_str = row[4] + "\n" + f"rule=Rule(name='{row[1]}', descr='{row[2]}', func={row[3]})" + "\n" + "self.rule_library.append(rule)"      
                    try:
                        exec(exec_str)
                    except Exception as e:
                        print(repr(e))
#################################################################
