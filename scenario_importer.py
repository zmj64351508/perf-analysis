import re
import numpy as np
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
			mpstat_cnt = 0
			isp_module = ""
			isp_module_idx = None
			monitor_timestamp = 0
			line = ""
			new_line = True
			cam_idx = 0
			for l in f.readlines():
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

				search = re.search(r'(\[(\d+)\])?(.*)', line)
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
					busy = 1 - float(search.group(9)) / 100
					key = 'a720.PNC.cpu_utilization'
					if key not in self.all_series:
						self.all_series[key] = TimeSeries([], [], '%', Better.LOWER)
					self.all_series[key].add_one_data(timestamp, busy)
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
					self.all_series[key].add_one_data(monitor_timestamp, bw)
					continue
				# bandwidth monitor
				search = re.search(r'\*\*(Average|Full) Bandwidth\*\*', line)
				if search:
					monitor_timestamp = timestamp
					cam_idx = 0
					continue
				if monitor_timestamp > 0:
					search = re.search(r'^(.+): (\d+) ([KMG]+B/s)', line)
					if search:
						name = search.group(1).lower()
						# workaround for duplicate cam
						if name == 'cam':
							cam_idx += 1
							if cam_idx % 2 == 0:
								continue
						if name == 'cpu':
							name = 'a720.PNC'
						elif name.startswith('cpu '):
							name = name.replace('cpu ', 'a720.')
						key = f'{name}.monitor.total_bw'
						bw = int(search.group(2))
						unit = search.group(3)
						if key not in self.all_series:
							self.all_series[key] = TimeSeries([], [], unit, Better.HIGHER)
						self.all_series[key].add_one_data(monitor_timestamp, bw)
						continue


	def get_all_series(self):
		if 'ddr.monitor.sum_total_bw' not in self.all_series:
			total_bw = None
			total_bw_timestamp = None
			total_bw_unit = ""
			for key in self.all_series:
				if key.endswith('.monitor.total_bw') and not key.startswith("ddr"):
					if total_bw is None:
						total_bw = self.all_series[key].get_data_series()
						total_bw_timestamp = self.all_series[key].get_timestamp_series()
						total_bw_unit = self.all_series[key].get_unit()
					else:
						total_bw += self.all_series[key].get_data_series()
			if total_bw is not None:
				timestamp = total_bw_timestamp.tolist() if total_bw_timestamp is not None else None
				data = total_bw.tolist() if total_bw is not None else None
				self.all_series['ddr.monitor.sum_total_bw'] = TimeSeries(timestamp, data, total_bw_unit, Better.HIGHER)
		return self.all_series
