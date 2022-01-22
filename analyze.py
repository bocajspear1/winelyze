import argparse
from ast import dump 
import docker
import random
import string
import os
import shutil 
import time
import subprocess 
import tarfile

def main():
    parser = argparse.ArgumentParser(description='Analyze a wine debug syscall dump')
    parser.add_argument('--sample', help='Sample name', required=True)
    parser.add_argument('--dump', help='Path to WINE debug syscall dump', required=True)

    args = parser.parse_args()

    if not os.path.exists(args.dump):
        print("Invalid path to file")
        return 1

    dump_file = open(args.dump, "r")
    original = dump_file.read()
    dump_file.close()

    lines = original.split("\n")
    pid = None

    i = 0 
    while pid is None and i < len(lines):
        line = lines[i]
        if "loaddll:build_module Loaded" in line and args.sample in line:
            line_split = line.split(":", 2)
            pid = line_split[1]
            print(f"Found target pid: {pid}|{int(pid, 16)}")
        i+=1
    
    proc_lines = []

    for line in lines:
        if f":{pid}:" in line:
            proc_lines.append(line)

    calls = []
    condense_map = {}

    print("Condensing...")
    for line in proc_lines:
        line_split = line.split(" ", 1)
        head = line_split[0].lower()
        back = line_split[1]
        
        if ":call" in head:
            if "ret=" not in back:
                continue
            ret_id = int(back.split("ret=")[1], 16)
            condense_map[ret_id] = back
        elif ":ret" in head:
            if "ret=" not in back:
                continue
            ret_id = int(line_split[1].split("ret=")[1], 16)
            if ret_id in condense_map:
                resplit = line_split[1].split(" ")
                retval = resplit[-2]
                # print(retval)
                calls.append(condense_map[ret_id] + " " + retval)
                del condense_map[ret_id]
            else:
                print("Did not find match!")
                print(line)
        elif ":trace:loaddll" in head:
            print("Loadded dll: " + line_split[1])


    outfile = open("output.log", "w")
    for line in calls:
        outfile.write(line + "\n")
    outfile.close()

main()