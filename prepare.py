from adbutils import adb
import time

def set_scaling_governors(governor, start, end):
    for i in range(start, end + 1):
        dev.shell("echo %s > /sys/bus/cpu/devices/cpu%d/cpufreq/scaling_governor" % (governor, i))

def set_max_freq(freq, start, end):
    for i in range(start, end + 1):
        dev.shell("echo %s > /sys/bus/cpu/devices/cpu%d/cpufreq/scaling_max_freq" % (freq, i))

def show_cpu_status(start, end):
    for i in range(start, end + 1):
        print("cpu%d status: " % i)
        print("  governor:", dev.shell("cat /sys/bus/cpu/devices/cpu%d/cpufreq/scaling_governor" % i))
        print("  frequency:", dev.shell("cat /sys/bus/cpu/devices/cpu%d/cpufreq/scaling_cur_freq" % i))
        print("  max frequency:", dev.shell("cat /sys/bus/cpu/devices/cpu%d/cpufreq/scaling_max_freq" % i))
        print("  online:", dev.shell("cat /sys/bus/cpu/devices/cpu%d/online" % i))

def set_cpu_online(start, end, online):
    for i in range(start, end + 1):
        dev.shell("echo %d > /sys/bus/cpu/devices/cpu%d/online" % (online, i))

if __name__ == "__main__":
    print(adb.device_list())
    dev = adb.device()
    cpu_min = 0
    cpu_max = 7
    cpu_big_min = 4
    cpu_big_max = cpu_max
    cpu_little_min = cpu_min
    cpu_little_max = 3
    set_scaling_governors("performance", cpu_min, cpu_max)
    set_cpu_online(cpu_min, cpu_max, 1)
    set_max_freq(500000, cpu_min, cpu_max)
    #set_cpu_online(cpu_big_min, cpu_big_max, 0)
    #set_cpu_online(cpu_min, cpu_min, 0)
    #set_cpu_online(cpu_little_min, cpu_little_max, 0)
    #set_cpu_online(cpu_big_min, cpu_big_min+2, 0)
    #set_cpu_online(0, 3, 1)
    #set_max_freq(1000000, 0, 7)
    #set_cpu_online(4, 7, 0)

    show_cpu_status(cpu_min, cpu_max)
    #i = 0
    #while True:
    #    print("set max freq: %d" % i, end='\r')
    #    set_max_freq(1000000, 0, 7)
    #    time.sleep(0.5)
    #    i = i + 1
