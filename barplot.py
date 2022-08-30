"""Show barplot from given results.

Directories containing the result to compare shall be specified via
command line parameters.

Python >= 3.8.
"""
import argparse
import re
import glob
import os.path as pt
import json
from itertools import cycle

import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np


MAIN_HELP = '''
Show (vertical) barplot given a list of directories containing
 statistics.

Stat files shall be in json format, and shall be named as:
 stats-ins-XX.ext, where X is a digit and .ext is one between: .json,
 .txt.
'''


STAT_FILE_RE = re.compile(r'stats-ins-([0-9]+)\.(txt|json)')
THRESHOLD = 300.
NUM_INSTANCES = 40

DATA_TYPE = dict[str, dict[str, list[float]]]


def gather(directories: list[str], keynames: list[str]) -> DATA_TYPE:
    """Gather all data from the given directories.

    Data is returned in a nested data structure constructed as
    follows: bars['dirname']['key'][0 ... NUM_INSTANCES - 1]
    """
    # For each directory, list values for all keys
    bars: DATA_TYPE = {}

    for directory in directories:
        base_dirname = pt.basename(directory)

        # Fill bars by default with exceeding values
        bars[base_dirname] = {}
        for key in keynames:
            bars[base_dirname][key] = [
                THRESHOLD + 1 for _ in range(NUM_INSTANCES)
            ]

        for filename in glob.glob(pt.join(directory, '*')):
            re_result = STAT_FILE_RE.match(pt.basename(filename))

            # Skip if not a stat file
            if re_result is None:
                continue

            # Extract info
            index = int(re_result.groups()[0]) - 1
            if index >= NUM_INSTANCES:
                print(f'File index is greater than {NUM_INSTANCES}, '
                      'skipping')

            with open(filename) as fin:
                data = json.load(fin)

            for key in keynames:
                bars[base_dirname][key][index] = data[key]
    return bars


def plot(data: DATA_TYPE):
    """(TODO) show given data in a barplot."""
    indeces = np.array([i for i in range(NUM_INSTANCES)])

    # Ticks for smaller graphs
    # ticks = np.array([i for i in range(0, NUM_INSTANCES, 5)])
    ticks = indeces

    # Adjust bar width based on number of categories (directories)
    width = 1
    bar_step = 1 / (len(data) + 1)
    bar_width = np.arange(-width / 2, width / 2, bar_step)[1:]

    # Fix colors for each key, only the first one shall cycle colors
    fig, ax = plt.subplots()
    # Deplete first key
    keys_ex = iter(next(iter(data.values())).keys())
    first_key = next(keys_ex)
    keys_ex = tuple(keys_ex)
    color_cycle = cycle(plt.rcParams["axes.prop_cycle"].by_key()["color"])
    keys_colors = {key: next(color_cycle) for key in keys_ex}

    keys_artists = {key: [] for key in keys_ex}
    first_key_artists = []
    for dir_index, dirname in enumerate(data.keys()):
        # Total value for each bar accounting for all keys
        total_values = [
            sum(data[dirname][k][i] for k in data[dirname].keys())
            for i in range(NUM_INSTANCES)
        ]

        last_key = None
        for key in data[dirname].keys():
            # Stack keys in order
            if last_key is None:
                bottom = None
                color = next(color_cycle)
            else:
                bottom = data[dirname][last_key]
                color = keys_colors[key]
            last_key = key

            barplot = plt.bar(indeces + bar_width[dir_index],
                              data[dirname][key],
                              width=bar_step, bottom=bottom, label=dirname,
                              color=color)

            keys_artists.get(key, first_key_artists).append(barplot)

            # Style bars exceeding the threshold
            for index, total_value in enumerate(total_values):
                if total_value > THRESHOLD:
                    barplot[index].set_alpha(0.4)

    plt.axhline(y=THRESHOLD, color='red')
    plt.xticks(ticks, ticks + 1)
    plt.yscale('log')
    plt.legend([*first_key_artists,
                *[Patch(color=color) for color in keys_colors.values()]],
               [*data.keys(), *keys_ex])

    plt.show()


def main(directories: list[str], keynames: list[str]):
    plot(gather(directories, keynames))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=MAIN_HELP)

    parser.add_argument('directories', metavar='STATS_DIR', nargs='+',
                        help='Directory containing stat files')
    parser.add_argument('-k', '--keyname', action='append',
                        dest='keynames', metavar='KEYNAME',
                        help='Key name in the stat files used as y '
                             'value for the bars in the plot. '
                             'If specified multiple times, the given '
                             'values will be rendered as stacked bars '
                             '(order matters)')
    args = parser.parse_args()

    print(args)

    main(args.directories, args.keynames)
