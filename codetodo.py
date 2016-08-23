#! /usr/bin/env python

from __future__ import print_function
import subprocess
import os
import sys
import re
from tabulate import tabulate
from termcolor import colored
import argparse
import time
from rglob import rglob
from fnmatch import fnmatch
import multiprocessing as mp
import mimetypes

if sys.stdout.encoding == "UTF-8":
   CHECK_MARK = u"\u2714".encode("utf-8")
   CROSS_MARK = u"\u2718".encode("utf-8")
else:
   CHECK_MARK = "[OK]"
   CROSS_MARK = "[  ]"


keywords = [
    "@TODO",
    "@FIXME",
]

blacklist = [
    "*.swp",
    "*cache"
]

PROC_COUNT = mp.cpu_count()

def glob_pattern(p):
    return rglob(os.getcwd(), p)

    # for f in files:
        # print(f)

    # return files

if sys.stdout.isatty():
    red = lambda s: colored(s, "red", attrs=["bold"])
    green = lambda s: colored(s, "green")
    yellow = lambda s: colored(s, "yellow", attrs=["bold"])
    bold = lambda s: colored(s, attrs=["bold"])
else:
    identity = lambda s:s
    red = identity
    green = identity
    yellow = identity
    bold = identity

def mimefilter(r):
    mime = mimetypes.guess_type(r)
    return mime[0] and "text" in mime[0]

def find_in_file(filename):
    # print("find_in_file", filename)
    with open(filename, "r") as f:
        lines = f.read().strip().split("\n")

    matched = []
    for i, l in enumerate(lines):
        if any(k in l for k in keywords):
            matched.append( ( filename, i+1, l ) )
    return matched
    # return filter(lambda l: any(k in l for k in keywords), lines)

def get_grep(args, pool):
    files = []
 
    if len(args.allow) > 0:
        results = pool.map(glob_pattern, args.allow)
        
        for r in results:
            for f in r:
                files.append(f)

    else:
        for dirpath, dirname, filenames in os.walk(os.getcwd()):
            for f in filenames:
                files.append(os.path.join(dirpath, f))


    files = filter(lambda f: not any(fnmatch(f, b) for b in blacklist), files)
    files = filter(mimefilter, files)

    
    # print(len(files))
    async_result = pool.map_async(find_in_file, files)
    
    total_chunks = async_result._number_left

    while not async_result.ready():
        if sys.stdout.isatty():
            sys.stdout.write("\r{}/{}".format(len(files) - async_result._number_left*len(files)/total_chunks, len(files)))
            sys.stdout.flush()
        time.sleep(0.1)
    
    if sys.stdout.isatty():
        sys.stdout.write("\r")
    line_results = async_result.get()
    lines = []    

    for r in line_results:
        for l in r:
            lines.append(l)
    
    
    return lines


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--allow", "-a", 
        action="append", 
        default=[],
        help="Specify patterns by which to glob for files. Separated by ;. Use quotation marks"
    )
    parser.add_argument(
        "--plain", 
        action="store_true",
        help="Print in plain format."
    )
    args = parser.parse_args()

    pool = mp.Pool(processes=PROC_COUNT) 

    lines = get_grep(args, pool)
    rows = []
    for line in lines:
        filename, fileline, comment_line = line
        # filename, fileline, comment_line = line.split(":", 2)
        # print(red(filename), red(comment_line))

        filename = os.path.relpath(filename, os.getcwd())

        comment_type = re.search('@(.*?):', comment_line)
        if not comment_type:
            continue
        
        comment_type = comment_type.group(1)
        comment_type = comment_type.replace("(", "").replace(")", "")
        prio = comment_type.count("!")
        comment_type = comment_type.replace("!", "").strip()

        rest, comment = comment_line.split(":", 1)
        
        done = "DONE" in comment
        
        comment = comment.replace("DONE", "")
        comment = comment.strip()

        # print(filename, fileline, comment_type, comment)
        rows.append((comment_type, prio, filename, fileline, comment, done))

    type_prios = {
        "TODO": 10,
        "FIXME": 50
    }


    # rows = filter(mimefilter, rows)

    try:
        if len(args.allow) > 0:
            rows = filter(lambda r: any([fnmatch(r[2], p) for p in args.allow]), rows)
        rows = reversed(sorted(rows, key=lambda r: (0 if r[5] else 1, r[2], type_prios[r[0]], r[1] ) ))
    except Exception as e:
        # print(e)
        raise
    # print(tabulate(rows, headers=["type", "prio", "file", "comment"]))

    if not args.plain:
        print_fancy(rows)
    else:
        print_plain(rows)

def print_plain(rows):
    for row in rows:
        ttype, prio, filename, line, comment, done = row

        if done:
            continue

        print(ttype, comment, ": {}:{}".format(filename, line))


def print_fancy(rows):
    for row in rows:
        ttype, prio, filename, line, comment, done = row
        if ttype == "TODO":
            cprint = yellow
        else:
            cprint = red

        if done:
            cprint = green

        stat = CHECK_MARK if done else CROSS_MARK
        prio_line = (" (" if prio > 0 else "") + prio*"!" + (")" if prio > 0 else "")
        print(cprint("{stat} {type}{prio}: {cm}".format(stat=stat, prio=prio_line, type=(ttype), cm=comment)))
        print("{}:{}".format(filename, bold(line)))
        print("")    


if __name__ == "__main__":
    main()
