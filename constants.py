"""
Constants include
Weightages of components of BANKNIFTY index as of October'19
Note: these are raw weightages and don't add up to 1. They have been scaled later

Apart from this, it defines 
stock_names, 
constituents, 
index,
risk free rate 
which are global variables
"""

#Based on October 2019
weightage = { 'AXISBANK' : 0.1235,
              'HDFCBANK' : 0.3145,
              'ICICIBANK': 0.1883,
#               'INDUSINDBK':0.0745,
              'KOTAKBANK': 0.1478,
              'SBIN'     : 0.0929};

constituents = [*weightage]
index_name = "BANKNIFTY"
stock_names = constituents.copy()
stock_names.append(index_name)

risk_free_rate_global = 0.054
