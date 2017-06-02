import json
import re
import time
import sqlite3
import requests
from pprint import pprint
from bs4 import BeautifulSoup
from malta_roc_gather import generate_extracted_data


def main():

    for entity in generate_extracted_data():
        pprint(entity)


if __name__ == '__main__':
    main()
