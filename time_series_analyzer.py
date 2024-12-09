import os, sys
import argparse
import re
import glob
from scenario_importer import ScenarioImporter
import time_series_viewer
from config import config
from time_series_selector import TimeSeriesSelector
import csv_exporter


def filter_series(all_series, filter_string):
	if len(filter_string) == 0:
		return all_series
	filtered_series = {}
	for key in all_series:
		search = re.search(filter_string, key)
		if search is not None:
			filtered_series[key] = all_series[key]
	return filtered_series


if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("-o", "--output", type=str, default="", help="Output directory")
	parser.add_argument("-g", "--gui", action="store_true", help="Show GUI")
	parser.add_argument("-f", "--filter", type=str, default="", help="Series filter, regex supported")
	parser.add_argument("-l", "--list", action="store_true", help="List name of series")
	parser.add_argument('input_files', nargs='+', help='List of files to process.')
	args = parser.parse_args()

	importer = ScenarioImporter()
	for file in args.input_files:
		for path in glob.glob(file, recursive=True):
			print('Importing from ', path)
			importer.import_from_path(path)
	print('=' * 80)
	viewer = []

	all_series = importer.get_all_series()
	all_series = filter_series(all_series, args.filter)
	if args.list:
		print('Listing series:')
		for k in sorted(all_series):
			print(k)
		sys.exit(0)

	for k, v in all_series.items():
		print(f'{k} count {v.count()}')
		if v.get_unit() == "%":
			print(f'{k} avg   {v.calc_average()*100:.2f}%')
			print(f'{k} worst {v.calc_worst()*100:.2f}%')
			print(f'{k} best  {v.calc_best()*100:.2f}%')
		else:
			print(f'{k} avg   {v.calc_average():.2f}')
			print(f'{k} worst {v.calc_worst():.2f}')
			print(f'{k} best  {v.calc_best():.2f}')
		print('=' * 80)

	if args.output != "":
		args.output = os.path.normpath(args.output)
		if not os.path.exists(args.output):
			os.makedirs(args.output)
		print(f'Saving csv results')
		csv_exporter.save(os.path.join(args.output, "result.csv"), all_series)
		for k, v in all_series.items():
			print(f'Saving figure for {k}')
			time_series_viewer.add_viewer(k, v)
			time_series_viewer.save(args.output, )
			time_series_viewer.clear()

	if args.output != "":
		sys.exit(0)

	if args.gui:
		selector = TimeSeriesSelector(all_series)
		selector.show()
