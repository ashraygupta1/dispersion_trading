"""
dataframe to csv
csv to dataframe
scaling basket weightages
"""

import pandas as pd
from constants import stock_names

def df_to_csv(path, df):
    for stock in stock_names:
        try:
            df[stock].set_index('Time').to_csv(path+stock+'.csv')
        except:
            print('Failed to write csv for ', stock, '\n path: ', path)

def csv_to_df(path):
    df = {}
    for stock in stock_names:
        df[stock] = pd.read_csv(path+stock+'.csv')
        print(stock, df[stock].shape)
    return df

#as of October2019
def basket_weightage(weightage):
    total_weightage = sum(weightage.values());
    scaled_weightage = {k: v / total_weightage for k, v in weightage.items()}
    return scaled_weightage