import re
import numpy as np
from time_series import TimeSeries
from time_series import Better
import config

class ScenarioImporter:
	def __init__(self):
		self.all_series = {}
		self.post_processed = False
		pass

	def import_from_path(self, path: str, offset=0):
		zebu_log = False
		with open(path, "r") as f:
			for l in f.readlines(10):
				if re.search(r'TX>.*RX>', l):
					zebu_log = True
					break

		with open(path, "r") as f:
			bpu_model = ""
			vpu_frame = None
			vdsp_core = None
			lineno = 0
			raw_lineno = 0
			mpstat_cnt = 0
			isp_module = ""
			isp_module_idx = None
			monitor_timestamp = 0
			line = ""
			new_line = True
			cam_idx = 0
			for l in f.readlines():
				raw_lineno += 1
				try:
					if zebu_log:
						search = re.search(r'RX> (.*)', l)
						if search and search.group(1) != None:
							# skip error data
							if search.group(1).strip().startswith("Erroneous data"):
								continue
							if new_line:
								line = search.group(1)
							else:
								line += search.group(1)
							if line.rstrip().endswith("\\010"):
								lineno += 1
								#if lineno <= 10:
								#	print(line)
								new_line = True
							else:
								new_line = False
								continue
						else:
							line = ""
							new_line = True
							ValueError(f"Failed to parse line: {line}")

						line = line.rstrip()
						if line.endswith('\\010'):
							line = line[:-4]
						line = line.rstrip()
						if line.endswith('\\013'):
							line = line[:-4]
						line = line.rstrip()

						search = re.search(r'^(\[(\d+)\])?(.*)', line)
						if search:
							if search.group(2) != None:
								timestamp = int(search.group(2))
							else:
								timestamp = None
							line = search.group(3)
						else:
							ValueError(f"Failed to parse line: {line}")
					else:
						line = l.rstrip()
						timestamp = None
					# vpu
					search = re.search(r'Start testing frame (\d+)', line)
					if search:
						vpu_frame = int(search.group(1))
						continue
					search = re.search(r'Core id:(\d+).*cycles this frame , (\d+) cycle', line)
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
						continue
					# bpu
					search = re.search(r'BPU model\[(.*)\] sum: read_bw\[(\d+)\] MB/s; write_bw\[(\d+)\] MB/s', line)
					if search:
						model = search.group(1)
						read_bw = int(search.group(2))
						write_bw = int(search.group(3))
						bw = read_bw + write_bw
						key = f'bpu.{model}.bw'
						if key not in self.all_series:
							self.all_series[key] = TimeSeries([], [], 'MB/s', Better.HIGHER)
						self.all_series[key].add_one_data(timestamp, bw)
						continue
					search = re.search(r'BPU model\[(.*)\].*fps\[(\d+)\]', line)
					if search:
						bpu_model = search.group(1)
						bpu_model_fps = int(search.group(2))
						key = f'bpu.{bpu_model}.fps'
						if key not in self.all_series:
							self.all_series[key] = TimeSeries([], [], 'fps', Better.HIGHER)
						self.all_series[key].add_one_data(timestamp, bpu_model_fps)
						continue
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
							bw = float(search.group(1)) * 2
							if key not in self.all_series:
								self.all_series[key] = TimeSeries([], [], 'MB/s', Better.HIGHER)
							self.all_series[key].add_one_data(timestamp, bw)
							continue
					# PNC
					search = re.search(r'all\s+(\d+.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)', line)
					if search:
						mpstat_cnt += 1
						# skip the first 2 seconds
						if mpstat_cnt <= 2:
							continue
						busy = 100 - float(search.group(9))
						key = 'a720.PNC.cpu_utilization'
						if key not in self.all_series:
							self.all_series[key] = TimeSeries([], [], '%', Better.LOWER)
						self.all_series[key].add_one_data(timestamp, busy)
						continue
					search = re.search(',(instructions|cycles|cpu-clock|r60|r61),', line)
					if search:
						perf_output = line.strip().split(',')
						perf_timestamp = float(perf_output[0]) * 1e9
						perf_counter = float(perf_output[1])
						perf_name = perf_output[3]
						metric = float(perf_output[6])
						metric_unit = perf_output[7]
						#key = f'a720.PNC.perf.{perf_name}'
						#if key not in self.all_series:
						#	self.all_series[key] = TimeSeries([], [], 'count', Better.HIGHER)
						#self.all_series[key].add_one_data(int(perf_timestamp), perf_counter)
						metric_key = ""
						if metric_unit == 'K/sec':
							metric /= 1024
						elif metric_unit == 'G/sec':
							metric *= 1024
						elif metric_unit == '/sec':
							metric /= 1024 * 1024
						elif metric_unit == 'M/sec':
							pass
						elif metric_unit == 'insn per cycle':
							metric_key = 'a720.PNC.perf.ipc'
							metric_unit = 'ipc'
						elif metric_unit == "CPUs utilized":
							metric_key = 'a720.PNC.perf.cpus'
							metric_unit = 'count'

						beat_size = config.config['bus.beat_size']
						if perf_name == 'r60' or perf_name == 'r61':
							if perf_name == 'r60':
								metric_key = 'a720.PNC.perf.bus_access_rd'
							else:
								metric_key = 'a720.PNC.perf.bus_access_wr'
							if beat_size > 0:
								metric *= beat_size
								metric_unit = 'MB/s'
							else:
								metric_unit = 'Mbeat/s'
						if metric_key != "":
							if metric_key not in self.all_series:
								self.all_series[metric_key] = TimeSeries([], [], metric_unit, Better.HIGHER)
							self.all_series[metric_key].add_one_data(int(perf_timestamp), metric)
						continue
					# cam
					search = re.search('(?:\[0m)?([a-z]+)(\d+) pipe info:', line)
					if search:
						isp_module = search.group(1)
						isp_module_idx = search.group(2)
						continue
					if isp_module != "":
						search = re.search(r' fps:(\d+\.\d+)', line)
						if search:
							fps = float(search.group(1))
							key = f'cam.{isp_module}.{isp_module_idx}.fps'
							if key not in self.all_series:
								self.all_series[key] = TimeSeries([], [], 'fps', Better.HIGHER)
							self.all_series[key].add_one_data(timestamp, fps)
							isp_module = ""
							isp_module_idx = None
							continue
						search = re.search(r'max hw proc tm:(\d+\.\d+)ms', line)
						if search:
							time = float(search.group(1))
							key = f'cam.{isp_module}.{isp_module_idx}.hw_process_time'
							if key not in self.all_series:
								self.all_series[key] = TimeSeries([], [], 'ms', Better.LOWER)
							self.all_series[key].add_one_data(timestamp, time)
							continue
					search = re.search(r'Display get wb frame done,fps = (\d+\.\d+), bw = (\d+)', line)
					if search:
						key = 'dpu.fps'
						fps = float(search.group(1))
						if key not in self.all_series:
							self.all_series[key] = TimeSeries([], [], 'fps', Better.HIGHER)
						self.all_series[key].add_one_data(timestamp, fps)

						key = 'dpu.bw'
						bw = int(search.group(2)) / 1024 / 1024
						if key not in self.all_series:
							self.all_series[key] = TimeSeries([], [], 'MB/s', Better.HIGHER)
						self.all_series[key].add_one_data(timestamp, bw)
						continue
					# cpu memcpy
					search = re.search(r'Core(\d+):.*cpu memcpy test bandwidth: (\d+) MB/s', line)
					if search:
						core_id = int(search.group(1))
						bw = int(search.group(2))
						key = f'a720.{core_id}.memcpy'
						if key not in self.all_series:
							self.all_series[key] = TimeSeries([], [], 'MB/s', Better.HIGHER)
						self.all_series[key].add_one_data(timestamp, bw)
						continue
					# gpua
					search = re.search(r'handle_output_ri.*diff:(\w+)', line)
					if search:
						#fps = 1e9 / int("0x" + search.group(1), 16)
						fps = 1e9 / int(search.group(1))
						key = "gpua.fps"
						if key not in self.all_series:
							self.all_series[key] = TimeSeries([], [], "fps", Better.HIGHER)
						self.all_series[key].add_one_data(timestamp, fps)
						continue
					# bandwidth monitor
					search = re.search(r'\*\*(Average|Full) Bandwidth\*\*', line)
					if search:
						monitor_timestamp = timestamp
						cam_idx = 0
						continue
					if monitor_timestamp > 0:
						# stripe leading color codes
						search = re.search(r'(?:\[36m.*\[0m)(.*)', line)
						if search:
							striped_line = search.group(1)
						else:
							striped_line = line
						search = re.search(r'^(.+): (\d+) ([KMG]+B/s)', striped_line)
						if search:
							name = search.group(1).lower()
							if name.endswith(' read'):
								rw = 'read'
								name = name[:-5]
							elif name.endswith(' write'):
								rw = 'write'
								name = name[:-6]
							elif name.endswith(' total'):
								rw = 'total'
								name = name[:-6]
							else:
								rw = 'total'
							
							# workaround for duplicate cam
							if name == 'cam':
								cam_idx += 1
								if cam_idx % 2 == 0:
									continue
							if name == 'cpu':
								name = 'a720.PNC'
							elif name.startswith('cpu '):
								name = name.replace('cpu ', 'a720.')
							key = f'{name}.monitor.{rw}_bw'
							bw = int(search.group(2))
							unit = search.group(3)
							if key not in self.all_series:
								self.all_series[key] = TimeSeries([], [], unit, Better.HIGHER)
							self.all_series[key].add_one_data(monitor_timestamp, bw)
							continue
						# for ddr limit req
						#search = re.search(r'(Read|Write): ((\d| )+)', striped_line)
						#if search:
						#	rw = search.group(1).lower()
						#	watermark = search.group(2).split()
						#	for i, v in enumerate(watermark):
						#		key = f'ddr.{i}.{rw}.monitor.limit_req'
						#		wm = int(v)
						#		if key not in self.all_series:
						#			self.all_series[key] = TimeSeries([], [], 'count', Better.HIGHER)
						#		self.all_series[key].add_one_data(monitor_timestamp, wm)
						#	continue
				except Exception as e:
					print("Warning:", e)
					print("  path:", path)
					print("  line:", raw_lineno)
					print("  timestamp:", timestamp)
					print("  content:", line)

	def pad_and_add(self, a, b):
		max_length = max(len(a), len(b))
		new_a = np.zeros(max_length, dtype=a.dtype)
		new_b = np.zeros(max_length, dtype=b.dtype)
		new_a[:len(a)] = a
		new_b[:len(b)] = b
		return new_a + new_b

	def add_series(self, series_0, series_1):
		data = self.pad_and_add(series_0.get_data_series(), series_1.get_data_series())
		timestamp = series_0.get_timestamp_series()
		unit = series_0.get_unit()
		better = series_0.get_better()
		return TimeSeries(timestamp, data, unit, better)

	def minus_series(self, series_0, series_1):
		data = self.pad_and_add(series_0.get_data_series(), series_1.get_data_series() * (-1))
		timestamp = series_0.get_timestamp_series()
		unit = series_0.get_unit()
		better = series_0.get_better()
		return TimeSeries(timestamp, data, unit, better)

	def sum_series(self, pattern, new_name):
		if new_name not in self.all_series:
			new_series = []
			new_timestamp = []
			new_unit = ""
			for key in self.all_series:
				if re.search(pattern, key):
					print(f'{new_name} add by {key}')
					if len(new_series) == 0:
						new_series = self.all_series[key].get_data_series()
						new_timestamp = self.all_series[key].get_timestamp_series()
						new_unit = self.all_series[key].get_unit()
						new_better = self.all_series[key].get_better()
					else:
						new_series = self.pad_and_add(new_series, self.all_series[key].get_data_series())
			if len(new_series) > 0:
				timestamp = new_timestamp.tolist() if new_timestamp is not None else None
				data = new_series.tolist() if new_series is not None else None
				self.all_series[new_name] = TimeSeries(timestamp, data, new_unit, new_better)

	def sum_perf_cpus(self, name):
		if name in self.all_series and 'a720.PNC.perf.cpus':
			ipc = self.all_series[name].get_data_series()
			ipc_ts = self.all_series[name].get_timestamp_series()
			cpus = self.all_series['a720.PNC.perf.cpus'].get_data_series()
			cpus_ts = self.all_series['a720.PNC.perf.cpus'].get_timestamp_series()
			ipc_unit = self.all_series[name].get_unit()
			if np.array_equal(cpus_ts, ipc_ts):
				new_ipc = ipc * cpus
				self.all_series[name+'_total'] = TimeSeries(ipc_ts, new_ipc, ipc_unit, Better.HIGHER)
				self.all_series.pop(name)
				return True
			else:
				print(f'{name}: perf cpus series has different timestamps')
			return False

	def calc_total_bw(self):
		total_bw = {}
		for key in self.all_series:
			total_key = None
			if key.endswith('.monitor.read_bw'):
				total_key = key.replace('read_bw', 'total_bw(r+w)')
			elif key.endswith('.monitor.write_bw'):
				total_key = key.replace('write_bw', 'total_bw(r+w)')
			if total_key is None:
				continue
			if total_key in total_bw:
				total_bw[total_key] = self.add_series(total_bw[total_key], self.all_series[key])
			else:
				total_bw[total_key] = self.all_series[key]

		for key in total_bw:
			if key not in self.all_series:
				self.all_series[key] = total_bw[key]

	def get_all_series(self):
		if not self.post_processed:
			self.calc_total_bw()
			self.sum_series(r'(?<!ddr)\.monitor\.total_bw$', 'ddr.monitor.sum_total_bw')
			self.sum_series(r'(?<!ddr)\.monitor\.total_bw\(r\+w\)', 'ddr.monitor.sum_total_bw(r+w)')
			self.sum_series(r'(?<!ddr)\.monitor\.read_bw', 'ddr.monitor.sum_read_bw')
			self.sum_series(r'(?<!ddr)\.monitor\.write_bw', 'ddr.monitor.sum_write_bw')
			self.sum_series(r'a720.*\.monitor\.total_bw$', 'a720.monitor.sum_total_bw')
			self.sum_series(r'a720.*\.monitor\.total_bw\(r\+w\)', 'a720.monitor.sum_total_bw(r+w)')
			self.sum_series(r'a720.*\.monitor\.read_bw', 'a720.monitor.sum_read_bw')
			self.sum_series(r'a720.*\.monitor\.write_bw', 'a720.monitor.sum_write_bw')
			#self.sum_series('a720.*memcpy', 'a720.sum.memcpy')
			self.sum_perf_cpus('a720.PNC.perf.ipc')
			self.sum_perf_cpus('a720.PNC.perf.bus_access_rd')
			self.sum_perf_cpus('a720.PNC.perf.bus_access_wr')
			if "a720.PNC.perf.cpus" in self.all_series:
				self.all_series.pop('a720.PNC.perf.cpus')
			if 'a720.PNC.cpu_utilization' in self.all_series:
				self.sum_series(r'a720\.(b0|b1)\.monitor\.total_bw$', 'a720.PNC.monitor.sum_total_bw')
				self.sum_series(r'a720\.(b0|b1)\.monitor\.total_bw\(r\+w\)', 'a720.PNC.monitor.sum_total_bw(r+w)')
			self.post_processed = True
		return self.all_series
