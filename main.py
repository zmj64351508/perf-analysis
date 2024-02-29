import csv, sys, os
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from fnmatch import fnmatch
import argparse

class ReadableNumber(object):
    def __init__(self, num):
        self.raw = num

    def __str__(self):
        if self.raw >= 1000000000:
            return "%.3fG" % (self.raw / 1000000000)
        if self.raw >= 1000000:
            return "%.3fM" % (self.raw / 1000000)
        if self.raw >= 1000:
            return "%.3fK" % (self.raw / 1000)
        return str(self.raw)

class PlotInteraction(object):
    def __init__(self, fig):
        self.press = False
        self.ctrl = False
        self.fig = fig
        self.fig.canvas.mpl_connect("key_press_event", self.on_key_press(self))
        self.fig.canvas.mpl_connect("key_release_event", self.on_key_release(self))
        self.fig.canvas.mpl_connect("scroll_event", self.on_mouse_scroll(self))

    class on_key_press(object):
        def __init__(self, holder):
            self.holder = holder

        def __call__(self, event):
            if event.key == "control":
                self.holder.ctrl = True

    class on_key_release(object):
        def __init__(self, holder):
            self.holder = holder

        def __call__(self, event):
            if event.key == "control":
                self.holder.ctrl = False

    class on_mouse_scroll(object):
        def __init__(self, holder):
            self.holder = holder

        def __call__(self, event):
            ax = event.inaxes
            x_min, x_max = ax.get_xlim()
            y_min, y_max = ax.get_ylim()
            x_step = (x_max - x_min) / 10
            y_step = (y_max - y_min) / 10
            if event.button == 'up':
                if not self.holder.ctrl:
                    ax.set(xlim=(x_min + x_step, x_max - x_step))
                else:
                    ax.set(ylim=(y_min + y_step, y_max - y_step))
            elif event.button == 'down':
                if not self.holder.ctrl:
                    ax.set(xlim=(x_min - x_step, x_max + x_step))
                else:
                    ax.set(ylim=(y_min - y_step, y_max + y_step))
            self.holder.fig.canvas.draw_idle()


def plot_record(records, start, end, type, fig=None, subplt=None):
    x = range(0, records.get_total_ms(), records.get_interval_ms())
    if not fig:
        fig = plt.figure()
        subplt = fig.add_subplot(1, 1, 1)

    series = records.get_metric_series(type)

    for name in series:
        #print(name, series[name])
        subplt.plot(x, series[name], '-o', label=records.get_raw_path() + ': ' + name, alpha=1.00)
    subplt.legend(loc = 'upper right')
    subplt.yaxis.set_major_formatter(ticker.EngFormatter(unit=''))
    subplt.yaxis.set_major_locator(ticker.MaxNLocator(nbins=16))
    subplt.xaxis.set_major_formatter(ticker.FormatStrFormatter('%d ms'))
    subplt.axvline(x=start, linestyle='--')
    subplt.axvline(x=end, linestyle='--')
    fig.set_figheight(8)
    fig.set_figwidth(15)
    PlotInteraction(fig)
    return fig, subplt


def statistics(records, start, end, type):
    series = records.get_metric_series(type)
    interval = records.get_interval_ms()
    start = int(start / interval)
    if end == 0 or end == -1:
        end = -1
    else:
        end = int(end / interval)
    print("")
    print(records.get_raw_path() + ":")
    for name in series:
        print(name)
        data = series[name][start:end]

        def __post_process(a):
            if args.human:
                a = ReadableNumber(a)
            return a

        print("  max:", __post_process(max(data)))
        print("  min:", __post_process(min(data)))
        print("  avg:", __post_process(sum(data)/len(data)))


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
    def __init__(self, interval, raw_path):
        self.list = []
        self.interval = interval
        self.raw_path = raw_path

    def __str__(self):
        ret = 'interval: %d ms, length: %d' % (self.interval, len(self.list))
        ret += ', '
        for r in self.list:
            ret += r.__str__() + ', '
        return ret[:-2]

    def get_raw_path(self):
        return self.raw_path

    def append(self, record):
        self.list.append(record)

    def get_metric_series(self, filter='*'):
        series = {}
        post_process = lambda a: a
        for r in self.list:
            m = r.get_metrics()
            for m_name in m:
                name = m_name + '_bw'
                if fnmatch(name, filter):
                    if name not in series.keys():
                        series[name] = []
                    # do some data post process
                    if fnmatch(name, '*bus-access*'):
                        post_process = lambda a: a * args.bus_access_width
                    elif fnmatch(name, '*cpu-cycles*'):
                        post_process = lambda a : a * 1000000000
                    series[name].append(post_process(m[m_name].get_bw()))
                name = m_name + '_cnt'
                if fnmatch(name, filter):
                    if name not in series.keys():
                        series[name] = []
                    series[name].append(post_process(m[m_name].get_cnt()))
        if args.normalize:
            for name in series:
                series[name] = [x / max(series[name]) for x in series[name]]
        return series


    def get_metric_series_name(self):
        names = []
        m = self.list[0].get_metrics()
        for m_name in m:
            names.append(m_name + '_bw')
            names.append(m_name + '_cnt')
        return names


    def get_total_ms(self):
        return len(self.list) * self.interval

    def get_interval_ms(self):
        return self.interval


def open_records(file_path):
    record_list = RecordList(args.interval, file_path)

    with open(file_path, newline='') as csvfile:
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

        return record_list

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--list', help='List all available filters.', action='store_true')
    parser.add_argument('-s', '--stats', help='Show statistics.', action='store_true')
    parser.add_argument('-H', '--human', help='Print as human readable.', action='store_true')
    parser.add_argument('-n', '--normalize', action='store_true')
    parser.add_argument('-f', '--filter', help='Filter for data series, which can be called multiple times. Each one will create an individual figure', action='append')
    parser.add_argument('-i', '--input', help='Input file, which can be called multiple times.', action='append')
    parser.add_argument('--interval', help='Time interval for input serials.', type=int, default=100) #ms
    parser.add_argument('--start', help='Start time(ms).', type=int, default=0)
    parser.add_argument('--end', help='End time(ms).', type=int, default=-1)
    parser.add_argument('--bus-access-width', dest='bus_access_width', help='Bus access width for each AXI beat. Known: Tensor G2/RK3588: 128; 8+Gen1: 256', type=int, default=1)
    args = parser.parse_args()

    record_lists = []
    for file_path in args.input:
        record_lists.append(open_records(os.path.normpath(file_path)))
    if args.list:
        for record_list in record_lists:
            print(record_list.get_raw_path() + ':')
            for name in record_list.get_metric_series_name():
                print('  ' + name)
            print('total time: %d ms' % record_list.get_total_ms())
        sys.exit(0)

    if not args.filter or len(args.filter) == 0:
        args.filter = ['*']

    if args.stats:
        for filter in args.filter:
            for record_list in record_lists:
                statistics(record_list, args.start, args.end, filter)
        sys.exit(0)

    for filter in args.filter:
        fig = plt.figure()
        subplt = fig.add_subplot(1, 1, 1)
        for record_list in record_lists:
            plot_record(record_list, args.start, args.end, filter, fig=fig, subplt=subplt)
    plt.show()
    