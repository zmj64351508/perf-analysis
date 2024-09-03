import os, sys, time
from adbutils import adb

def get_layers(dev):
    content = dev.shell('dumpsys SurfaceFlinger')
    layers = []
    for line in content.split('\n'):
        if 'Output' in line:
            layers.append(line[line.find('(')+1:-1])
    return layers


def get_top_layer(dev):
    return get_layers(dev)[0]

    
def get_layer_actual_present_timestamp(dev, layer):
    content = dev.shell('dumpsys SurfaceFlinger --latency "%s"' % layer)
    content = content.split('\n')
    refresh_rate = round(1e9 / int(content[0]))
    latency_list = []
    for line in content[1:-1]:
        data = line.split()
        # DesiredPresentTime, ActualPresentTime, FinishTime
        # Use ActualPresentTime
        latency_list.append(int(data[1]))
    return refresh_rate, latency_list


def calc_frame_rate(timestamp_list, start_timestamp):
    if len(timestamp_list) == 0:
        return 0

    frame_count = 0
    if start_timestamp < timestamp_list[0]:
        start_timestamp = timestamp_list[0]
    end_timestamp = timestamp_list[-1]

    for timestamp in timestamp_list:
        if timestamp <= start_timestamp or timestamp == 0:
            continue
        frame_count += 1

    interval = end_timestamp - start_timestamp
    #print("interval: %f, start: %d, end: %d" % (interval / 1e9, start_timestamp, end_timestamp))

    if interval > 0:
        return int(1e9 * float(frame_count) / float(interval))
    else:
        return 0


def fps_sf_latency(dev):
    layer = get_top_layer(dev)
    last_ts = 0
    refresh_rate, ts_list = get_layer_actual_present_timestamp(dev, layer)
    last_ts = ts_list[-1]
    while True:
        layer = get_top_layer(dev).lstrip('[').rstrip(']')
        timestamp = device_date(dev)
        refresh_rate, ts_list = get_layer_actual_present_timestamp(dev, layer)
        print(f'{timestamp}, 0, {layer}, {calc_frame_rate(ts_list, last_ts)}')
        sys.stdout.flush()
        last_ts = ts_list[-1]
        time.sleep(1)


def clear_timestats(dev):
    dev.shell('dumpsys SurfaceFlinger --timestats -disable -clear')


def enable_timestats(dev):
    dev.shell('dumpsys SurfaceFlinger --timestats -enable')


def disable_timestats_and_dump(dev):
    return dev.shell('dumpsys SurfaceFlinger --timestats -disable -dump -clear')


def capture_timestats(dev, interval):
    return dev.shell('dumpsys SurfaceFlinger --timestats -enable && sleep %f && dumpsys SurfaceFlinger --timestats -disable -dump -clear' % interval)


def device_date(dev):
    return dev.shell(r'date +"%s.%N"')


def timestats_data(line):
    return line[line.find('=')+1:].strip()


def fps_sf_timestats(dev):
    clear_timestats(dev)
    while True:
        enable_timestats(dev)
        time.sleep(1)
        date = device_date(dev)
        uid = 0
        layer = "none"
        fps = 0
        content = disable_timestats_and_dump(dev)
        for line in content.split('\n'):
            if line.startswith('uid'):
                uid = int(timestats_data(line))
            elif line.startswith('layerName '):
                layer = timestats_data(line)
                #print(layer)
            elif line.startswith('averageFPS '):
                fps = float(timestats_data(line))
                break
        print(f'{date}, {uid}, {layer}, {fps}')
        sys.stdout.flush()



if __name__ == '__main__':
    dev = adb.device()
    print('timestamp, uid, layer, fps')
    #fps_sf_latency(dev)
    fps_sf_timestats(dev)

    