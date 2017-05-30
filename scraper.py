# You don't have to do things with the ScraperWiki and lxml libraries.
# You can use whatever libraries you want: https://morph.io/documentation/python
# All that matters is that your final data is written to an SQLite database
# called "data.sqlite" in the current working directory which has at least a table
# called "data".

import requests
import urllib
import pprint
from pyquery import PyQuery

pp = pprint.PrettyPrinter(indent=2)

letters = [
  'Select First Letter', ' ', '"', '\'', '(', '@', '0', '1', '2', '3',
  '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D',
  'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N',
  'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X',
  'Y', 'Z',
]

headers = {
    'Pragma': 'no-cache',
    'Origin': 'http://rocsupport.mfsa.com.mt',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q=0.8,ro;q=0.6,la;q=0.4',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Cache-Control': 'no-cache',
    'Referer': 'http://rocsupport.mfsa.com.mt/pages/SearchCompanyInformation.aspx',
    'Connection': 'keep-alive',
    'DNT': '1',
}

cookies = {
    '__utma': '93865246.35980861.1495823328.1495823328.1495823328.1',
    '__utmc': '93865246',
    '__utmz': '93865246.1495823328.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none)',
}

data = [
  # ('ctl00_RadScriptManager1_TSM', ';;System.Web.Extensions, Version=3.5.0.0, Culture=neutral, PublicKeyToken=31bf3856ad364e35:en:eb198dbd-2212-44f6-bb15-882bde414f00:ea597d4b:b25378d2;Telerik.Web.UI, Version=2013.3.1015.35, Culture=neutral, PublicKeyToken=121fae78165ba3d4:en:014dc8f9-7cb3-42f7-a773-fe899684c823:16e4e7cd:f7645509:24ee1bba:f46195d3:2003d0b8:1e771326:88144a7a:aa288e2d:ed16cbdc:58366029'),
  # ('__EVENTTARGET', 'ctl00$cphMain$RadComboBoxFirstLetter'),
  # ('__EVENTARGUMENT', '{"Command":"Select","Index":25}'),
  # # ('__EVENTTARGET', 'ctl00$cphMain$RadGrid1'),
  # # ('__EVENTARGUMENT', 'FireCommand:ctl00$cphMain$RadGrid1$ctl00;PageSize;50'),
  # ('ctl00$cphMain$RadComboBoxFirstLetter', 'J'),
  # # ('ctl00$cphMain$RadGrid1$ctl00$ctl03$ctl01$PageSizeComboBox', '50'),
  # # ('ctl00_cphMain_RadGrid1_ctl00_ctl03_ctl01_PageSizeComboBox_ClientState', '{"logEntries":[],"value":"50","text":"50","enabled":true,"checkedIndices":[],"checkedItemsTextOverflows":false}'),
  # ('ctl00_cphMain_RadComboBoxFirstLetter_ClientState', '{"logEntries":[],"value":"J","text":"P","enabled":true,"checkedIndices":[],"checkedItemsTextOverflows":false}'),
  # ('__EVENTTARGET', 'ctl00$cphMain$RadGrid1$ctl00$ctl03$ctl01$ctl28'),
  # ('__EVENTARGUMENT', ''),
]

def requestLetter(data, letter):
    extraPayload = [
        ('ctl00$cphMain$RadComboBoxFirstLetter', letter),
        ('__EVENTTARGET', 'ctl00$cphMain$RadComboBoxFirstLetter'),
        ('__EVENTARGUMENT', '{"Command":"Select","Index":%s}' % letters.index(letter)),
        ('ctl00_cphMain_RadComboBoxFirstLetter_ClientState',
         '{"logEntries":[],"value":"%s","text":"%s","enabled":true,"checkedIndices":[],"checkedItemsTextOverflows":false}' % (letter, letter)),
        ('ctl00_cphMain_RadGrid1_ClientState', ''),
    ]
    data.extend(extraPayload)
    return data

def nextPage(data, state, validation, generator, tsm):
    blacklist = [
        '__EVENTTARGET',
        '__EVENTARGUMENT',
        'ctl00_cphMain_RadComboBoxFirstLetter_ClientState',
        # 'ctl00$cphMain$RadComboBoxFirstLetter',
        # 'ctl00_cphMain_RadComboBoxFirstLetter_ClientState',
        # 'ctl00_cphMain_RadGrid1_ClientState',
    ]
    for item in blacklist:
        for idx, tup in enumerate(data):
            if tup[0] == item:
                del data[idx]
    extraPayload = [
        # # ('__EVENTTARGET', 'ctl00$cphMain$RadGrid1'),
        # # ('__EVENTARGUMENT', 'FireCommand:ctl00$cphMain$RadGrid1$ctl00;PageSize;50'),
        ('ctl00$RadScriptManager1', 'ctl00$cphMain$ctl00$cphMain$RadGrid1Panel|ctl00$cphMain$RadGrid1$ctl00$ctl03$ctl01$ctl28'),
        ('ctl00_RadScriptManager1_TSM', tsm),
        ('__EVENTTARGET', 'ctl00$cphMain$RadGrid1$ctl00$ctl03$ctl01$ctl28'),
        ('__EVENTARGUMENT', ''),
        ('__VIEWSTATE', state),
        ('__VIEWSTATEGENERATOR', generator),
        ('__EVENTVALIDATION', validation),
        ('ctl00_cphMain_RadComboBoxFirstLetter_ClientState', ''),
        ('ctl00$cphMain$RadGrid1$ctl00$ctl03$ctl01$PageSizeComboBox', '10'),
        ('ctl00_cphMain_RadGrid1_ctl00_ctl03_ctl01_PageSizeComboBox_ClientState', ''),
        ('ctl00_cphMain_RadGrid1_ClientState', ''),
        ('ctl00_cphMain_RadGrid1_rfltMenu_ClientState', ''),
        ('ctl00$cphMain$RadGrid1$ctl00$ctl02$ctl02$FilterTextBox_CompanyName', ''),
        ('ctl00$cphMain$RadGrid1$ctl00$ctl02$ctl02$FilterTextBox_CompanyId', ''),
        ('__ASYNCPOST', 'true'),
        ('RadAJAXControlID', 'ctl00_cphMain_RadAjaxManager1'),
    ]
    data.extend(extraPayload)
    pp.pprint(data)
    return data

def makeRequest(data):
    return requests.post(
        'http://rocsupport.mfsa.com.mt/pages/SearchCompanyInformation.aspx',
        headers=headers,
        data=data,
        cookies=cookies
    )

def getResults(html):
    pq = PyQuery(html)
    rows = pq('tr.rgRow td:first-child')
    rows += pq('tr.rgAltRow td:first-child')

    if rows:
        for row in rows:
            print(row.text)
    else:
        print("No rows")

def extractTSM(html):
    pq = PyQuery(html)
    # scripts = [i.text() for i in pq.items('script')]
    scripts = pq('script')
    telerik = ''
    for s in scripts:
        if 'src' in s.attrib:
            if '/Telerik' in s.attrib['src']:
                telerik = s.attrib['src']
    if telerik != '':
        quoted = telerik.split('CombinedScripts_=')[-1]
        telerik = urllib.unquote(quoted)
    return telerik.replace('+', ' ')

def extractViewState(text):
    view_state = ''
    for line in iter(text.splitlines()):
        if '|70|updatePanel|' in line:
            view_state = line
            break
    view_state = view_state.split('|__VIEWSTATE|')[-1]
    view_state = view_state.split('|')[0]
    return view_state

def extractValidation(text):
    validation = ''
    for line in iter(text.splitlines()):
        if '|70|updatePanel|' in line:
            validation = line
            break
    validation = validation.split('|__EVENTVALIDATION|')[-1]
    validation = validation.split('|')[0]
    return validation


d = requestLetter(data, 'M')
res = makeRequest(d)
getResults(res.text)

cookies['ASP.NET_SessionId'] = res.cookies['ASP.NET_SessionId']

print('---------------------------------------')


headers['X-MicrosoftAjax'] = 'Delta=true'
s = PyQuery(res.text)('input#__VIEWSTATE').val()
g = PyQuery(res.text)('input#__VIEWSTATEGENERATOR').val()
v = PyQuery(res.text)('input#__EVENTVALIDATION').val()
t = extractTSM(res.text)
dnp = nextPage(data=d, state=s, validation=v, generator=g, tsm=t)
resnp = makeRequest(dnp)
pp.pprint(resnp.text)
getResults(resnp.text)
