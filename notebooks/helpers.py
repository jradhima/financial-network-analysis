import numpy as np
import pandas as pd
import networkx as nx

from bs4 import BeautifulSoup
from sec_edgar_downloader import Downloader
from requests_html import HTMLSession
import time
import operator
import os
from datetime import datetime

import matplotlib.pyplot as plt
import matplotlib.cm as cm
import seaborn as sns
    

class Filing13F:
    """ 
        Class containing common stock portfolio information from an institutional investor.
        1. Parsed from 13F-HR filing from SEC Edgar database.

    """
    
    # If True prints out results in console
    debug = False
    
    
    def __init__(self,filepath=''):
        """ Initialize object """
        self.filepath = filepath # Path of file
        
        # Directly call parse_file() when filepath is provided with __init__
        if self.filepath:
            self.parse_file(self.filepath)
            

    def parse_file(self, filepath=''):
        """ Parses relevant information from 13F-HR text file """
        self.filepath = filepath # Path of file
        
        if self.debug:
            print(self.filepath)
            
        # Opens document and passes to BeautifulSoup object.
        doc = open(filepath)
        soup = BeautifulSoup(doc, 'html.parser') # OBS! XML parser will not work with SEC txt format
        
        # Print document structure and tags in console
        if self.debug:
            print(soup.prettify())
            
            for tag in soup.find_all(True):
                print(tag.name)
        
        ## --- Parse content using tag strings from txt document: <tag> content </tag>
        # OBS html.parser uses tags in lowercase
        
        # Name of filing company
        self.company = soup.find('filingmanager').find('name').string
        # Company identifier: Central Index Key
        self.CIK = soup.find('cik').string
        # Form type: 13F-HR
        self.formtype = soup.find('type').string
        # 13F-HR file number
        self.fileNumber = soup.find('form13ffilenumber').string
        # Reporting date (e.g. 03-31-2020)
        self.period_of_report_date = datetime.strptime(soup.find('periodofreport').string, '%m-%d-%Y').date()
        # Filing date (up to 45 days after reporting date)
        self.filing_date = datetime.strptime(soup.find('signaturedate').string, '%m-%d-%Y').date()
                
        ## --- Parse stock list: Each stock is marked with an infoTable parent tag
        stocklist = soup.find_all('infotable') # List of parent tag objects
        
        # Initialize lists
        name = []     # Company name
        cusip = []    # CUSIP identifier
        value = []    # Total value of holdings
        amount = []   # Amount of stocks
        #price_per_share = []  # Share price on reporting day != purchase price
        poc = []      # Put/Call options
        symbol = []   # Trading symbol
        
        # Fill lists with each stock
        for s in stocklist:
            # Company name & Title of class (e.g. COM, Class A, etc)
            n = s.find("nameofissuer").string
            n = n.replace('.','') # Remove dots
            
            c = s.find("titleofclass").string
            if c != "COM":
                name.append(n+" ("+c+")")
            else:
                name.append(n)
                
            # CUSIP identifier
            cusip.append(s.find("cusip").string)
            # Total value of holdings
            v = int(s.find("value").string)
            value.append(v)
            # Amount of stocks
            ssh = int(s.find("shrsorprnamt").find("sshprnamt").string)
            amount.append(ssh)
            # Share price on reporting day (OBS! != purchase price)
            #price_per_share.append(round(v*1000/ssh,2))    
            
            # Put/Call options
            put_or_call = s.find("putcall")
            if put_or_call:
                poc.append(put_or_call.string)
            else:
                poc.append('No')
            

        # Create dictionary        
        #stock_dict = {"filed name":name,  "cusip":cusip, "value":value, "amount":amount,
        #       "price_per_share":price_per_share, "put_or_call":poc}
        
        # Create dictionary        
        stock_dict = {"filed name":name,  "cusip":cusip, "value":value, "amount":amount, "put_or_call":poc}
        # Store in dataframe
        data = pd.DataFrame(stock_dict)
        data['owner'] = self.company
        data['cik'] = self.CIK
        data['report_date'] = self.period_of_report_date
        
        # Drop rows with put/call option
        indexes =  data[  data['put_or_call'] != 'No' ].index
        data.drop(indexes, inplace=True)
        # data.set_index('symbol', inplace=True)
        #data.set_index('filed name', inplace=True)
        
        self.data = data
        
        return
    
class xml_parser:
    def __init__(self, parsepath):
        self.path = parsepath
        
    def parse(self, num, savepath):
        dfs = []
        count = 1

        # traverse everything starting from folder 'sec-edgar-filings'
        for pathnames, dirnames, filenames in os.walk(self.path):
            # check if every file if it's a submission file
            for file in filenames:
                if file == 'full-submission.txt':

                    filepath = pathnames + os.sep + file

                    # some xml files have a 'ns1:' prefix which is annoying, replace it
                    with open(filepath) as f:
                        newText=f.read().replace('ns1:', '')

                    with open(filepath+'new', "w") as f:
                        f.write(newText)

                    # create a Filing object, parse it, and add data to dataframe
                    filing = Filing13F()
                    filing.parse_file(filepath+'new')
                    dfs.append(filing.data)

                    count += 1
                    if count % 50 == 0:
                        print(f"Already parsed {count} filings!")
            if count % num == 0:
                break
        
        df = pd.concat(dfs, ignore_index=True)
        df.to_csv(savepath)


class sec_loader:
    def __init__(self, foldname):
        self.name = foldname
        
    def fetch(self, codes, date1, date2):
        """
        Codes: CIK codes to fetch data for
        Date1: Start date (after) format YYYY-MM-DD
        Date2: End date (bafore) format YYYY-MM-DD
        """

        loader = Downloader(self.name)

        # this is more or less useless, we may want to know which companies we downloaded filings for
        success = []

        # this is needed afterwards, we will iterate over CIK's we failed to download data because
        # the downloaded sometimes fails to download anything for no clear reason
        fail = []

        # run over our codes and...
        for code in codes:

            print(f"Trying CIK Number: {code}")

            # try downloading for a CIK
            try:
                # get 13F-HR filings for the period between 'before' and 'after'
                # since this is 3 months (a quarter) we should only get 1 filing
                num = loader.get('13F-HR', code, after=date1, before=date2)
                print(f"Downloaded {num} files from company {code} \n")
                success.append(code)
            except:
                # we couldn't download anything, add CIK to list for us to try again later
                print(f"Something went wrong with company {code} \n")
                fail.append(code)

            # sleep so we don't have problems with the SEC
            time.sleep(0.11)


        # by now we have run once over all CIK's and have downloaded filings for some
        # we will try again for all CIK's we couldn't get a filing, until we get one

        # we need a counter to not get stuck in an infinite loop, some CIK's might not
        # have filing info or other issues may apply
        count = 0

        # while there are companies we don't have data for, scrape and scrape again
        while len(fail) > 0:

            print(f'Failed to get data for {len(fail)} companies.\nTrying again.\n')

            # each time we loop over all the companies we failed to get data the previous time
            # increment the counter
            count += 1

            # 50 is an arbitrary threshold, depending on our patience and how much we want
            # to get all possible data, this is the total number of iterations we are willing to try
            if count > 50:
                break

            # for every company we failed to get data, try again
            for code in fail:
                print(f"Trying CIK Number: {code}")

                try:
                    num = loader.get('13F-HR', code, after=date1, before=date2)
                    print(f"Downloaded {num} files from company {code} \n")
                    success.append(code)
                    fail.remove(code)
                except:
                    print(f"Something went wrong with company {code} \n")

                time.sleep(0.11)
        


class cik_loader:
    def __init__(self):
        pass
    
    def fetch(self, days, filepath):
        codes = []
        session = HTMLSession()
        url = 'https://www.sec.gov/cgi-bin/current?'

        for page in range(days):

            params = f"q1={page}&q2=0&q3=13F-HR"
            r = session.get(url + params)
            time.sleep(0.11)

            try:
                text = r.html.find('pre', first=True).text
                date = text[:100].split()[7]
                filings = text.replace(date, '').split('\n ')[-1].split('  ')

                firms = {'CIK': [filing.split()[1].zfill(10) for filing in filings],
                        'Name': [' '.join(filing.split()[2:]) for filing in filings],
                        'Type': [filing.split()[0] for filing in filings]}
                codes.append(pd.DataFrame(firms))
            except:
                print(f'No fillings on {date}, or other error')
        
        df = pd.concat(codes, ignore_index=True)
        df.drop_duplicates('CIK').drop(columns='Type').to_csv(filepath)


class clmap:
    def __init__(self, datapath):
        self.data = pd.read_csv(datapath)
        
    def __repr__(self):
        return "Performs necessary calculations and returns a clustermap"
        
    def calculate(self, method, figsize):
        """
        Performs calculations on our DataFrame and returns a clustermap.
        
        Method can be one of ['single', 'complete', 'centroid', 'ward']
        """
        self.data['issuer'] = self.data['cusip'].apply(lambda x: x[:6])
        
        totalValue = self.data.groupby('owner')['value'].sum()
        self.data = self.data.merge(totalValue, how='left', left_on='owner', right_index=True)
        
        self.data.drop(columns=['Unnamed: 0', 'cusip', 'amount', 'put_or_call', 'report_date'], inplace=True)
        
        self.data['norm_value'] = self.data['value_x'] / self.data['value_y']
        
        mask = self.data['value_x'] == 0
        self.data = self.data.loc[~mask]

        self.data = self.data.groupby(['cik','issuer']).agg({'norm_value': 'sum'}).reset_index()

        wideDf = self.data.pivot(index='cik', columns='issuer', values='norm_value').fillna(value=0)

        correlation = wideDf.transpose().corr()
        
        plt.figure(figsize=figsize)

        return sns.clustermap(correlation, method=method)


class netmap:
        def __init__(self, datapath):
            self.data = pd.read_csv(datapath)
        
        def __repr__(self):
            return "Performs necessary calculations and returns a network"

        def calculate(self, threshold, gravity, num, figsize):
            """
            Performs calculations on our DataFrame and returns a network.

            Threshold can be any possitive value between 0 and 1.

            Gravity is a parameter that regulates the spring values for the graph layout.
            Lower values lead to more spread-out visualizations.
            Larger values lead to more clustered layouts.

            Labels is the number of labels that will be visualized on the network.
            """
            self.data['issuer'] = self.data['cusip'].apply(lambda x: x[:6])

            totalValue = self.data.groupby('owner')['value'].sum()
            self.data = self.data.merge(totalValue, how='left', left_on='owner', right_index=True)

            self.data.drop(columns=['Unnamed: 0', 'cusip', 'amount', 'put_or_call', 'report_date'], inplace=True)

            self.data['norm_value'] = self.data['value_x'] / self.data['value_y']

            mask = self.data['value_x'] == 0
            self.data = self.data.loc[~mask]

            issuers = self.data.drop_duplicates(subset='issuer')
            issuers['label'] = issuers['filed name'].apply(lambda x: ' '.join(x[:].split(' ')[:3]))
            issuers = issuers[['label', 'issuer']]

            self.data = self.data.groupby(['cik','issuer']).agg({'norm_value': 'sum'}).reset_index()

            investors = []
            companies = []

            G=nx.Graph()

            for i in self.data.index:
                edge = self.data.iloc[i,]
                if edge['norm_value'] > threshold:
                    G.add_edge(edge['cik'], edge['issuer'], weight=edge['norm_value'] ** (1/gravity))
                    investors.append(edge['cik'])
                    companies.append(edge['issuer'])

            degCent = nx.degree_centrality(G)
            pos = nx.spring_layout(G)
            print(f"Nodes in graph: {len(G.nodes())}\nEdges in graph: {len(G.edges())}")

            # calculate node size based on centrality for each group
            investorSize = [degCent[investor]**1.5 * 10000 for investor in investors]
            issuerSize = [degCent[issuer]**1.5 * 10000 for issuer in companies]

            # calculate edge size
            edgeSize = [d['weight'] ** (gravity) for (u, v, d) in G.edges(data=True)]

            sorted_x = sorted(degCent.items(), key=operator.itemgetter(1), reverse=True)
            central = [item[0] for item in sorted_x[:num] if type(item[0]) == str]

            # turn list into dictionary
            labels = {}
            for code in central:
                try:
                    labels[code] = issuers[issuers['issuer'] == code]['label'].item()
                except:
                    labels[code] = code

            # draw nodes
            plt.figure(figsize=figsize)
            nx.draw_networkx_nodes(G, pos, nodelist=investors, node_size=investorSize, alpha=0.5, node_color='r')

            # draw nodes
            nx.draw_networkx_nodes(G, pos, nodelist=companies, node_size=issuerSize, alpha=0.5, node_color='b')

            # edges
            nx.draw_networkx_edges(
                G, pos, width=edgeSize, alpha=0.4, edge_color="k")

            # labels
            nx.draw_networkx_labels(G, pos, labels=labels, font_size=16, font_family="sans-serif", font_color='k');