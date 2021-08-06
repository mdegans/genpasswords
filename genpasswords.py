#!/usr/bin/python3

# Copyright 2021 Michael de Gans

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


"""
Generate a key=value file using a template. See README.md for the format and
`passwords.ini.in` for an example.
"""
import argparse
import os
import secrets
import sys

from typing import (
    TextIO,
    Union,
    Iterable,
)

THIS_DIR = os.path.dirname(os.path.realpath(__file__))


def process_line(line: str, eol="\n") -> str:
    """
    A line is in the format name=nbytes:kind where `name` is the key, nbytes is
    the number of bytes passed to `secret` and the kind is the kind of random
    number desired.

    Supported kinds are are hex,

    >>> line = process_line('somename=16:hex')
    >>> line.split('=')[0]
    'somename'
    >>> len(line.split('=')[1].strip())
    32

    base64,

    >>> line = process_line('somename=12:base64')
    >>> line.split('=')[0]
    'somename'
    >>> len(line.split('=')[1].strip())
    16

    """
    name, params = line.split("=")
    nbytes = int(params.split(":")[0])
    kind = params.split(":")[1].strip()
    if kind == "hex":
        password = secrets.token_hex(nbytes)
    elif kind == "base64":
        password = secrets.token_urlsafe(nbytes)
    else:
        raise RuntimeError(f"{kind} is not 'hex' or 'base64'")
    return f"{name}={password}{eol}"


def gen_passwords(i: Union[str, Iterable[str]], o: Union[str, TextIO]):
    # open any filenames as file objects
    if isinstance(i, str):
        with open(i, "r") as i:
            return gen_passwords(i, o)
    if isinstance(o, str):
        with open(o, "w") as o:
            return gen_passwords(i, o)
    for line in i:
        # ignore empty lines
        if not line.strip():
            o.write(line)
            continue
        # ignore comment lines
        if line.startswith("#"):
            o.write(line)
            continue
        # write the processed line
        o.write(process_line(line))


if __name__ == "__main__":
    import argparse
    import doctest

    # run tests first.
    failed, passed = doctest.testmod()
    if failed:
        sys.exit(failed)

    ap = argparse.ArgumentParser(
        description="Generate a `passwords.ini` from a `passwords.ini.in`",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    ap.add_argument(
        "-i",
        help="template in file",
        default=os.path.join(
            THIS_DIR,
            "passwords.ini.in",
        ),
    )
    ap.add_argument(
        "-o",
        help="out passwords file",
        default=os.path.join(THIS_DIR, "passwords.ini"),
    )

    gen_passwords(**vars(ap.parse_args()))
