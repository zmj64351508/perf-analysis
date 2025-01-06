import numpy as np
import enum

class Better(enum.Enum):
	HIGHER = 1
	LOWER = 2


class TimeSeries(object):
	def __init__(self, timestamp_ns: list, data: list, unit: str, better: Better) -> None:
		"""
		timestamp should in nanoseconds
		"""
		self.timestamp = timestamp_ns
		self.data = data
		self.unit = unit
		self.better = better
		if self.timestamp is None:
			self.timestamp = []

	def add_data(self, timestamp: list, data: list) -> None:
		if len(timestamp) != len(data):
			raise ValueError("Timestamp and data must have the same length")
		self.timestamp += timestamp
		self.data += data

	def add_one_data(self, timestamp, data) -> None:
		if len(self.timestamp) > 0 and timestamp is None:
			message = f"Ignoring timestamp of series, original length of timestamp is {len(self.timestamp)}"
			self.timestamp = []
			raise ValueError(message)
		if timestamp is not None and len(self.timestamp) == len(self.data):
			self.timestamp.append(timestamp)
		self.data.append(data)
		if len(self.timestamp) > 0 and len(self.data) != len(self.timestamp):
			raise ValueError(f"Timestamp and data must have the same length, otherwise timestamp should be empty, adding timestamp {timestamp}, data {data}")

	def count(self) -> int:
		return len(self.data)

	def get_timestamp_series(self) -> np.array:
		if self.timestamp is not None and len(self.timestamp) > 0:
			return np.array(self.timestamp)
		else:
			return np.arange(len(self.data))

	def get_data_series(self) -> np.array:
		return np.array(self.data)

	def get_unit(self) -> str:
		return self.unit

	def get_timestamp_unit(self) -> str:
		if self.timestamp is not None and len(self.timestamp) > 0:
			return "ns"
		else:
			return "sample"

	def get_better(self) -> Better:
		return self.better

	def calc_average(self) -> float:
		if len(self.data) == 0:
			return 0
		return sum(self.data) / len(self.data)

	def calc_max(self):
		if len(self.data) == 0:
			return 0
		return max(self.data)

	def calc_min(self):
		if len(self.data) == 0:
			return 0
		return min(self.data)

	def calc_best(self):
		if len(self.data) == 0:
			return 0
		if self.better == Better.HIGHER:
			return max(self.data)
		else:
			return min(self.data)

	def calc_worst(self):
		if len(self.data) == 0:
			return 0
		if self.better == Better.HIGHER:
			return min(self.data)
		else:
			return max(self.data)

	def calc_std(self) -> float:
		if len(self.data) == 0:
			return 0
		return np.std(self.data)

	def slice(self, start: int, end: int) -> "TimeSeries":
		if start is None and end is None or start == end:
			return self

		timestamps = self.get_timestamp_series()
		if timestamps is None:
			timestamps = np.arange(len(self.data))

		if start is None:
			start = 0
		if end is None:
			end = timestamps[-1]
		print(f'slice from {start} to {end}')

		start_idx, end_idx = np.searchsorted(timestamps, (start, end))
		end_idx = min(len(timestamps), end_idx)
		print(f'slice index from {start_idx} to {end_idx}')
		timestamp_segment = timestamps[start_idx:end_idx]
		data_segment = self.data[start_idx:end_idx]

		return TimeSeries(timestamp_segment, data_segment, self.unit, self.better)	