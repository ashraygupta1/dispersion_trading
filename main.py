import pandas as pd
from intraday_trade import intraday_trading_ledger

pd.set_option('display.max_columns', None)

"""
This calls the intraday trading ledger which executes the intraday trade
"""
df_trading_ledger = intraday_trading_ledger()
df_trading_ledger

print("The program has terminated.")