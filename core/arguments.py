import argparse

parser = argparse.ArgumentParser(description='Reddit bot for reversing gifs')

parser.add_argument('--queue', '-q', action='store_false', default=True, help='Run in database queueing mode')