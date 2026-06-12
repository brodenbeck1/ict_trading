import pandas as pd
from pathlib import Path


class csvReader:

   def __init__(self, timeframe, weeks=None, data_dir=None):
       self.timeframe = timeframe
       self.weeks = weeks
       
       if data_dir is None:
           # Default to ict_trading/Data directory
           self.data_dir = Path(__file__).parent.parent / 'Data'
       else:
           self.data_dir = Path(data_dir)

   def read_NQ(self):
       df = pd.read_csv(self.data_dir / 'nq_futures_1m_cleaned.csv')
       df['timestamp'] = pd.to_datetime(df['timestamp'])
       df = df.set_index('timestamp').sort_index()
       
       # Filter by weeks if specified
       if self.weeks is not None:
           cutoff_date = df.index.max() - pd.Timedelta(weeks=self.weeks)
           df = df[df.index >= cutoff_date]

       agg = {
           'open': 'first',
           'high': 'max',
           'low': 'min',
           'close': 'last',
           'volume': 'sum'
       }

       resampled = df.resample(self.timeframe).agg(agg) # '5T' = 5 minutes, '1H' = 1 hour, 'D' = day, etc.
       return resampled

   def read_ES(self):
       df = pd.read_csv(self.data_dir / 'es_futures_1m_cleaned.csv')
       df['timestamp'] = pd.to_datetime(df['timestamp'])
       df = df.set_index('timestamp').sort_index()
       
       # Filter by weeks if specified
       if self.weeks is not None:
           cutoff_date = df.index.max() - pd.Timedelta(weeks=self.weeks)
           df = df[df.index >= cutoff_date]

       agg = {
           'open': 'first',
           'high': 'max',
           'low': 'min',
           'close': 'last',
           'volume': 'sum'
       }

       resampled = df.resample(self.timeframe).agg(agg) # '5T' = 5 minutes, '1H' = 1 hour, 'D' = day, etc.
       return resampled

   def read_YM(self):
       df = pd.read_csv(self.data_dir / 'ym_futures_1m_cleaned.csv')
       df['timestamp'] = pd.to_datetime(df['timestamp'])
       df = df.set_index('timestamp').sort_index()
       
       # Filter by weeks if specified
       if self.weeks is not None:
           cutoff_date = df.index.max() - pd.Timedelta(weeks=self.weeks)
           df = df[df.index >= cutoff_date]

       agg = {
           'open': 'first',
           'high': 'max',
           'low': 'min',
           'close': 'last',
           'volume': 'sum'
       }

       resampled = df.resample(self.timeframe).agg(agg) # '5T' = 5 minutes, '1H' = 1 hour, 'D' = day, etc.
       return resampled