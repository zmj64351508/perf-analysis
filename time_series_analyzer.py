import os, sys
import argparse
import re
import glob
import tkinter as tk
from scenario_importer import ScenarioImporter
from time_series_viewer import TimeSeriesViewerManager
from config import config
from time_series_selector import TimeSeriesSelector
import csv_exporter
import series_importer_exporter


def filter_series(all_series, filter_string):
	if len(filter_string) == 0:
		return all_series
	filtered_series = {}
	for key in all_series:
		search = re.search(filter_string, key)
		if search is not None:
			filtered_series[key] = all_series[key]
	return filtered_series


def slice_serices(all_series, start, end):
	new_series = {}
	for k, v in all_series.items():
		new_series[k] = v.slice(start, end)
	return new_series


if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("-o", "--output", type=str, default="", help="Output directory")
	parser.add_argument("-g", "--gui", action="store_true", help="Show GUI")
	parser.add_argument("-f", "--filter", type=str, default="", help="Series filter, regex supported")
	parser.add_argument("-l", "--list", action="store_true", help="List name of series")
	parser.add_argument("-s", "--start", type=int, default=None, help="start timestamp")
	parser.add_argument("-e", "--end", type=int, default=None, help="end timestamp")
	parser.add_argument("-c", "--convert", type=str, nargs='?', default="", help="Convert to standard data format, argument is prefix")
	parser.add_argument("-i", "--input_format", type=str, default="unknown", help="Input format (candidates: scenario, series)")
	parser.add_argument("--beat_size", type=int, default=0, help="Bus beat size")
	parser.add_argument('input_files', nargs='+', help='List of files to process.')
	args = parser.parse_args()

	config["bus.beat_size"] = args.beat_size

	if args.input_format == "series":
		importer = series_importer_exporter.SeriesImporter()
	elif args.input_format == "scenario":
		importer = ScenarioImporter()
	else:
		importer = None
	
	for file in args.input_files:
		splited = file.split('#')
		file = splited[0]
		if len(splited) > 1:
			offset = int(splited[1])
		else:
			offset = 0
		for path in glob.glob(file, recursive=True):
			if os.path.isdir(path):
				args.input_files.append(os.path.join(path, "*"))
				continue
			else:
				print(f'Importing from {path}, offset={offset}')
				# Guess importer if not specified
				if importer is None:
					if path.endswith(".series"):
						importer = series_importer_exporter.SeriesImporter()
					else:
						importer = ScenarioImporter()
				importer.import_from_path(path, offset=offset)
	print('=' * 80)
	viewer = []

	all_series = importer.get_all_series()
	all_series = filter_series(all_series, args.filter)
	all_series = slice_serices(all_series, args.start, args.end)
	if args.list:
		print('Listing series:')
		for k in sorted(all_series):
			print(k)
		sys.exit(0)

	if args.convert != "":
		series_importer_exporter.save(args.output, all_series, args.convert)
		sys.exit(0)

	if args.output != "":
		viewer_mgr = TimeSeriesViewerManager(None)
		args.output = os.path.normpath(args.output)
		if not os.path.exists(args.output):
			os.makedirs(args.output)
		print(f'Saving csv results')
		csv_exporter.save(os.path.join(args.output, "result.csv"), all_series)
		for k, v in all_series.items():
			print(f'Saving figure for {k}')
			viewer_mgr.add_seperated_viewer(k, v)
			viewer_mgr.save(args.output)
			viewer_mgr.clear()
		sys.exit(0)

	if args.gui:
		root = tk.Tk()
		viewer_mgr = TimeSeriesViewerManager(root)
		selector = TimeSeriesSelector(root, viewer_mgr, all_series)
		root.mainloop()
		sys.exit(0)

	for k in sorted(all_series):
		print(f'{k} count {all_series[k].count()}')
		unit = all_series[k].get_unit()
		print(f'{k} avg   {all_series[k].calc_average():.2f} {unit}')
		print(f'{k} worst {all_series[k].calc_worst():.2f} {unit}')
		print(f'{k} best  {all_series[k].calc_best():.2f} {unit}')
		print(f'{k} std  {all_series[k].calc_std():.2f} {unit}')
		print('=' * 80)

