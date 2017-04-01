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
from functools import partial

from pygments import highlight
from pygments.lexers import get_lexer_for_filename
from pygments.formatters import TerminalFormatter

if sys.stdout.encoding == "UTF-8":
   CHECK_MARK = u"\u2714".encode("utf-8")
   CROSS_MARK = u"\u2718".encode("utf-8")
else:
   CHECK_MARK = "[OK]"
   CROSS_MARK = "[  ]"


keywords = [
    "TODO",
    "FIXME",
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
    # print(r, mime)
    return mime[0] and "text" in mime[0]

def find_in_file(filename, ncontext=0):
    # print("find_in_file", filename)
    with open(filename, "r") as f:
        lines = f.read().strip().split("\n")

    matched = []
    for i, l in enumerate(lines):
        if any(k in l for k in keywords):
            context = "\n".join(lines[i:i+ncontext])
            matched.append( ( filename, i+1, l, context) )
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
    # files = filter(mimefilter, files)
    # print(files)


    # print(len(files))
    async_result = pool.map_async(partial(find_in_file, ncontext=args.context), files)
    
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

    style = parser.add_mutually_exclusive_group()

    style.add_argument(
        "--plain", 
        action="store_true",
        help="Print in plain format."
    )

    style.add_argument(
        "--md",
        action="store_true",
        help="Print in markdown task list format"
    )

    parser.add_argument(
        "--context", "-c",
        action="store",
        nargs="?",
        const=5,
        type=int,
        default=0,
        help="Show lines following the comment"
    )

    args = parser.parse_args()
    
    pool = mp.Pool(processes=PROC_COUNT) 

    lines = get_grep(args, pool)
    rows = []
    for line in lines:
        filename, fileline, comment_line, context = line
        # filename, fileline, comment_line = line.split(":", 2)
        # print(red(filename), red(comment_line))

        filename = os.path.relpath(filename, os.getcwd())

        # regex = '@(.*?):'
        # regex = '(TODO|FIXME)(.*?)(:| )'
        # regex = r"(TODO|FIXME)(?:(?:\((.*?)\))?|(?:\[(.*?)\])?){2}[ :](.*?)$"
        regex = r"(TODO|FIXME)(?:(?:\((.*?)\))?|(?:\[(.*?)\])?){2}[ :{](.*?)[}]?$"
        comm = re.search(regex, comment_line)
        if not comm:
            continue

        keyword = comm.group(1)
        if comm.group(2):
            prio = comm.group(2).count("!")
        else:
            prio = 0
        done = comm.group(3) == "x"
        comment = comm.group(4).strip()
 

        rows.append((keyword, prio, filename, fileline, comment, done, context))

    type_prios = {
        "TODO": 10,
        "FIXME": 50
    }


    # rows = filter(mimefilter, rows)

    try:
        if len(args.allow) > 0:
            rows = filter(lambda r: any([fnmatch(r[2], p) for p in args.allow]), rows)
        rows = reversed(sorted(rows, key=lambda r: (0 if r[5] else 1, r[1], type_prios[r[0]], r[2], 1/float(r[3] ) )))
    except Exception as e:
        # print(e)
        raise
    # print(tabulate(rows, headers=["type", "prio", "file", "comment"]))

    
    if args.plain:
        print_plain(rows)
    elif args.md:
        print_md(rows, show_context=args.context)
    else:
        print_fancy(rows, context=args.context > 0)

def print_md(rows, show_context=False):
    for row in rows:
        ttype, prio, filename, line, comment, done, context = row

        ch = "[x]" if done else "[ ]"

        print("- {d} {tt} {cm}: {fn}:{ln}".format(d=ch, tt=ttype, cm=comment, fn=filename, ln=line))
        if show_context:
            lexer = get_lexer_for_filename(filename)
            lang = lexer.aliases[0]

            print("```{}".format(lang))
            print(context)
            print("```")
        

def print_plain(rows):
    for row in rows:
        ttype, prio, filename, line, comment, done, _ = row

        if done:
            continue

        print(ttype, comment, ": {}:{}".format(filename, line))


def print_fancy(rows, context=False):
    for row in rows:
        ttype, prio, filename, line, comment, done, context = row
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

        if context:
            lexer = get_lexer_for_filename(filename)
            print(highlight(context, lexer, TerminalFormatter()))

        print("")    


if __name__ == "__main__":
    main()
