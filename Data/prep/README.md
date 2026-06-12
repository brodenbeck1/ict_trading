# ZST to CSV Converter

A Python utility for converting Zstandard (.zst) compressed files to CSV format, specifically designed for financial data from Databento.

## Features

- **Single file conversion**: Convert individual ZST files to CSV
- **Batch processing**: Convert multiple ZST files in a directory
- **Memory efficient**: Processes large files using streaming decompression
- **Data validation**: Displays data shape and column information
- **Flexible output**: Automatic or custom output file naming
- **Error handling**: Robust error handling with cleanup
- **Logging**: Comprehensive logging for monitoring progress

## Installation

1. Make sure you have Python 3.7+ installed
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install zstandard pandas
```

## Usage

### Single File Conversion

Convert a single ZST file to CSV:

```bash
python Data/prep/zst_to_csv_conversion.py input_file.csv.zst
```

Specify output file:
```bash
python Data/prep/zst_to_csv_conversion.py input_file.csv.zst output_file.csv
```

Keep intermediate decompressed file:
```bash
python Data/prep/zst_to_csv_conversion.py input_file.csv.zst --keep-intermediate
```

### Batch Conversion

Convert all ZST files in a directory:

```bash
python Data/prep/batch_zst_converter.py /path/to/zst/files
```

Convert with custom output directory:
```bash
python Data/prep/batch_zst_converter.py /path/to/zst/files --output-dir /path/to/csv/files
```

Recursive search for ZST files:
```bash
python Data/prep/batch_zst_converter.py /path/to/zst/files --recursive
```

### Example with Your Data

Convert the Databento financial data file:

```bash
cd Data/prep
python zst_to_csv_conversion.py ../GLBX-20250604-8Q67AQFEMK/glbx-mdp3-20100606-20250603.ohlcv-1m.csv.zst
```

## File Structure

```
Finance/
├── Data/
│   ├── GLBX-20250604-8Q67AQFEMK/
│   │   ├── glbx-mdp3-20100606-20250603.ohlcv-1m.csv.zst  # Input ZST file
│   │   ├── metadata.json                                  # Data metadata
│   │   └── ...
│   └── prep/
│       ├── zst_to_csv_conversion.py                      # Main converter
│       └── batch_zst_converter.py                        # Batch processor
├── requirements.txt                                       # Dependencies
└── README.md                                             # This file
```

## Data Format

The converter is optimized for OHLCV (Open, High, Low, Close, Volume) financial data with the following columns:

- `ts_event`: Timestamp
- `rtype`: Record type
- `publisher_id`: Data publisher ID
- `instrument_id`: Financial instrument ID
- `open`: Opening price
- `high`: Highest price
- `low`: Lowest price
- `close`: Closing price
- `volume`: Trading volume
- `symbol`: Trading symbol

## Command Line Options

### zst_to_csv_conversion.py

- `input_file`: Input ZST file to convert (required)
- `output_file`: Output CSV file (optional)
- `--keep-intermediate`: Keep the intermediate decompressed file
- `--verbose, -v`: Enable verbose logging

### batch_zst_converter.py

- `input_dir`: Input directory containing ZST files (required)
- `--output-dir, -o`: Output directory for CSV files
- `--recursive, -r`: Search for ZST files recursively
- `--keep-intermediate`: Keep intermediate decompressed files
- `--verbose, -v`: Enable verbose logging

## Performance

The converter is designed for efficiency:

- **Streaming decompression**: Processes files in 16KB chunks to minimize memory usage
- **Large file support**: Can handle multi-gigabyte files without memory issues
- **Progress logging**: Shows conversion progress for large files

Example performance with your data:
- Input: 701.61 MB CSV data (compressed as ZST)
- Processing time: ~3 seconds
- Memory usage: Minimal due to streaming

## Error Handling

The converter includes comprehensive error handling:

- File validation (existence, correct extension)
- Automatic cleanup of partial files on errors
- Detailed error messages and logging
- Graceful handling of corrupted data

## Contributing

Feel free to extend the converter with additional features such as:

- Support for other compression formats
- Data filtering and transformation
- Custom output formats
- Performance optimizations

## License

This project is provided as-is for educational and research purposes.
