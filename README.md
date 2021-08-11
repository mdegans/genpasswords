# genpasswords.py

[![codecov](https://codecov.io/gh/mdegans/genpasswords/branch/main/graph/badge.svg?token=FQF8KPFRC9)](https://codecov.io/gh/mdegans/genpasswords)

Is a simple script to generate a `key=value` style file using a template.

An input file should have lines in the format:
```ini
keyname=nbytes:kind
```

where...
* `keyname` is the desired key (and not changed)
* `nbytes` is the length of the password in bytes
* `kind` is either `base64` or `hex`. base64 is a better choice for passwords

Any blank lines or lines starting with `#` are ignored.

## A note on word passwords

Word passwords will be picked from `/usr/share/dict/words` by default, which may
contain offensive words depending on the dictionary. Supply a `--bad-words` file
to disallow certain words or a `--words` file to use an alternative dictionary.
