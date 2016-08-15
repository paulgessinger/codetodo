#! /usr/bin/env python

from __future__ import print_function
import subprocess
import os
import sys
import re
from tabulate import tabulate
from termcolor import colored
import argparse
from glob import glob
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

def glob_pattern(p):
    return rglob(os.getcwd(), p)

    # for f in files:
        # print(f)

    # return files


red = lambda s: colored(s, "red", attrs=["bold"])
green = lambda s: colored(s, "green")
yellow = lambda s: colored(s, "yellow", attrs=["bold"])
bold = lambda s: colored(s, attrs=["bold"])


def find_in_file(filename):
    with open(filename, "r") as f:
        lines = f.read().strip().split("\n")

    matched = []
    for i, l in enumerate(lines):
        if any(k in l for k in keywords):
            matched.append( ( filename, i, l ) )
    return matched
    # return filter(lambda l: any(k in l for k in keywords), lines)

def get_grep(args, pool):
    # cmd = "grep -rnw {} -e '@FIXME' -e '@TODO'".format(os.getcwd())
    # p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr = subprocess.PIPE)
    # out, err = p.communicate()

    # with open("cache") as f:
        # out = f.read()

    # lines = out.split("\n")[:-1]
    # lines = filter(lambda l: "Binary file" not in l, lines)


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
    
    line_results = pool.map(find_in_file, files)

    lines = []    

    for r in line_results:
        for l in r:
            lines.append(l)
    
    
    return lines

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow", "-a", action="append", default=[])
    args = parser.parse_args()

    pool = mp.Pool(processes=mp.cpu_count()) 

    lines = get_grep(args, pool)
    rows = []
    for line in lines:
        filename, fileline, comment_line = line
        # filename, fileline, comment_line = line.split(":", 2)
        # print(red(filename), red(comment_line))

        filename = os.path.relpath(filename, os.getcwd())

        comment_type = re.search('@(.*):', comment_line)
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

    def mimefilter(r):
        mime = mimetypes.guess_type(r[2])
        return mime[0] and "text" in mime[0]

    rows = filter(mimefilter, rows)

    try:
        if len(args.allow) > 0:
            rows = filter(lambda r: any([fnmatch(r[2], p) for p in args.allow]), rows)
        
        rows = reversed(sorted(rows, key=lambda r: (0 if r[5] else 1, r[2], type_prios[r[0]], r[1] ) ))
    except:
        print("error")
    # print(tabulate(rows, headers=["type", "prio", "file", "comment"]))




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
