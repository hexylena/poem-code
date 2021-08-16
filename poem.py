#!/usr/bin/env python3
import argparse
import pprint
import math
import random
import copy
import os
import re
import logging
import sys

logging.basicConfig(level=logging.INFO)
if "SEED" in os.environ:
    random.seed(int(os.environ["SEED"]))


poems_original = {
    "jabberwocky": """
’Twas brillig, and the slithy toves

     Did gyre and gimble in the wabe:

All mimsy were the borogoves,

     And the mome raths outgrabe.
""",
    "bodington": """
Have you never known
A glass-bottomed day
When your minutes can be seen
Flowing beneath you
In every direction
But the one you mean?

Have you never known
A winterproof night
When wrong feels right
When the heart's chill
Is a matter of will

And mother's pride
Is safe inside
An envelope of ice
And doesn't even hear
A cock crow thrice
    """,
    "yours": """
The life that I have
Is all that I have
And the life that I have
Is yours.

The love that I have
Of the life that I have
Is yours and yours and yours.

A sleep I shall have
A rest I shall have
Yet death will be but a pause.

For the peace of my years
In the long green grass
Will be yours and yours and yours.
    """,
    "degaul": """
 Is De Gaulle's prick
Twelve inches thick?
Can it rise
To the size
Of a proud flag-pole?
And does the sun shine
From his arse-hole?
    """,
    "middle": """
Oh baby
Why don't you just meet me in the middle
I'm losing my mind just a little
So why don't you just meet me in the middle
In the middle
    """,
}


def fix(k, v):
    v = v.replace("\n", " ")
    v = v.lower()
    v = re.sub("[^a-z -]", "", v)
    normal = re.sub(" +", " ", v).strip()
    yield k, normal.split()
    if "-" in normal:
        yield f"{k}.alt", normal.replace("-", " ", 1).split()


poems = {}
for (k, v) in poems_original.items():
    for (k2, v2) in fix(k, v):
        poems[k2] = v2

# __import__('pprint').pprint(poems)


def codewords(poem, n=5):
    return random.sample(list(enumerate(poems[poem], start=1))[0:26], 5)


def pad(msg, l):
    msg = msg.replace(" ", "")
    _, msgmod = divmod(len(msg), l)
    if msgmod != 0:
        toadd = l - msgmod
    else:
        toadd = 0

    msg += toadd * "X"
    return msg


def split(msg, length):
    out = []
    for i in range(0, len(msg), length):
        out.append(list(msg[i : i + length]))
    return out


def debug(*args):
    logging.debug(pprint.pformat(args))


def _decode(msg, poem="jabberwocky"):
    msg = msg.replace(" ", "")
    indicator, msg = (msg[0:5], msg[5:])
    indicator_words = [ord(x.lower()) - 96 for x in indicator]
    debug(indicator, indicator_words)
    indicator_words = [poems[poem][x - 1] for x in indicator_words]
    debug(indicator, indicator_words)
    ordering = alphabetize_codeword("".join(indicator_words))
    sorder = list(range(1, len(ordering) + 1))

    w = len(msg) / len(ordering)
    debug("z", msg, w)
    if int(w) != w:
        # The message is longer than expected, need to trim.
        w = math.floor(w)
        msg = msg[0 : w * len(ordering)]
    w = int(w)

    # Last group all X stripping
    lastgroup = msg[(w - 1) * len(ordering) :]
    if all(x == "X" for x in lastgroup):
        w -= 1
        msg = msg[0 : w * len(ordering)]

    debug("z", msg, w)
    msg = transpose([sorder] + transpose(split(msg, w)))
    msg = sorted(msg, key=lambda x: ordering.index(x[0]))
    msg = transpose(msg)

    out = "".join(["".join(x) for x in msg[1:]])
    return out


def alphabetize_codeword(word):
    fixed = [None] * len(word)
    o = 1
    for i in range(26):
        k = chr(i + 97)
        for p, c in enumerate(word):
            if k == c:
                fixed[p] = o
                o += 1
    return fixed


def transpose(matrix):
    return list(map(list, zip(*matrix)))


def _encode(msg, poem="jabberwocky"):
    indicator_unparse = codewords(poem)
    # We could select the five words THE WABE TOVES TWAS MOME, which are at positions 4, 13, 6, 1, and 21 in the poem, and describe them with the corresponding indicator group DMFAU.
    # indicator_unparse = [(4, 'the'), (13, 'wabe'), (6, 'toves'), (1, 'twas'), (21, 'mome')]

    indicator = "".join([chr(96 + x[0]) for x in indicator_unparse]).upper()
    indicator_words = [x[1] for x in indicator_unparse]
    debug(indicator_unparse, indicator, indicator_words)
    ordering = alphabetize_codeword("".join(indicator_words))

    msg = pad(msg, len(ordering))
    v = [ordering] + split(msg, len(ordering))

    tarr = transpose(v)

    tarr = sorted(tarr, key=lambda x: x[0])
    out = ["".join(x[1:]) for x in tarr]
    out = indicator + "".join(out)
    return out


def _space(msg):
    for i, x in enumerate(msg):
        if i > 0 and i % 5 == 0:
            yield " "
        yield x


def space(msg):
    return "".join(_space(msg))


def encode(msg, poem, rounds=2):
    for i in range(rounds):
        msg = _encode(msg, poem=poem)
        debug("+", i, msg)
    return msg


def decode(msg, poem, rounds=2):
    for i in range(rounds):
        debug("-", rounds - i - 1, msg)
        msg = _decode(msg, poem=poem)
    return msg


def prepmsg(msg):
    msg = msg.upper()
    msg = re.sub("[^A-Z]", "", msg)
    return msg


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="En/decode using poem code")
    parser.add_argument("message")
    parser.add_argument(
        "-a",
        type=str,
        choices=("enc", "dec", "dec-test", "fixed", "selftest", "print-poems"),
        help="Action, encrypt or decrypt",
    )
    parser.add_argument("-p", type=str, choices=poems.keys(), help="Poem")
    parser.add_argument("-r", type=int, default=2, help="Rounds")
    parser.add_argument("-s", action="store_true", help="Space output")
    args = parser.parse_args()

    if args.a == "enc":
        m = prepmsg(args.message)
        print(m)
        enc = encode(m, args.p, rounds=args.r)
        if args.s:
            print(space(enc))
        else:
            print(enc)
        print(decode(enc, args.p, rounds=args.r))
    elif args.a == "dec":
        m = prepmsg(args.message)
        print(decode(m, args.p, rounds=args.r))
    elif args.a == "dec-test":
        m = prepmsg(args.message)
        for poem in poems.keys():
            print(poem)
            try:
                print(decode(m, poem, rounds=args.r))
            except:
                print("Error")
    elif args.a == "selftest":
        msg = prepmsg(args.message)
        for p in poems.keys():
            for i in range(100):
                print(f"==============={p}/{i} ====")
                random.seed(i)
                enc = encode(msg, p, rounds=2)
                dec = decode(enc, p, rounds=2)
                print(enc)
                print(dec)
                if dec.rstrip("X") != msg:
                    print(i, enc)
                    print(i, dec)
                    sys.exit()
    elif args.a == "print-poems":
        for k, v in poems_original.items():
            print(f"==== {k} ====")
            print(v)
