import struct
import matplotlib.pyplot as plt
from matplotlib.widgets import SpanSelector
from matplotlib.offsetbox import AnchoredText
import numpy as np
import argparse

def get_unit_scale(unit_string):
	if unit_string == "GB" or unit_string == "GiB":
		unit_scale = 1024 * 1024 * 1024
	elif unit_string == "MB" or unit_string == "MiB":
		unit_scale = 1024 * 1024
	elif unit_string == "KB" or unit_string == "KiB":
		unit_scale = 1024
	else:
		unit_scale = 1
	return unit_scale
	

def read_bandwidth_data(file_path):
	with open(file_path, 'rb') as f:
		# Read header
		if not args.no_header:
			head = f.read(64)
			unpack_head = struct.unpack('<QQQQQQQQ', head)
			magic = unpack_head[0]
			if magic != 0x2B1A3D4C99630F7A:
				print("Failed to parse file: invalid magic")
				exit(1)
			start_time_ns = unpack_head[1]
			end_time_ns = unpack_head[2]
			interval_ms = unpack_head[3]
			count = unpack_head[4]
			avg = unpack_head[5]
		else:
			start_time_ns = args.start_ns
			end_time_ns = 0
			interval_ms = args.interval_ms
			count = 0
			avg = 0

		print("Information from input file:")
		print(f"  Start: {start_time_ns} ns")
		print(f'  End: {end_time_ns} ns')
		print(f"  Interval: {interval_ms} ms")
		print(f"  Count: {count}")
		print(f'  Avg: {avg} MB/s')

		unit_scale = get_unit_scale(args.unit)
	
		# Read data
		read_data = []
		write_data = []
		i = 0
		while True:
			if i >= count:
				break
			# read bandwidth
			chunk = f.read(4)
			if len(chunk) < 4:
				break
			read = struct.unpack('<I', chunk)[0]
			read_data.append(read * 32 / unit_scale / (interval_ms / 1000))
			# write bandwidth
			chunk = f.read(4)
			if len(chunk) < 4:
				break
			write = struct.unpack('<I', chunk)[0]
			write_data.append(write * 32 / unit_scale / (interval_ms / 1000))
			# Bandwidth is in B/s, counter value should multiply by 32 to get bytes
			i += 1
	read_data = np.array(read_data)
	write_data = np.array(write_data)

	assert(len(read_data) == len(write_data))
	
	# Convert timestamps axis
	start = start_time_ns / 1e6
	stop = start+len(read_data)
	timestamps_ms = np.arange(start=start, stop=stop, step=interval_ms)

	# Workaround: sometime length of timestamps will not equal to data, maybe bug in np.arrange
	if len(timestamps_ms) - len(read_data) != 0:
		timestamps_ms.resize(len(read_data))

	return timestamps_ms, {"Read":read_data, "Write":write_data}

def read_bandwidth_data_perf_x86(file_path):
	import csv
	data = {}
	timestamps_ms = []
	unit = ""
	with open(file_path, mode='r', newline='', encoding='utf-8') as file:
		csv_reader = csv.reader(file)
		for row in csv_reader:
			if len(row) == 0 or row[0].startswith("#"):
				continue
			timestamp_ms = float(row[0]) * 1000
			data_size = float(row[1])
			unit = row[2]
			name = row[3]
			interval_ns = float(row[4])
			bandwidth = data_size / (interval_ns / 1e9)
			if not name in data:
				data[name] = []
			data[name].append(bandwidth)
			if not timestamp_ms in timestamps_ms:
				timestamps_ms.append(timestamp_ms)

	unit_scale = get_unit_scale(unit) / get_unit_scale(args.unit)
		
	ret = {"Read": np.zeros(len(timestamps_ms)), "Write": np.zeros(len(timestamps_ms))}
	for key, value in data.items():
		if "read" in key:
			ret["Read"] += np.array(value) * unit_scale
		elif "write" in key:
			ret["Write"] += np.array(value) * unit_scale

	return np.array(timestamps_ms), ret


class BandwidthAnalyzer:
	def __init__(self, timestamps_ms, data, name):
		self.timestamps_ms = timestamps_ms
		self.data = data
		self.name = name
		self.fig, self.ax = plt.subplots(figsize=(15, 7))
		self.stat_text = AnchoredText("", loc="upper right", bbox_transform=self.ax.transAxes, prop={'alpha': 0.7}, )

		self.ax.add_artist(self.stat_text)
		
		self.line, = self.ax.plot(timestamps_ms, data, label=f"Bandwidth ({args.unit}/s)")
		self.ax.set_xlabel("Time (ms)")
		self.ax.set_ylabel(f"Bandwidth ({args.unit}/s)")
		self.ax.set_title(f"{self.name} Bandwidth Over Time")
		self.ax.legend(loc='upper left')
		
		self.span = SpanSelector(self.ax, self.on_select, 'horizontal', useblit=True,
									props=dict(alpha=0.3, facecolor='blue'), interactive=True)
		self.show_statistics(0, 0)

	def on_select(self, xmin, xmax):
		self.show_statistics(xmin, xmax)

	def show_statistics(self, start_ms, end_ms):
		min_bw, max_bw, mean_bw, start, end = self.calculate_statistics(start_ms, end_ms)
		text = f"""Statistics:
Start: {start:.3f} ms 
End: {end:.3f} ms
Dur: {end-start:.3f} ms
Min: {min_bw:.3f} {args.unit}/s
Max: {max_bw:.3f} {args.unit}/s
Avg: {mean_bw:.3f} {args.unit}/s"""
		self.stat_text.txt.set_text(text)
		plt.draw()

	def show(self):
		plt.show()

	def calculate_statistics(self, start_ms, end_ms):
		if start_ms == end_ms:
			start = 0
			end = len(self.timestamps_ms)
			data_segment = self.data
		else:
			start, end = np.searchsorted(self.timestamps_ms, (start_ms, end_ms))
			end = min(len(self.timestamps_ms), end)
			data_segment = self.data[start:end]
			if len(data_segment) == 0:
				start = 0
				end = len(self.timestamps_ms)
				data_segment = self.data
		
		min_bandwidth = np.min(data_segment)
		max_bandwidth = np.max(data_segment)
		mean_bandwidth = np.mean(data_segment)
		
		return min_bandwidth, max_bandwidth, mean_bandwidth, start+self.timestamps_ms[0], end+self.timestamps_ms[0]


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Bandwdith viewer")
	parser.add_argument("file_path", type=str, help="input file path")
	parser.add_argument("--no-header", default=False, action="store_true", help="parse input file without header")
	parser.add_argument("--interval-ms", type=int, default=1, help="interval in milliseconds(only use with --no-header)")
	parser.add_argument("--start-ns", type=int, default=0, help="start time in nanoseconds(only use with --no-header)")
	parser.add_argument("-u", "--unit", type=str, default="GB", help="unit: GB, MB, KB, B")
	parser.add_argument("--type", type=str, default="chipvi", help="type: chipvi, perf")
	args = parser.parse_args()

	if args.type == "chipvi":
		timestamps_ms, data = read_bandwidth_data(args.file_path)
	elif args.type == "perf":
		timestamps_ms, data = read_bandwidth_data_perf_x86(args.file_path)

	for name, series in data.items():
		analyzer = BandwidthAnalyzer(timestamps_ms, series, name)
	plt.show()