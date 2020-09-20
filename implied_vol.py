"""
Implied volatility calculation and all its helper functions
Also can be used to filter for call and put options of strike just above and below spot
"""

import pandas as pd
from py_vollib.black_scholes import implied_volatility
from constants import risk_free_rate_global

#Filters near the money call/put options from the whole set
def option_type_helper(df, option_type ):
    df_typed = df[df.type==option_type];
    grouped = df_typed.groupby(['Time'])
    if option_type == "call":
        temp = grouped.apply(lambda g: g[g['strike']>=g['Spot']]).reset_index(drop=True)
    elif option_type == "put":
        temp = grouped.apply(lambda g: g[g['strike']<=g['Spot']]).reset_index(drop=True)
    else:
        raise Exception("Option type neither call nor put. Value was: ", option_type )#to catch if option type is erroneous
        
    grouped = temp.groupby(['Time'])
    
    if option_type == "call":
        df_typed_atm = grouped.apply(lambda g: g[ g.loc[:,'strike'] == g.loc[:,'strike'].min() ]).reset_index(drop=True)
    elif option_type == "put":
        df_typed_atm = grouped.apply(lambda g: g[ g.loc[:,'strike'] == g.loc[:,'strike'].max() ]).reset_index(drop=True)
        
    df_typed_atm_filtered = df_typed_atm.filter(["Time", "Spot", "strike","ask_px", "bid_px", "mid_px","days_to_expiry"])
    return df_typed_atm_filtered

#Implied vol of call options based on Spot, strike, days to expiry, mid price of call option
def imp_vol_call(df):
    df_call = option_type_helper(df,"call")
    df_call.loc[:,'Imp_vol_call'] = df_call.apply( lambda g: implied_volatility.implied_volatility(
                                                            g['mid_px'], g['Spot'],g['strike'],g['days_to_expiry']/365.25,risk_free_rate_global,'c'), axis=1 );
    return df_call.filter(["Time", "Spot","strike", "Imp_vol_call"])

#Implied vol of put options based on Spot, strike, days to expiry, mid price of put option
def imp_vol_put(df):
    df_put = option_type_helper(df,"put")
    df_put.loc[:,'Imp_vol_put'] = df_put.apply( lambda g: implied_volatility.implied_volatility(
                                                            g['mid_px'], g['Spot'],g['strike'],g['days_to_expiry']/365.25,risk_free_rate_global,'p'), axis=1 );
    return df_put.filter(["Time", "Spot","strike", "Imp_vol_put"])

#lambda func for intraday option vol
def imp_vol_from_call_put_vol(x):
    if x['strike_call'] == x['strike_put']:
        return (x['Imp_vol_call'] + x['Imp_vol_put']) / 2
    else:
        return (((x['strike_call'] - x['Spot']) * x['Imp_vol_put'] + (x['Spot'] - x['strike_put']) * x['Imp_vol_call'] )
                / (x['strike_call'] - x['strike_put']) )

#Option's implied vol by weighing call and put options of nearest strikes, 
#if spot == call_strike == put_strike, take (imp_vol_call + imp_vol_put)/2
def option_imp_vol_intraday(df):
    df_imp_vol_call = imp_vol_call(df)
    df_imp_vol_put = imp_vol_put(df)
    df_imp_vol = df_imp_vol_call.join(df_imp_vol_put.set_index( ['Time', 'Spot'] ), on = ['Time', 'Spot'], how='inner', lsuffix = '_call', rsuffix = '_put')
    df_imp_vol.loc[:,'Imp_vol_ATM']= df_imp_vol.apply( imp_vol_from_call_put_vol, axis = 1 )
    df_imp_vol_filtered = df_imp_vol[df_imp_vol['Imp_vol_ATM'] < 1] #To filter cases with high vol noise- we don't expect too high vol with this data as of now
    return df_imp_vol_filtered
