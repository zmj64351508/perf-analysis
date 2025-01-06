import csv

def save(path, all_series):
	with open(path, 'w', newline='') as file:
		writer = csv.writer(file)
		writer.writerow(['Name', 'Avg', 'Best', 'Worst', 'Std', 'Count'])
		for key in sorted(all_series):
			val = all_series[key]
			unit = ""
			if val.get_unit() == "%":
				unit = "%"
			avg = f'{val.calc_average():.2f}{unit}'
			best = f'{val.calc_best():.2f}{unit}'
			worst = f'{val.calc_worst():.2f}{unit}'
			std = f'{val.calc_std():.2f}{unit}'
			writer.writerow([key, avg, best, worst, std, f'{val.count()}'])