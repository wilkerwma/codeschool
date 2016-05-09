import argparse
import markio


# Create an argument parser.
parser = argparse.ArgumentParser('markio')
parser.add_argument(
    '--validate', '-v',
    action='store_true',
    help='validate input file'
)
parser.add_argument('input', help='input Markio file')


def main(args=None):
    args = parser.parse_args(args)

    try:
        source = markio.parse(args.input)
    except SyntaxError as ex:
        print('Error: ' + str(ex))
        print('Your file is invalid!')
        raise SystemExit(not bool(args.validate))

    if args.validate:
        print('Your markio source is valid!')
        return

if __name__ == '__main__':
    main(['-h'])