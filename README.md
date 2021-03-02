# Table Parser

This simple Python program is a parser example, which reads HTML table and some other related pages. It extracts data from table cells and other pages into a list and a dictionary and stores in SQLite database. Hope it will be useful for someone, as this task seems to be common enough.  
The parser just gets the raw html page, then finds all `<TD>` tags, then fetches data from them, then loads pages related to these data, parses them, retrieves additional data from these pages (RegEx and BeautifulSoup examples are present), saves everything to DB.  
You can find cookie saving and loading, log in to the site by POST request and some other useful code snippets here.  
The license for the software is **BSD-like**. You can use it almost without limitations.

## Program requirements

Python 3.8 or 3.9 will do. Other versions was not tested.  
You need to install the following packages:

* BeautifulSoup (4.9 or newer tested)
* Requests (2.24 or newer tested)

How to install them? Through pip:  
```
pip install bs4 requests
```

## How to use this software  
You should carefully read the code and **change it** to your needs.  
This code is an abstract example.  
There are some test files in the directory `testfiles`, you can upload them to a test website to see how the program works with them.  

#### The following is the dictionary of elements and their types:
```python
elements_dict[elem_ID]['elem_ID'] # integer
elements_dict[elem_ID]['name1'] # string
elements_dict[elem_ID]['name2'] # string
elements_dict[elem_ID]['name3'] # string
elements_dict[elem_ID]['date_and_time'] # datetime (in DB text)
elements_dict[elem_ID]['somecontent'] # string
elements_dict[elem_ID]['somelinks'] # list (in DB text)
elements_dict[elem_ID]['somedata'] # string
```
