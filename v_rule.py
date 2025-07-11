#
# project: CSV Validator
#
# Vaidation Rule Module
#
# georgios mountzouris 2025 (gmountzouris@efka.gov.gr)
#

class Rule():
    def __init__(self, name, descr, func):
        self.name = name
        self.descr = descr
        self.func = func

    def apply(self, value, value_range):
        try:
            return (value, self.func(value, value_range))
        except ValueError:
            return (value, False)
