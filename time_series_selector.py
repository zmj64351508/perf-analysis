import re
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import time_series_viewer
from config import config


class TimeSeriesList(tk.Frame):
	def __init__(self, root, all_series):
		super().__init__(root)
		self.all_series = all_series
		
		self.canvas = tk.Canvas(self, highlightthickness=0)
		self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
		
		scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
		scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
		
		roll_frame=tk.Frame(self.canvas)
		roll_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
		self.canvas.create_window((0,0), window=roll_frame, anchor='nw')
		self.canvas.configure(yscrollcommand=scrollbar.set)
		roll_frame.bind("<Configure>", self.configure)
		roll_frame.bind("<MouseWheel>", self.on_mousewheel)

		self.check_vars = []
		self.checks = []
		self.checks_dict = {}
		self.list = list(sorted(self.all_series))
		for i, option in enumerate(self.list):
			var = tk.BooleanVar()
			chk = ttk.Checkbutton(roll_frame, text=option, variable=var)
			chk.grid(row=i, column=0, sticky="nw")
			self.check_vars.append(var)
			self.checks.append(chk)
			self.checks_dict[option] = chk
			chk.bind("<MouseWheel>", self.on_mousewheel)

	def set_series_visibility(self, name, visible):
		if name not in self.checks_dict:
			return
		if visible:
			self.checks_dict[name].grid()
			self.checks_dict[name].bind_all("<MouseWheel>", self.on_mousewheel)
		else:
			self.checks_dict[name].grid_remove()
			self.checks_dict[name].unbind_all("<MouseWheel>")

	def configure(self, event):
		self.canvas.configure(scrollregion=self.canvas.bbox("all"))

	def on_mousewheel(self, event):
		self.canvas.yview_scroll(-1 * int(event.delta / 120), "units")
	
	def select_all(self):
		for i, chk in enumerate(self.checks):
			if chk.winfo_viewable():
				self.check_vars[i].set(True)

	def deselect_all(self):
		for i, chk in enumerate(self.checks):
			if chk.winfo_viewable():
				self.check_vars[i].set(False)

	def toggle_select_all(self):
		for i, chk in enumerate(self.checks):
			if chk.winfo_viewable():
				chk.invoke()

	def get_selection(self):
		return [self.list[i] for i, var in enumerate(self.check_vars) if var.get()]


class SearchBox(tk.Frame):
	def __init__(self, parent, search_command, text="Search"):
		super().__init__(parent)
		self.search_command = search_command
		self.input = tk.Entry(self, relief="solid")
		self.input.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, anchor=tk.NW)
		search_button = ttk.Button(self, text=text, command=self._search)
		search_button.pack(side=tk.LEFT, padx=(2,0), anchor=tk.NE)
		clear_button = ttk.Button(self, text="Clear", command=self.clear)
		clear_button.pack(side=tk.LEFT, padx=(2,0), anchor=tk.NE)
		self.bind_all("<Return>", lambda e: self._search())

	def _search(self):
		self.search_command(self.input.get())

	def clear(self):
		self.input.delete(0, tk.END)
		self._search()

	def focus_set(self):
		return self.input.focus_set()


class TimeSeriesSelector(tk.Frame):
	def __init__(self, all_series, root=None):
		self.all_series = all_series
		if not root:
			root = tk.Tk()
		self.root = root
		self.root.title("Select Time Series")
		self.root.geometry("800x600")
		self.root.protocol("WM_DELETE_WINDOW", self.on_close)

		super().__init__(root)
		super().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

		left_frame = tk.Frame(self, borderwidth=2, relief="solid")
		left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5, anchor=tk.NW)

		filter_input = SearchBox(left_frame, self.filter, text="Filter")
		filter_input.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5, anchor=tk.NW)
		filter_input.focus_set()

		select_button_frame = tk.Frame(left_frame)
		select_button_frame.pack(side=tk.TOP, anchor=tk.NW)
		select_all_button = ttk.Button(select_button_frame, text="Select All", command=self.select_all)
		select_all_button.pack(side=tk.LEFT, padx=(5, 5))
		deselect_all_button = ttk.Button(select_button_frame, text="Deselect All", command=self.deselect_all)
		deselect_all_button.pack(side=tk.LEFT, padx=(0, 5))

		self.series_list = TimeSeriesList(left_frame, self.all_series)
		self.series_list.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5, anchor=tk.NW)

		right_frame = tk.Frame(self)
		right_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5, anchor=tk.NW)

		time_viewer_frame = tk.Frame(right_frame)
		time_viewer_frame.pack(side=tk.TOP, padx=5, anchor=tk.NW)
		self.use_time_viewer = tk.BooleanVar()
		self.use_time_viewer.set(True)
		chk = ttk.Checkbutton(time_viewer_frame, text="Time-based analysis in ", variable=self.use_time_viewer)
		chk.pack(side=tk.LEFT)
		self.time_viewer_type = ttk.Combobox(time_viewer_frame, values=["seperated viewer", "combined viewer"])
		#self.time_viewer_type.bind("<<ComboboxSelected>>", self.time_viewer_type_select)
		self.time_viewer_type.set("seperated viewer")
		self.time_viewer_type.pack(side=tk.LEFT)

		self.use_perodic_analysis = tk.BooleanVar()
		chk = ttk.Checkbutton(right_frame, text="Perodic analysis", variable=self.use_perodic_analysis)
		chk.pack(side=tk.TOP, padx=5, anchor=tk.NW)

		self.show_data_point = tk.BooleanVar()
		chk = ttk.Checkbutton(right_frame, text="Show data points", variable=self.show_data_point)
		chk.pack(side=tk.TOP, padx=5, anchor=tk.NW)

		confirm_button = ttk.Button(right_frame, text="Confirm", command=self.confirm_selection)
		confirm_button.pack(side=tk.BOTTOM, padx=(0, 5), anchor=tk.SW)

		self.bind_all("<Control-s>", lambda e: self.series_list.toggle_select_all())
		self.bind_all("<Control-q>", lambda e: self.series_list.select_all())
		self.bind_all("<Control-w>", lambda e: self.series_list.deselect_all())
		self.bind_all("<Control-Return>", lambda e: self.confirm_selection())
		self.bind_all("<Control-d>", lambda e: filter_input.clear())

	def filter(self, text):
		if len(text) == 0:
			for key in self.all_series:
				self.series_list.set_series_visibility(key, True)
		else:
			for key in self.all_series:
				if re.search(text, key):
					self.series_list.set_series_visibility(key, True)
				else:
					self.series_list.set_series_visibility(key, False)	

	def select_all(self):
		self.series_list.select_all()

	def deselect_all(self):
		self.series_list.deselect_all()

	def confirm_selection(self):
		selected_series = self.series_list.get_selection()
		print("Selected series:", selected_series)
		if self.show_data_point.get():
			config["plot.marker"] = "."
		else:
			config["plot.marker"] = ""

		try:
			for option in selected_series:
				if self.use_time_viewer.get():
					if self.time_viewer_type.get() == "combined viewer":
						time_series_viewer.add_combined_viewer(self.root, option, self.all_series[option])
					else:
						time_series_viewer.add_seperated_viewer(self.root, option, self.all_series[option])
				if self.use_perodic_analysis.get():
					time_series_viewer.add_perodic_analysis(self.root, option, self.all_series[option])
			time_series_viewer.show(self.root)
		except Exception as e:
			time_series_viewer.clear()
			messagebox.showerror("Error", message=str(e))

	def show(self):
		self.root.mainloop()

	def on_close(self):
		time_series_viewer.clear()
		self.root.destroy()
