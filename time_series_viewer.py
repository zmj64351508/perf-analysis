import os
import tkinter as tk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import SpanSelector
from matplotlib.offsetbox import AnchoredText
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from astropy.timeseries import LombScargle
from config import config

viewer = {}
combined_all_series = {}
perodic_analysis_viewers = {}

def show(parent):
	global combined_all_series
	if len(combined_all_series) > 0:
		TimeSeriesCombinedViewer(parent, combined_all_series)
	combined_all_series = {}
	#plt.show()

def clear():
	global viewer, combined_all_series, perodic_analysis_viewers
	plt.close()
	for key in viewer:
		viewer[key].destroy()
	for key in perodic_analysis_viewers:
		perodic_analysis_viewers[key].destroy()
	viewer = {}
	combined_all_series = {}
	perodic_analysis_viewers = {}

def save(path):
	for key in sorted(viewer):
		viewer[key].save(path)

def add_seperated_viewer(parent, name, series):
	if name not in viewer:
		viewer[name] = TimeSeriesViewer(parent, name, series)

def add_combined_viewer(parent, name, series):
	if name not in combined_all_series:
		combined_all_series[name] = series

def add_perodic_analysis(parent, name, series):
	if name not in perodic_analysis_viewers:
		perodic_analysis_viewers[name] = PerodicAnalysisViewer(parent, name, series)


class TimeSeriesViewerBase(tk.Toplevel):
	def __init__(self, parent, fig):
		super().__init__(parent)
		self.canvas = FigureCanvasTkAgg(fig, master=self)
		self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
		self.canvas.draw()
		toolbar = NavigationToolbar2Tk(self.canvas, self)
		toolbar.update()
		self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
		#self.window.protocol("WM_DELETE_WINDOW", self.on_close)

	def set_window_title(self, title):
		self.title(title)

	#def on_close(self):
	#	self.destory()


class PerodicAnalysisViewer(TimeSeriesViewerBase):
	def __init__(self, parent, name, series):
		self.name = name
		self.series = series
		self.fig, self.ax = plt.subplots(figsize=(15, 7))
		super().__init__(parent, self.fig)

		self.set_window_title(self.name)
		self.fig.canvas.mpl_connect('close_event', self.on_close)

		time = series.get_timestamp_series()
		values = series.get_data_series()

		if time is None:
			time = np.arange(len(values))

		frequency, power = LombScargle(time, values).autopower()

		self.ax.plot(1 / frequency, power, marker=config["plot.marker"])
		self.ax.set_title(f'{name} Lomb-Scargle periodogram')
		self.ax.set_xlabel('period')
		self.ax.set_ylabel('power')

	def on_close(self, event):
		global perodic_analysis_viewers
		perodic_analysis_viewers.pop(self.name, None)

		
class TimeSeriesCombinedViewer(TimeSeriesViewerBase):
	def __init__(self, parent, all_series):
		self.fig, self.ax = plt.subplots(figsize=(15, 7))
		super().__init__(parent, self.fig)

		self.time_unit = "ns"
		self.unit = ""
		self.lines = []
		for name, series in all_series.items():
			print(f"plotting {name}")
			data = series.get_data_series()
			timestamps = series.get_timestamp_series() if series.get_timestamp_series() is not None else np.arange(len(series.data))
			self.ax.plot(timestamps, data, label=f"{name} ({series.get_unit()})", marker=config["plot.marker"])
			if self.unit == "":
				self.unit = series.get_unit()
			elif self.unit != series.get_unit():
				raise ValueError(f"All series must have the same unit. {self.unit} vs. {series.get_unit()}")

		self.ax.legend(loc='upper left')
		self.ax.set_xlabel(f"time ({self.time_unit})")
		self.ax.set_ylabel(f"({self.unit})")


class TimeSeriesViewer(TimeSeriesViewerBase):
	def __init__(self, parent, name, series):
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

		if (len(self.timestamps) != len(self.data)):
			raise ValueError(f"Time and data series must have the same length. {len(self.timestamps)} vs. {len(series.data)}")

		self.name = name
		self.fig, self.ax = plt.subplots(figsize=(15, 7))
		super().__init__(parent, self.fig)

		self.set_window_title(self.name)
		self.fig.canvas.mpl_connect('close_event', self.on_close)
		self.stat_text = AnchoredText("", loc="upper right", bbox_transform=self.ax.transAxes, prop={'alpha': 0.7}, )

		self.ax.add_artist(self.stat_text)
		
		self.line, = self.ax.plot(self.timestamps, self.data, label=f"{name} ({series.get_unit()})", marker=config["plot.marker"])
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