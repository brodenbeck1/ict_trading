import pandas as pd

def clean_futures_data(input_file, output_file):
    """
    Cleans 1-minute OHLCV futures data by retaining only the symbol with the highest daily volume for each day.

    Args:
        input_file (str): Path to the input CSV file.
        output_file (str): Path to save the cleaned CSV file.
    """
    # Read the data
    df = pd.read_csv(input_file)

    # Ensure 'ts_event' is a datetime column
    df['ts_event'] = pd.to_datetime(df['ts_event'])

    #rename ts_event to timestamp
    df = df.rename(columns={'ts_event': 'timestamp'})

    # Extract the date from the timestamp
    df['date'] = df['timestamp'].dt.date

    # Group by date and symbol, summing the volume for each group
    daily_volume = df.groupby(['date', 'symbol'])['volume'].sum().reset_index()

    # Find the symbol with the highest volume for each day
    top_symbols = daily_volume.loc[daily_volume.groupby('date')['volume'].idxmax()]

    # Merge the top symbols back with the original data
    cleaned_data = df.merge(top_symbols[['date', 'symbol']], on=['date', 'symbol'])

    # Drop the 'date' column as it's no longer needed
    cleaned_data = cleaned_data.drop(columns=['date'])

    # Save the cleaned data to the output file
    cleaned_data.to_csv(output_file, index=False)

    print(f"Cleaned data saved to {output_file}")

# Example usage
input_file = '/Users/blakerodenbeck/Projects/Data/raw/NQ_GLBX-20251121-LW69NAX5TA/glbx-mdp3-20250604-20251117.ohlcv-1m.csv'
output_file = '/Users/blakerodenbeck/Projects/Data/NQ_futures_1m_cleaned_new.csv'
clean_futures_data(input_file, output_file)