# genpasswords.py

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