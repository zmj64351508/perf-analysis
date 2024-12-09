import re
from time_series import TimeSeries
from time_series import Better

class ScenarioImporter:
	def __init__(self):
		self.all_series = {}
		pass

	def import_from_path(self, path: str):
		with open(path, "r") as f:
			bpu_model = ""
			vpu_frame = None
			vdsp_core = None
			lineno = 0
			mpstat_title_lineno = 0
			mpstat_cnt = 0
			isp_module = ""
			isp_module_idx = None
			monitor_timestamp = 0
			for line in f.readlines():
				lineno += 1
				search = re.search(r'RX> (\[(\d+)\])?(.*)', line)
				if search:
					if search.group(2) != None:
						timestamp = int(search.group(2))
					else:
						timestamp = None
					line = search.group(3)
				else:
					ValueError(f"Failed to parse line: {line}")
				# vpu
				search = re.search(r'Start testing frame (\d+)', line)
				if search:
					vpu_frame = int(search.group(1))
					continue
				search = re.search(r'Core id:(\d+).*cycles this frame , (\d+)', line)
				if search and vpu_frame != None and vpu_frame == 1:
					vpu_core = int(search.group(1))
					if vpu_core == 0:
						vpu_name = "0.jdec"
					elif vpu_core == 1:
						vpu_name = "1.jenc"
					elif vpu_core == 2:
						vpu_name = "2.vdec"
					elif vpu_core == 3:
						vpu_name = "3.venc0"
					elif vpu_core == 4:
						vpu_name = "4.venc1"
					else:
						vpu_name = f'{vpu_core}'
					vpu_cycle = int(search.group(2))
					key = f'vpu.{vpu_name}.cycle'
					if key not in self.all_series:
						self.all_series[key] = TimeSeries([], [], 'cycle', Better.LOWER)
					self.all_series[key].add_one_data(timestamp, vpu_cycle)
				search = re.search(r'BPU model\[(.*)\].*fps\[(\d+)\]', line)
				if search:
					bpu_model = search.group(1)
					bpu_model_fps = int(search.group(2))
					key = f'bpu.{bpu_model}.fps'
					if key not in self.all_series:
						self.all_series[key] = TimeSeries([], [], 'fps', Better.HIGHER)
					self.all_series[key].add_one_data(timestamp, bpu_model_fps)
					continue
				# bpu
				if bpu_model != "":
					search = re.search(r'read_bw\[(\d+)\].*write_bw\[(\d+)\]', line)
					if search:
						key = f'bpu.{bpu_model}.read_bw'
						bw = int(search.group(1))
						if key not in self.all_series:
							self.all_series[key] = TimeSeries([], [], 'MB/s', Better.HIGHER)
						self.all_series[key].add_one_data(timestamp, bw)

						key = f'bpu.{bpu_model}.write_bw'
						bw = int(search.group(2))
						if key not in self.all_series:
							self.all_series[key] = TimeSeries([], [], 'MB/s', Better.HIGHER)
						self.all_series[key].add_one_data(timestamp, bw)
						continue
				# vdsp
				search = re.search(r'VDSP Chip_Vi test function, Processor ID: \[(\d+)\]', line)
				if search:
					vdsp_core = int(search.group(1))
					continue
				if vdsp_core != None:
					search = re.search(r'DDR R/W Bandwidth: (.*) MB/s', line)
					if search:
						key = f'vdsp.{vdsp_core}.copy_rw'
						bw = float(search.group(1))
						if key not in self.all_series:
							self.all_series[key] = TimeSeries([], [], 'MB/s', Better.HIGHER)
						self.all_series[key].add_one_data(timestamp, bw)
						continue
				# PNC
				search = re.search(r'%idle', line)
				if search:
					mpstat_title_lineno = lineno
					continue
				if lineno == mpstat_title_lineno + 2:
					search = re.search(r'(\d+\.\d+)', line)
					if search:
						mpstat_cnt += 1
						# skip the first 2 seconds
						if mpstat_cnt <= 2:
							continue
						busy = 1 - float(search.group(1)) / 100
						key = 'a720.PNC.cpu_utilization'
						if key not in self.all_series:
							self.all_series[key] = TimeSeries([], [], '%', Better.LOWER)
						self.all_series[key].add_one_data(timestamp, busy)
						continue
				# isp
				search = re.search('(?:\[0m)?([a-z]+)(\d+) pipe info:', line)
				if search:
					isp_module = search.group(1)
					isp_module_idx = search.group(2)
					continue
				if isp_module != "":
					search = re.search("  fps:(\d+\.\d+)", line)
					if search:
						fps = float(search.group(1))
						key = f'isp.{isp_module}.{isp_module_idx}.fps'
						if key not in self.all_series:
							self.all_series[key] = TimeSeries([], [], 'fps', Better.HIGHER)
						self.all_series[key].add_one_data(timestamp, fps)
						isp_module = ""
						isp_module_idx = None
						continue
				# bandwidth monitor
				search = re.search(r'\*\*Average Bandwidth\*\*', line)
				if search:
					monitor_timestamp = timestamp
					continue
				if monitor_timestamp > 0:
					search = re.search(r'^(\w+): (\d+) ([KMG]+B/s)', line)
					if search:
						name = search.group(1).lower()
						key = f'{name}.monitor.total_bw'
						bw = int(search.group(2))
						unit = search.group(3)
						if key not in self.all_series:
							self.all_series[key] = TimeSeries([], [], unit, Better.HIGHER)
						self.all_series[key].add_one_data(monitor_timestamp, bw)


	def get_all_series(self):
		return self.all_series
