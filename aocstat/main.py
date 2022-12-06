import argparse
import sys


def start(args=sys.argv):
    args = args[1:]
    parser = argparse.ArgumentParser(
        description="Interact with Advent of Code from your terminal."
    )
    args = parser.parse_args(args)

    # display help if empty
    if len(args.__dict__) == 0:
        parser.print_help()


if __name__ == "__main__":
    start()
