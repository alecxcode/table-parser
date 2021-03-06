#!/usr/bin/python3
# coding: UTF-8

# Copyright (c) 2021, Alexander Vankov
# Permission to use, copy, modify, and/or distribute this software for any purpose with or without fee is hereby granted provided that redistributions of source code retain the above copyright notice and this condition.
# THIS SOFTWARE IS PROVIDED "AS IS" AND WITHOUT ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.

# Tested with:
# Python 3.8 or 3.9
# package versions:
# beautifulsoup4 4.9
# requests       2.24

import sys
import re
import time
import datetime
from datetime import datetime
from datetime import timedelta
import os.path
import sqlite3
import requests
from bs4 import BeautifulSoup

# Initial variables:
prog_name = "Table Parser"
prog_ver = "0.9"
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0"
start_url = "http://127.0.0.1" # place your address here
myheaders = {"User-Agent": user_agent}
mycookies = {}
username = "your_login_name" # place your login here
password_file = "authdata.dat" # store your password in this file
text_to_understand_not_logged_in = "Some text that shows your are not logged in" # insert your text
# Load auth data:
try:
    f = open(password_file, "r")
    password = f.readline()
    f.close()
except Exception as e:
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Loading: unable to get authdata" + "\n" + str(e))
# authdata - login and password if required to login
# you need to see the complete data with you browser developer tools:
authdata = {"username": username, "password": password}
# Some codes:
req_timeout = 100 # time to wait for responce (requests package)
conn_error = 801 # some error code related to connection problems
force_encd = False # set this to True if your need encd value below
encd = 'utf-8' # web pages encoding, not applicable if force_encd = False

# Dicts and lists:
# from local DB:
elements_list_db = [] # List from DB [elemet ID, elemet ID, ...]
elements_dict_db = {} # Dict from DB {elemet ID: {name: value}}
# From the web page:
elements_list = [] # List from the page [elemet ID, elemet ID, ...]
elements_dict = {} # Dict from the page {elemet ID: {name: value}}
# New elements found on the page:
new_elements_list = [] # New elements from the page

# Some colors for terminal output
BLUE = '\033[1;34m'
GREEN = '\033[1;32m'
RED = '\033[1;31;48m'
END = '\033[0;37m'



# Functions definitions

# Save cookies:
def saveCookies():
    try:
        f = open("cookies.dat", "w")
        for item in mycookies:
            f.write(item + ' = ' + mycookies[item] + '\n')
        f.close()
    except Exception as e:
        print(curtime(), "saveCookies: unable to save cookies file" + "\n" + str(e))

# Load cookies:
def loadCookies():
    mycookies.clear()
    try:
        f = open("cookies.dat", "r")
        for stringcook in f:
            onecooklist = stringcook.rstrip().split(' = ', 1)
            mycookies[onecooklist[0]] = onecooklist[1]
        f.close()
    except Exception as e:
        print(curtime(), "loadCookies: unable to open cookies file" + "\n" + str(e))

# Check if the user is logged in, and login if not:
def checkLogin():
    try:
        r = requests.get(start_url, headers = myheaders, cookies = mycookies, timeout = req_timeout)
        if r.status_code >= 400:
            print(curtime(), 'checkLogin: HTTP_Error:', r.status_code)
            return r.status_code
    except Exception as e:
        print(curtime(), "checkLogin: connection failure" + "\n" + str(e))
        return conn_error
    if text_to_understand_not_logged_in in r.text:
        print(curtime(), "User is not logged in")
        with requests.Session() as s:
            try:
                r = s.post(start_url, data = authdata, headers = myheaders, timeout = req_timeout)
                mycookies.clear()
                mycookies.update(requests.utils.dict_from_cookiejar(s.cookies))
                print(curtime(), "User now is logged in")
                saveCookies()
                if r.status_code >= 400:
                    print(curtime(), 'checkLogin: HTTP_Error:', r.status_code)
                    return r.status_code
                else:
                    if force_encd:
                        r.encoding = encd
                    return r.text
            except Exception as e:
                print(curtime(), "checkLogin: login failure" + "\n" + str(e))
                return conn_error
    else:
        if force_encd:
            r.encoding = encd
        return r.text

# Build elements dict and list from the raw html page:
def buildElemsDict(raw_html):
    soup = BeautifulSoup(raw_html, 'html.parser')
    trows = soup.find_all('tr')
    for row in trows:
        cells = row.find_all('td')
        if len(cells) > 0:
            element = {}
            # below is an integer extraction example:
            element['elem_ID'] = int(cells[0].text.strip())
            # below is some text data extraction examples:
            element['name1'] = cells[1].text.strip()
            element['name2'] = cells[2].text.strip()
            element['name3'] = cells[3].text.strip()
            # could be more table data cells ...
            # below is date and time extraction example:
            element['date_and_time'] = datetime.strptime(cells[4].text.strip(), '%Y-%m-%d %H:%M')
            # could be more table data cells ...
            elements_dict[element['elem_ID']] = element # add to dict
            elements_list.append(element['elem_ID']) # add to list
            elements_list.sort()

# Let's suppose each element has additional data on its page:
def addElemsDetails(elemslist):
    for elem_ID in elemslist:
        raw_page = getElemPage(elem_ID)
        if type(raw_page) == int:
            print(curtime(), 'addElemsDetails: get element failure ' + str(elem_ID))
            return raw_page
        # The code of this function could be some different, surely
        # Example of regex search, non-greedy, dot inclides newlines:
        elem_data_regex = re.compile('<p id="someid">.*?</p>', flags=re.DOTALL)
        elem_data = elem_data_regex.search(raw_page).group().replace('<p id="someid">', '').replace('</p>', '').strip()
        # Make the soup from the element page:
        tsoup = BeautifulSoup(raw_page, 'html.parser')
        # Update the elements dict with example of beautifulsoup search:
        elements_dict[elem_ID]['somecontent'] = tsoup.find('div', id = "some_content_id").text.strip()
        elements_dict[elem_ID]['somelinks'] = tsoup.find_all('a', class_= "some_link_class")
        elements_dict[elem_ID]['somedata'] = elem_data

# Get element page:
def getElemPage(elem_ID):
    if type(elem_ID) != str:
        elem_ID = str(elem_ID)
    complete_url = start_url + '/' + elem_ID + '.html' # could be some different, surely
    try:
        r = requests.get(complete_url, headers = myheaders, cookies = mycookies, timeout = req_timeout)
        if r.status_code >= 400:
            print(curtime(), 'getElemPage: ' + elem_ID + ' HTTP_Error:', r.status_code)
            return r.status_code
        else:
            if force_encd:
                r.encoding = encd
            return r.text
    except Exception as e:
        print(curtime(), "getElemPage: connection to element failed " + elem_ID + "\n" + str(e))
        return conn_error

# Load files from element page:
def getElemFiles(elem_ID):
    # this is not complete in this version of the script
    pass

# Find new elements which are not in DB:
def findNewElems():
    for elem_ID in elements_list:
        if elem_ID not in elements_list_db:
            new_elements_list.append(elem_ID)
    new_elements_list.sort()

# Add elemtnts to DB:
def addElemsIntoDB(elemslist):
    elements_to_add = []
    for ins_elem in elemslist:
        elements_to_add.append((elements_dict[ins_elem]['elem_ID'],
                               elements_dict[ins_elem]['name1'],
                               elements_dict[ins_elem]['name2'],
                               elements_dict[ins_elem]['name3'],
                               elements_dict[ins_elem]['date_and_time'].strftime('%Y-%m-%d %H:%M'),
                               elements_dict[ins_elem]['somecontent'],
                               str(elements_dict[ins_elem]['somelinks']),
                               elements_dict[ins_elem]['somedata']))
    c.executemany('INSERT INTO elements VALUES (?,?,?,?,?,?,?,?)', elements_to_add)
    conn.commit()

# Delete elements from DB:
def deleteElemsFromDB(elemslist):
    elements_to_delete = []
    for ins_elem in elemslist:
        elements_to_delete.append((elements_dict[ins_elem]['elem_ID'],))
    c.executemany('DELETE FROM elements WHERE elem_ID=?', elements_to_delete)
    conn.commit()

# Update somedata value:
def updateDataInBD(elem_ID, performer_fullname):
    somedata = elements_dict[elem_ID]['somedata']
    data_to_update = (somedata, elem_ID)
    c.execute('UPDATE elements SET somedata=?, WHERE elem_ID=?', data_to_update)
    conn.commit()

# Analyze element using parsed and extracted data:
def analyzeElem(elem_ID):
    pass # place your code to do smth with data extracted
    some_result = None
    return some_result

# Return current time in string human readable form:
def curtime():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")



# Main code
# -------------------
# Greeting on launch:
print(prog_name)
print('Version: ' + prog_ver)
print(GREEN + '''

      TABLE PARSER
       _--------_
      |[0]    [0]|
      |    ..    |
       \__====__/
          |  |
      ANALYZER BOT

''' + END)

# Open log:
try:
   logfilename = datetime.now().strftime('%Y-%m') + '-log.txt'
   l = open(logfilename, 'a', encoding=encd)
   sys.stdout = l # redirection to log file, comment when testing
except Exception as e:
   print(curtime(), RED, "Cannot open log file", END, "\n", str(e))

# Print current time, uncomment for testing or if necessary:
# print('Bot run at:', curtime())

# loading cookies:
loadCookies()

# Check if the user is logged in, and login if not,
# and get the start page:
resp = checkLogin()

# If no errors, then build dict and list of elements:
if type(resp) == int:
    print(curtime(), 'Server error while trying to connect:', resp)
else:
    buildElemsDict(resp)

# load elements table from DB, or create DB if it does not exist:
if os.path.exists('tablep.db'):
    # Open DB and load data to dict
    conn = sqlite3.connect('tablep.db')
    c = conn.cursor()
    c.execute('SELECT * FROM elements ORDER BY elem_ID DESC')
    # comment the line above and uncomment below if you need to set SQL limit
    # c.execute('SELECT * FROM elements ORDER BY elem_ID DESC LIMIT 1024')
    result = ''
    while not result == None:
        result = c.fetchone()
        if not result == None:
            # Add to list:
            elem_ID = result[0]
            elements_list_db.append(elem_ID)
            # Add to dict:
            element = {}
            element['elem_ID'] = result[0]
            element['name1'] = result[1]
            element['name2'] = result[2]
            element['name3'] = result[3]
            element['date_and_time'] = datetime.strptime(result[4], '%Y-%m-%d %H:%M')
            element['somecontent'] = result[5]
            element['somelinks'] = BeautifulSoup(result[6], 'html.parser').find_all('a')
            element['somedata'] = result[7]
            elements_dict_db[element['elem_ID']] = element
    elements_list_db.sort()
else:
    # Create new DB if it does not exist:
    conn = sqlite3.connect('tablep.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE elements
             (elem_ID INTEGER PRIMARY KEY,
             name1 TEXT,
             name2 TEXT,
             name3 TEXT,
             date_and_time TEXT,
             somecontent TEXT,
             somelinks TEXT,
             somedata TEXT)''')
    conn.commit()

# Looking for new elements:
findNewElems()
# Printing new elements found:
if new_elements_list:
    print(curtime(), 'Found new elements:', new_elements_list)
# Update new elements list:
addElemsDetails(new_elements_list)

for each_elem in elements_list:
    if each_elem in elements_list_db:
        elements_dict[each_elem]['somecontent'] = elements_dict_db[each_elem]['somecontent']
        elements_dict[each_elem]['somelinks'] = elements_dict_db[each_elem]['somelinks']
        elements_dict[each_elem]['somedata'] = elements_dict_db[each_elem]['somedata']

# Updating DB with new elements found:
addElemsIntoDB(new_elements_list)
print(curtime(), 'Added to DB:', new_elements_list)

# Here is some placeholder code:
for each_elem in new_elements_list:
    some_return_value = analyzeElem(each_elem)
# You can add some code to send POST requests, etc.

# Close connection to DB, and close log:
conn.close()
f.close()

# # Print debug info: all elements in the dict:
# # uncomment if required for testing
# print(elements_list)
# print(elements_dict)
# print(elements_list_db)
# print(elements_dict_db)
