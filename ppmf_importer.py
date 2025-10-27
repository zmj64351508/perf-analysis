import os
import pandas as pd
from time_series import TimeSeries
from time_series import Better

class PPMFImporter:
	def __init__(self):
		self.all_series = {}

	def import_from_path(self, path, offset=0):
		df = pd.read_csv(path)
		if df.shape[1] < 2:
			raise ValueError("CSV file must have at least two columns: timestamp and data.")
		timestamps = tuple((df[df.columns[0]] + offset) * 1000 * 1000)
		for i, col_name in enumerate(df.columns[1:]):
			split_name = col_name.split(':')
			if len(split_name) == 2:
				series_name = split_name[0].strip()
				series_unit = split_name[1].strip()
			else:
				series_name = split_name[0].strip()
				series_unit = ""
			self.all_series[os.path.basename(path).split('.')[0] + '.' + series_name] = TimeSeries(timestamps, tuple(df[col_name]), unit=series_unit, better=Better.HIGHER)
	
	def get_all_series(self):
		return self.all_series
				
