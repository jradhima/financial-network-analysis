"""
Module to create network
"""

import numpy as np
import pandas as pd
import operator
import base64

import networkx as nx
import matplotlib
# Necessary backend
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import seaborn as sns

def create_correlation_network(year, threshold, linkage):
    """
    Generate the graph based on correlation
    """
    df = pd.read_csv('data/filingsEnd{}.csv'.format(year))
    df = df.sample(frac=.1, replace=False, random_state=13)
    df = df.reset_index(inplace=False)
    # an issuer can have multiple different CUSIP's (first class shares, normal shares, etc)
    # they are all money however so we will aggregate them in the future
    df['issuer'] = df['cusip'].apply(lambda x: x[:6])
    # compute total value for each CIK, to normalize investments later
    totalValue = df.groupby('owner')['value'].sum()
    df = df.merge(totalValue, how='left', left_on='owner', right_index=True)
    df.drop(columns=['Unnamed: 0', 'cusip', 'amount', 'put_or_call', 'report_date'], inplace=True)
    print(df.columns)
    # compute normalized value
    df['norm_value'] = df['value_x'] / df['value_y']
    mask = df['value_x'] == 0
    df = df.loc[~mask]
    issuers = df.drop_duplicates(subset='issuer')
    issuers['label'] = issuers['filed name'].apply(lambda x: ' '.join(x[:].split(' ')[:3]))
    # perform final aggregation and inspect
    issuers = issuers[['label', 'issuer']]
    df = df.groupby(['cik','issuer']).agg({'norm_value': 'sum'})
    df = df.reset_index()
    wideDf = df.pivot(index='cik', columns='issuer', values='norm_value').fillna(value=0)
    correlation = wideDf.transpose().corr()
    # cluster the correlation matrix to show connectivity
    clmap = sns.clustermap(correlation, method=linkage)

    # Necessary to refresh newly saved fig
    corr_matrix = "data/corr_matrix.png"
    clmap.savefig(corr_matrix)
    encoded_matrix = base64.b64encode(open(corr_matrix, 'rb').read())

    # now pick an 'gravity' factor
    # factors above 1 lead to a more clustered graph
    # factors below 1 lead to a more spread-out graph
    # values between 0.5-1 make best graphs
    # lower threshold values need lower gravity factors
    gravity = 0.4
    df = df.sample(frac=.1, replace=False, random_state=13)
    df = df.reset_index(inplace=False)
    investors = []
    companies = []
    G=nx.Graph()
    for i in df.index:
        edge = df.iloc[i,]
        if edge['norm_value'] > threshold:
            G.add_edge(edge['cik'], edge['issuer'], weight=edge['norm_value'] ** (1/gravity))
            investors.append(edge['cik'])
            companies.append(edge['issuer'])
            # calculate centrality
    degCent = nx.degree_centrality(G)
    # get positions
    pos = nx.spring_layout(G)  # positions for all nodes
    # calculate node size based on centrality for each group
    investorSize = [degCent[investor]**1.5 * 10000 for investor in investors]
    issuerSize = [degCent[issuer]**1.5 * 10000 for issuer in companies]
    # calculate edge size
    edgeSize = [d['weight'] ** (gravity) for (u, v, d) in G.edges(data=True)]
    #pick how many labels you want displayed
    num = 20
    # get num most central issuers
    sorted_x = sorted(degCent.items(), key=operator.itemgetter(1), reverse=True)
    central = [item[0] for item in sorted_x[:num] if type(item[0]) == str]
#
    # turn list into dictionary
    labels = {}
    for code in central:
        try:
            labels[code] = issuers[issuers['issuer'] == code]['label'].item()
        except:
            labels[code] = code

    plt.figure(figsize=(15,15))
    nx.draw_networkx_nodes(G, pos, nodelist=investors, node_size=investorSize, alpha=0.5, node_color='r')
    nx.draw_networkx_nodes(G, pos, nodelist=companies, node_size=issuerSize, alpha=0.5, node_color='b')
    nx.draw_networkx_edges(
        G, pos, width=edgeSize, alpha=0.4, edge_color="k")
    nx.draw_networkx_labels(G, pos, labels=labels, font_size=10, font_family="sans-serif", font_color='k');

    corr_network = "data/corr_network.png"
    plt.savefig('data/corr_network.png')
    encoded_network = base64.b64encode(open(corr_network, 'rb').read())

    return encoded_network, encoded_matrix


if __name__ == "__main__":
    create_correlation_network("2017", .5)
