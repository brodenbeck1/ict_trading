#!/usr/bin/env python3
"""
ZST to CSV Converter

This program converts Zstandard (.zst) compressed files to CSV format.
Specifically designed for financial data from Databento with OHLCV format.

Usage:
    python zst_to_csv_conversion.py <input_file.zst> [output_file.csv]
    
If output file is not specified, it will create a CSV file with the same base name.
"""

import os
import sys
import argparse
import zstandard as zstd
import pandas as pd
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def decompress_zst_file(input_path: str, output_path: str = None) -> str:
    """
    Decompress a .zst file to a temporary or specified output file.
    
    Args:
        input_path (str): Path to the input .zst file
        output_path (str, optional): Path for the output file. If None, creates temp file.
        
    Returns:
        str: Path to the decompressed file
    """
    input_file = Path(input_path)
    
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    if not input_file.suffix == '.zst':
        raise ValueError(f"Input file must have .zst extension, got: {input_file.suffix}")
    
    # Determine output path
    if output_path is None:
        # Remove .zst and get the underlying filename
        output_path = input_file.with_suffix('')
    
    output_file = Path(output_path)
    
    logger.info(f"Decompressing {input_path} to {output_path}")
    
    # Initialize decompressor
    dctx = zstd.ZstdDecompressor()
    
    try:
        with open(input_file, 'rb') as ifh:
            with open(output_file, 'wb') as ofh:
                # Decompress in chunks for memory efficiency
                reader = dctx.stream_reader(ifh)
                while True:
                    chunk = reader.read(16384)  # 16KB chunks
                    if not chunk:
                        break
                    ofh.write(chunk)
        
        logger.info(f"Successfully decompressed to {output_path}")
        return str(output_file)
        
    except Exception as e:
        logger.error(f"Error during decompression: {e}")
        # Clean up partial file if error occurred
        if output_file.exists():
            output_file.unlink()
        raise


def process_csv_data(csv_path: str, output_path: str = None) -> str:
    """
    Process the decompressed CSV data and optionally save to a new file.
    
    Args:
        csv_path (str): Path to the CSV file
        output_path (str, optional): Path for the processed output file
        
    Returns:
        str: Path to the processed CSV file
    """
    logger.info(f"Processing CSV data from {csv_path}")
    
    try:
        # Read the CSV file
        df = pd.read_csv(csv_path)
        
        # Log basic information about the data
        logger.info(f"Data shape: {df.shape}")
        logger.info(f"Columns: {list(df.columns)}")
        
        # Display first few rows for verification
        logger.info(f"First 5 rows:\n{df.head()}")
        
        # If output path is specified and different from input, save the processed data
        if output_path and output_path != csv_path:
            df.to_csv(output_path, index=False)
            logger.info(f"Processed data saved to {output_path}")
            return output_path
        else:
            logger.info(f"Data processed successfully from {csv_path}")
            return csv_path
            
    except Exception as e:
        logger.error(f"Error processing CSV data: {e}")
        raise


def convert_zst_to_csv(input_path: str, output_path: str = None, keep_intermediate: bool = False) -> str:
    """
    Main function to convert ZST file to CSV.
    
    Args:
        input_path (str): Path to the input .zst file
        output_path (str, optional): Path for the final CSV output
        keep_intermediate (bool): Whether to keep intermediate decompressed file
        
    Returns:
        str: Path to the final CSV file
    """
    input_file = Path(input_path)
    
    # Determine output path if not provided
    if output_path is None:
        if input_file.suffix == '.zst':
            # If input is .csv.zst, output will be .csv
            output_path = str(input_file.with_suffix(''))
            if not output_path.endswith('.csv'):
                output_path += '.csv'
        else:
            output_path = str(input_file.with_suffix('.csv'))
    
    # Step 1: Decompress the ZST file
    decompressed_path = decompress_zst_file(input_path)
    
    try:
        # Step 2: Process the CSV data
        final_path = process_csv_data(decompressed_path, output_path)
        
        # Step 3: Clean up intermediate file if requested
        if not keep_intermediate and decompressed_path != final_path:
            Path(decompressed_path).unlink()
            logger.info(f"Removed intermediate file: {decompressed_path}")
        
        return final_path
        
    except Exception as e:
        # Clean up intermediate file in case of error
        if Path(decompressed_path).exists() and not keep_intermediate:
            Path(decompressed_path).unlink()
        raise


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Convert ZST compressed files to CSV format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python zst_to_csv_conversion.py data.csv.zst
  python zst_to_csv_conversion.py data.csv.zst output.csv
  python zst_to_csv_conversion.py data.csv.zst --keep-intermediate
        """
    )
    
    parser.add_argument('input_file', help='Input ZST file to convert')
    parser.add_argument('output_file', nargs='?', help='Output CSV file (optional)')
    parser.add_argument('--keep-intermediate', action='store_true', 
                       help='Keep the intermediate decompressed file')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        result_path = convert_zst_to_csv(
            args.input_file, 
            args.output_file, 
            args.keep_intermediate
        )
        print(f"✅ Conversion completed successfully!")
        print(f"📄 Output file: {result_path}")
        
        # Show file size information
        result_file = Path(result_path)
        if result_file.exists():
            size_mb = result_file.stat().st_size / (1024 * 1024)
            print(f"📊 File size: {size_mb:.2f} MB")
            
    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()