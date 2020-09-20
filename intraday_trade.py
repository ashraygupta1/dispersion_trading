"""
This is our intraday trader which trades on implied correlations for now
"""

import pandas as pd

from read_preprocess import read_data,process_data,sampling
from helper_fns import df_to_csv, csv_to_df, basket_weightage
from implied_vol import option_type_helper, imp_vol_call, imp_vol_put, imp_vol_from_call_put_vol, option_imp_vol_intraday
from correlations import DirtyCorrelation, CleanCorrelation, stationarity_test, make_stationary, thresholds_clean
from trading_helper import action_market, PnL_Calc, tradewise_PnL
from constants import weightage, constituents, index_name, stock_names
from inputs import start_date, end_date, all_dates, forbidden_dates, sampling_freq, amount

def get_all_trading_data():
    df_all = read_data(stock_names, all_dates, forbidden_dates)
    process_data(df_all, stock_names)

    #save all data
    path = 'NewData/AllData/'
    df_to_csv(path, df_all)

    # read all data
    path = 'NewData/AllData/'
    df_all = csv_to_df(path)

    #save sampled data
    df_sampled = sampling(df_all, sampling_freq)
    # sampled_path = 'NewData/AllData/Sampled10min/'
    # df_to_csv(sampled_path, df_sampled)

    #read sampled data
    # sampled_path = 'NewData/AllData/Sampled10min/'
    # df_sampled = csv_to_df(sampled_path)

    #call_put_df
    df_calls = {}
    df_puts = {}
    df = df_sampled.copy()
    for stock in stock_names:
        df_calls[stock] = option_type_helper(df[stock],"call")
        df_puts[stock] = option_type_helper(df[stock],"put")
    
    #save call put data
    # df_to_csv('NewData/AllData/Sampled10min/Call/',df_calls)
    # df_to_csv('NewData/AllData/Sampled10min/Put/',df_puts)

    #read call put data
    # df_calls = csv_to_df('NewData/AllData/Sampled10min/Call/')
    # df_puts = csv_to_df('NewData/AllData/Sampled10min/Put/')

    #implied_vol
    df_imp_vol_stock = {}
    df = df_sampled.copy()
    for stock in stock_names:
        df_imp_vol_stock[stock] = option_imp_vol_intraday(df[stock])

    #save implied_vol data
    # df_to_csv('NewData/AllData/Sampled10min/Imp_vol/', df_imp_vol_stock)

    #read implied_vol data
    # df_imp_vol_stock = csv_to_df('NewData/AllData/Sampled10min/Imp_vol/')

    df_all = df_sampled.copy()

    # Correl_series = DirtyCorrelation(df_imp_vol_stock)['Corr']
    clean_correl = CleanCorrelation(df_imp_vol_stock)

    corr_window = clean_correl
    stationarity_test(corr_window['Corr'])

    corr_stationary = make_stationary(clean_correl.copy())
    stationarity_test(corr_stationary['Corr'])

    thresholds = thresholds_clean(corr_stationary['Corr'])

    scaled_weights = basket_weightage(weightage)
    scaled_weights[index_name] = sum(scaled_weights.values()) * -1
    return df_all, df_calls, df_puts, corr_stationary, thresholds, scaled_weights

# position=1 means long constituents, short index. position = -1 means otherwise
# if position =1 ,weight= -1 for index, short index call & put, so short delta call, long delta put
# Delta hedging: long delta call, short delta put.
# avg delta(per single stock)((entry + exit)/2)* quantity(stock) * -1(hedge) * change in spot price(for PnL)

def intraday_trading_ledger():
    df_all, df_calls, df_puts, corr_df, thresholds, scaled_weights = get_all_trading_data()
    # corr_df = corr_stationary
    # thresholds = thresholds_clean(corr_df['Corr'])
    position_held = 0
    enter_time = 0
    exit_time = 0
    df_entry = pd.DataFrame()
    df_exit = pd.DataFrame()
    df_ledger_settled_all = pd.DataFrame()
    df_tradewise_PnL_all = pd.DataFrame()
    for i in range(len(corr_df)):
        if( (position_held==1) | (position_held==-1)):
            if( (corr_df['Corr'].iloc[i] <= thresholds.get('lower_exit') ) | ( corr_df['Corr'].iloc[i] >= thresholds.get('upper_exit') ) ):
                exit_time = corr_df['Time'].iloc[i]
                # try:
                df_exit = action_market(exit_time, -position_held, scaled_weights, enter_time, df_calls, df_puts, df_all).reset_index()
                position_held = 0
                print("\nAbout to exit \n enter time: ",enter_time,"\nexit: ", exit_time,"\n pos: ", position_held, " i: ", i)

                df_ledger_settled = PnL_Calc(df_entry, df_exit)
                df_tradewise_PnL = tradewise_PnL(df_ledger_settled)

                if(df_ledger_settled_all.empty):
                    df_ledger_settled_all = df_ledger_settled
                    df_tradewise_PnL_all = df_tradewise_PnL
                else:
                    df_ledger_settled_all = df_ledger_settled_all.append(df_ledger_settled)
                    df_tradewise_PnL_all = df_tradewise_PnL_all.append(df_tradewise_PnL)
                # except:
                #     print("\nFailed :",exit_time)
    #             break
                    
        elif(position_held == 0 ):
            enter_time = corr_df['Time'].iloc[i]
            if corr_df['Corr'].iloc[i] <= thresholds.get('lower_enter') :
                position_held = -1
                print("\nEntering \n enter_time: ",enter_time,"\n pos: ", position_held, " i: ", i)
                df_entry = action_market(enter_time, position_held, scaled_weights, enter_time, df_calls, df_puts, df_all).reset_index()
                
            elif corr_df['Corr'].iloc[i] >= thresholds.get('upper_enter') :
                position_held = 1
                print("\nEntering \n enter_time: ",enter_time,"\n pos: ", position_held, " i: ", i)
                df_entry = action_market(enter_time, position_held, scaled_weights, enter_time, df_calls, df_puts, df_all).reset_index()
                
    return df_ledger_settled_all