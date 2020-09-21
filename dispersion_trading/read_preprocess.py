"""
Reads all data
Preprocesses it
Has sampling functionality defined to sample data at any frequency
"""

import pandas as pd
import datetime
from constants import stock_names
from inputs import all_dates_str, input_path

def read_data(stock_names, all_dates, forbidden_dates):
    path = input_path
        
    column_names = ['Time','Spot','NaN','strike','type','bid_px','ask_px','trade_px','delta','volatility','gamma','theta','vega','days_to_expiry','intrinsic_value','time_value']
    df_all = {}
    
    for date in all_dates_str:
        df_temp = {}
        if date in forbidden_dates:
            continue
        for stock in stock_names:
            df_temp[stock] = pd.read_csv(path+date+'/'+stock+'/data.csv',header=0,index_col=False, names = column_names)
            df_temp[stock].Time = pd.to_datetime(date + ' ' + df_temp[stock]['Time'])

            if stock in df_all.keys():
                df_all[stock] = pd.concat([df_all[stock], df_temp[stock]])
            else:
                df_all[stock] = df_temp[stock]
    return df_all


#Very basic cleaning as of now. Will improve later
def process_data(df_all, stock_names):
    columns_to_scale = ['Spot','strike','bid_px','ask_px','trade_px','intrinsic_value','time_value']
    for stock in stock_names:
        df_all[stock].drop(['NaN'], inplace=True, axis=1)
        df_all[stock].set_index('Time')
        for col in columns_to_scale:
            df_all[stock].loc[:,col] = df_all[stock].loc[:,col]/100
        df_all[stock].loc[:,'mid_px'] = ( df_all[stock].loc[:,'bid_px'] + df_all[stock].loc[:,'ask_px'] )/2;

def minute_from_datetime(date):
    date_str = date.strftime('%Y-%m-%d %H:%M:%S') if isinstance(date, datetime.datetime) else date
    return datetime.datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S').time().minute

def sampling(df, freq):
    df_sampled  = {}
    for stock in stock_names:
        df_t = df[stock].copy()        
        s = minute_from_datetime(df_t.Time.iloc[0]) % freq
        df_sampled[stock] = df_t[df_t.Time.apply(lambda x: minute_from_datetime(x) % freq == s )]
    return df_sampled