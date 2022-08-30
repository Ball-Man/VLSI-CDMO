"""Show barplot from given results.

Directories containing the result to compare shall be specified via
command line parameters.

Python >= 3.8.
"""
import argparse


MAIN_HELP = '''
Show (vertical) barplot given a list of directories containing
 statistics.

Stat files shall be in json format, and shall be named as:
 stats-ins-XX.ext, where X is a digit and .ext is one between: .json,
 .txt.
'''


def main(*args):
	pass


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
