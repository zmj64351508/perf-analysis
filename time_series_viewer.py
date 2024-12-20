import os
import tkinter as tk
import numpy as np
import matplotlib.figure as figure
from matplotlib.widgets import SpanSelector
from matplotlib.offsetbox import AnchoredText
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from astropy.timeseries import LombScargle
from config import config

class TimeSeriesViewerManager:
	def __init__(self, parent):
		self.seperated_viewer = {}
		self.combined_all_series = {}
		self.combiled_viewers = []
		self.perodic_analysis_viewers = {}
		self.parent = parent

	def new_parent_window(self):
		if self.parent is None:
			return None
		else:
			root = tk.Toplevel(self.parent)
			return root

	def show(self):
		if len(self.combined_all_series) > 1:
			viewer = TimeSeriesCombinedViewer(self.new_parent_window(), self, self.combined_all_series)
			viewer.pack(fill=tk.BOTH, expand=True)
			self.combiled_viewers.append(viewer)
		elif len(self.combined_all_series) == 1:
			for key in self.combined_all_series:
				self.add_seperated_viewer(key, self.combined_all_series[key])
		self.combined_all_series = {}

	def clear(self):
		self.seperated_viewer = {}
		self.combined_all_series = {}
		self.perodic_analysis_viewers = {}
		self.combiled_viewers = []

	def save(self, path):
		for key in sorted(self.seperated_viewer):
			self.seperated_viewer[key].save(path)

	def add_seperated_viewer(self, name, series):
		if name not in self.seperated_viewer:
			viewer = TimeSeriesViewer(self.new_parent_window(), self, name, series)
			viewer.pack(fill=tk.BOTH, expand=True)
			self.seperated_viewer[name] = viewer

	def remove_seperated_viewer(self, name):
		self.seperated_viewer.pop(name, None)

	def add_combined_viewer(self, name, series):
		if name not in self.combined_all_series:
			self.combined_all_series[name] = series

	def add_perodic_analysis(self, name, series):
		if name not in self.perodic_analysis_viewers:
			viewer = PerodicAnalysisViewer(self.new_parent_window(), self, name, series)
			viewer.pack(fill=tk.BOTH, expand=True)
			self.perodic_analysis_viewers[name] = viewer

	def remove_perodic_analysis(self, name):
		self.perodic_analysis_viewers.pop(name, None)

	def for_all_viewers(self, func):
		for k, v in self.seperated_viewer.items():
			func(k, v)
		for v in self.combiled_viewers:
			func(None, v)

class MarkCommand:
	def __init__(self, axes, x):
		self.axes = axes
		self.x = x
		self.lines = []

	def do_mark(self):
		for ax in self.axes:
			self.lines.append(ax.axvline(x=self.x, color='red', linestyle='-', linewidth=1))

	def undo_mark(self):
		for line in self.lines:
			line.remove()

class TimeSeriesNavigationToolbar(NavigationToolbar2Tk):
	def __init__(self, canvas, parent):
		self.data_x = None
		self.data_y = None
		super().__init__(canvas, parent)

	def set_message(self, s):
		if self.data_x is None or self.data_y is None:
			super().set_message(s)
		else:
			super().set_message(f'data({self.data_x:.2f}, {self.data_y:.2f}) ' + s)

	def update_x_y(self, x, y):
		self.data_x = x
		self.data_y = y

class TimeSeriesViewerBase(tk.Frame):
	def __init__(self, parent, mgr):
		super().__init__(parent)
		self.fig = figure.Figure(figsize=(15, 7))
		self.ax = self.fig.add_subplot(111)
		self.mark_command = None
		self.mark_command_history = []
		self.canvas = FigureCanvasTkAgg(self.fig, master=self)
		self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
		self.canvas.draw()
		self.toolbar = TimeSeriesNavigationToolbar(self.canvas, self)
		self.toolbar.update()
		self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
		self.canvas.mpl_connect("button_press_event", self.on_right_click)
		self.canvas.mpl_connect('motion_notify_event', self.on_motion)
		self.popup_menu = tk.Menu(self, tearoff=0)
		self.popup_menu.add_command(label="Sync scale", command=self.menu_sync_scale)
		self.popup_menu.add_command(label="Mark", command=self.menu_mark)
		self.popup_menu.add_command(label="Sync marks", command=self.menu_sync_marks)
		self.popup_menu.add_command(label="Undo mark", command=self.menu_undo_mark)
		self.popup_menu.add_command(label="Clear mark", command=self.menu_clear_mark)
		highlight_marker = '.'
		if config['plot.marker'] == '.':
			highlight_marker = 'o'
		self.highlight, = self.ax.plot([], [], highlight_marker)
		self.mgr = mgr

	def set_window_title(self, title):
		self.winfo_toplevel().title(title)

	def get_mgr(self):
		return self.mgr

	def mark(self, x):
		command = MarkCommand(self.fig.axes, x)
		command.do_mark()
		self.mark_command_history.append(command)
		self.canvas.draw()

	def on_motion(self, event):
		ax = event.inaxes
		if not ax:
			return
		self.nearest_point(ax, event.xdata, event.ydata)

	def on_right_click(self, event):
		ax = event.inaxes
		if not ax:
			return
		if event.button == 3:
			try:
				self.mark_x = event.xdata
				self.scale_x_min = ax.get_xlim()[0]
				self.scale_x_max = ax.get_xlim()[1]
				self.popup_menu.tk_popup(event.guiEvent.x_root, event.guiEvent.y_root)
			finally:
				self.popup_menu.grab_release()

	def nearest_point(self, ax, x, y):
		lines = self.get_lines()
		series_count = len(lines)
		if series_count == 0:
			return
		
		xlim = ax.get_xlim()
		xrange = xlim[1] - xlim[0]
		ylim = ax.get_ylim()
		yrange = ylim[1] - ylim[0]
		min_index = np.zeros(series_count, dtype=int)
		distances = np.zeros(series_count)
		for i in range(series_count):
			x_series = self.get_x_series(ax, i)
			y_series = self.get_y_series(ax, i)
			if x_series is None or y_series is None:
				return
			d = np.sqrt(((x_series - x) / xrange * self.winfo_width()) ** 2 + ((y_series - y) / yrange * self.winfo_height()) ** 2)
			min_index[i] = np.argmin(d)
			distances[i] = np.min(d)
		series_index = np.argmin(distances)
		value_index = min_index[series_index]
		x_series = self.get_x_series(ax, series_index)
		y_series = self.get_y_series(ax, series_index)
		self.highlight.set_data(x_series[value_index], y_series[value_index])
		self.highlight.set_color(lines[series_index].get_color())
		self.toolbar.update_x_y(x_series[value_index], y_series[value_index])
		self.fig.canvas.draw_idle()

	def get_lines(self):
		return []

	def get_x_series(self, axes, index):
		return None
		
	def get_y_series(self, axes, index):
		return None

	def set_x_scale(self, min, max):
		for ax in self.fig.axes:
			ax.set_xlim([min, max])
		self.canvas.draw()

	def undo_mark(self):
		try:
			command = self.mark_command_history.pop()
		except IndexError:
			command = None
		if command:
			command.undo_mark()
			self.canvas.draw()

	def clear_mark(self):
		for command in self.mark_command_history:
			command.undo_mark()
		self.mark_command_history.clear()
		self.canvas.draw()

	def menu_sync_scale(self):
		self.get_mgr().for_all_viewers(lambda k, v : v.set_x_scale(self.scale_x_min, self.scale_x_max))

	def menu_mark(self):
		if self.mark_x is not None:
			self.get_mgr().for_all_viewers(lambda k, v : v.mark(self.mark_x))

	def menu_sync_marks(self):
		self.get_mgr().for_all_viewers(lambda k, v : v.clear_mark() if v is not self else None)
		for command in self.mark_command_history:
			self.get_mgr().for_all_viewers(lambda k, v : v.mark(command.x) if v is not self else None)

	def menu_undo_mark(self):
		self.get_mgr().for_all_viewers(lambda k, v : v.undo_mark())

	def menu_clear_mark(self):
		self.get_mgr().for_all_viewers(lambda k, v : v.clear_mark())

	#def on_close(self):
	#	self.destory()


class PerodicAnalysisViewer(TimeSeriesViewerBase):
	def __init__(self, parent, mgr, name, series):
		self.name = name
		self.series = series
		super().__init__(parent, mgr)

		self.set_window_title(self.name)
		self.fig.canvas.mpl_connect('close_event', self.on_close)

		time = series.get_timestamp_series()
		values = series.get_data_series()

		if time is None:
			time = np.arange(len(values))

		frequency, power = LombScargle(time, values).autopower()


		self.x = 1 / frequency
		self.y = power
		self.line = self.ax.plot(self.x, self.y, marker=config["plot.marker"])
		self.ax.set_title(f'{name} Lomb-Scargle periodogram')
		self.ax.set_xlabel('period')
		self.ax.set_ylabel('power')

	def on_close(self, event):
		self.get_mgr().remove_perodic_analysis(self.name)

	def get_lines(self):
		return self.line

	def get_x_series(self, axes, index):
		return self.x

	def get_y_series(self, axes, index):
		return self.y

		
class TimeSeriesCombinedViewer(TimeSeriesViewerBase):
	def __init__(self, parent, mgr, all_series):
		super().__init__(parent, mgr)

		self.time_unit = None
		self.unit = ""
		self.lines = []
		self.x = []
		self.y = []
		for name, series in all_series.items():
			print(f"plotting {name}")
			data = series.get_data_series()
			timestamps = series.get_timestamp_series()
			if timestamps is None:
				timestamps = np.arange(len(series.data))
				time_unit = "sample"
			else:
				time_unit = "ns"
			if self.time_unit is None:
				self.time_unit = time_unit
			elif self.time_unit != time_unit:
				raise ValueError(f"All series must have the same timestamp unit. {self.time_unit} vs. {time_unit}")
			self.lines += self.ax.plot(timestamps, data, label=f"{name} ({series.get_unit()})", marker=config["plot.marker"])
			self.x.append(timestamps)
			self.y.append(data)
			if self.unit == "":
				self.unit = series.get_unit()
			elif self.unit != series.get_unit():
				raise ValueError(f"All series must have the same unit. {self.unit} vs. {series.get_unit()}")
		self.ax.legend(loc='upper left')
		self.ax.set_xlabel(f"time ({self.time_unit})")
		self.ax.set_ylabel(f"({self.unit})")
		self.set_window_title("Combined Viewer")

	def get_lines(self):
		return self.lines

	def get_x_series(self, axes, index):
		return self.x[index]

	def get_y_series(self, axes, index):
		return self.y[index]


class TimeSeriesViewer(TimeSeriesViewerBase):
	def __init__(self, parent, mgr, name, series):
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
		super().__init__(parent, mgr)

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
									props=dict(alpha=0.3, facecolor='blue'), interactive=True, button=1)
		self.show_statistics(0, 0)

	def get_lines(self):
		return [self.line]

	def get_x_series(self, axes, index):
		return self.timestamps

	def get_y_series(self, axes, index):
		return self.data

	def on_select(self, xmin, xmax):
		self.show_statistics(xmin, xmax)

	def on_close(self, event):
		self.get_mgr().remove_seperated_viewer(self.name)

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
		self.fig.canvas.draw_idle()

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