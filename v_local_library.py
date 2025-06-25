#
# project: CSV Validator
#
# Rule library
#
# georgios mountzouris 2025 (gmountzouris@efka.gov.gr)
#

import re
import math
from v_rule import Rule
from datetime import datetime
from string import whitespace

rule_library = list()

""" 3 Steps to import custom rules to library """
""" 
#1 Write a Function
Warning! 
Two arguments: $1 value to check, $2 value range 
Always return boolean
"""
def dummy(x, value_range):
    """
    ***dummy function*** 

    :param x: value to check
    :param value_range: list of values to check

    :return: tuple of boollean and the value x
    """ 
    for y in value_range:
        if x % y == 0:
            continue
        else:
            return False
    return True

""" 
#2 Rule Instantiation 
Give a name, a description and the function to apply to your rule
"""
rule = Rule(name='R1', descr='Dummy Rule #1', func=dummy)

""" #3 Import to Rule Library """
rule_library.append(rule)

##################################################################
# ......................:: LOCAL LIBRARY ::......................#
##################################################################

rule_library.clear()

##################################################################

#In value range [0]
def in_value_range(value, value_range):
    if value_range and len(value_range) == 2:
        return (float(value.replace(',', '.')) >= float(value_range[0].replace(',', '.')) and float(value.replace(',', '.')) <= float(value_range[1].replace(',', '.')))
    else:
        return True

rule = Rule(name='in_value_range', descr='Check if the column values \nare in the given value range (e.g 10~100)', func=in_value_range)
rule_library.append(rule)
##################################################################

#In acceptable values [1]
def in_acceptable_values(value, value_range):
    if value_range:
        return (value in value_range)
    else:
        return True

rule = Rule(name='in_acceptable_values', descr='Check if the column contains \nonly the given acceptable values (e.g. 12,25,50,99)', func=in_acceptable_values)
rule_library.append(rule)
##################################################################

#In value range [2]
def not_in_value_range(value, value_range):
    if value_range and len(value_range) == 2:
        return not (float(value.replace(',', '.')) >= float(value_range[0].replace(',', '.')) and float(value.replace(',', '.')) <= float(value_range[1].replace(',', '.')))
    else:
        return True

rule = Rule(name='not_in_value_range', descr='Check if the column values \nare not in the given value range (e.g 10~100)', func=not_in_value_range)
rule_library.append(rule)
##################################################################

#Not acceptable values [3]
def not_acceptable_values(value, value_range):
    if value_range:
        return not (value in value_range)
    else:
        return True

rule = Rule(name='not_acceptable_values', descr='Check if the column contains \nvalues which are not in the given value list (e.g. 12,25,50,99)', func=not_acceptable_values)
rule_library.append(rule)
##################################################################

#Grater than [4]
def greater_than(value, value_range):
    if value_range:
        return (float(value.replace(',', '.')) > float(value_range[0].replace(',', '.')))
    else:
        return True

rule = Rule(name='greater_than', descr='Check if the column values \nare greater than the given value', func=greater_than)
rule_library.append(rule)
##################################################################

#Grater or equal [5]
def greater_or_equal(value, value_range):
    if value_range:
        return (float(value.replace(',', '.')) >= float(value_range[0].replace(',', '.')))
    else:
        return True

rule = Rule(name='greater_or_equal', descr='Check if the column values \nare greater than or equal to the given value', func=greater_or_equal)
rule_library.append(rule)
##################################################################

#Less than [6]
def less_than(value, value_range):
    if value_range:
        return (float(value.replace(',', '.')) < float(value_range[0].replace(',', '.')))
    else:
        return True

rule = Rule(name='less_than', descr='Check if the column values \nare less than the given value', func=less_than)
rule_library.append(rule)
##################################################################

#Less or equal [7]
def less_or_equal(value, value_range):
    if value_range:
        return (float(value.replace(',', '.')) <= float(value_range[0].replace(',', '.')))
    else:
        return True

rule = Rule(name='less_or_equal', descr='Check if the column values \nare less than or equal to the given value', func=less_or_equal)
rule_library.append(rule)
##################################################################

#equal [8]
def equal_to(value, value_range):
    if value_range:
        return (float(value.replace(',', '.')) == float(value_range[0].replace(',', '.')))
    else:
        return True

rule = Rule(name='equal_to', descr='Check if the column values \nare equal to the given value', func=equal_to)
rule_library.append(rule)
##################################################################

#Not equal [9]
def not_equal_to(value, value_range):
    if value_range:
        return (float(value.replace(',', '.')) != float(value_range[0].replace(',', '.')))
    else:
        return True

rule = Rule(name='not_equal_to', descr='Check if the column values \nare not equal to the given value', func=not_equal_to)
rule_library.append(rule)
##################################################################

#Is null [10]
def is_null(value, value_range):
    return (str(value) == "")

rule = Rule(name='is_null', descr='Check if the column contains null values', func=is_null)
rule_library.append(rule)
##################################################################

#Is not null [11]
def is_not_null(value, value_range):
    return (not is_null(value, value_range))

rule = Rule(name='is_not_null', descr='Check if the column contains not null values', func=is_not_null)
rule_library.append(rule)
##################################################################

#Is numeric [12]
def is_numeric(value, value_range):
    return str(value).isnumeric()

rule = Rule(name='is_numeric', descr='Check if the column contains numeric values', func=is_numeric)
rule_library.append(rule)
##################################################################

#Is boolean [13]
def is_boolean(value, value_range):
    return (str(value) == '0' or str(value) == '1' 
            or str(value).upper() == 'TRUE' or str(value).upper() == 'FALSE' 
            or str(value).upper() == 'T' or str(value).upper() == 'F' 
            or str(value).upper() == 'YES' or str(value).upper() == 'NO' 
            or str(value).upper() == 'Y' or str(value).upper() == 'N')

rule = Rule(name='is_boolean', descr='Check if the column contains boolean values', func=is_boolean)
rule_library.append(rule)
##################################################################

#Is string [14]
def is_string(value, value_range):
    return isinstance(value, str)

rule = Rule(name='is_string', descr='Check if the column contains string values', func=is_string)
rule_library.append(rule)
##################################################################

#String length between [15]
def string_length_between(value, value_range):
    if value_range and len(value_range) == 2:
        return (value_range[0] <= len(value) <= value_range[1])
    else:
        return True

rule = Rule(name='string_length_between', descr='Check if the column contains string values \nwhich length is within the value range (e.g. 5~15)', func=string_length_between)
rule_library.append(rule)
##################################################################

#Starts with [16]
def starts_with(value, value_range):
    if value_range:
        for s in value_range:
            if value.startswith(s):
                return True
        return False
    else:
        return True

rule = Rule(name='starts_with', descr='Check if the column contains values \nwhich start with one of the given values (e.g. GR,GRE,GRC)', func=starts_with)
rule_library.append(rule)
##################################################################

#Ends with [17]
def ends_with(value, value_range):
    if value_range:
        for s in value_range:
            if value.endswith(s):
                return True
        return False
    else:
        return True

rule = Rule(name='ends_with', descr='Check if the column contains values \nwhich end with one of the given values (e.g. GR,GRE,GRC)', func=ends_with)
rule_library.append(rule)
##################################################################

#Not starts with [18]
def not_starts_with(value, value_range):
    if value_range:
        for s in value_range:
            if value.startswith(s):
                return False
        return True
    else:
        return True

rule = Rule(name='not_starts_with', descr='Check if the column contains values \nwhich not start with one of the given values (e.g. GR,GRE,GRC)', func=not_starts_with)
rule_library.append(rule)
##################################################################

#Not ends with [19]
def not_ends_with(value, value_range):
    if value_range:
        for s in value_range:
            if value.endswith(s):
                return False
        return True
    else:
        return True

rule = Rule(name='not_ends_with', descr='Check if the column contains values \nwhich not end with one of the given values (e.g. GR,GRE,GRC)', func=not_ends_with)
rule_library.append(rule)
##################################################################
#No leading whitespace [20]
def no_leading_whitespace(value, value_range):
    if value:
        return not (value[0] in whitespace)
    else:
        return True

rule = Rule(name='no_leading_whitespace', descr='Check if the column contains values \nwhich have no leading whitespace', func=no_leading_whitespace)
rule_library.append(rule)
##################################################################

#No trailing whitespace [21]
def no_trailing_whitespace(value, value_range):
    if value:
        return not (value[-1] in whitespace)
    else:
        return True

rule = Rule(name='no_trailing_whitespace', descr='Check if the column contains values \nwhich have no trailing whitespace', func=no_trailing_whitespace)
rule_library.append(rule)
##################################################################

#No inner space [22]
def no_inner_space(value, value_range):
    if value:
        return not (len(value.strip().split()) > 1)
    else:
        return True

rule = Rule(name='no_inner_space', descr='Check if the column contains values \nwhich do not have inner whitespace', func=no_inner_space)
rule_library.append(rule)
##################################################################

#No inner multiple spaces [23]
def no_inner_multispace(value, value_range):
    if value:
        space = 0
        for c in value.strip():
            if c == " ":
                if space == 0:
                    space += 1
                elif space == 1:
                    return False
            elif space == 1:
                space = 0
        return True
    else:
        return True

rule = Rule(name='no_inner_multispace', descr='Check if the column contains values \nwhich do not have multiple inner spaces', func=no_inner_multispace)
rule_library.append(rule)
##################################################################

#No space [24]
def no_space(value, value_range):
    return not (' ' in value)

rule = Rule(name='no_space', descr='Check if the column contains values \nwhich do not have whitespaces', func=no_space)
rule_library.append(rule)
##################################################################

#Matches decimal format [25]
def matches_decimal_format(value, value_range):
    return True if value and (len(value.split(',')[-1]) == 2) else False

rule = Rule(name='matches_decimal_format', descr='Check if the column contains values \nwhich are float numbers with comma and 2 decimal places', func=matches_decimal_format)
rule_library.append(rule)
##################################################################

#Matches date format with slashes [26]
def valid_date_slash_format(value, value_range):
    res = True
    format = "%d/%m/%Y"
    pattern_str = r'^\d{2}/\d{2}/\d{4}$'
    if re.match(pattern_str, value):
        try:
            res = bool(datetime.strptime(value, format))
        except ValueError:
            res = False
    else:
        res = False
    return res

rule = Rule(name='valid_date_slash_format', descr='Check if the column values match with date format DD/MM/YYY', func=valid_date_slash_format)
rule_library.append(rule)
##################################################################

#Matches date format with dashes [27]
def valid_date_dash_format(value, value_range):
    res = True
    format = "%d-%m-%Y"
    pattern_str = r'^\d{2}-\d{2}-\d{4}$'
    if re.match(pattern_str, value):
        try:
            res = bool(datetime.strptime(value, format))
        except ValueError:
            res = False
    else:
        res = False
    return res

rule = Rule(name='valid_date_dash_format', descr='Check if the column values match with date format DD-MM-YYY', func=valid_date_dash_format)
rule_library.append(rule)
##################################################################

#AMKA check [28]
def amka_check(amka, value_range):

    #amka = str(amka)

    def is_valid_amka_date(_amka):
        d = _amka[:2]
        m = _amka[2:4]
        y = _amka[4:6]
        amka_date = y + '-' + m + '-' + d
        date_format = '%y-%m-%d'
        try:
            dateObject = datetime.strptime(amka_date, date_format)
        except ValueError:
            return False
        return True

    sum = 0
    i = 0
    dbl = 0

    # Check if the input is null
    if not amka or amka is None:
        return False
    
    amka = amka.strip().zfill(11)
    
    # Check if is valid date the first 6 digits of the input
    #if not is_valid_amka_date(amka):
    #    return False
        
    # Check if the input length is 11
    if len(amka) != 11:
        return False
    
	# Check if the input is a valid integer
    if not amka.isdigit():
        return False
    
    # Convert to integer for validation
    amka_number = int(amka)
    if amka_number == 0 or amka_number > 99999999999 or amka_number < 1010000000:
        return False
    
    # Calculate the checksum
    while i < 10:
        i += 1
        dbl = int(amka[10 - i]) * 2
        sum += dbl % 10
        if dbl > 9:
            sum += math.floor(dbl / 10)  # Add the tens place
        i += 1
        dbl = int(amka[10 - i])
        sum += dbl  # Add the digit directly
    
    c = sum % 10
    chk = (10 - c) % 10

	# Check the last digit (checksum)
    if amka[10] == str(chk):
        return True

    return False

rule = Rule(name='is_valid_amka', descr='Check if the column contains valid AMKA numbers', func=amka_check)
rule_library.append(rule)
##################################################################

#AFM check [29]
def afm_check(afm, value_range):
    """Checks if the passed AFM is a valid AFM number

    Parameters
    ----------
    afm : str
        A string to be check if it's a valid AFM
    
    Returns
    -------
        A boolean result
    """

    #afm = str(afm)

    if len(afm) != 9:
        return False

    if not re.match(r"^\d+$", afm):
        return False

    if afm == "0" * 9:
        return False

    body = afm[:8]
    sum = 0
    
    for i in range(len(body)):
        digit = body[i]
        sum += int(digit) << (8 - i)
    
    calc = sum % 11
    d9 = int(afm[8])
    valid = calc % 10 == d9
    
    return valid

rule = Rule(name='is_valid_afm', descr='Check if the column contains valid AFM numbers', func=afm_check)
rule_library.append(rule)
##################################################################
