import datetime
import hashlib
import json
import re

# from geopy import Nominatim
from time import sleep

from lxml import etree

from src.bstsouecepkg.extract import Extract
from src.bstsouecepkg.extract import GetPages


class Handler(Extract, GetPages):
    base_url = 'https://www.scc.virginia.gov'
    NICK_NAME = base_url.split('//')[-1]
    fields = ['overview']
    overview = {}
    tree = None
    api = None

    header = {
        'User-Agent':
            'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0',
        'Accept':
            'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9;application/json',
        'accept-language': 'en-US,en;q=0.9,ru-RU;q=0.8,ru;q=0.7',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    def appendToResult(self, result, listOfValues, appendLink=None):
        for value in listOfValues:
            result.append(f'{value}?={appendLink}')
        return result

    def getResultListFromResponse(self, type, response=None, searchquery=None, appendLink=None, reqType=None):
        result = []
        if type == 'api' and response:
            data = json.loads(response.content)
            try:
                companies = data['InsurersResponse']['Insurer']
                # print(companies)
                for company in companies:
                    name = company['NAME_EN']
                    # print(name)
                    # name = company['name'].replace(' ', '-')
                    # link = f'https://www.princeedwardisland.ca/en/feature/pei-business-corporate-registry-original#/service/LegacyBusiness/LegacyBusinessView;e=LegacyBusinessView;business_number={code}'
                    if searchquery in name:
                        if appendLink:
                            result.append(f'{name}?={appendLink}?={reqType}')
                        else:
                            result.append(name)
            except:
                return None
        if type == 'tree' and searchquery:
            names = self.get_by_xpath(f'//tr/td[2]/text()')
            labels = self.get_by_xpath('//table[@title="Company Search Results"]//tr//td[1]/a/@href')
            labels = [l.split("'")[-2] for l in labels]
            # if names:
            #     if appendLink:
            #         result = self.appendToResult(result, names, appendLink)
            #     else:
            #         result = self.appendToResult(result, names)
            if labels and names:
                for l, n in zip(labels, names):
                    result.append(f'{searchquery}?={l}?={n}')
        return result

    def getASPhiddenFields(self):
        names = self.get_by_xpath('//input[@type="hidden"]//@name')
        temp = {}
        for name in names:
            val = self.get_by_xpath(f'//input[@name="{name}"]//@value')
            if val:
                temp[name] = val[0]
            else:
                temp[name] = ''
        return temp

    def getpages(self, searchquery):
        url = 'https://www.scc.virginia.gov/boi/ConsumerInquiry/Search.aspx?searchType=company'

        # response = self.get_tree(
        #     url,
        #     headers=self.header)
        result = []
        i = 0
        if type(url) == list:
            for u in url:
                # print(u)
                if i == 0:
                    self.get_working_tree_api(u, 'api')
                    result.extend(self.getResultListFromResponse('tree', searchquery=searchquery, appendLink=u))
                else:
                    link = 'https://www.tamm.abudhabi/jssapi/Request/executerequest'
                    data = {
                        'body': {'Insurers': {'RequestType': u}},
                        'url': "https://api.abudhabi.ae/ws/InsuranceServices/1.0/Insurers"}
                    # print(data)
                    api = self.get_content(link, headers=self.header, method='POST', data=json.dumps(data))
                    # print(api.content)

                    result.extend(
                        self.getResultListFromResponse('api', searchquery=searchquery, appendLink=link, response=api,
                                                       reqType=u))
                i += 1
        else:
            url = 'https://www.scc.virginia.gov/boi/ConsumerInquiry/default.aspx'
            self.get_working_tree_api(url, 'tree')
            data = self.getASPhiddenFields()
            data['__EVENTTARGET'] = 'ctl00$MainContent$lbCompany'
            url = 'https://www.scc.virginia.gov/boi/ConsumerInquiry/Search.aspx?searchType=company'
            self.get_working_tree_api(url, 'tree', method='POST', data=data)
            # self.check_tree()
            data = self.getASPhiddenFields()
            data['__EVENTTARGET'] = 'ctl00$MainContent$btnCmpySearch'
            # data['ctl00$MainContent$rblAgActive']= 'Y'
            # data['ctl00$MainContent$txtAgLicenseNum']=''
            # data['ctl00$MainContent$txtAgNPN']=''
            # data['ctl00$MainContent$rblAgStartsWith']= 'Y'
            # data['ctl00$MainContent$txtLast']=''
            # data['ctl00$MainContent$txtFirst']=''
            # data['ctl00$MainContent$txtAgCity']=''
            # data['ctl00$MainContent$ddlAgState']=''
            # data['ctl00$MainContent$txtAgZipcode']=''
            # data['ctl00$MainContent$ddlAgInsuranceType']=''
            # data['ctl00$MainContent$ddlAgLicenseType']=''
            # data['ctl00$MainContent$hfAgPageNumber']=''
            # data['ctl00$MainContent$rblAgyActive']= 'Y'
            # data['ctl00$MainContent$txtAgyLicenseNum']=''
            # data['ctl00$MainContent$txtAgyNPN']=''
            # data['ctl00$MainContent$rblAgyStartsWith']= 'Y'
            # data['ctl00$MainContent$txtAgyName']=''
            # data['ctl00$MainContent$txtAgyCity']=''
            # data['ctl00$MainContent$ddlAgyState']=''
            # data['ctl00$MainContent$txtAgyZipcode']=''
            # data['ctl00$MainContent$ddlAgyInsuranceType']=''
            # data['ctl00$MainContent$ddlAgyLicenseType']=''
            # data['ctl00$MainContent$hfAgyPageNumber']=''
            # data['ctl00$MainContent$txtCompanyNumber']=''
            # data['ctl00$MainContent$rblCmpyStartsWith']= 'Y'
            data['ctl00$MainContent$txtCmpyName'] = searchquery
            # data['ctl00$MainContent$ddlCmpyType']=''
            # data['ctl00$MainContent$ddlLOA']=''
            # data['ctl00$MainContent$hfCmpyPageNumber']=''
            # data['ctl00$MainContent$rblNavType']= 'I'
            # data['ctl00$MainContent$rblNavAgyStartsWith']= 'Y'
            # data['ctl00$MainContent$txtNavEntityName']=''
            # data['ctl00$MainContent$txtNavFirstName']=''
            # data['ctl00$MainContent$txtNavCity']=''
            # data['ctl00$MainContent$ddlNavState']=''
            # data['ctl00$MainContent$txtNavZipCode']=''
            # data['ctl00$MainContent$txtNavLicenseNum']=''
            # data['ctl00$MainContent$txtNavNPN']=''
            # data['ctl00$MainContent$ddlOrderBy']= 'Name'
            # data['ctl00$MainContent$hfNavPageNumber']=''
            # data['ctl00$MainContent$hfActiveTabIndex']= '2'
            # data['ctl00$MainContent$hfLastView']= '2'

            self.get_working_tree_api(url, 'tree', method='POST', data=data)
            #k_tree()
            # data = self.getASPhiddenFields()
            #
            # data['__EVENTTARGET'] = 'ctl00$MainContent$gvCmpyResults'
            # data['__EVENTARGUMENT'] = 'Select$1'
            # data['ctl00$MainContent$txtCmpyName'] = 'bank'
            # print(data)
            # self.get_working_tree_api(url, 'tree', method='POST', data=data)
            # self.check_tree()
            result = self.getResultListFromResponse('tree', searchquery=searchquery)
            # result.extend(self.getResultListFromResponse('tree', searchquery=searchquery), appendLink=)
        self.session.close()
        if result:
            return result

    def get_by_xpath(self, xpath):
        try:
            el = self.tree.xpath(xpath)
        except Exception as e:
            print(e)
            return None
        if el:
            el = [i.strip() for i in el]
            el = [i for i in el if i != '']
            return el
        else:
            return None

    def reformat_date(self, date, format):
        date = datetime.datetime.strptime(date.strip(), format).strftime('%Y-%m-%d')
        return date

    def get_business_class(self, xpathCodes=None, xpathDesc=None, xpathLabels=None):
        res = []
        if xpathCodes:
            codes = self.get_by_xpath(xpathCodes)
        if xpathDesc:
            desc = self.get_by_xpath(xpathDesc)
        if xpathLabels:
            labels = self.get_by_xpath(xpathLabels)

        for c, d, l in zip(codes, desc, labels):
            temp = {
                'code': c.split(' (')[0],
                'description': d,
                'label': l.split('(')[-1].split(')')[0]
            }
            res.append(temp)
        if res:
            self.overview['bst:businessClassifier'] = res

    def get_post_addr(self, tree):
        addr = self.get_by_xpath(tree, '//span[@id="lblMailingAddress"]/..//text()', return_list=True)
        if addr:
            addr = [i for i in addr if
                    i != '' and i != 'Mailing Address:' and i != 'Inactive' and i != 'Registered Office outside NL:']
            if addr[0] == 'No address on file':
                return None
            if addr[0] == 'Same as Registered Office' or addr[0] == 'Same as Registered Office in NL':
                return 'Same'
            fullAddr = ', '.join(addr)
            temp = {
                'fullAddress': fullAddr if 'Canada' in fullAddr else (fullAddr + ' Canada'),
                'country': 'Canada',

            }
            replace = re.findall('[A-Z]{2},\sCanada,', temp['fullAddress'])
            if not replace:
                replace = re.findall('[A-Z]{2},\sCanada', temp['fullAddress'])
            if replace:
                torepl = replace[0].replace(',', '')
                temp['fullAddress'] = temp['fullAddress'].replace(replace[0], torepl)
            try:
                zip = re.findall('[A-Z]\d[A-Z]\s\d[A-Z]\d', fullAddr)
                if zip:
                    temp['zip'] = zip[0]
            except:
                pass
        # print(addr)
        # print(len(addr))
        if len(addr) == 4:
            temp['city'] = addr[-3]
            temp['streetAddress'] = addr[0]
        if len(addr) == 5:
            temp['city'] = addr[-4]
            temp['streetAddress'] = addr[0]
        if len(addr) == 6:
            temp['city'] = addr[-4]
            temp['streetAddress'] = ', '.join(addr[:2])

        return temp

    def get_address(self, xpath=None, zipPattern=None, key=None, returnAddress=False, addr=None, zip=None,
                    noAddress=False):
        if xpath:
            addr = self.get_by_xpath(xpath)
            # print(addr, xpath)
        if key:
            addr = self.get_by_api(key)
        if noAddress:
            if zip and zip != '-':
                temp = {
                    'streetAddress': zip,
                    'fullAddress': f'PO Box {zip}, Abu Dhabi',
                    'country': 'Abu Dhabi'
                }
            else:
                temp = {
                    'fullAddress': f'Abu Dhabi',
                    'country': 'Abu Dhabi'
                }
            self.overview['mdaas:RegisteredAddress'] = temp

        if addr:
            # print(addr)
            if type(addr) == list:
                addr = ''.join(addr)
            if '\n' in addr:
                splitted_addr = addr.split('\n')
            if ', ' in addr:
                splitted_addr = addr.split(', ')

            addr = addr.replace('\n', ' ')
            # print(addr)
            # splitted_addr = addr.split('\n')
            # print(addr)
            addr = addr[0] if type(addr) == list else addr
            temp = {
                'fullAddress': addr,
                'country': 'Philippines'
            }
            # print(addr)
            zip = re.findall(zipPattern, addr)
            if zip:
                temp['zip'] = zip[0]
            try:
                patterns = ['Suite\s\d+']
                for pattern in patterns:
                    pat = re.findall(pattern, addr)
                    if pat:
                        first_part = addr.split(pat[0])
                        temp['streetAddress'] = first_part[0] + pat[0]
            except:
                pass
            try:
                if temp['zip']:
                    city = addr.replace(temp['zip'], '')
            except:
                pass
            try:
                if temp['streetAddress']:
                    city = city.replace(temp['streetAddress'], '')
            except:
                pass
                city = addr.replace(',', '').strip()
                city = re.findall('[A-Z][a-z]+\sCity', city)
                temp['city'] = city[0]
            try:
                if temp['city']:
                    temp['streetAddress'] = addr.split(temp['city'])[0][:-2]
            except:
                pass
            if returnAddress:
                return temp
            self.overview['mdaas:RegisteredAddress'] = temp

    def get_address_by_several_fields(self):
        temp = {}
        streetAddress = self.get_by_xpath('//span[@id="ctl00_MainContent_lblAddress1"]/text()')
        zip = self.get_by_xpath('//span[@id="ctl00_MainContent_lblZip"]/text()')
        city = self.get_by_xpath('//span[@id="ctl00_MainContent_lblCity"]/text()')
        state = self.get_by_xpath('//span[@id="ctl00_MainContent_lblState"]/text()')
        fullAddress = ''
        if streetAddress:
            temp['streetAddress'] = streetAddress[0]
            fullAddress += streetAddress[0] + ', '
        if city:
            fullAddress += city[0] + ', '
        if state:
            fullAddress += state[0] + ', '
        if zip:
            temp['zip'] = zip[0]
            fullAddress += zip[0] + ', '
        fullAddress += 'United States'
        temp['country'] = 'United States'
        temp['fullAddress'] = fullAddress
        self.overview['mdaas:PostalAddress'] = temp


    def get_prev_names(self, tree):
        prev = []
        names = self.get_by_xpath(tree,
                                  '//table[@id="tblPreviousCompanyNames"]//tr[@class="row"]//tr[@class="row"]//td[1]/text() | //table[@id="tblPreviousCompanyNames"]//tr[@class="row"]//tr[@class="rowalt"]//td[1]/text()',
                                  return_list=True)
        dates = self.get_by_xpath(tree,
                                  '//table[@id="tblPreviousCompanyNames"]//tr[@class="row"]//tr[@class="row"]//td[2]/span/text() | //table[@id="tblPreviousCompanyNames"]//tr[@class="row"]//tr[@class="rowalt"]//td[2]/span/text()',
                                  return_list=True)
        #
        # print(names)
        if names:
            names = [i for i in names if i != '']
        if names and dates:
            for name, date in zip(names, dates):
                temp = {
                    'name': name,
                    'valid_to': date
                }
                prev.append(temp)
        return prev

    def getFrombaseXpath(self, tree, baseXpath):
        pass

    def get_by_api(self, key):
        try:
            el = self.api[key]
            return el
        except:
            return None

    def fillField(self, fieldName, key=None, xpath=None, test=False, reformatDate=None):
        els = None
        el = None
        if xpath:
            if type(xpath) == list:
                els = [self.get_by_xpath(el) for el in xpath]
            else:
                el = self.get_by_xpath(xpath)
        if key:
            el = self.get_by_api(key)
        if test:
            print(el)
        if el or els:
            if type(el) == list and len(el) == 1:
                el = el[0].strip()
            if fieldName == 'vcard:organization-name':
                self.overview[fieldName] = el.split('(')[0].strip()
            if fieldName == 'localName':
                self.overview[fieldName] = el.split('(')[0].strip()
            if fieldName == 'hasURL':
                self.overview[fieldName] = el.strip()
            if fieldName == 'bst:description':
                self.overview[fieldName] = el.strip()
            if fieldName == 'bst:registrationId':
                self.overview[fieldName] = el.strip()
            if fieldName == 'registeredIn':
                self.overview[fieldName] = el.strip()

            if fieldName == 'hasActivityStatus':
                self.overview[fieldName] = el

            if fieldName == 'Service':
                # print(el)
                if type(el) == list:
                    self.overview[fieldName] = {'serviceType': ', '.join(el)}
                else:
                    self.overview[fieldName] = {'serviceType': el}

            if fieldName == 'regExpiryDate':
                self.overview[fieldName] = self.reformat_date(el, reformatDate) if reformatDate else el

            if fieldName == 'vcard:organization-tradename':
                self.overview[fieldName] = el.split('\n')[0].strip()

            if fieldName == 'bst:email':
                if 'mailto:' in el:
                    el = el.split('mailto:')[1]
                self.overview[fieldName] = el

            if fieldName == 'bst:aka':
                names = el.split('\n')
                if len(names) > 1:
                    names = [i.strip() for i in names[1:]]
                    self.overview[fieldName] = names

            if fieldName == 'lei:legalForm':
                self.overview[fieldName] = {
                    'code': '',
                    'label': el}

            if fieldName == 'identifiers':
                self.overview[fieldName] = {
                    'other_company_id_number': el
                }
            if fieldName == 'map':
                self.overview[fieldName] = el[0] if type(el) == list else el

            if fieldName == 'previous_names':
                if els:
                    res = []
                    for n, fr, to in zip(*els):
                        temp = {
                            'name': n,
                            'valid_from': fr if '-' in fr else self.reformat_date(fr, '%m/%d/%Y'),
                            'valid_to': to if '-' in to else self.reformat_date(to, '%m/%d/%Y')
                        }
                        res.append(temp)
                    #print(res)
                    if res:
                        self.overview[fieldName] = res
                    return 0
                if el:
                    el = el.strip()
                    el = el.split('\n')
                    if len(el) < 1:
                        self.overview[fieldName] = {'name': [el[0].strip()]}
                    else:
                        el = [i.strip() for i in el]
                        res = []
                        for i in el:
                            temp = {
                                'name': i
                            }
                            res.append(temp)
                        self.overview[fieldName] = res

            if fieldName == 'isIncorporatedIn':
                if reformatDate:
                    self.overview[fieldName] = self.reformat_date(el, reformatDate)
                else:
                    self.overview[fieldName] = el

            if fieldName == 'sourceDate':
                self.overview[fieldName] = self.reformat_date(el, '%d.%m.%Y')

            if fieldName == 'agent':
                # print(el)
                self.overview[fieldName] = {
                    'name': el.split('\n')[0],
                    'mdaas:RegisteredAddress': self.get_address(returnAddress=True, addr=' '.join(el.split('\n')[1:]),
                                                                zipPattern='[A-Z]\d[A-Z]\s\d[A-Z]\d')
                }
                # print(self.get_address(returnAddress=True, addr=' '.join(el.split('\n')[1:]),
                # zipPattern='[A-Z]\d[A-Z]\s\d[A-Z]\d'))
            if fieldName == 'tr-org:hasRegisteredPhoneNumber':
                if type(el) == list and len(el) > 1:
                    el = el[0]
                self.overview[fieldName] = el

            if fieldName == 'hasRegisteredFaxNumber':
                if type(el) == list and len(el) > 1:
                    el = el[0]
                self.overview[fieldName] = el

    def check_tree(self):
        print(self.tree.xpath('//text()'))

    def get_working_tree_api(self, link_name, type, method='GET', data=None):
        if type == 'tree':
            self.tree = self.get_tree(link_name,
                                      headers=self.header, verify=False, method=method, data=data)
        if type == 'api':
            # data = {
            #     "appName": "LegacyBusiness",
            #     "featureName": "LegacyBusiness",
            #     "metaVars": {
            #         "save_location": None,
            #         "service_id": None
            #     },
            #     "queryName": "LegacyBusinessView",
            #     "queryVars": {
            #         "activity": "LegacyBusinessView",
            #         "business_number": link_name,
            #         "service": "LegacyBusiness"
            #     }
            # }
            #
            # print(link_name)
            self.api = self.get_content(link_name,
                                        headers=self.header, method='GET')

            # print(self.api)
            self.api = json.loads(self.api.content)
            self.api = self.api['data']['serviceCodeData']['GIDescription']
            self.tree = etree.HTML(self.api)
            # print(tree.xpath('//td'))

    def removeQuotes(self, text):
        text = text.replace('"', '')
        return text

    def get_overview(self, link_name):
        company_name = link_name.split('?=')[-1]
        searchquery = link_name.split('?=')[0]
        # label = link_name.split('?=')[0]
        # url = link_name.split('?=')[1]
        # print(link_name)

        url = 'https://www.scc.virginia.gov/boi/ConsumerInquiry/default.aspx'
        self.get_working_tree_api(url, 'tree')
        data = self.getASPhiddenFields()
        data['__EVENTTARGET'] = 'ctl00$MainContent$lbCompany'
        url = 'https://www.scc.virginia.gov/boi/ConsumerInquiry/Search.aspx?searchType=company'
        self.get_working_tree_api(url, 'tree', method='POST', data=data)
        data = self.getASPhiddenFields()
        data['__EVENTTARGET'] = 'ctl00$MainContent$btnCmpySearch'
        data['ctl00$MainContent$txtCmpyName'] = searchquery

        self.get_working_tree_api(url, 'tree', method='POST', data=data)
        #self.check_tree()

        label = self.get_by_xpath(f'//tr/td[2]/text()[contains(., "{company_name}")]/../../td[1]/a/@href')
        if label:
            label = label[0]
            label = label.split("'")[-2]
            data = self.getASPhiddenFields()
            data['__EVENTTARGET'] = 'ctl00$MainContent$gvCmpyResults'
            data['__EVENTARGUMENT'] = 'Select$1'
            data['ctl00$MainContent$txtCmpyName'] = 'bank'
            self.get_working_tree_api(url, 'tree', method='POST', data=data)
            self.overview = {}
            self.overview['isDomiciledIn'] = 'US'
            self.overview['@source-id'] = self.NICK_NAME
            self.overview['sourceDate'] = datetime.datetime.today().strftime('%Y-%m-%d')

            self.fillField('vcard:organization-name', xpath=f'//span[@id="ctl00_MainContent_lblName"]/text()')
            self.fillField('tr-org:hasRegisteredPhoneNumber', xpath=f'//span[@id="ctl00_MainContent_lblPhone"]/text()')
            self.fillField('identifiers', xpath=f'//span[@id="ctl00_MainContent_lblNumber"]/text()')
            self.fillField('bst:registrationId', xpath=f'//span[@id="ctl00_MainContent_lblNumber"]/text()')
            self.fillField('hasURL', xpath=f'//a[@id="ctl00_MainContent_aCmpyWeb"]/text()')
            self.fillField('bst:description', xpath=f'//div[@id="ctl00_MainContent_ucDesc_divPropCasual"]//text()[1]')
            self.fillField('Service', xpath=f'//table[@id="ctl00_MainContent_gvAuthLn"]//tr//td[1]/text()')
            prev_names = [f'//table[@id="ctl00_MainContent_gvCmpyAlias"]//tr/td[1]/text()',
                          f'//table[@id="ctl00_MainContent_gvCmpyAlias"]//tr/td[3]/text()',
                          f'//table[@id="ctl00_MainContent_gvCmpyAlias"]//tr/td[4]/text()']
            self.fillField('previous_names', xpath=prev_names)
            self.fillField('registeredIn', xpath=f'//span[@id="ctl00_MainContent_lblDomState"]/text()')
            self.get_address_by_several_fields()
            self.overview['regulator_name'] = 'Common wealth of virginia - State Corporation Commission'
            self.overview['regulatorAddress'] = {
                "fullAddress": 'State Corporation Commission 1300 E. Main St.Richmond, Virginia 23219',
                "city": 'Richmond', "country": 'United State'}
            self.overview['regulator_url'] = self.base_url
            self.overview['RegulationStatus'] = 'Authorised'

            # print(self.overview)
            # exit()
        # url = 'https://www.gov.ph/es/directory-of-department-and-agencies.html'

        # print(link_name)

        # if 'doh-offices_en' in url:
        #     self.get_working_tree_api(url, 'api')
        #     baseXpath = f'//tr//td[2]/text()[contains(., "{company_name}")]/../..'
        #     self.fillField('vcard:organization-name', xpath=f'{baseXpath}//td[2]/text()')
        #
        #     self.fillField('bst:email', xpath=f'{baseXpath}//td[3]/text()')
        #     self.fillField('tr-org:hasRegisteredPhoneNumber', xpath=f'{baseXpath}//td[5]/text()')
        #     self.fillField('hasRegisteredFaxNumber', xpath=f'{baseXpath}//td[6]/text()')
        #
        #     zip = self.get_by_xpath(f'{baseXpath}//td[7]/text()')
        #     if zip:
        #         zip = zip[0]
        #         self.get_address(zip=zip, noAddress=True)
        # else:
        #     data = {
        #         'body': {'Insurers': {'RequestType': link_name.split('?=')[-1]}},
        #         'url': "https://api.abudhabi.ae/ws/InsuranceServices/1.0/Insurers"}
        #     api = self.get_content(url, headers=self.header, method='POST', data=json.dumps(data))
        #     self.api = json.loads(api.content)
        #     self.api = self.api['InsurersResponse']['Insurer']
        #     for comp in self.api:
        #         if comp['NAME_EN'] == company_name:
        #             self.api = comp
        #             break
        #     # print(self.api)
        #     self.fillField('vcard:organization-name', key='NAME_EN')
        #     self.fillField('localName', key='NAME_AR')
        #     self.fillField('identifiers', key='LICENSE_NUMBER')

        return self.overview
        # print(self.overview)
        # # exit()
        # try:
        #     self.fillField('vcard:organization-name', xpath=f'{baseXpath}/h4/text()')
        # except:
        #     return None
        # print(self.api)

        # self.overview['isDomiciledIn'] = 'PH'
        #
        #
        # self.fillField('tr-org:hasRegisteredPhoneNumber', xpath=f'{baseXpath}/p[@class="telfax"]/text()')
        # self.fillField('bst:email', xpath=f'{baseXpath}/p[@class="email"]/a/@href')
        # self.get_address(xpath=f'{baseXpath}/p[@id="address"]//*/text()', zipPattern='\d{4}')
        # print(self.overview)

        # self.overview['bst:sourceLinks'] = link_name

        # self.fillField('vcard:organization-tradename', key='Trade Name(s)')
        # self.fillField('hasActivityStatus', key='Status')
        # self.fillField('bst:aka', key='Trade Name(s)')
        # self.fillField('previous_names', key='Former Name(s)')
        # self.fillField('lei:legalForm', key='Business Type')
        # self.fillField('isIncorporatedIn', key='Registration Date', reformatDate='%d-%b-%Y')
        # self.fillField('identifiers', key='Registration Number')
        # self.fillField('Service', key='Business In')
        # self.fillField('agent', key='Chief Agent')
        # self.fillField('previous_names', key='Former Name(s)')
        # self.fillField('regExpiryDate', key='Expiry Date', reformatDate='%d-%b-%Y')
        # self.overview[
        #     'bst:registryURI'] = f'https://www.princeedwardisland.ca/en/feature/pei-business-corporate-registry-original#/service/LegacyBusiness/LegacyBusinessView;e=LegacyBusinessView;business_number={self.api["Registration Number"]}'

        # print(self.overview)
        # exit()
        # self.fillField('lei:legalForm', '//div/text()[contains(., "Legal form")]/../following-sibling::div//text()')
        # self.fillField('identifiers', '//div/text()[contains(., "Registry code")]/../following-sibling::div//text()')
        # self.fillField('map', '//div/text()[contains(., "Address")]/../following-sibling::div/a/@href')
        # self.fillField('incorporationDate', '//div/text()[contains(., "Registered")]/../following-sibling::div/text()')

        # self.fillField('bst:businessClassifier', '//div/text()[contains(., "EMTAK code")]/../following-sibling::div/text()')
        # self.get_business_class('//div/text()[contains(., "EMTAK code")]/../following-sibling::div/text()',
        #                         '//div/text()[contains(., "Area of activity")]/../following-sibling::div/text()',
        #                         '//div/text()[contains(., "EMTAK code")]/../following-sibling::div/text()')
        #
        # self.get_address('//div/text()[contains(., "Address")]/../following-sibling::div/text()',
        #                  zipPattern='\d{5}')
        #
        # self.overview['sourceDate'] = datetime.datetime.today().strftime('%Y-%m-%d')

        # self.overview['@source-id'] = self.NICK_NAME

        # print(self.overview)
        # return self.overview

    # def get_officership(self, link_name):
    #     self.get_working_tree_api(link_name, 'api')
    #
    #     names = self.get_by_api('Officer(s)')
    #     if '\n' in names:
    #         names = names.split('\n')
    #     # roles = self.get_by_xpath(
    #     #     '//div/text()[contains(., "Right of representation")]/../following-sibling::div//tr/td[3]/text()')
    #
    #     off = []
    #     names = [names] if type(names) == str else names
    #     roles = []
    #     for name in names:
    #         roles.append(name.split(' - ')[-1])
    #     names = [i.split(' - ')[0] for i in names]
    #
    #     # roles = [roles] if type(roles) == str else roles
    #     for n, r in zip(names, roles):
    #         home = {'name': n,
    #                 'type': 'individual',
    #                 'officer_role': r,
    #                 'status': 'Active',
    #                 'occupation': r,
    #                 'information_source': self.base_url,
    #                 'information_provider': 'Prince Edward Island Corporate Registry'}
    #         off.append(home)
    #     return off

    # def get_documents(self, link_name):
    #     docs = []
    #     self.get_working_tree(link_name)
    #     docs_links = self.get_by_xpath('//div/a/text()[contains(., "PDF")]/../@href')
    #     docs_links = docs_links if type(docs_links) == list else [docs_links]
    #     docs_links = [f'{self.base_url}{i}' for i in docs_links]
    #     for doc in docs_links:
    #         temp = {
    #             'url': doc,
    #             'description': 'Summary of company details'
    #         }
    #         docs.append(temp)
    #     return docs

    # def get_financial_information(self, link_name):
    #     self.get_working_tree(link_name)
    #     fin = {}
    #     summ = self.get_by_xpath('//div/text()[contains(., "Capital")]/../following-sibling::div//text()')
    #     if summ:
    #         summ = re.findall('\d+', summ[0])
    #         if summ:
    #             fin['Summary_Financial_data'] = [{
    #                 'summary': {
    #                     'currency': 'Euro',
    #                     'balance_sheet': {
    #                         'authorized_share_capital': ''.join(summ)
    #                     }
    #                 }
    #             }]
    #     return fin
    # def get_shareholders(self, link_name):
    #
    #     edd = {}
    #     shareholders = {}
    #     sholdersl1 = {}
    #
    #     company = self.get_overview(link_name)
    #     company_name_hash = hashlib.md5(company['vcard:organization-name'].encode('utf-8')).hexdigest()
    #     self.get_working_tree_api(link_name, 'api')
    #     # print(self.api)
    #
    #     try:
    #         names = self.get_by_api('Shareholder(s)')
    #         if len(re.findall('\d+', names)) > 0:
    #             return edd, sholdersl1
    #         if '\n' in names:
    #             names = names.split('\n')
    #
    #         holders = [names] if type(names) == str else names
    #
    #         for i in range(len(holders)):
    #             holder_name_hash = hashlib.md5(holders[i].encode('utf-8')).hexdigest()
    #             shareholders[holder_name_hash] = {
    #                 "natureOfControl": "SHH",
    #                 "source": 'Prince Edward Island Corporate Registry',
    #             }
    #             basic_in = {
    #                 "vcard:organization-name": holders[i],
    #                 'isDomiciledIn': 'CA'
    #             }
    #             sholdersl1[holder_name_hash] = {
    #                 "basic": basic_in,
    #                 "shareholders": {}
    #             }
    #     except:
    #         pass
    #
    #     edd[company_name_hash] = {
    #         "basic": company,
    #         "entity_type": "C",
    #         "shareholders": shareholders
    #     }
    #     #print(sholdersl1)
    #     return edd, sholdersl1
