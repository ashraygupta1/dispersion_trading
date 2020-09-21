"""
Dirty Correlation
Clean Correlation
stationarity test and convert series to stationary series by first differencing
Return thresholds based on series based on mean and variance
"""

import pandas as pd
import numpy as np
from statsmodels.tsa.stattools import adfuller
from helper_fns import basket_weightage
from constants import weightage, constituents, index_name, stock_names

#Dirty Correlation
def DirtyCorrelation(df_stock):
    scaled_weightage = basket_weightage(weightage)
    df_vols = {}
    for stock in stock_names:
        df_vols[stock] = df_stock[stock].filter(['Time','Imp_vol_ATM'])
    index_vol = df_vols[index_name]
    weighted_vol = pd.DataFrame({ 'Time': index_vol['Time'], 'Imp_vol_ATM' : np.zeros(len(index_vol.index)) })
    for constituent in constituents:
        weighted_vol['Imp_vol_ATM'] += df_vols[constituent]['Imp_vol_ATM'] * scaled_weightage[constituent]
    vol_ratio = index_vol['Imp_vol_ATM']/weighted_vol['Imp_vol_ATM']
    dirty_correl = pd.DataFrame({ 'Time': index_vol['Time'], 'Corr': vol_ratio**2 })
    return dirty_correl

#Clean Correlation
def CleanCorrelation(df_stock):
    scaled_weightage = basket_weightage(weightage)
    df_vols = {}
    for stock in stock_names:
        df_vols[stock] = df_stock[stock].filter(['Time', 'Imp_vol_ATM'])
    index_vol = df_vols[index_name]
    comp_vol_sq = np.zeros(len(index_vol.index))
    for constituent in constituents:
        comp_vol_sq += (scaled_weightage[constituent] * df_vols[constituent]['Imp_vol_ATM']) ** 2
    denominator = np.zeros(len(index_vol.index))
    for i in range(len(constituents)):
        for j in range(i+1,len(constituents)):
            denominator += 2*scaled_weightage[constituents[i]]* scaled_weightage[constituents[j]]* df_vols[constituents[i]]['Imp_vol_ATM'] * df_vols[constituents[i]]['Imp_vol_ATM']

    corr = (index_vol['Imp_vol_ATM']**2 - comp_vol_sq )/denominator
    clean_correl = pd.DataFrame({ 'Time': index_vol['Time'], 'Corr': corr })
    print("Mean: ", clean_correl['Corr'].mean())
    print("Std Dev: ", clean_correl['Corr'].std())
    return clean_correl

#Check if a series is stationary and print statistics
def stationarity_test(series):
    mean = series.mean()
    std = series.std()
    print('mean: ',mean, '\nstd: ',std)
    result = adfuller(series)
    print('ADF Statistic: %f' % result[0])
    print('p-value: %f' % result[1])
    print('Critical Values:')
    for key, value in result[4].items():
        print('\t%s: %.3f' % (key, value))
    series.plot()

#Convert a non-stationary series to stationary one using first order differencing
def make_stationary(series):
    series['Corr'] = series['Corr'] - series['Corr'].shift(1)
    return series.dropna()

#Generate thresholds for entry and exits, given a series
def thresholds_clean(Correl_series):
    mean = Correl_series.mean()
    std = Correl_series.std()
    thresholds_dict = { 'lower_enter': mean - 2*std, 'lower_exit': mean - 2*std, 'upper_enter': mean + 2*std, 'upper_exit' : mean + 2*std}
    for key in thresholds_dict:
        print(key, ": ", thresholds_dict[key])
    return thresholds_dict