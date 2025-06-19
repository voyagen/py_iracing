import argparse
from .client import iRacingClient
from .constants import VERSION

def main() -> None:
    """
    The main entry point for the py_iracing command-line interface.
    """
    parser = argparse.ArgumentParser(description='A command-line interface for the py_iracing library.')
    parser.add_argument('-v', '--version', action='version', version=f'py_iracing {VERSION}', help='show version and exit')
    parser.add_argument('--test', help='use test file as irsdk mmap')
    parser.add_argument('--dump', help='dump irsdk mmap to file')
    parser.add_argument('--parse', help='parse current irsdk mmap to file')
    args = parser.parse_args()

    ir = iRacingClient()
    ir.startup(test_file=args.test, dump_to=args.dump)

    if args.parse:
        ir.parse_to(args.parse)

if __name__ == '__main__':
    main()