import argparse
from ast import dump 
import docker
import random
import string
import os
import shutil 
import time
import subprocess 
import json

def get_called(call_list, depth=0):
    i = 0

    calls = []

    while i < len(call_list):
        line = call_list[i]
        head = line[0]
        back = line[1]

        

        if ":Call" in head:
            if "ret=" not in back:
                i+=1 
                continue
            # print(("    " * depth) +"Found call: ", str(line))
            ret_id = back.split("ret=")[1]

            raw_subcalls = []
            found = False
            i_start = i
            i+=1
            while i < len(call_list) and not found:
                next_line = call_list[i]
                if ":Ret" in next_line[0] and f"ret={ret_id}" in next_line[1]:
                    found = True
                    # print(("    " * depth) + str(next_line))
                    raw_subcalls.append(next_line)
                else:
                    raw_subcalls.append(next_line)
                    i+=1

            if found:
                # print(("    " * depth) + "Found match: ", str(next_line))
                resplit = next_line[1].split(" ")
                retval = resplit[-2]
                calls.append({
                    "call":  back.strip() + " " + retval,
                    "subcalls": get_called(raw_subcalls, depth+1)
                })
            else:
                calls.append({
                    "call":  back.strip() + " retval=???",
                    # "subcalls": get_called(raw_subcalls, depth+1)
                    "subcalls": []
                })
                # print("Must not return, revert")
                i = i_start+1
        elif ":trace:loaddll" in head:
            pass
            # print("Loaded dll: " + back)
        i+=1   

    return calls

def called_to_string(calls, depth=0):
    output = ""
    for call in calls:
        output += (("    " * depth) + call['call']) + "\n"
        if len(call['subcalls']) > 0:
            output += (called_to_string(call['subcalls'], depth+1))
    return output

def main():
    parser = argparse.ArgumentParser(description='Analyze a wine debug syscall dump')
    parser.add_argument('--tmp', help='tmp dir', required=True)


    args = parser.parse_args()

    if not os.path.exists(args.tmp):
        print("Invalid path to tmp dir")
        return 1

    items = os.listdir(args.tmp)

    sample = None 
    for item in items:
        if item.endswith(".exe"):
            sample = item 
    
    if sample is None:
        print("Could not find sample")
        return 1

    print(sample)

    dump_file = open(args.tmp + "/test.log", "r")
    original = dump_file.read()
    dump_file.close()

    lines = original.split("\n")
    pid = None

    i = 0 
    while pid is None and i < len(lines):
        line = lines[i]
        if "loaddll:build_module Loaded" in line and sample in line:
            line_split = line.split(":", 2)
            pid = line_split[0]
            print(f"Found target pid: {pid} => {int(pid, 16)}")
        i+=1

    if pid is None:
        print("Could not determine target pid")
        return []
    
    thread_map = {}

    for line in lines:
        if line.startswith(f"{pid}:"):
            line_split = line.split(":", 2)
            tid = line_split[1]
            if tid not in thread_map:
                thread_map[tid] = []
            thread_map[tid].append(line.split(" ", 1))

    out_thread = {}
    outfile = open(args.tmp + "calls.txt", "w")

    for tid in thread_map:
        print(f"\n\nTID = {int(tid, 16)}")
        calls = get_called(thread_map[tid])
        out_thread[int(tid, 16)] = calls
        outfile.write(called_to_string(calls))

    outjson = open(args.tmp + "calls.json", "w")
    outjson.write(json.dumps(out_thread))
    outjson.close()

    outfile.close()

main()