# codetodo

Scans the working dir for text files, and looks for @TODO and @FIXME comments.
It will then print the todos, sorted by file, and type (TODO or FIXME).
It checks for priorities assigned via ! (e.g. @TODO!!:) and will sort accordingly.
Allows to input file name patterns to accept todos from.

## Install
```
pip install codetodo
```

## Usage
```
usage: codetodo [-h] [--allow ALLOW]

optional arguments:
  -h, --help            show this help message and exit
  --allow ALLOW, -a ALLOW
```

## License
MIT License, see LICENSE.txt
