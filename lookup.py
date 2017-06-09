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
_DOCUMENTS_URL_TEMPLATE = 'http://registry.mfsa.com.mt/documentsList.do?action=companyDetails&companyId={}'
_DOCUMENTS_URL_PAGED_TEMPLATE = 'http://registry.mfsa.com.mt/documentsList.do?action=companyDetails&companyId={}&pager.offset={}'


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

        # Extract general data about the issued and authorised shares
        entity['authorised_shares'] = list()
        entity['total_authorised_shares'] = soup.find('td', text=re.compile('.*Total No\. of Authorised Shares.*'))
        entity['total_authorised_shares'] = entity['total_authorised_shares'].findNextSibling('td').get_text().strip()
        entity['total_authorised_shares'] = re.sub('\s+|\n', ' ', entity['total_authorised_shares']).strip()
        entity['total_authorised_shares'] = re.sub(',', '', entity['total_authorised_shares']).strip()
        entity['total_authorised_shares_value'] = re.match('.*\(.*?([0-9\.]+).*\).*', entity['total_authorised_shares'])
        entity['total_authorised_shares_value'] = eval(entity['total_authorised_shares_value'].groups()[0].strip())
        entity['total_authorised_shares'] = eval(re.sub('\(.*\).*', '', entity['total_authorised_shares']))
        entity['total_issued_shares'] = soup.find('td', text=re.compile('.*Total No\. of Issued Shares.*'))
        entity['total_issued_shares'] = entity['total_issued_shares'].findNextSibling('td').get_text().strip()
        entity['total_issued_shares'] = re.sub('\s+|\n', ' ', entity['total_issued_shares']).strip()
        entity['total_issued_shares'] = re.sub(',', '', entity['total_issued_shares']).strip()
        entity['total_issued_shares_value'] = re.match('.*\(.*?([0-9\.]+).*\).*', entity['total_issued_shares'])
        entity['total_issued_shares_value'] = eval(entity['total_issued_shares_value'].groups()[0].strip())
        entity['total_issued_shares'] = eval(re.sub('\(.*\).*', '', entity['total_issued_shares']))
        entity['authorised_shares'] = list()
        table_rows = soup.find('td', text=re.compile('.*Nominal Value Per Share in .*'))
        currency = re.match('.*Nominal Value Per Share in (.*)', table_rows.get_text().strip())
        currency = currency.groups()[0].strip()
        entity['shares_currency'] = currency

        table_rows = table_rows.findParent('table').findAll('tr')

        # If there is info about the issued shares extract each line and add it to the list
        if len(table_rows) > 1:
            for row in table_rows[1:]:
                row_data = row.select('td')
                share = dict()
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
            section = re.match('\s*(.*?)\(.*\).*', table.get_text().strip()).groups()[0]
            entity['involved_parties'][section] = list()
            sections[section] = list()
            table = table.findParent('tr')

            for party in table.findNextSiblings():
                if party.find('hr'):
                    break

                sections[section].append(party)

        # Extract the data from each section
        for section, involved_parties in sections.items():
            for party in involved_parties:
                # If the row is empty skip it
                if not party.get_text().strip():
                    continue

                # If this is a table head also skip it
                if party.find('td', {'class': 'tablehead'}):
                    continue

                if party.find('tr', {'onmouseout': "this.className='pNormal'"}):
                    party_dict = dict()
                    party_data = party.findAll('td')
                    party_dict['name'] = party_data[0].get_text().strip()
                    party_dict['name'] = re.split('\n', party_dict['name'])
                    if len(party_dict['name']) > 1:
                        party_dict['name'], party_dict['party_id'] = party_dict['name'][0], party_dict['name'][1]
                    elif len(party_dict['name']) == 1:
                        party_dict['name'] = party_dict['name'][0]
                        party_dict['party_id'] = ''
                    else:
                        party_dict['name'] = ''
                        party_dict['party_id'] = ''

                    party_dict['address'] = party_data[1].get_text().strip()
                    party_dict['nationality'] = party_data[2].get_text().strip()

                    # If this party is a shareholder add the details about the shares they hold
                    if section.lower() == 'shareholders':
                        party_dict['shares'] = dict()
                        shares_data = party.findNext('td', text=re.compile('.*Shares.*'), attrs={'class': 'tableHeadDark'})
                        shares_data = shares_data.findNext('td', {'class': 'tablehead'}).findParent('tr').findNextSibling('tr')
                        shares_data = shares_data.findAll('td')
                        party_dict['shares']['type'] = shares_data[0].get_text().strip()
                        party_dict['shares']['class'] = shares_data[1].get_text().strip()
                        party_dict['shares']['issued_shares'] = re.sub(',', '', shares_data[2].get_text().strip()).strip()
                        party_dict['shares']['issued_shares'] = eval(party_dict['shares']['issued_shares'])
                        party_dict['shares']['paid_up_%'] = eval(shares_data[3].get_text().strip())
                        party_dict['shares']['nominal_value_per_share'] = eval(shares_data[4].get_text().strip())

                    entity['involved_parties'][section].append(party_dict)

        # Gather the data about all the documents
        entity['documents'] = list()
        documents_url = _DOCUMENTS_URL_TEMPLATE.format(entity['company_id'])
        response = _SESSION.get(documents_url)
        try:
            if entity['company_id'] == 'C 37840':
                raise FloatingPointError
        except:
            with open('error.htm', 'wt') as error:
                error.write(response.text)
                break

        soup = BeautifulSoup(response.text, 'lxml')
        offset = 0
        while True:
            pass

        # pprint(entity)
        print()
        print()
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
