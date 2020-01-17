#!/bin/python3
#
# Test script to convert datatime entries and search data within given log file
# Author: Igor Yozhikov <medput@gmail.com>
# Provides as-is
#
import os
import re
import sys
import getopt
from datetime import datetime
from pytz import timezone

# Placeholder for short date to be converted
last_dt = {'year': '', 'tz': ''}

# Functions
def convert_tz(s_input, tz='US/Pacific', dt_format='%d/%b/%Y:%H:%M:%S %z'):
    o_datetime = datetime.strptime(s_input, dt_format)
    # Set year and TZ values obtained from long datemine string at the same log entry:
    if o_datetime.tzinfo == None and o_datetime.year == 1900:
        o_datetime = o_datetime.replace(year=last_dt['year'],tzinfo=timezone(last_dt['tz']))
    else:
        last_dt['year'] = int(o_datetime.year)
        last_dt['tz'] = str(o_datetime.tzinfo)
    o_datetime_pacific = o_datetime.astimezone(timezone(tz))
    return o_datetime_pacific.strftime(dt_format)

def search_in_log(s_input,search_string):
    found_counter = 0
    if len(search_string.split("=")) == 2:
        search_key=search_string.split("=")[0]
        search_val=search_string.split("=")[1]
        # Searching among HTTP requests
        if search_key in ('method', 'request'):
            pattern = r"\"(HEAD|GET|POST|PUT|DELETE)\s.+?\w\""
            match = re.search(pattern,s_input)
            if match:
                if re.search(search_val,match.group()):
                    found_counter += 1
        # Searching among client software
        elif search_key in ('software', 'client'):
            pattern = r"\"\w.*?\""
            # last entry in the line like: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.59 Safari/537.36"
            match = re.findall(pattern,s_input)[-1]
            if match:
                if re.search(search_val,match):
                    found_counter += 1
        # Searching among response codes 
        elif search_key in ('response', 'code'):
            pattern = r"\s\d{3}\s"
            match = re.search(pattern,s_input)
            if match:
                if re.search(search_val,match.group()):
                    found_counter += 1
    else:
        # Search for all matches
        search_val=search_string
        matches = re.findall(search_val,s_input)
        found_counter += len(matches)
    return found_counter

def read_log(input_filename,search_string=''):
    # Datetime regex
    # Example: Nov 28 23:05:14
    dtime_short_re = r"^\w{3}\s\d{1,2}\s\d{1,2}:\d{1,2}:\d{1,2}"
    # Example: 28/Nov/2016:23:06:53 +0000
    dtime_long_re = r"\d{1,2}\/\w{3}\/\d{4}:\d{1,2}:\d{1,2}:\d{1,2}\s(\+||\-)\d{4}"
    search_counter = 0
    with open(input_filename) as fp:
        for line in fp:
            # Working with date entries
            match_long = re.search(dtime_long_re, line)
            if match_long:
                l_initial_date = match_long.group()
                l_converted_date = convert_tz(l_initial_date)
            match_short = re.search(dtime_short_re, line)
            if match_short:
                s_initial_date = match_short.group()
                s_converted_date = convert_tz(s_initial_date,'US/Pacific','%b %d %H:%M:%S')
            # Replace dates with converted values
            new_line = re.sub(dtime_short_re,s_converted_date,line,1)
            new_line = re.sub(dtime_long_re,l_converted_date,new_line,1)
            print(new_line.rstrip('\r\n'))
            # Search
            if len(search_string) > 0:
                search_counter += search_in_log(new_line,search_string)
    if len(search_string) > 0:
        print("""############# S E A R C H   R E S U L T S #############
        Search request: \"%s\", found: %i entries""" % (search_string,search_counter))

# main
def main():
    input_filename = ''
    search_string = ''
    # Processsing command line arguments
    if len(sys.argv) == 1:
        print("""Usage %s -i[--input] filename -s[--search] search_string
        search_string - 'any data' will search all occurrences
        search_string - key=value will search at prticular parts of log entry
            key: method or request, value=GET,POST,PUT,DELETE,etc
            key: software or client, value=Chrome, Mozlilla, UptimeRobot, etc
            key: response or code, value=200, 304, 404, etc
        """ % sys.argv[0])
        exit(1)
    try:
        options, restopts = getopt.gnu_getopt(
            sys.argv[1:],
            'i:s:',
            ['input=',
            'search=',
            ])
    except getopt.GetoptError as err:
        print('ERROR:', err)
        sys.exit(1)
    for opt, arg in options:
        if opt in ('-i', '--input'):
            if os.path.exists(arg) or os.path.isfile(arg):
                input_filename = arg
            else:
                print('Wrong file path %s or access or file type!' % arg)
                exit(1)
        elif opt in ('-s', '--search') :
            if len(arg) > 0:
                search_string = arg
            else:
                pass
    # Processsing log file
    read_log(input_filename,search_string)

if __name__ == "__main__":
    main()