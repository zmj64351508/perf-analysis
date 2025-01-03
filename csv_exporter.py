import csv

def save(path, all_series):
	with open(path, 'w', newline='') as file:
		writer = csv.writer(file)
		writer.writerow(['Name', 'Avg', 'Best', 'Worst', 'Std', 'Count'])
		for key in sorted(all_series):
			val = all_series[key]
			if val.get_unit() == "%":
				avg = f'{val.calc_average() * 100:.2f}%'
				best = f'{val.calc_best() * 100:.2f}%'
				worst = f'{val.calc_worst() * 100:.2f}%'
				std = f'{val.calc_std() * 100:.2f}%'
			else:
				avg = f'{val.calc_average():.2f}'
				best = f'{val.calc_best():.2f}'
				worst = f'{val.calc_worst():.2f}'
				std = f'{val.calc_std():.2f}'
			writer.writerow([key, avg, best, worst, std, f'{val.count()}'])