"""
This is the trading helper function which builds the ledger when entry or exit action is given
Also PnL calculaton stockwise
PnL calculation for whole trade indexed by entry and exit times
"""

import pandas as pd
from collections import OrderedDict
from py_vollib.black_scholes import implied_volatility as iv
from py_vollib.black_scholes.greeks import analytical

from constants import stock_names, risk_free_rate_global
from inputs import all_dates, forbidden_dates, sampling_freq, amount
from inputs import parent_folder, sampled_path, call_path, put_path, vol_path
from inputs import save, read_from_saved
from read_preprocess import read_data, process_data, sampling
from helper_fns import df_to_csv, csv_to_df
from implied_vol import option_type_helper, option_imp_vol_intraday

#Constituent capital = Index capital
#Ideally the constituent capital should be divided by corresponding weights and then this individual constituent amount should 
#be used to buy options of that stock

#what if data not available for some strike at some time?
def action_market(Time, position, scaled_weights, enter_time,df_calls,df_puts,df_all):
    #If enter_time == Time, means entry. else exit
    enter = enter_time==Time
    df_ledger = pd.DataFrame()
    for stock in stock_names:
#         print(stock,'\n')
        strike_call = df_calls[stock][df_calls[stock]['Time'] == enter_time]['strike'].iloc[0]
        strike_put = df_puts[stock][df_puts[stock]['Time'] == enter_time]['strike'].iloc[0]
        
        df = df_all[stock]
        df_call_row = df[(df.Time == Time) & (df.strike == strike_call) & (df.type == 'call') ]
        df_put_row = df[(df.Time == Time) & (df.strike == strike_put) & (df.type == 'put') ]
                
        spot = df_call_row['Spot'].iloc[0]
        
        days_to_expiry_call = df_call_row['days_to_expiry'].iloc[0]
        days_to_expiry_put = df_put_row['days_to_expiry'].iloc[0]
        
        risk_free_rate = risk_free_rate_global
        
        weight = scaled_weights[stock] * position
        bid_ask = 'ask_px' if weight>=0 else 'bid_px'
        call_px = df_call_row[bid_ask].iloc[0]
        put_px = df_put_row[bid_ask].iloc[0]
        call_bid_px = df_call_row['bid_px'].iloc[0]
        call_ask_px = df_call_row['ask_px'].iloc[0]
        put_bid_px = df_put_row['bid_px'].iloc[0]
        put_ask_px = df_put_row['ask_px'].iloc[0]
        
        call_mid_px = df_call_row['mid_px'].iloc[0]
        put_mid_px = df_put_row['mid_px'].iloc[0]
        
        implied_vol_call = iv.implied_volatility(call_mid_px, spot,strike_call, days_to_expiry_call/365.25,risk_free_rate,'c')
        implied_vol_put = iv.implied_volatility(put_mid_px, spot,strike_put, days_to_expiry_put/365.25,risk_free_rate,'p')
        
        df_temp = pd.DataFrame.from_records([OrderedDict({"time" : Time, 
                                              "stock" : stock,
                                              "spot" : spot,
#                                               "risk_free_rate" : risk_free_rate,
#                                               "days_to_expiry": days_to_expiry,
                                              "weight": weight,
                                              "strike_call": strike_call,
                                              "Imp_vol_call" : implied_vol_call,
                                              "call_bid_px": call_bid_px,
                                              "call_ask_px": call_ask_px,
                                              "call_px": call_px,
#                                               "call_qty": call_qty,
                                              "delta_call" : analytical.delta('c', spot, strike_call, days_to_expiry_call/365.25, risk_free_rate, implied_vol_call ),
                                              "strike_put" : strike_put,
                                              "Imp_vol_put" : implied_vol_put,
                                              "put_bid_px": put_bid_px,
                                              "put_ask_px": put_ask_px,
                                              "put_px": put_px,
#                                               "put_qty": put_qty,
                                              "delta_put" : analytical.delta('p', spot, strike_put, days_to_expiry_put/365.25, risk_free_rate, implied_vol_put ),
                                                         })], index = ['time','stock'])
        if(enter==1):
            df_temp['call_qty'] = df_temp.weight * (0.5*amount) / df_temp.call_px
            df_temp['put_qty'] = df_temp.weight * (0.5*amount) / df_temp.put_px
        if(df_ledger.empty):
            df_ledger = df_temp
        else:
            df_ledger = df_ledger.append(df_temp)
    return df_ledger

def PnL_Calc(df_entry, df_exit):
    df = df_entry.join(df_exit.set_index( ['stock'] ), on = ['stock'], how='outer', lsuffix = '_entry', rsuffix = '_exit')

    df['call_change'] = ( df['call_px_exit'] - df['call_px_entry'] ) * df['call_qty']
    df['call_delta_pnl'] = (-0.5)*(df['delta_call_entry']+df['delta_call_exit'])* df['call_qty'] * (df['spot_exit'] - df['spot_entry'])
    df['PnL_call'] = df['call_change'] + df['call_delta_pnl']

    df['put_change'] = ( df['put_px_exit'] - df['put_px_entry'] ) * df['put_qty']
    df['put_delta_pnl'] = (-0.5)*(df['delta_put_entry']+df['delta_put_exit'])* df['put_qty'] * (df['spot_exit'] - df['spot_entry'])
    df['PnL_put'] = df['put_change'] + df['put_delta_pnl']
    
    return df

def tradewise_PnL(df):
    grouped = df.groupby(['time_entry', 'time_exit'])
    PnL_call = grouped['PnL_call'].sum()[0]
    PnL_put = grouped['PnL_put'].sum()[0]
    result = pd.DataFrame({'time_entry': [grouped['time_entry'].unique()[0][0]],
                          'time_exit' : [grouped['time_exit'].unique()[0][0]],
                            'entry'
                          'PnL_call': [PnL_call],
                          'PnL_put': [PnL_put], 
                          'PnL_total': [PnL_call + PnL_put] })
    return result

def print_shape(df_struc):
    for stock in stock_names:
        print(stock, ": ", df_struc[stock].shape)

def read_raw_data():
    if(read_from_saved):
        df_all = csv_to_df(parent_folder)
    else:
        df_all = read_data(stock_names, all_dates, forbidden_dates)
        process_data(df_all, stock_names)

    if(save):
        df_to_csv(parent_folder, df_all)

    print_shape(df_all)
    return df_all

def read_sampled_data(df_all):
    if(read_from_saved):
        df_sampled = csv_to_df(sampled_path)
    else:
        df_sampled = sampling(df_all, sampling_freq)
    
    if(save):
        df_to_csv(sampled_path, df_sampled)

    print_shape(df_sampled)
    return df_sampled

def read_call_put_data(df_sampled):
    if(read_from_saved):
        df_calls = csv_to_df(call_path)
        df_puts = csv_to_df(put_path)
    else:
        df_calls = {}
        df_puts = {}
        df = df_sampled.copy()
        for stock in stock_names:
            df_calls[stock] = option_type_helper(df[stock],"call")
            df_puts[stock] = option_type_helper(df[stock],"put")
    
    if(save):
        df_to_csv(call_path, df_calls)
        df_to_csv(put_path, df_puts)

    print("Call Options: ")
    print_shape(df_calls)
    print("\nPut Options: ")
    print_shape(df_puts)
    return df_calls, df_puts

def read_imp_vol_data(df_sampled):
    if(read_from_saved):
        df_imp_vol_stock = csv_to_df(vol_path)
    else:
        df_imp_vol_stock = {}
        df = df_sampled.copy()
        for stock in stock_names:
            df_imp_vol_stock[stock] = option_imp_vol_intraday(df[stock])
    
    if(save):
        df_to_csv(vol_path, df_imp_vol_stock)

    print_shape(df_imp_vol_stock)
    return df_imp_vol_stock
