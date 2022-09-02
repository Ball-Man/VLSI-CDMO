"""Convert a directory of instances into json format.

A naive upper bound for the height is computed using a stripe based
first fit method. Such results are also encoded into the json instance.
This could be seen as a form of preprocessing, but still, it is a
way to improve the results.

Python >= 3.8.
"""
import os
import os.path as pt
import sys
import glob
import json

from first_fit import get_max_height


def main(dirname: str):
    # Build new directory
    newdirname = f'{dirname}_json'
    os.makedirs(newdirname, exist_ok=True)

    # Build new instance files
    for instance in glob.glob(pt.join(dirname, '*')):
        # Build corresponding dictionary
        with open(instance) as fin:
            instance_lines = fin.read().splitlines()

        width = int(instance_lines[0])
        n = int(instance_lines[1])
        instance_lines = instance_lines[2:]
        circuits = list(map(lambda x: [int(s) for s in x.strip().split(' ')],
                            instance_lines))
        instance_dict = {
            'width': width,
            'n': n,
            'circuits': circuits,
            'max_height': get_max_height(width, circuits)
        }

        # Write new file
        newinstancename = f'{pt.basename(pt.splitext(instance)[0])}.json'
        with open(pt.join(newdirname, newinstancename), 'w') as fout:
            json.dump(instance_dict, fout)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Please provide a directory', file=sys.stderr)
        sys.exit()

    filename = sys.argv[1]
    main(filename)
