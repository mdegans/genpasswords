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
import functools
import os
import secrets
import sys

try:
    from tqdm import tqdm
except ImportError:  # pragma no cover
    tqdm = None  # pragma no cover

from typing import (
    FrozenSet,
    TextIO,
    Union,
    Iterable,
    Tuple,
    Iterator,
)

THIS_DIR = os.path.dirname(os.path.realpath(__file__))
DEFAULT_DICTIONARY = "/usr/share/dict/words"
DEFAULT_BAD_WORDS = (
    "igger",
    "adolf",
    "hitler",
)



@functools.lru_cache(maxsize=None)
def get_words(
    dictionary: Union[str, Tuple[str, ...], Iterator[str]] = DEFAULT_DICTIONARY,
    bad_words: Union[str, Tuple[str, ...]] = DEFAULT_BAD_WORDS,
) -> Tuple[str, ...]:
    """
    Get a frozenset of words from a file of line separated words.

    Args:
        dictionary: filename or Iterable of line separated words.
            strings that are not .alpha() are skipped
        bad_words: filename or Iterable of forbidden words (or partial matches)

    Returns:
        FrozenSet[str]: [description]

    Example Usage:

    Any hashable (immutable) iterable can be used, not just FrozenSet.

    >>> a = get_words(('bigger', 'tigger', 'expected'), ('igger',))
    >>> a
    ('expected',)

    Repeated calls with the same arguments return a cached result.
    (to avoid repeated parsing of files and contents)

    >>> b = get_words(('bigger', 'tigger', 'expected'), ('igger',))
    >>> b is a
    True
    >>> c = get_words(frozenset(('bigger', 'tigger', 'expected')), frozenset(('igger',)))
    >>> c is a
    False
    >>> c == a
    True
    """
    # load bad_words as a set of str
    if isinstance(bad_words, str):
        with open(bad_words) as f:
            print(f"Loading bad words from: {bad_words}")
            return get_words(
                dictionary, (word.strip().lower() for word in bad_words)  # type: ignore
            )

    # load the dictionary if any
    if isinstance(dictionary, str):
        print(f"Parsing words from: {dictionary}")
        with open(dictionary) as f:
            if tqdm:
                f = tqdm(f, unit=" words")
            dictionary = (l.strip() for l in f)
            return get_words(dictionary, bad_words)

    # strip any whitespace around words
    dictionary = (word.strip() for word in dictionary)

    # we want only alpha, lowercase words
    dictionary = (word.lower() for word in dictionary if word.isalpha())

    # we want to filter out any words containing bad words
    if bad_words:
        bad_words = tuple(bad_words)
        dictionary = (
            word
            for word in dictionary
            if not any(bad in word for bad in bad_words)
        )

    # remove any duplicates and return a tuple
    return tuple(set(dictionary))


def word_password(
    n_words: int,
    dictionary: Union[str, Tuple[str, ...], Iterator[str]] = DEFAULT_DICTIONARY,
    bad_words: Union[str, Tuple[str, ...]] = DEFAULT_BAD_WORDS,
):
    try:
        return "".join(
            secrets.choice(get_words(dictionary, bad_words)).capitalize()  # type: ignore
            for _ in range(n_words)
        )
    except FileNotFoundError as e:
        raise FileNotFoundError(f"`--words` file not found: {e.filename}") from e
    except IndexError:
        raise RuntimeError(f"No valid words found in: {dictionary}")


def process_line(
    line: str,
    eol="\n",
    dictionary: Union[str, Tuple[str, ...], Iterator[str]] = DEFAULT_DICTIONARY,
    bad_words: Union[str, Tuple[str, ...]] = DEFAULT_BAD_WORDS,
) -> str:
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
    name, params = line.strip().split("=")
    nbytes = int(params.split(":")[0])
    kind = params.split(":")[1].strip()
    if kind == "hex":
        password = secrets.token_hex(nbytes)
    elif kind == "base64":
        password = secrets.token_urlsafe(nbytes)
    elif kind == "words":
        password = word_password(nbytes, dictionary, bad_words)
    else:
        raise RuntimeError(f"{kind} is not 'hex', 'words' or 'base64'")
    return f"{name}={password}{eol}"


def gen_passwords(
    i: Union[str, Iterable[str]],
    o: Union[str, TextIO],
    dictionary: Union[str, Tuple[str, ...], Iterator[str]] = DEFAULT_DICTIONARY,
    bad_words: Union[str, Tuple[str, ...]] = DEFAULT_BAD_WORDS,
):
    # open any filenames as file objects
    if isinstance(i, str):
        with open(i, "r") as i:
            return gen_passwords(i, o, dictionary, bad_words)
    if isinstance(o, str):
        with open(o, "w") as o:
            return gen_passwords(i, o, dictionary, bad_words)
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
        o.write(process_line(line, dictionary=dictionary, bad_words=bad_words))


def cli_main(args=None):
    import argparse
    import doctest

    # run tests first.
    failed, _ = doctest.testmod()
    if failed:
        sys.exit(failed)  # pragma no cover

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
    ap.add_argument(
        "--words",
        dest="dictionary",
        help="path to words file for word passwords",
        default=DEFAULT_DICTIONARY,
    )
    ap.add_argument(
        "--bad-words",
        help="path to a bad words file to exclude from --words",
        default=None,
    )

    gen_passwords(**vars(ap.parse_args(args)))


if __name__ == "__main__":
    cli_main()  # pragma no cover
