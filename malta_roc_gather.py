import re
import time
import requests
from pprint import pprint
from bs4 import BeautifulSoup
from selenium.webdriver import PhantomJS


# Set the base url
_BASE_URL = 'http://rocsupport.mfsa.com.mt/pages/SearchCompanyInformation.aspx'

# Start a global browser and set it's attributes
_BROWSER = PhantomJS()
_BROWSER.set_window_size(1920, 1080)


def generate_results_pages():
    """
    Go to the first page and extract the parameters then navigate to the first pages of
    results.

    :return: Yield rows of companies
    """

    # Get the page
    _BROWSER.get(_BASE_URL)

    # Find the letters
    _BROWSER.find_element_by_xpath('//input[@id="ctl00_cphMain_RadComboBoxFirstLetter_Input"]').click()
    time.sleep(1)
    _BROWSER.save_screenshot('error2.png')

    letters_length = len(_BROWSER.find_elements_by_xpath('//ul[@class="rcbList"][1]//li'))+1
    letter_xpath_template = '//ul[@class="rcbList"][1]//li[{}]'

    # Iterate through all the letters
    for index in range(2, letters_length):

        letter_xpath = letter_xpath_template.format(index)
        print(letter_xpath)
        _BROWSER.find_element_by_xpath('//div[@id="ctl00_cphMain_RadComboBoxFirstLetter"]').click()
        _BROWSER.find_element_by_xpath(letter_xpath).click()





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
    # for entity in generate_extracted_data():
    #     print(entity)
    generate_results_pages()


if __name__ == '__main__':
    main()
