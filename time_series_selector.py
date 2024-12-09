import tkinter as tk
from tkinter import ttk
import time_series_viewer

class TimeSeriesSelector(object):
	def __init__(self, all_series, root=None):
		self.all_series = all_series
		if not root:
			root = tk.Tk()
		self.root = root
		self.root.title("Select Time Series")

		self.check_vars = []
		self.options = list(sorted(self.all_series))

		for i, option in enumerate(self.options):
			var = tk.BooleanVar()
			chk = ttk.Checkbutton(root, text=option, variable=var)
			chk.grid(row=i, column=0, sticky=tk.W)
			self.check_vars.append(var)

		select_all_button = ttk.Button(root, text="Select All", command=self.select_all)
		select_all_button.grid(row=len(self.options), column=0, sticky=tk.W+tk.E)

		deselect_all_button = ttk.Button(root, text="Deselect All", command=self.deselect_all)
		deselect_all_button.grid(row=len(self.options)+1, column=0, sticky=tk.W+tk.E)

		confirm_button = ttk.Button(root, text="Confirm", command=self.confirm_selection)
		confirm_button.grid(row=len(self.options)+2, column=0, columnspan=2, sticky=tk.W+tk.E)

	def select_all(self):
		for var in self.check_vars:
			var.set(True)

	def deselect_all(self):
		for var in self.check_vars:
			var.set(False)

	def confirm_selection(self):
		selected_options = [option for option, var in zip(self.options, self.check_vars) if var.get()]
		print("Selected options:", selected_options)
		for option in selected_options:
			time_series_viewer.add_viewer(option, self.all_series[option])
		time_series_viewer.show()

	def show(self):
		self.root.mainloop()
