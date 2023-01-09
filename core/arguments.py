import argparse

parser = argparse.ArgumentParser(description='Reddit bot for reversing gifs')

parser.add_argument('--cutoff', '-c', action='store', default=None, help="Integer, how many days old requests to allow")
parser.add_argument('--queue', '-q', action='store_false', default=True, help='Run in database queueing mode')