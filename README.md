# Dispersion_Trading
Dispersion trading assignment based on implied correlations of index v/s components

# Setting Up
The directory structure is as follows: <br />
> dispersion_trading/ <br />
>
> >  Data/ <br />
> >
> > >    AllData/ <br />
> > >    DispersionDumps/ <br />
> > >    Output/ <br />
> >
> >  constants.py <br />
> >  correlations.py <br />
> >  helper_fns.py <br />
> >  implied_vol.py <br />
> >  inputs.py  <br />
> >  intraday_trade.py <br />
> >  main.py <br />
> >  read_preprocess.py <br />
> >  trading_helper.py <br />
>
> setup.py <br />
<br />

# Running the code
The raw datewise, tradewise data sits in DispersionDumps. The data has not been uploaded to this repository. Please add it and then run: <br />
> py main.py  <br />
in folder dispersion_trading from Command Prompt <br />

# Inputs
The inputs can be changed in inputs.py <br />
> start and end dates <br />
> forbidden dates (excluded dates) <br />
> sampling frequency <br />
> amount (total capital) <br />
> input and output file paths <br />
> save <br />
> read_from_saved <br />

## Saving Time
Cache functionality has been added to save time in subsequent runs with same underlying sampled, filtered call-put, implied volatility data. The dataframes can be stored as csv's and easily retrieved. <br />
> For saving: toggle save = 1<br />
> For reading in subsequent runs: toggle save = 0 and read_from_saved = 1 <br />
in inputs.py <br />

# Output

<br />
The output would be stored in Output folder: <br />

Output File | Contents
------------ | -------------
stockwise_position_PnL.csv | Stock-wise, position-wise summary of all call and put options with PnL break up as well
Timewise_PnL_summary | Consolidated Call, Put, Total Option for each entry and exit time

<br />

