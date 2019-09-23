import pandas
import requests
import os.path
import json
import lxml
import re
import xlsxwriter
from collections import OrderedDict
from copy import deepcopy
from time import sleep
from bs4 import BeautifulSoup
from pandas import DataFrame, Series
from pandas.io.json import json_normalize
from argparse import ArgumentParser

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
        self.search_term = search_args.search_term
        self.search_type_input = search_args.search_type
        self.search_type = self.SEARCH_TYPES[search_args.search_type]
        self.search_zip = search_args.search_zip
        self.min_percentile = search_args.min_percentile
        self.search_term_id = None
        self.__update_session_headers()
        
    def __check_valid_input(self, response):
        match_func = lambda x: re.search(self.search_term, x) is not None
        df = DataFrame(response.json()).T
        df = DataFrame(df['Procedures']['TypeAheadLists'])
        df['Match'] = df['DisplayNameEnglish'].apply(match_func)
        match_df = df[df['Match'] == True]
        if match_df.index.__len__() > 1:
            for k,v in dict(match_df[['DisplayNameEnglish','ProcedureId']].values).items():
                print(k,v)
            print(f'\nThere are Multiple Matches for {self.search_term}.\n'+\
                  f'Please Enter the Number from the list above Corresponding '+\
                  f'to the desired {self.search_type_input}:\n')
            self.search_term_id = int(input('\nEnter ID: '))
            new_df = match_df[match_df['ProcedureId'] == self.search_term_id]
            self.search_term = new_df['DisplayNameEnglish'].values[0]
        return response
            
    def _execute_request(self, url, method='GET', params=None, call_before_return=None):
        """ Class Universal Request Method,
                Rate Limits the period between consecutive requests to 1 second
                
            `call_before_return` can be any function defined within the class or as a
                lambda function. The function must only take a response-like object as
                it does not alter the object, but can alter the initial parameters that
                were provided by the user. i.e. search_term if the input matches more than 
                one category available on the site.
        """
        sleep(1)
        if params is None:
            params = {}
        response = self.session.request(url=url, method=method, params=params)
        print(response.url)
        try:
            if len(response.text) < 10000:
                print(response.json(),'\n')
        except:
#             print(response.text,'\n')
            pass
        if call_before_return is not None:
            call_before_return(response)
        return response
        
    def __define_log_params(self):
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
    
    def __update_session_headers(self, response=None):
        """
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
                if 'Set-Cookie' in copy_response.headers.keys():
                    loop_count += 1
                    header = copy_response.headers.pop('Set-Cookie')
                    if re.match('discard=true', header.lower()) is None:
                        for c1 in header.split(';'):
                            c2 = c1.split('=')
                            if c2.__len__() > 0 and c2.__len__() % 2 == 0:
                                v, k = c2.pop(), c2.pop()
                                self.session.cookies.update({k: v})
                    try:
                        self.session.headers['Cookie'] += '; '+header
                    except (KeyError):
                        self.session.headers['Cookie'] = header
                else:
                    break
    
    def export_fair_priced_procedure_data(self):
        """ The main tool to perform a data export for procedures at or below a fair price
        """
        response = self._perform_search()
        self.price = self.__define_fair_price(response)
        df = DataFrame(response.json())
        writer = pandas.ExcelWriter(os.path.abspath(os.path.join('.','Results',self.search_term+'.xlsx')),
                            engine='xlsxwriter')
        df = DataFrame(DataFrame([resp['ProcedureDetails']['FacilityInformation']])['Facilities'][0])
        df = df[(df['CashPriceSortValue'] <= self.price) & (df['CashPriceSortValue'] > 0)]
        df.to_excel(excel_writer=writer, sheet_name=r.search_term)
        writer.save()
        
        print(fr'Your Results Have Been Saved in the Excel Workbook Found Here: {writer.path}')
        return df
    
    def __define_fair_price(self, response):
        """ Get the floating point value of a "Fair" Procedure Price
        """
        df = DataFrame(response.json())
        price = df['ProcedureDetails']['PricingInformations'][0]['FairPrice'].replace('$','')
        return float(price)
    
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
    resp = r.export_fair_priced_procedure_data()
    