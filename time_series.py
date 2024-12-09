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

	def add_data(self, timestamp: list, data: list) -> None:
		if len(timestamp) != len(data):
			raise ValueError("Timestamp and data must have the same length")
		self.timestamp += timestamp
		self.data += data

	def add_one_data(self, timestamp, data) -> None:
		if self.timestamp is not None and timestamp is not None:
			self.timestamp.append(timestamp)
		elif self.timestamp is not None and timestamp is None:
			self.timestamp = None
			print("Warning: ignoring timestamp")
		self.data.append(data)
		if self.timestamp is not None and len(self.timestamp) > 0 and len(self.data) != len(self.timestamp):
			raise ValueError(f"Timestamp and data must have the same length, otherwise timestamp should be empty, adding timestamp {timestamp}, data {data}")

	def count(self) -> int:
		return len(self.data)

	def get_timestamp_series(self) -> np.array:
		if self.timestamp is not None and len(self.timestamp) > 0:
			return np.array(self.timestamp)
		else:
			return None

	def get_data_series(self) -> np.array:
		return np.array(self.data)

	def get_unit(self) -> str:
		return self.unit

	def calc_average(self) -> float:
		return sum(self.data) / len(self.data)

	def calc_best(self):
		if self.better == Better.HIGHER:
			return max(self.data)
		else:
			return min(self.data)

	def calc_worst(self):
		if self.better == Better.HIGHER:
			return min(self.data)
		else:
			return max(self.data)