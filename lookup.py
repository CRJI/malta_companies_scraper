import json
import pickle
import re
import time
import sqlite3
import requests
from pprint import pprint
from random import randint
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from gather import generate_extracted_data
from gather import main as gather_main


_INDEX_URL = 'http://registry.mfsa.com.mt/index.jsp'
_LOGIN_URL = 'https://registry.mfsa.com.mt/login.do'
_LOGON_URL = 'https://registry.mfsa.com.mt/logon.do'
_SEARCH_URL = 'http://registry.mfsa.com.mt/companySearch.do?action=companyDetails'

_LOGIN_DATA = {
    'username': 'blacksea',
    'password': 'Bugsy11133',
}

_SESSION = requests.Session()

def perform_login():
    """
    Function handles the login onto the reistry.mfsa platfom
    :return: Nothing
    """

    response = _SESSION.get(_LOGIN_URL)
    soup = BeautifulSoup(response.text, 'lxml')
    # Instantiate a params dict and add the token, login data, and mouse position on the logon button
    params = dict()
    params['token'] = soup.find('input', {'name': 'org.apache.struts.taglib.html.TOKEN'})['value']
    params.update(_LOGIN_DATA)
    params['logon.x'] = '45'
    params['logon.y'] = '10'

    response = _SESSION.post(_LOGON_URL, json=params)


def generate_something():
    """
    Login and go to the search page. There perform the search based on the company id.
    For each company gather the
    :return:
    """

    perform_login()

    company_file = open('test_set.log', 'rb')
    entity_list = pickle.load(company_file)

    index = 100
    # Navigate to the search url and
    for entity in entity_list:

        # Perform the search for this entity
        _SESSION.get(_SEARCH_URL)
        params = dict()
        params['companyId'] = entity['company_id']
        params['companyName'] = ''
        params['companyNameComplexCombination'] = 'on'
        params['search.x'] = str(randint(10, 81))
        params['search.y'] = str(randint(4, 15))
        response = _SESSION.post(_SEARCH_URL, data=params)
        soup = BeautifulSoup(response.text, 'lxml')
        try:
            entity['registration_date'] = soup.find(
                'td',
                text=re.compile('.*Registration Date.*')
            ).findNextSibling('td').get_text().strip()
        except:
            with open('error.htm', 'wt') as error:
                error.write(response.text)
                break
        authorised_shares_url = soup.find('a', text=re.compile('.*Authorised Shares.*'))['href']
        authorised_shares_url = urljoin(_SEARCH_URL, authorised_shares_url)
        response = _SEARCH_URL.get(authorised_shares_url)
        soup = BeautifulSoup(response.text, 'lxml')

        table_rows = soup.find('td', text=re.compile('.*Authorised Share Capital.*')).findParent('tbody')
        table_rows = len(table_rows.findAll('tr')) - 1 # Because table header

        print(entity)
        print()
        index -= 1
        if not index:
            break


def main():

    # for entity in generate_extracted_data():
    #     pprint(entity)

    # perform_login()
    generate_something()


if __name__ == '__main__':
    main()
