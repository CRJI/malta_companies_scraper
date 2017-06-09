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
_SEARCH_PAGE_URL = 'http://registry.mfsa.com.mt/companySearch.do?action=companyDetails'
_SEARCH_URL = 'http://registry.mfsa.com.mt/companiesReport.do?action=companyDetails'
_INVOLVED_PARTIES_URL = 'http://registry.mfsa.com.mt/companyDetailsRO.do?action=involvementList'
_AUTHORISED_CAPITAL_URL = 'http://registry.mfsa.com.mt/companyDetailsRO.do?action=authorisedCapital'


_LOGIN_DATA = {
    'username': 'blacksea',
    'password': 'Bugsy11133',
}

_HEADERS = { 'Accept':'*/*',
    'Accept-Encoding':'gzip, deflate, sdch',
    'Accept-Language':'en-US,en;q=0.8',
    'Cache-Control':'max-age=0',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36'
}

_SESSION = requests.Session()


def generate_something():
    """
    Login and go to the search page. There perform the search based on the company id.
    For each company gather the
    :return:
    """


    _SESSION.headers.update(_HEADERS)
    _SESSION.get(_INDEX_URL)

    # Perform login
    response = _SESSION.get(_LOGIN_URL)
    soup = BeautifulSoup(response.text, 'lxml')

    # Instantiate a params dict and add the token, login data, and mouse position on the logon button
    params = dict()
    params['token'] = soup.find('input', {'name': 'org.apache.struts.taglib.html.TOKEN'})['value']
    params.update(_LOGIN_DATA)
    params['logon.x'] = '45'
    params['logon.y'] = '10'

    _SESSION.post(_LOGON_URL, data=params)

    # Get the test data from the pickle file
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
        entity['registration_date'] = soup.find(
            'td',
            text=re.compile('.*Registration Date.*')
        ).findNextSibling('td').get_text().strip()
        authorised_shares_url = soup.find('a', text=re.compile('.*Authorised Shares.*'))['href']
        authorised_shares_url = urljoin(_INDEX_URL, authorised_shares_url)
        response = _SESSION.get(_AUTHORISED_CAPITAL_URL)
        soup = BeautifulSoup(response.text, 'lxml')

        entity['authorised_shares'] = list()
        currency =  ''
        table_rows = soup.find('td', text=re.compile('.*Nominal Value Per Share in .*'))
        currency = re.match('.*Nominal Value Per Share in (.*)', table_rows.get_text().strip())
        currency = currency.groups()[0].strip()
        table_rows = table_rows.findParent('table').findAll('tr')

        # If there is info about the issued shares extract each line and add it to the list
        if len(table_rows) > 1:
            for row in table_rows[1:]:
                row_data = row.select('td')
                share = dict()
                share['currency'] = currency
                share['authorised_share_capital'] = re.sub(',', '', row_data[0].get_text().strip())
                share['authorised_share_capital'] = eval(share['authorised_share_capital'])
                share['type'] = re.sub('\s*', '', row_data[1].get_text().strip())
                share['nominal_value_per_share'] = eval(row_data[2].get_text().strip())
                share['issued_shares'] = re.sub(',', '', row_data[3].get_text().strip())
                share['issued_shares'] = eval(share['issued_shares'])
                entity['authorised_shares'].append(share)

        # Extract the data about the involved parties
        entity['involved_parties'] = dict()

        # Load the involved parties page
        response = _SESSION.get(_INVOLVED_PARTIES_URL)
        soup = BeautifulSoup(response.text, 'lxml')

        tables = soup.findAll('td', {'class': 'tableheadDark', 'colspan': '3'})

        # Separate the big table into definite sections
        sections = dict()
        for table in tables:
            table = table.findParent('tr')
            party_type = re.match('\s*(.*?)\(.*\).*', table.get_text().strip()).groups()[0]
            entity['involved_parties'][party_type] = list()
            sections[party_type] = list()
            for party in table.findNextSiblings('tr'):
                if party.find('hr'):
                   break

                sections[party_type].append(party)

        # Extract the data from each section
        for section, involved_parties in sections.items():
            for party in involved_parties:
                print(involved_parties)
                # If the row is empty skip it
                if not party.get_text().strip():
                    continue

                # If this is a table head also skip it
                if party.find('td', {'class': 'tablehead'}):
                    continue

                if party.has_attr('onmouseout'):
                    party_dict = dict()
                    party_data = party.findAll('td')
                    party_dict['name'] = party_data[0].get_text().strip()

                    entity['involved_parties'][section].append(party_dict)



        try:
            pass
        except:
            with open('error.htm', 'wt') as error:
                error.write(response.text)
                break



        pprint(entity)
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
