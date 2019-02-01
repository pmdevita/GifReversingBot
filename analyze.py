import json
from pprint import pprint
import operator

with open("stats.json") as f:
    stats = json.load(f)


users_sorted = sorted(stats['users'].items(), key=operator.itemgetter(1))
pprint(users_sorted)

karma = sorted(stats['upvotes'].items(), key=operator.itemgetter(1))
pprint(karma)
