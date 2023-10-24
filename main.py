import csv, sys
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from fnmatch import fnmatch

def plot_record(records, start, end, type):
    x = range(0, records.get_total_ms(), records.get_interval_ms())
    fig = plt.figure()
    cnt_plt = fig.add_subplot(1, 1, 1)
    series = records.get_metric_series(filter='*'+type)
    for name in series:
        print(name, series[name])
        cnt_plt.plot(x, series[name], label=name, alpha=1.00)
    cnt_plt.legend(loc = 'upper right')
    cnt_plt.yaxis.set_major_formatter(ticker.EngFormatter(unit=''))
    cnt_plt.yaxis.set_major_locator(ticker.MaxNLocator(nbins=16))
    cnt_plt.xaxis.set_major_formatter(ticker.FormatStrFormatter('%d ms'))
    cnt_plt.axvline(x=start, linestyle='--')
    cnt_plt.axvline(x=end, linestyle='--')
    fig.set_figheight(8)
    fig.set_figwidth(15)

    
def plot_estimate_bw(records, interval, start, end, name):
    estimate = []
    length = len(records[name])
    x = range(0, length * interval, interval)
    for i in range(length):
        t1_old = records['raw-inst-retired_util'][i]*1000/interval
        t2_old = records[name+'_util'][i]*1000/interval
        t1_new = 1 / 1.27 * t1_old
        bw_old = records[name][i]
        d = t2_old * bw_old
        t2_new = t1_old + t2_old - t1_new
        bw_new = d / t2_new
        estimate.append(bw_new)

    plt.plot(x, estimate, label='estimate', alpha=1.00)
    plt.plot(x, records[name], label='origin', alpha=1.00)

    plt.legend(loc = 'upper right')
    plt.gca().yaxis.set_major_formatter(ticker.EngFormatter(unit=''))
    plt.gca().yaxis.set_major_locator(ticker.MaxNLocator(nbins=16))
    plt.gca().xaxis.set_major_formatter(ticker.FormatStrFormatter('%d ms'))
    plt.gcf().set_figheight(8)
    plt.gcf().set_figwidth(15)
    plt.gca().axvline(x=start, linestyle='--')
    plt.gca().axvline(x=end, linestyle='--')



def plot_percent_sum(records, start, end, type, deno, nume):
    x = range(0, records.get_total_ms(), records.get_interval_ms())
    fig = plt.figure()
    sum_plt = fig.add_subplot(1, 1, 1)

    data = records.get_percent_series(deno, nume, type)

    label_name = type + ':'
    for name in nume:
        label_name += ' %s +' % name
    label_name = label_name[:-1]

    sum_plt.plot(x, data, label=label_name, alpha=1.00)

    sum_plt.legend(loc = 'upper right')
    sum_plt.yaxis.set_major_formatter(ticker.PercentFormatter())
    sum_plt.xaxis.set_major_formatter(ticker.FormatStrFormatter('%d ms'))
    sum_plt.axvline(x=start, linestyle='--')
    sum_plt.axvline(x=end, linestyle='--')
    fig.set_figheight(8)
    fig.set_figwidth(15)


def statistics(records, interval, start=0, end=0):
    print('from %d ms to %d ms'%(start, end))
    for nouse, name in enumerate(records):
        total = 0
        time_ms = 1
        record = records[name]
        if end == 0:
            total = sum(record[int(start/interval):])
            length = len(record) - int(start/interval)
        else:
            total = sum(record[int(start/interval):int(end/interval)])
            length = int(end/interval) - int(start/interval)
        print(name + ' total: %.2f' % total)
        print(name + ' max: %.2f' % max(record))
        print(name + ' avg: %.2f' % (total / length))


class Metric(object):
    def __init__(self, cnt, bw):
        self.cnt = cnt
        self.bw = bw

    def __str__(self):
        return r'{cnt: %d, bw: %d}' % (self.cnt, self.bw)

    def get_bw(self):
        return self.bw

    def get_cnt(self):
        return self.cnt


class Record(object):
    def __init__(self):
        self.metric = {}

    def __str__(self):
        ret = ''
        for m in self.metric:
            ret += '' + m + ': ' + self.metric[m].__str__() + ', '
        return ret[:-2]

    def add_metric(self, name, val):
        self.metric[name] = val

    def get_metric(self, name):
        return self.metric[name]

    def get_metrics(self):
        return self.metric


class RecordList(object):
    def __init__(self, interval):
        self.list = []
        self.interval = interval

    def __str__(self):
        ret = 'interval: %d ms, length: %d' % (self.interval, len(self.list))
        ret += ', '
        for r in self.list:
            ret += r.__str__() + ', '
        return ret[:-2]

    def append(self, record):
        self.list.append(record)

    def get_metric_series(self, filter='*'):
        series = {}
        for r in self.list:
            m = r.get_metrics()
            for m_name in m:
                name = m_name + '_bw'
                if fnmatch(name, filter):
                    if name not in series.keys():
                        series[name] = []
                    series[name].append(m[m_name].get_bw())
                name = m_name + '_cnt'
                if fnmatch(name, filter):
                    if name not in series.keys():
                        series[name] = []
                    series[name].append(m[m_name].get_cnt())
        return series


    def get_percent_series(self, deno, nume, type):
        data = []
        for r in self.list:
            nume_val = 0
            for name in nume:
                if type == 'bw':
                    nume_val += r.get_metric(name).get_bw()
                else:
                    nume_val += r.get_metric(name).get_cnt()
            if type == 'bw':
                data.append(nume_val / r.get_metric(deno).get_bw() * 100)
            else:
                data.append(nume_val / r.get_metric(deno).get_cnt() * 100)
        return data


    def get_total_ms(self):
        return len(self.list) * self.interval

    def get_interval_ms(self):
        return interval


if __name__ == '__main__':

    start = 600
    end = 5400
    interval = 100 # ms

    record_list = RecordList(interval)

    with open(sys.argv[1], newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        record = None
        for row in reader:
            # skip useless rows
            if row[0] == 'Performance counter statistics':
                record = Record()
                continue
            elif row[0] == 'Total test time':
                record_list.append(record)
                continue

            if len(row) < 5:
                continue

            cnt = int(row[0])
            name = row[1]
            bw = float(row[2])
            unit = row[3]
            if unit == 'G/sec':
                bw *= 1000 * 1000 * 1000
            elif unit == 'M/sec':
                bw *= 1000 * 1000

            record.add_metric(name, Metric(cnt, bw))

    #statistics(records, interval, start, end)
    plot_record(record_list, start, end, 'cnt')
    plot_record(record_list, start, end, 'bw')
    plot_percent_sum(record_list, start, end, 'bw', 'raw-inst-retired', ('raw-mem-access-rd', 'raw-mem-access-wr'))
    plot_percent_sum(record_list, start, end, 'bw', 'raw-inst-retired', ('raw-bus-access-rd','raw-bus-access-wr'))
    #plot_estimate_bw(records, interval, start, end, 'raw-bus-access-rd')
    #plot_estimate_bw(records, interval, start, end, 'raw-bus-access-wr')
    plt.show()
    