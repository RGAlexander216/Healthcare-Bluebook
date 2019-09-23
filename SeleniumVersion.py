import pandas
import requests
import os.path
import json
import lxml
import re
import selenium
import chromedriver_binary
import chromedriver_binary as chromedriver

from collections import OrderedDict
from copy import deepcopy
from time import sleep
from bs4 import BeautifulSoup
from pandas import DataFrame, Series
from pandas.io.json import json_normalize
from argparse import ArgumentParser
from selenium import webdriver
from selenium.webdriver import Chrome, chrome, ChromeOptions

if chromedriver.chromedriver_filename not in list(os.environ.values()):
    os.environ.update({'ChromeDriver':chromedriver.chromedriver_filename})

driver = Chrome()

from Requester import Requester

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-s', '--search_term', type=str,
                        help='Search Term, Use double-quotes for terms with spaces',
                        default='MRI')
    parser.add_argument('-t', '--search_type', type=str,
                        help='Search Type (Procedure, Doctor, Hospital)',
                        default='Procedure')
    parser.add_argument('-z', '--search_zip', type=int,
                        help='Search Zip Code',
                        default=37201)
    parser.add_argument('-m', '--min_percentile', type=int,
                        help='Minimum Percentile to Return',
                        default=80)
    try:
        search_args = parser.parse_args()
    except (UsageError, SystemExit):
        search_args = parser.parse_known_args()[0]
    
    r = Requester(search_args)
    r.perform_search()
    driver.get('https://www.healthcarebluebook.com/ui/consumerfront')
    sleep(3)
    try:
        driver.find_element_by_css_selector('#tbZipCode2').send_keys(r.search_zip)
        driver.find_element_by_xpath('//*[@id="searchZipButton"]').click()
    except:
        pass
    driver.find_element_by_xpath('//*[@id="ibSearch"]').send_keys(r.search_term)
    driver.find_element_by_xpath('//*[@id="searchControls"]/div[3]').click()
    sleep(3)
    try:
        driver.find_element_by_xpath('//*[@id="primarySection"]/div[2]/div[2]/div/div/div[2]/a[4]').click()
        sleep(3)
    except:
        pass
    driver.get('https://www.healthcarebluebook.com/ui/consumerfront')
    sleep(3)
    driver.find_element_by_xpath('//*[@id="ibSearch"]').send_keys(r.search_term)
    driver.find_element_by_xpath('//*[@id="searchControls"]/div[3]').click()

