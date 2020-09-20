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
# end_date = '07-01-2019'

all_dates = pd.bdate_range(start=start_date, end = end_date)
all_dates_str = all_dates.strftime('%Y%m%d')
forbidden_dates = ['20190812','20190815','20190830']#data missing
forbidden_dates.extend(['20190725', '20190829'])#option expiry dates hence high volatility noise
forbidden_dates.extend(['20190828']) #imp vol for BANKNIFTY wrong at 9:16am->this is a temp fix

sampling_freq = 10

amount = 1000