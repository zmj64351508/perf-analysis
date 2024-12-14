# Install
```bash
pip install matplotlib numpy astropy
```

# Example
```bash
python time_series_analyzer.py <path-to-log> -g   # Use interactive GUI
python time_series_analyzer.py <path-to-log> -o <path-to-output-dir>  # Generate csv and plots
```

# Usage
```bash
usage: time_series_analyzer.py [-h] [-o OUTPUT] [-g] [-f FILTER] [-l] input_files [input_files ...]

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
```