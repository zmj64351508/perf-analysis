import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.dates as mdates
from datetime import datetime
import argparse
import chardet

def wrap_text(text, width):
    words = text.split(' ')
    wrapped_lines = []
    line = ''

    for word in words:
        if len(line) + len(word) + 1 <= width:
            if line:
                line += ' '
            line += word
        else:
            if len(word) > width:  # 单词本身就超过宽度，进行截断
                while len(word) > width:
                    wrapped_lines.append(word[:width])
                    word = word[width:]
                line = word
            else:
                wrapped_lines.append(line)
                line = word

    if line:  # 追加最后一行
        wrapped_lines.append(line)

    return '\n'.join(wrapped_lines)


def plot(df):
    local_timezone = datetime.now().astimezone().tzinfo
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s', utc=True).dt.tz_convert(local_timezone)

    plt.figure(figsize=(10, 6))
    plt.plot(df['timestamp'], df['fps'], marker='o', linestyle='-', label='fps')

    # 在layer发生变化时标注
    for i in range(0, len(df)):
        if df['layer'].iloc[i] == 'none':
            continue
        if i == 0 or (i > 1 and df['layer'].iloc[i] != df['layer'].iloc[i-1]):
            text = wrap_text(df["layer"].iloc[i], width=15)
            plt.annotate(text, 
                         (df['timestamp'].iloc[i], df['fps'].iloc[i]),
                         textcoords="offset points", xytext=(0,20), ha='center', color='red',
                         arrowprops=dict(arrowstyle="->", connectionstyle="arc3", color="red"))

    plt.xlabel('Timestamp')
    plt.ylabel('FPS')
    plt.grid(True) 
    date_format = mdates.DateFormatter('%H:%M:%S.%f')
    plt.gcf().gca().xaxis.set_major_formatter(date_format)
    plt.xticks(rotation=45)
    plt.legend()
    plt.show()

def main():
    parser = argparse.ArgumentParser(description="Plot FPS over Time from a CSV file or stdin.")
    parser.add_argument('-i', '--input', type=str, help="Path to the CSV file.")
    args = parser.parse_args()

    if args.input:
        with open(args.input, 'rb') as file:
            raw_data = file.read(10000)
            result = chardet.detect(raw_data)

        df = pd.read_csv(args.input, encoding=result['encoding'], skipinitialspace=True)

        print("mean:", df['fps'].mean())
        print("std:", df['fps'].std())
        plot(df)

if __name__ == "__main__":
    main()
