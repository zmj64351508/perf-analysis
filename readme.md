# Introduction
This is a tool to analyze time series data. It can generate statistics and plots from the input files

Supported input file format:
- chipvi log files from ZEBU

# Install
```bash
pip3 install matplotlib numpy astropy
```

# Example
```bash
python3 time_series_analyzer.py <path-to-log>  # Show statistics
python3 time_series_analyzer.py <path-to-log> -g   # Use interactive GUI
python3 time_series_analyzer.py <path-to-log> -o <path-to-output-dir>  # Generate csv and plots
python3 time_series_analyzer.py <path-to-log> -s <timestamp> -e <timestamp>  # Statistics for a specific time periodt
```

# Usage
```bash
usage: time_series_analyzer.py [-h] [-o OUTPUT] [-g] [-f FILTER] [-l] [-s START] [-e END] input_files [input_files ...]

positional arguments:
  input_files           List of files to process.

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Output directory
  -g, --gui             Show GUI
  -f FILTER, --filter FILTER
                        Series filter, regex supported
  -l, --list            List name of series
  -s START, --start START
                        start timestamp
  -e END, --end END     end timestamp
```