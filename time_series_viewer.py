import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import SpanSelector
from matplotlib.offsetbox import AnchoredText

viewer = {}

def show():
	plt.show()

def clear():
	global viewer
	plt.close()
	viewer = {}

def save(path):
	for key in sorted(viewer):
		viewer[key].save(path)

def add_viewer(name, series):
	if name not in viewer:
		viewer[name] = TimeSeriesViewer(name, series)

class TimeSeriesViewer:
	def __init__(self, name, series):
		self.series = series
		self.data = series.get_data_series()
		if series.get_unit() == "%":
			self.data = self.data * 100
		self.timestamps = series.get_timestamp_series()
		if self.timestamps is None:
			self.time_unit = "sample"
			self.timestamps = np.arange(len(series.data))
		else:
			self.time_unit = "ns"
		self.name = name
		self.fig, self.ax = plt.subplots(figsize=(15, 7))
		self.fig.canvas.manager.set_window_title(self.name)
		self.fig.canvas.mpl_connect('close_event', self.on_close)
		self.stat_text = AnchoredText("", loc="upper right", bbox_transform=self.ax.transAxes, prop={'alpha': 0.7}, )

		self.ax.add_artist(self.stat_text)
		
		self.line, = self.ax.plot(self.timestamps, self.data, label=f"{name} ({series.get_unit()})")
		self.ax.set_xlabel(f"time ({self.time_unit})")
		self.ax.set_ylabel(f"{name} ({series.get_unit()})")
		self.ax.set_title(f"{self.name} over time")
		self.ax.legend(loc='upper left')
		
		self.span = SpanSelector(self.ax, self.on_select, 'horizontal', useblit=True,
									props=dict(alpha=0.3, facecolor='blue'), interactive=True)
		self.show_statistics(0, 0)

	def on_select(self, xmin, xmax):
		self.show_statistics(xmin, xmax)

	def on_close(self, event):
		global viewer
		viewer.pop(self.name, None)

	def show_statistics(self, start_ns, end_ns):
		min_bw, max_bw, mean_bw, start, end = self.calculate_statistics(start_ns, end_ns)
		text = f"""Statistics:
Start: {start:.3f} {self.time_unit}
End: {end:.3f} {self.time_unit}
Dur: {end-start:.3f} {self.time_unit}
Min: {min_bw:.3f} {self.series.get_unit()}
Max: {max_bw:.3f} {self.series.get_unit()}
Avg: {mean_bw:.3f} {self.series.get_unit()}"""
		self.stat_text.txt.set_text(text)
		plt.draw()

	def calculate_statistics(self, start_ns, end_ns):
		if start_ns == end_ns:
			start = 0
			end = len(self.timestamps)
			data_segment = self.data
		else:
			start, end = np.searchsorted(self.timestamps, (start_ns, end_ns))
			end = min(len(self.timestamps), end)
			data_segment = self.data[start:end]
			if len(data_segment) == 0:
				start = 0
				end = len(self.timestamps)
				data_segment = self.data
		
		min_bandwidth = np.min(data_segment)
		max_bandwidth = np.max(data_segment)
		mean_bandwidth = np.mean(data_segment)
		
		return min_bandwidth, max_bandwidth, mean_bandwidth, self.timestamps[start], self.timestamps[end-1]

	def save(self, path, *args, **kargs):
		self.fig.savefig(os.path.join(path, f'{self.name}.png'), *args, **kargs)