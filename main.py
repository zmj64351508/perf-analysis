import csv, sys
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from fnmatch import fnmatch

class PlotInteraction(object):
    def __init__(self, fig):
        self.lastx = 0
        self.lasty = 0
        self.press = False
        self.ctrl = False
        self.fig = fig
        self.fig.canvas.mpl_connect("button_press_event", self.on_mouse_press(self))
        self.fig.canvas.mpl_connect("button_release_event", self.on_mouse_release(self))
        self.fig.canvas.mpl_connect("motion_notify_event", self.on_mouse_move(self))
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

    class on_mouse_press(object):
        def __init__(self, holder):
            self.holder = holder
        def __call__(self, event):
            if event.inaxes:  # 判断鼠标是否在axes内
                if event.button == 1:  # 判断按下的是否为鼠标左键1（右键是3）
                    self.holder.press = True
                    self.holder.lastx = event.xdata  # 获取鼠标按下时的坐标X
                    self.holder.lasty = event.ydata  # 获取鼠标按下时的坐标Y

    class on_mouse_move(object):
        def __init__(self, holder):
            self.holder = holder
        def __call__(self, event):
            axtemp = event.inaxes
            if axtemp:
                if self.holder.press:  # 按下状态
                    # 计算新的坐标原点并移动
                    # 获取当前最新鼠标坐标与按下时坐标的差值
                    x = event.xdata - self.holder.lastx
                    y = event.ydata - self.holder.lasty
                    # 获取当前原点和最大点的4个位置
                    x_min, x_max = axtemp.get_xlim()
                    y_min, y_max = axtemp.get_ylim()

                    x_min = x_min - x
                    x_max = x_max - x
                    y_min = y_min - y
                    y_max = y_max - y

                    axtemp.set_xlim(x_min, x_max)
                    axtemp.set_ylim(y_min, y_max)
                    self.holder.fig.canvas.draw()  # 绘图动作实时反映在图像上

    class on_mouse_release(object):
        def __init__(self, holder):
            self.holder = holder
        def __call__(self, event):
            if self.holder.press:
                self.holder.press = False  # 鼠标松开，结束移动

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


def plot_record(records, start, end, type):
    x = range(0, records.get_total_ms(), records.get_interval_ms())
    fig = plt.figure()
    cnt_plt = fig.add_subplot(1, 1, 1)
    series = records.get_metric_series(filter='*'+type)
    for name in series:
        #print(name, series[name])
        cnt_plt.plot(x, series[name], label=name, alpha=1.00)
    cnt_plt.legend(loc = 'upper right')
    cnt_plt.yaxis.set_major_formatter(ticker.EngFormatter(unit=''))
    cnt_plt.yaxis.set_major_locator(ticker.MaxNLocator(nbins=16))
    cnt_plt.xaxis.set_major_formatter(ticker.FormatStrFormatter('%d ms'))
    cnt_plt.axvline(x=start, linestyle='--')
    cnt_plt.axvline(x=end, linestyle='--')
    fig.set_figheight(8)
    fig.set_figwidth(15)
    PlotInteraction(fig)


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


def statistics(records, start, end, type, post_process=lambda a : a):
    series = records.get_metric_series(filter='*' + type)
    interval = records.get_interval_ms()
    print("statistics:")
    for name in series:
        print(name)
        start = int(start/interval)
        if end == 0 or end == -1:
            end = -1
        else:
            end = int(end/interval)
        data = series[name][start:end]
        print("max:", post_process(max(data)))
        print("min:", post_process(min(data)))
        print("avg:", post_process(sum(data)/len(data)))


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

    start = 0
    end = -1
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

    # post_process MB/s
    statistics(record_list, start, end, 'cpu-cycles_bw')
    statistics(record_list, start, end, 'instructions_bw', lambda a: a*1000)
    # 128 for pixel7/rk3588, 256 for xiaomi pad
    statistics(record_list, start, end, 'access*bw', lambda a: a*256/1000000)


    #plot_record(record_list, start, end, 'cnt')
    plot_record(record_list, start, end, 'access*bw')
    plot_record(record_list, start, end, 'cpu-cycles*bw')
    #mplcursors.cursor()
    plt.show()
    