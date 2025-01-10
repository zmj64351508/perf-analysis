# Introduction
This is a tool to analyze time series data. It can generate statistics and plots from the input files

Supported input file format:
- chipvi log files from ZEBU (default)
- standard series format

# Install
```bash
pip3 install matplotlib numpy astropy
```

# Basic Example
```bash
python3 time_series_analyzer.py <path-to-log>  # Show statistics
python3 time_series_analyzer.py <path-to-log> -g   # Use interactive GUI
python3 time_series_analyzer.py <path-to-log> -f <filter-string>  # Filter series
python3 time_series_analyzer.py <path-to-log> -o <path-to-output-dir>  # Generate csv and plots
python3 time_series_analyzer.py <path-to-log> -s <timestamp> -e <timestamp>  # Statistics for a specific time periodt
```

# Compare Different Series
You can convert log files to standard series format and add a prefix to differentiate them. Then you can use the `-i series` option to analyze them together.
```bash
python3 time_series_analyzer.py <path-to-log> -c <prefix> -o <path-to-output>  # Convert to standard series format
python3 time_series_analyzer.py <path-to-standard-series> -i series  # Use standard series format for analysis
python3 time_series_analyzer.py <path-to-log>#+1000 <path-to-log>#-2000 # Align multiple series by specifing offset
```

# Usage
```bash
usage: time_series_analyzer.py [-h] [-o OUTPUT] [-g] [-f FILTER] [-l] [-s START] [-e END] [-c [CONVERT]] [-i INPUT_FORMAT] input_files [input_files ...]

positional arguments:
  input_files           List of files to process. Offset can be specified after files, like "log.txt#+100"

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
  -c [CONVERT], --convert [CONVERT]
                        Convert to standard data format, argument is prefix
  -i INPUT_FORMAT, --input_format INPUT_FORMAT
                        Input format (candidates: scenario, series)
```