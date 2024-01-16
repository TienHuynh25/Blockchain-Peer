#!/usr/bin/python3

# Inspiration https://docs.python.org/3/library/hashlib.html
import hashlib

m = hashlib.sha256()
m.update(b"Nobody inspects")
m.update(b" the spammish repetition")
m.digest()

# as a string
print(m.hexdigest())

# Is it the same...? Definitely not!
m = hashlib.sha256()
m.update(b" the spammish repetition")
m.update(b"Nobody inspects")
m.digest()

# as a string
print(m.hexdigest())
