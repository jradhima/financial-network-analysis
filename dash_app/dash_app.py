"""
Heroku app instructions. Make sure you install Heroku-CLI and have git installed.
Then go to their site and create an app. You can also do it from the CLI.

To set up the repo (on Windows I ran all of this from Git bash):
git init
heroku git:remote -a sec-network-analysis

git add .
git commit -m "update"
git push heroku master

Make sure Procfile has the line
web: gunicorn dash_app:server
and that your requirements has all dependencies. Heroku will install them when you push

From the command line you might have to do
heroku ps:scale web=1
once you push.

heroku logs --tail
for logs
"""

import pandas as pd
import numpy as np
from pathlib import Path
import operator
import base64

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import networkx as nx

from plotly_network_temporal import make_temporal_plot
from investor_correlation import create_correlation_network

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

# Init figures
corr_matrix = "data/corr_matrix.png"
encoded_matrix = base64.b64encode(open(corr_matrix, 'rb').read())
corr_net = "data/corr_network.png"
encoded_net = base64.b64encode(open(corr_net, 'rb').read())

fig_temporal = make_temporal_plot()

app.layout = html.Div([
    html.H1(children = 'Uncovering the Network', style={'text-align': 'center'}),
    html.P(children = 'Investment firms with over 100M $ under management are required by law to file a 13F report on a quarterly basis, where they disclose their holdings to the Securities and Exchange Commission (SEC). Such a report includes information about the investment manager, the firm, and the positions the firm holds including the total value, the number of shares, the type of asset, etc. The goal of this project is to perform network analysis on the US financial market and examine the connectivity of the market and how it evolves over time, to the extent possible.', style={'text-align': 'center', 'margin-top': "15px"}),
    html.P(children = 'In this figure the user can perform a basic exploratory analysis of the network connectivity for a limited set of investment managers for 2017-2020. While no conclusions can be drawn, it is intended to give a general idea of the connectivty between investment managers. In the slider below the figure, the year can be selected.', style={'text-align': 'center', 'margin-top': "15px"}),
    dcc.Graph(figure=fig_temporal, style={'width': '50%'}),
    html.P(children = "Hierarchical clustering is then applied to the correlation matrix of the US financial market investors. The correlation matrix is based on an investment feature map, calculated assuming each investor is an observation and each possible investment is a feature. For a given investor, the feature vector's values are the normalized investments, i.e. the value of the position divided by the total value of all positions of the investor.", style={'text-align': 'center', 'margin-top. For the interactive options below, it will take approxmately 20 seconds for the figures to update.': "15px"}),
    html.H3(children = 'Select the year of reported 13F data you are interested in analyzing', style={'text-align': 'center', 'margin-top': "30"}),
    dcc.Slider(
        id='year-slider',
        min=2017,
        max=2020,
        value=2017,
        marks={year: year for year in ["2017", "2018", "2019", "2020"]},
        step=None),
    html.H2(children = 'Select the Agglomerative clustering linkage criterion', style={'text-align': 'center'}),
    html.Div([
        dcc.Dropdown(
                id='cluster-dropdown',
                options=[{'label': method, 'value': method} for method in ['single', 'complete', 'centroid', 'ward']],
                value='ward')
                ],
                style={"width": "50%"}),
    html.Img(src='data:image/png;base64,{}'.format(encoded_matrix.decode()), id='corr-matrix'),
    html.P(children = "Next, the network analysis of the US financial market is illustrated using a bipartite graph. Each investor (red node) is only connected to security issuers (blue nodes). An edge is included only if the normalized value of the position is larger than a predetermined threshold. Degree centrality is used for calculating node importance, with the assumption that the most important security issuers will be the ones that attract the highest number of important positions. This figure is affected by both the year slider above and the threshold slider below. The threshold slider will set the normalized position threshold for which any 2 nodes are determined to be connected. This figure is also affected by the linkage dropdown menu and year slider.", style={'text-align': 'center', 'margin-top': "15px"}),
    html.H3(children = 'Select the threshold', style={'text-align': 'center'}),
    dcc.Slider(
        id='threshold-slider',
        min=0.05,
        max=1,
        value=.05,
        marks={str(round(t,2)): str(round(t, 2)) for t in np.arange(0.05,1.01,0.05)},
        step=.05),
    html.Img(src='data:image/png;base64,{}'.format(encoded_net.decode()), id='corr-network'),
])

# https://community.plotly.com/t/multiple-outputs-in-dash-now-available/19437
@app.callback(
    [Output('corr-network', 'src'), Output('corr-matrix', 'src')],
    [Input('year-slider', 'value'), Input('threshold-slider', 'value')], Input('cluster-dropdown', 'value'))
def update_corr_figure(year, threshold, linkage):
    """
    Update the matplotlib figures

    https://github.com/plotly/dash/issues/71
    https://community.plotly.com/t/using-html-img-as-filter-in-callback/18046/2
    """
    corr_network, corr_matrix = create_correlation_network(year, threshold, linkage)
    #
    return 'data:image/png;base64,{}'.format(corr_network.decode()), 'data:image/png;base64,{}'.format(corr_matrix.decode())


if __name__ == "__main__":
    app.run_server(debug=True, use_reloader=False)  # Turn off reloader if inside Jupyter
