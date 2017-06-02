import re
import requests
from bs4 import BeautifulSoup


# Set the base url
_BASE_URL = 'http://rocsupport.mfsa.com.mt/pages/SearchCompanyInformation.aspx'

# Initialize the headers
_HEADERS = {
    'Pragma': 'no-cache',
    'Origin': 'http://rocsupport.mfsa.com.mt',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q=0.8,ro;q=0.6,la;q=0.4',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'DNT': '1',
}

# Start a global Session
_SESSION = requests.Session()
_SESSION.headers = _HEADERS


def generate_first_letter_pages():
    """
    Go to the first page and extract the parameters then navigate to the first pages of
    results.

    :return: Yield rows of companies
    """

    response = _SESSION.get(_BASE_URL)
    soup = BeautifulSoup(response.text, 'lxml')

    # Extract the letters that will be used to get to the actual results pages
    letters = soup.select('div.rcbScroll ul.rcbList li')[0]
    letters =[letter.get_text() for letter in letters.findNextSiblings('li')]

    # make a copy of the dictionary containing the universal parameters
    letter_params = {
        'ctl00_RadScriptManager1_TSM': (
        ';;System.Web.Extensions, Version=3.5.0.0, Culture=neutral,'
        ' PublicKeyToken=31bf3856ad364e35:en:eb198dbd-2212-44f6-bb15-882bde414f00:ea597d4b:b25378d2;Telerik.Web.UI,'
        ' Version=2013.3.1015.35, Culture=neutral,'
        ' PublicKeyToken=121fae78165ba3d4:en:014dc8f9-7cb3-42f7-a773-fe899684c823:16e4e7cd:f7645509:24ee1bba:'
        'f46195d3:2003d0b8:1e771326:88144a7a:aa288e2d:ed16cbdc:58366029:e330518b:c8618e41:e4f8f289;'
        ),
        '__EVENTTARGET':'ctl00$cphMain$RadComboBoxFirstLetter',
        '__EVENTARGUMENT':'',
        '__VIEWSTATE':'',
        '__VIEWSTATEGENERATOR':'',
        '__EVENTVALIDATION':'',
        'ctl00$cphMain$RadComboBoxFirstLetter': '',
        'ctl00_cphMain_RadComboBoxFirstLetter_ClientState': '',
        'ctl00_cphMain_RadGrid1_ClientState': '',
    }

    event_argument_template = "{{'Command': 'Select', 'Index': {}}}"
    first_letter_template = (
        "{{'logEntries':[],"
        "'value':'{0}',"
        "'text':'{1}',"
        "'enabled':true,"
        "'checkedIndices':[],"
        "'checkedItemsTextOverflows':false,}}"
    )

    for index, letter in enumerate(letters):
        index = index + 1
        print(letter, index)
        # print()
        with open('error.htm', 'w') as error:
            error.write(response.text)
            # input()

        # Set the arguments needed to navigate to the letter pages
        letter_params['__EVENTARGUMENT'] = event_argument_template.format(index)
        letter_params['__VIEWSTATE'] = soup.find('input', {'id': '__VIEWSTATE'})['value']
        letter_params['__VIEWSTATEGENERATOR'] = soup.find('input', {'id': '__VIEWSTATEGENERATOR'})['value']
        letter_params['__EVENTVALIDATION'] = soup.find('input', {'id': '__EVENTVALIDATION'})['value']
        letter_params['ctl00$cphMain$RadComboBoxFirstLetter'] = letter
        letter_params['ctl00_cphMain_RadComboBoxFirstLetter_ClientState'] = first_letter_template.format(letter, letter)
        print(letter_params)
        response = _SESSION.post(
            url=_BASE_URL,
            json=letter_params
        )
        soup = BeautifulSoup(response.text, 'lxml')
        yield soup


def generate_letter_index_page_rows():
    """
    Go to each index page of each letter set of results and extract the page
    to be processed further

    :return: Yield table containing the data to be parsed
    """

    # Build the set of parameters that will be used to navigate between
    # each index page of results for each letter
    index_page_params = {
        'ctl00$RadScriptManager1': 'ctl00$cphMain$ctl00$cphMain$RadGrid1Panel|ctl00$cphMain$RadGrid1$ctl00$ctl03$ctl01$ctl28',
        'ctl00_RadScriptManager1_TSM': (
        ';;System.Web.Extensions, Version=3.5.0.0, Culture=neutral,'
        ' PublicKeyToken=31bf3856ad364e35:en:eb198dbd-2212-44f6-bb15-882bde414f00:ea597d4b:b25378d2;Telerik.Web.UI,'
        ' Version=2013.3.1015.35, Culture=neutral,'
        ' PublicKeyToken=121fae78165ba3d4:en:014dc8f9-7cb3-42f7-a773-fe899684c823:16e4e7cd:f7645509:24ee1bba:'
        'f46195d3:2003d0b8:1e771326:88144a7a:aa288e2d:ed16cbdc:58366029:e330518b:c8618e41:e4f8f289;'
        ),
        '__EVENTTARGET': 'ctl00$cphMain$RadGrid1$ctl00$ctl03$ctl01$ctl28',
        '__EVENTARGUMENT': '',
        '__VIEWSTATE': '',
        '__VIEWSTATEGENERATOR': '',
        '__EVENTVALIDATION': '',
        'ctl00$cphMain$RadComboBoxFirstLetter': '',
        'ctl00_cphMain_RadComboBoxFirstLetter_ClientState': '',
        'ctl00$cphMain$RadGrid1$ctl00$ctl02$ctl02$FilterTextBox_CompanyName': '',
        'ctl00$cphMain$RadGrid1$ctl00$ctl02$ctl02$FilterTextBox_CompanyId': '',
        'ctl00$cphMain$RadGrid1$ctl00$ctl03$ctl01$PageSizeComboBox': '10',
        'ctl00_cphMain_RadGrid1_ctl00_ctl03_ctl01_PageSizeComboBox_ClientState': '',
        'ctl00_cphMain_RadGrid1_rfltMenu_ClientState': '',
        'ctl00_cphMain_RadGrid1_ClientState': '',
        '__ASYNCPOST': 'true',
        'RadAJAXControlID': 'ctl00_cphMain_RadAjaxManager1',
    }

    for bs_obj in generate_first_letter_pages():
        # If there is no pagination section continue to the next letter
        if not bs_obj.select('td.rgPagerCell.NextPrevAndNumeric'):
            # Extract the rows on the current page
            rows = bs_obj.findAll('tr', {'id': re.compile('ctl00_cphMain_RadGrid1_ctl00__[0-9]+')})

            # Yield the rows on the current page to be parsed
            for row in rows:
                yield row

            continue

        # Otherwise proceed to iterate through the pages containing results
        # Set the initial current_page value and last_page value
        current_page = bs_obj.find('a', {'class':'rgCurrentPage'}).get_trext().strip()
        last_page = bs_obj.select('div.rgWrap.rgInfoPart strong')[-1].get_text().strip()

        while current_page != last_page:
            # Extract the rows on the current page
            rows = bs_obj.findAll('tr', {'id': re.compile('ctl00_cphMain_RadGrid1_ctl00__[0-9]+')})

            # Yield the rows on the current page to be parsed
            for row in rows:
                yield row

            # Add the last parameter values to the list of parameters
            index_page_params['__VIEWSTATE'] = bs_obj.find('input', {'id': '__VIEWSTATE'})['value']
            index_page_params['__VIEWSTATEGENERATOR'] = bs_obj.find('input', {'id': '__VIEWSTATEGENERATOR'})['value']
            index_page_params['__EVENTVALIDATION'] = bs_obj.find('input', {'id': '__EVENTVALIDATION'})['value']

            # Request the next page of results from this letter
            response = requests(
                url=_BASE_URL,
                json=index_page_params
            ).text
            bs_obj = BeautifulSoup(response, 'lxml')
            current_page = bs_obj.find('a', {'class':'rgCurrentPage'}).get_trext().strip()


def generate_extracted_data():
    """
    Parse each retrieved page and extract the data form it

    :return: Yield dictionary containing the extracted data
    """

    for row in generate_letter_index_page_rows():

        entity = dict()
        data = row.select('td')

        # Extract the data from the row
        entity['name'] = data[0].get_text().strip()
        entity['company_id'] = data[1].get_text().strip()
        entity['address'] = data[2].get_text().strip()
        entity['status'] = data[3].get_text().strip()

        # Yield the extracted data
        yield entity


def main():
    for entity in generate_extracted_data():
        print(entity)


if __name__ == '__main__':
    main()
