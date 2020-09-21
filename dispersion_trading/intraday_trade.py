"""
This is our intraday trader which trades on implied correlations for now
"""

import pandas as pd
from datetime import datetime
from constants import weightage, constituents, index_name, stock_names
from inputs import all_dates, forbidden_dates, sampling_freq, amount, output_path
from helper_fns import basket_weightage
from correlations import DirtyCorrelation, CleanCorrelation, stationarity_test, make_stationary, thresholds_clean
from trading_helper import action_market, PnL_Calc, tradewise_PnL
from trading_helper import read_raw_data, read_sampled_data, read_call_put_data, read_imp_vol_data

option_expiry_date_str = '2019-07-24 15:26:00'
option_expiry_date = datetime.strptime(option_expiry_date_str, '%Y-%m-%d %H:%M:%S')

def get_all_trading_data():
    print("\n***** \nRaw Data\n*****")
    df_all = read_raw_data()

    print("\n***** \nSampled Data\n*****")
    df_sampled = read_sampled_data(df_all)

    print("\n***** \nFiltered Call Put Option Data\n*****")
    df_calls, df_puts = read_call_put_data(df_sampled)

    print("\n***** \nImplied Vol Data\n*****")
    df_imp_vol_stock = read_imp_vol_data(df_sampled)

    print("\n***** \nCorrelations\n*****")
    # df_correl = DirtyCorrelation(df_imp_vol_stock)
    df_correl = CleanCorrelation(df_imp_vol_stock)

    print("\n***** \nTesting Stationarity\n*****")
    stationarity_test(df_correl['Corr'])

    print("\n***** \nConvert series to Stationary series\n*****")
    df_corr_stationary = make_stationary(df_correl.copy())
    print("\n***** \nTesting Stationarity of converted series\n*****")
    stationarity_test(df_corr_stationary['Corr'])

    print("\n***** \nThresholds\n*****")
    thresholds = thresholds_clean(df_corr_stationary['Corr'])

    print("\n***** \nScaled weights of components\n*****")
    scaled_weights = basket_weightage(weightage)
    scaled_weights[index_name] = sum(scaled_weights.values()) * -1
    for key in scaled_weights:
        print(key, ": ", scaled_weights[key])

    return df_sampled, df_calls, df_puts, df_corr_stationary, thresholds, scaled_weights

# position=1 means long constituents, short index. position = -1 means otherwise
# if position =1 ,weight= -1 for index, short index call & put, so short delta call, long delta put
# Delta hedging: long delta call, short delta put.
# avg delta(per single stock)((entry + exit)/2)* quantity(stock) * -1(hedge) * change in spot price(for PnL)

def intraday_trading_ledger():
    df_all, df_calls, df_puts, corr_df, thresholds, scaled_weights = get_all_trading_data()
    
    print("\n***** \nLets Begin to Trade\n*****")

    position_held = 0
    enter_time = 0
    exit_time = 0
    df_entry = pd.DataFrame()
    df_exit = pd.DataFrame()
    df_ledger_settled_all = pd.DataFrame()
    df_tradewise_PnL_all = pd.DataFrame()
    for i in range(len(corr_df)):
        if((position_held==1) | (position_held==-1)):
            option_expiry_flag = (corr_df['Time'].iloc[i] == option_expiry_date) | (corr_df['Time'].iloc[i] == option_expiry_date_str )
            if( (corr_df['Corr'].iloc[i] <= thresholds.get('lower_exit') ) | ( corr_df['Corr'].iloc[i] >= thresholds.get('upper_exit') ) 
                | option_expiry_flag ):
                exit_time = corr_df['Time'].iloc[i]
                try:
                    df_exit = action_market(exit_time, -position_held, scaled_weights, enter_time, df_calls, df_puts, df_all).reset_index()
                    print("\nEnter time: ",enter_time,"\nExit: ", exit_time,"\n Position: ", position_held)
                    position_held = 0

                    df_ledger_settled = PnL_Calc(df_entry, df_exit)
                    df_tradewise_PnL = tradewise_PnL(df_ledger_settled)

                    if(df_ledger_settled_all.empty):
                        df_ledger_settled_all = df_ledger_settled
                        df_tradewise_PnL_all = df_tradewise_PnL
                    else:
                        df_ledger_settled_all = df_ledger_settled_all.append(df_ledger_settled)
                        df_tradewise_PnL_all = df_tradewise_PnL_all.append(df_tradewise_PnL)
                except:
                    print("\nFailed :",exit_time)
                    
        elif(position_held == 0 ):
            enter_time = corr_df['Time'].iloc[i]
            if corr_df['Corr'].iloc[i] <= thresholds.get('lower_enter') :
                position_held = -1
                df_entry = action_market(enter_time, position_held, scaled_weights, enter_time, df_calls, df_puts, df_all).reset_index()
                
            elif corr_df['Corr'].iloc[i] >= thresholds.get('upper_enter') :
                position_held = 1
                df_entry = action_market(enter_time, position_held, scaled_weights, enter_time, df_calls, df_puts, df_all).reset_index()

    total_PnL = df_tradewise_PnL_all.PnL_total.sum()
    print("\n****************************\nTotal Profit: {:.2f} %\n****************************\n".format( total_PnL / amount * 100 ))

    df_ledger_settled_all.to_csv(output_path + 'stockwise_position_PnL.csv')
    df_tradewise_PnL_all.to_csv(output_path + 'Timewise_PnL_summary.csv')

    return df_ledger_settled_all,df_tradewise_PnL