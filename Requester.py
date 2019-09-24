import pandas
import requests
import os
import json
import lxml
import re
import xlsxwriter
from collections import OrderedDict
from copy import deepcopy
from os import path
from time import sleep
from bs4 import BeautifulSoup
from pandas import DataFrame, Series
from pandas.io.json import json_normalize
from argparse import ArgumentParser
from IPython.core.error import UsageError
from IPython.display import display


class Requester(object):
    """ Object container for all http requests
    """
    HBB_URL = 'https://www.healthcarebluebook.com'
    CONSUMER_URL = f'{HBB_URL}/ui/consumerfront'
    UI_HOME_URL = f'{HBB_URL}/ui/home'
    APP_CONFIG_URL = f'{HBB_URL}/ui/assets/data/app-config.json'
    OTHER_VISITOR_URL = f'{HBB_URL}/api/HcbbUI/SetMarketplaceMedicare'
    SEARCH_API_URL = f'{HBB_URL}/api/HcbbUI/GetSearchResults'
    SEARCH_UI_URL = f'{HBB_URL}/ui/searchresults'
    APP_INIT_URL = f'{HBB_URL}/api/HcbbUI/applicationinit'
    SEARCH_LOG_URL = f'{HBB_URL}/api/HcbbUI/Log'
    SET_ZIP_URL = f'{HBB_URL}/api/HcbbUI/GetZipLocation'
    IDENT_URL = f'{HBB_URL}/api/HcbbUI/CheckIdentCookie'
    TYPE_AHEAD_URL = f'{HBB_URL}/api/HcbbUI/getTypeAheadLists'
    GET_LOG_URL = f'{HBB_URL}/api/HcbbUI/Log'
    PROC_DETAIL_UI_URL = f'{HBB_URL}/ui/proceduredetails'
    PROC_DETAIL_API_URL = f'{HBB_URL}/api/HcbbUI/GetProcedureDetails'
    SEARCH_TYPES = {'Procedure': '1', 'Doctor': '2', 'Hospital': '3'}
    
    def __init__(self, search_args):
        """ Creates the requests.Session() object for use throughout the class 
        """
        self.session = requests.Session()
        self.search_args = search_args
        self.search_term = search_args.search_term
        self.search_type_input = search_args.search_type
        self.search_type = self.SEARCH_TYPES[search_args.search_type]
        self.search_zip = search_args.search_zip
        self.search_term_id = None
        self.__update_session_headers()
    
    def export_fair_priced_procedure_data(self):
        """ The main tool to perform a data export for procedures at or below a fair price
        """
        response = self._perform_search()
        self.price = self.__define_fair_price(response)
        file_path = os.path.join('.','Results',self.search_term+'.xlsx')
        if not path.exists(path.dirname(file_path)):
            os.makedirs(path.dirname(file_path))
        writer = pandas.ExcelWriter(os.path.abspath(file_path),
                                    engine='xlsxwriter')
        df = DataFrame(response.json())
        df = DataFrame([df['ProcedureDetails']['FacilityInformation']])
        df = DataFrame(df['Facilities'][0])               
        df = df[df['CostIndicator'] == 1]
        df.to_excel(excel_writer=writer, sheet_name='Fair Priced Procedures')
        writer.save()
        print(f'Your Results Have Been Saved in the Excel '+\
              f'Workbook Found Here: {writer.path}')
        return df
            
    def _execute_request(self, url, method='GET', params=None, call_before_return=None):
        """ Class Universal Request Method,
                Rate Limits the period between consecutive requests to 1 second
                
            `call_before_return` can be any function defined within the class or as a
                lambda function. The function must only take a response-like object as
                it does not alter the object, but can alter the initial parameters that
                were provided by the user. i.e. search_term if the input matches  
                more than one category available on the site.
        """
        sleep(1.5)
        if params is None:
            params = {}
        response = self.session.request(url=url, method=method, params=params)
        
        if call_before_return is not None:
            call_before_return(response)
        return response
    
    def _perform_search(self):
        """ Retrieve the HTML Consumer Front User Interface HTML
                Returns as an BeatifulSoup (LXML) Markup Object
                
            This also specifies to the site that we should be looking at the
                non-physician, non-medicare price rates by internally calling
                the Requester.__set_marketplace_medicare_false() method
        """
        response = self._execute_request(url=self.CONSUMER_URL,
                                         method='GET',
                                         params={})
        response = self._execute_request(url=self.SEARCH_UI_URL,
                                         method='GET',
                                         params={'SearchTerms': self.search_term,
                                                 'Tab': 'ShopForCare'})
        response = self._execute_request(url=self.APP_INIT_URL,
                                         method='GET',
                                         params={})
        response = self._execute_request(url=self.TYPE_AHEAD_URL,
                                         method='GET',
                                         params={'GetZipList': 'true'},
                                         call_before_return=self.__check_valid_input)
        response = self._execute_request(url=self.OTHER_VISITOR_URL,
                                         method='GET',
                                         params={'Medicare': 'false'})
        response = self._execute_request(url=self.SET_ZIP_URL,
                                         method='GET',
                                         params={'request.ZipCode': str(self.search_zip)})
        response = self._execute_request(url=self.IDENT_URL,
                                         method='GET',
                                         params={})
        response = self._execute_request(url=self.TYPE_AHEAD_URL,
                                         method='GET',
                                         params={'GetZipList': 'true'},
                                         call_before_return=self.__check_valid_input)
        response = self._execute_request(url=self.GET_LOG_URL,
                                         method='GET',
                                         params=self.__define_log_params())
        response = self._execute_request(url=self.PROC_DETAIL_UI_URL+f'/{self.search_term_id}',
                                         method='GET',
                                         params={})
        response = self._execute_request(url=self.PROC_DETAIL_API_URL,
                                         method='GET',
                                         params={'Language': 'en',
                                                 'CftId': self.search_term_id})
        return response
    
    def __update_session_headers(self, response=None):
        """ If `response` is None this will update the user-agent header for the
            Requester.session object, however, if a response is provided this serves
            to update the 'Cookie' header of Requester.session.
        """
        loop_count = 0
        if response is None:
            user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '+\
                         '(KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36'
            self.session.headers['User-Agent'] = user_agent
            response = self.session.get(url=self.SEARCH_UI_URL)
        else:
            copy_response = deepcopy(response)
            while True:
                if 'Set-Cookie' in copy_response.headers.keys() and loop_count == 0:
                    loop_count += 1
                    header = copy_response.headers.pop('Set-Cookie')
                    try:
                        self.session.headers['Cookie'] += '; '+header
                    except (KeyError):
                        self.session.headers['Cookie'] = header
                else:
                    break
    
    def __define_log_params(self):
        """ Request Done within the Browser to Obtain Some Specific Session Cookies
        """
        params = {
            "request.level":"5",
            "request.pageName":"consumerfront",
            "request.url":"https://www.healthcarebluebook.com/ui/consumerfront",
            "request.zipCode":"00000","request.isMobileBrowser":"false",
            "request.userAgent":
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '+\
                '(KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36',
            "request.customerCode":"hcbb_prod",
            "request.language":"en"}
        return params
    
    def __define_fair_price(self, response):
        """ Get the floating point value of a "Fair" Procedure Price
        """
        df = DataFrame(response.json())
        if df['ProcedureDetails']['DisplayCaptcha'] is False:
            df = df['ProcedureDetails']['PricingInformations']
            price = df[0]['FairPrice']
            price = price.replace('$','')
            price = price.replace(',','')
            return float(price)
        else:
            raise SystemExit('Unfortunately The Site Is Requesting A '+\
                             'User Answer a reCAPTCHA image for human '+\
                             'Verification. This Cannot Be Bypassed Until'+\
                             'A New Session is Created or The Current IP '+\
                             'Address has Changed.')
        
    def __check_valid_input(self, response):
        match_func = lambda x: re.search(self.search_term, x) is not None
        df = DataFrame(response.json()).T
        df = DataFrame(df['Procedures']['TypeAheadLists'])
        df['Match'] = df['DisplayNameEnglish'].apply(match_func)
        match_df = df[df['Match'] == True][['DisplayNameEnglish','ProcedureId']]
        if match_df.index.__len__() > 1:
            match_df.sort_values(by='DisplayNameEnglish', inplace=True)
            for k,v in dict(match_df.values).items():
                print(f'{self.search_type_input} {v}: {k}')
            print(f'\nThere are Multiple Matches for {self.search_term}.\n'+\
                  f'Please Enter the Number from the list above Corresponding '+\
                  f'to the desired {self.search_type_input}.')
            while True:
                self.search_term_id = int(input(f'\nEnter {self.search_type_input} ID: '))
                if self.search_term_id in match_df['ProcedureId'].tolist():
                    break
                else:
                    print(f'The {self.search_type_input} ID Provided was not '+\
                          f'found in the list provided.\nPlease Enter a Valid '+\
                          f'{self.search_type_input} ID')
            new_df = match_df[match_df['ProcedureId'] == self.search_term_id]
            self.search_term = new_df['DisplayNameEnglish'].values[0]
        return response
        
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
                        default=37221)
    try:
        search_args = parser.parse_args()
    except (UsageError, SystemExit):
        pandas.set_option('display.max_columns', 999)
        search_args = parser.parse_known_args()[0]
    
    r = Requester(search_args)
    r.export_fair_priced_procedure_data()
    