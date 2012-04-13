#!/usr/bin/python

import sys

f = open("foo.gz", "rb")
data = f.read(1)
while data:
    sys.stdout.write("%02x" % ord(data))
    data = f.read(1)
print

