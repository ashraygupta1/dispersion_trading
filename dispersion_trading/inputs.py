"""
This is the inputs file. 
Start date, 
end date, 
forbidden dates, 
sampling frequency, 
total capital to trade 
can be set here
"""
import pandas as pd

start_date = '07-01-2019'
end_date = '08-30-2019'
# end_date = '07-02-2019'

all_dates = pd.bdate_range(start=start_date, end = end_date)
all_dates_str = all_dates.strftime('%Y%m%d')
forbidden_dates = ['20190812','20190815','20190830']#data missing
forbidden_dates.extend(['20190725', '20190829'])#option expiry dates hence high volatility noise
forbidden_dates.extend(['20190828']) #imp vol for BANKNIFTY wrong at 9:16am->this is a temp fix

sampling_freq = 10

amount = 1000

input_path = 'Data/DispersionDumps/'
parent_folder = 'Data/AllData/'
sampled_path = parent_folder + 'Sampled10min/'
call_path = sampled_path + 'Call/'
put_path = sampled_path + 'Put/'
vol_path = sampled_path + 'Imp_vol/'
output_path = 'Data/Output/'

#flag to save data
save = 0

#flag to read from already saved data. Should be false if save is true
read_from_saved  = 1 & (not(save))