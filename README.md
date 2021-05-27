# Modern Data Analytics Project: Uncovering the network   

This repository contains the Jupyter notebooks, data, and Dash app (running on Heroku) used for analysis of the 13 F filings from the Securities and Exchange Commission (SEC) of the United States.

## Data

The data directory contains the 13-F filings for 2017-2020. There is also a file containing all the years, but with only 10,000 sampled observations. 

## Notebooks   

The Jupyter notebooks contain code to (1) create a list of the CIKs of interest, (2) download the data from the SEC site, (3), parse the filing information out of the downoaded files, and (4) run the analysis. There is an additional notebook that creates a Plotly figure illustrating the basic connectivty between the investiment managers.

## Dash App   

The app can be found at https://sec-network-analysis.herokuapp.com/ and the code used to generate the app is in the dash_app directory. The figures generated in the notebooks can be seen in this app, though the data has been subsampled in the app (compared to the notebook analysis) so as to be able to update the figures quickly.
