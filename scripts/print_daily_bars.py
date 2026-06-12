

from read_data import csvReader 


def print_daily_bars():
    data = csvReader('D').read_NQ()
    print(data.head())

print_daily_bars()

