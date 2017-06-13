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

_HEADERS = {'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, sdch',
            'Accept-Language': 'en-US,en;q=0.8',
            'Cache-Control': 'max-age=0',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36'
            }

_SESSION = requests.Session()

_MAX_REQUESTS = 10000


def relogin():
    """
    Self explanatory
    """
    global _SESSION

    _SESSION.close()
    time.sleep(5)
    _SESSION = requests.Session()
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


def session_request(url, entity=None, get_respnse=True, type=None, params=None):
    global _MAX_REQUESTS, _SESSION

    def request(url, entity=None, get_respnse=True, type=None, params=None):
        global _MAX_REQUESTS

        _MAX_REQUESTS -= 1
        if type == 'post' and params:
            response = _SESSION.post(url, data=params)

        elif not params and type == 'post':
            raise ValueError('params argument must be provided when performing a post request')

        elif not type:
            response = _SESSION.get(url)

        if get_respnse:
            return response

    if _MAX_REQUESTS:
        return request(url, entity=entity, get_respnse=get_respnse, type=type, params=params)
    else:
        time.sleep(10)
        relogin()
        request(_SEARCH_URL, get_respnse=False)
        params = dict()
        params['companyId'] = entity['company_id']
        params['companyName'] = ''
        params['companyNameComplexCombination'] = 'on'
        params['search.x'] = str(randint(10, 81))
        params['search.y'] = str(randint(4, 15))
        request(_SEARCH_URL, type='post', params=params, get_respnse=False)
        response = request(url, entity=entity, get_respnse=get_respnse, type=type, params=params)
        if get_respnse:
            return response


def generate_lookup_data():
    """
    Login and go to the search page. There perform the search based on the company id.
    For each company gather the
    :return:
    """

    _SESSION.headers.update(_HEADERS)
    session_request(_INDEX_URL, get_respnse=False)

    # Perform login
    response = session_request(_LOGIN_URL)
    soup = BeautifulSoup(response.text, 'lxml')

    # Instantiate a params dict and add the token, login data, and mouse position on the logon
    params = dict()
    params['token'] = soup.find('input', {'name': 'org.apache.struts.taglib.html.TOKEN'})['value']
    params.update(_LOGIN_DATA)
    params['logon.x'] = '45'
    params['logon.y'] = '10'

    session_request(_LOGON_URL, get_respnse=False, type='post', params=params)

    # Navigate to the search url and
    for entity in generate_extracted_data():
        # Perform the search for this entity
        session_request(_SEARCH_URL)
        params = dict()
        params['companyId'] = entity['company_id']
        params['companyName'] = ''
        params['companyNameComplexCombination'] = 'on'
        params['search.x'] = str(randint(10, 81))
        params['search.y'] = str(randint(4, 15))
        response = session_request(_SEARCH_URL, type='post', params=params)

        soup = BeautifulSoup(response.text, 'lxml')
        entity['registration_date'] = soup.find(
            'td',
            text=re.compile('.*Registration Date.*')
        ).findNextSibling('td').get_text().strip()

        if soup.find('a', text=re.compile('.*Authorised Shares.*')):

            response = session_request(_AUTHORISED_CAPITAL_URL)
            soup = BeautifulSoup(response.text, 'lxml')

            # Extract general data about the issued and authorised shares
            entity['authorised_shares'] = list()
            entity['total_authorised_shares'] = soup.find('td', text=re.compile('.*Total No\. of Authorised Shares.*'))
            entity['total_authorised_shares'] = entity['total_authorised_shares'].findNextSibling(
                'td').get_text().strip()
            entity['total_authorised_shares'] = re.sub('\s+|\n', ' ', entity['total_authorised_shares']).strip()
            entity['total_authorised_shares'] = re.sub(',', '', entity['total_authorised_shares']).strip()
            entity['total_authorised_shares_value'] = re.match('.*\(.*?([0-9\.]+).*\).*',
                                                               entity['total_authorised_shares'])
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

        # Load the involved parties page
        response = session_request(_INVOLVED_PARTIES_URL)
        soup = BeautifulSoup(response.text, 'lxml')

        # Extract the data about the involved parties
        entity['involved_parties'] = dict()
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

                    party_dict['address'] = re.sub('\r|\s*', '', party_data[1].get_text().strip())
                    party_dict['nationality'] = party_data[2].get_text().strip()

                    # If this party is a shareholder add the details about the shares they hold
                    if section.lower() == 'shareholders':
                        party_dict['shares'] = dict()
                        shares_data = party.findNext('td', text=re.compile('.*Shares.*'),
                                                     attrs={'class': 'tableHeadDark'})
                        shares_data = shares_data.findNext('td', {'class': 'tablehead'}).findParent(
                            'tr').findNextSibling('tr')
                        shares_data = shares_data.findAll('td')
                        party_dict['shares']['type'] = shares_data[0].get_text().strip()
                        party_dict['shares']['class'] = shares_data[1].get_text().strip()
                        party_dict['shares']['issued_shares'] = re.sub(',', '',
                                                                       shares_data[2].get_text().strip()).strip()
                        party_dict['shares']['issued_shares'] = eval(party_dict['shares']['issued_shares'])
                        party_dict['shares']['paid_up_%'] = eval(shares_data[3].get_text().strip())
                        party_dict['shares']['nominal_value_per_share'] = eval(shares_data[4].get_text().strip())

                    entity['involved_parties'][section].append(party_dict)

        # Gather the data about all the documents
        entity['documents'] = list()
        documents_url = _DOCUMENTS_URL_TEMPLATE.format(entity['company_id'])
        response = session_request(documents_url)
        soup = BeautifulSoup(response.text, 'lxml')

        # Extract the data from the current first
        document_rows = soup.find('td', text=re.compile('Document In File'), attrs={'class': 'tablehead'})
        if not document_rows:
            response = session_request(documents_url)
            soup = BeautifulSoup(response.text, 'lxml')
            document_rows = soup.find('td', text=re.compile('Document In File'), attrs={'class': 'tablehead'})

        document_rows = document_rows.findParent('tr').findNextSiblings('tr',
                                                                        {'onmouseout': "this.className='pNormal'"})
        for row in document_rows:
            row_data = row.findAll('td')
            row_dict = dict()
            row_dict['preview'] = row_data[0].find('a')['href']
            row_dict['preview'] = urljoin(_INDEX_URL, row_dict['preview'])
            row_dict['date'] = row_data[1].get_text().strip()
            row_dict['archived'] = row_data[2].get_text().strip()
            row_dict['document_in_file'] = row_data[3].get_text().strip()

            if row_dict['document_in_file'] == 'NA':
                row_dict['document_in_file'] = None
            else:
                row_dict['document_in_file'] = eval(row_dict['document_in_file'])

            row_dict['year'] = row_data[4].get_text().strip()
            row_dict['comments'] = row_data[5].get_text().strip()
            row_dict['was_paid'] = row_data[6].get_text().strip()
            row_dict['purchase__link'] = row_data[1].get_text().strip()

            entity['documents'].append(row_dict)

        if soup.find('b', text=re.compile('.*Last Page.*\(.*\).*')):
            pages = soup.find('b', text=re.compile('.*Last Page.*\(.*\).*')).get_text().strip()
            pages = eval(re.match('.*\((.*)\).*', pages).groups()[0])
        else:
            continue

        for index in range(1, pages):
            offset = 20 * index
            documents_url = _DOCUMENTS_URL_PAGED_TEMPLATE.format(entity['company_id'], offset)
            response = session_request(documents_url)
            soup = BeautifulSoup(response.text, 'lxml')

            # Extract the data from the current first
            document_rows = soup.find('td', text=re.compile('Document In File'), attrs={'class': 'tablehead'})
            document_rows = document_rows.findParent('tr').findNextSiblings('tr',
                                                                            {'onmouseout': "this.className='pNormal'"})
            for row in document_rows:

                row_data = row.findAll('td')
                row_dict = dict()
                row_dict['preview'] = row_data[0].find('a')['href']
                row_dict['preview'] = urljoin(_INDEX_URL, row_dict['preview'])
                row_dict['date'] = row_data[1].get_text().strip()
                row_dict['archived'] = row_data[2].get_text().strip()
                row_dict['document_in_file'] = row_data[3].get_text().strip()
                if row_dict['document_in_file'] == 'NA':
                    row_dict['document_in_file'] = None
                else:
                    row_dict['document_in_file'] = eval(row_dict['document_in_file'])

                row_dict['year'] = row_data[4].get_text().strip()
                row_dict['comments'] = row_data[5].get_text().strip()
                row_dict['was_paid'] = row_data[6].get_text().strip()
                row_dict['purchase__link'] = row_data[1].get_text().strip()

                entity['documents'].append(row_dict)

        yield entity
        time.sleep(5)


def main():

    for entity in generate_lookup_data():
        print(json.dumps(entity))


if __name__ == '__main__':
    main()
