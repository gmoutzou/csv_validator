#
# project: CSV Validator
#
# Common Functions
#
# georgios mountzouris 2025 (gmountzouris@efka.gov.gr)
#

from dateutil.parser import parse

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
