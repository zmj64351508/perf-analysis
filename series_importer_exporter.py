import sys
import numpy as np
from time_series import TimeSeries
from time_series import Better

def save(path, all_series, prefix=""):
	if path == "":
		f = sys.stdout
	else:
		f = open(path, 'a')
	try:
		for name, series in all_series.items():
			with np.printoptions(threshold=np.inf, linewidth=np.inf):
				f.write("series: ")
				if prefix != "":
					f.write(f'{prefix}.{name}')
				else:
					f.write(name)
				f.write("\n")
				f.write("unit: ")
				f.write(str(series.get_unit()))
				f.write("\n")
				f.write("better: ")
				f.write(str(series.get_better()))
				f.write("\n")
				f.write("timestamp: ")
				ts = series.get_timestamp_series()
				if ts is not None:
					f.write(np.array2string(ts, separator=","))
				else:
					f.write("None")
				f.write("\n")
				f.write("data: ")
				f.write(np.array2string(series.get_data_series(), separator=","))
				f.write("\n")
				f.write("series end\n")
	except Exception as e:
		raise e
	finally:
		if path != "":
			f.close()

class SeriesImporter:
	def __init__(self):
		self.all_series = {}

	def import_from_path(self, path):
		with open(path, 'r') as f:
			name = ""
			unit = ""
			better = ""
			data = None
			timestamp = None
			lines = f.readlines()
			for line in lines:
				if line.startswith("series:"):
					name = line[7:].strip()
				elif line.startswith("unit:"):
					unit = line[5:].strip()
				elif line.startswith("better:"):
					better = eval(line[7:].strip())
				elif line.startswith("timestamp:"):
					timestamp = line[10:].strip()
					if timestamp == "None":
						timestamp = []
					else:
						timestamp = eval(timestamp)
				elif line.startswith("data:"):
					data = eval(line[5:].strip())
				elif line.startswith("series end"):
					self.all_series[name] = TimeSeries(timestamp, data, unit, better)
					name = ""
					unit = ""
					better = ""
					data = None
					timestamp = None
	
	def get_all_series(self):
		return self.all_series
				
