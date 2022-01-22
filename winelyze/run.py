import argparse 
import docker
import random
import string
import os
import shutil 
import time
import subprocess 
import tarfile

def condense_calls(raw_file, sample_name):
    dump_file = open(raw_file, "r")
    original = dump_file.read()
    dump_file.close()

    lines = original.split("\n")
    pid = None

    i = 0 
    while pid is None and i < len(lines):
        line = lines[i]
        if "loaddll:build_module Loaded" in line and sample_name in line:
            line_split = line.split(":", 2)
            pid = line_split[0]
            print(f"Found target pid: {pid} => {int(pid, 16)}")
        i+=1

    if pid is None:
        print("Could not determine target pid")
        return []
    
    proc_lines = []

    for line in lines:
        if line.startswith(f"{pid}:"):
            proc_lines.append(line)

    calls = []
    condense_map = {}

    print(f"Condensing {len(proc_lines)} lines...")
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
            print("Loaded dll: " + line_split[1])
    
    print(len(calls))
    return calls

def main():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--file', help='Sample to test')

    args = parser.parse_args()

    if not os.path.exists(args.file):
        print("Invalid path to file")
        return 1

    
    client = docker.from_env()

    try:
        container = client.containers.get('winelyze-1')
        container.remove()
    except docker.errors.NotFound:
        pass
    except docker.errors.APIError:
        pass

    tmp_dir = ''.join(random.choice(string.ascii_lowercase) for i in range(8))
    test_name = ''.join(random.choice(string.ascii_lowercase) for i in range(5))
    username = ''.join(random.choice(string.ascii_lowercase) for i in range(5))
    screenshot = ''.join(random.choice(string.ascii_lowercase) for i in range(6))
    sample_name =  f"{test_name}.exe"

    print(f"Temp Dir: {tmp_dir}")
    print(f"New Sample Name: {sample_name}")
    print(f"Screenshot Dir: {screenshot}")

    if not os.path.exists("./share"):
        os.mkdir("./share")

    share_dir = os.path.abspath(f"./share/{tmp_dir}")
    os.mkdir(share_dir)

    shutil.copy(args.file, f"{share_dir}/{test_name}.exe")

    vols = {
        share_dir: {"bind": f"/tmp/{tmp_dir}/", 'mode': 'ro'}
    }

    environment = {
        "TMPDIR": tmp_dir,
        "SAMPLENAME": sample_name,
        "USER": username,
        "SCREENSHOT": screenshot
    }

    cont_name = "winelyze-1"
    container = client.containers.create('winelyze', volumes=vols, environment=environment, detach=True, name=cont_name, network_mode="none", dns=["172.16.3.1"])
    container.start()

    try:
        subprocess.check_output(["/usr/bin/sudo", "/usr/bin/ovs-docker", "del-ports", "vmbr0", cont_name])
    except:
        pass

    subprocess.check_output(["/usr/bin/sudo", "/usr/bin/ovs-docker", "add-port", "vmbr0", "eth0", cont_name, "--ipaddress={}".format('172.16.3.4/24'), "--gateway={}".format('172.16.3.1')])

    print("Waiting for timeout or completion...")
    i = 0
    done = False
    while i < 6 and not done:
        time.sleep(30)
        container = client.containers.get('winelyze-1')
        print(container.status)
        if container.status != "running":
            done = True
        else:
            i += 1
    
    print("Stopping container...")
    container = client.containers.get('winelyze-1')
    container.stop()

    print("Getting test log...")
    strm, stat = container.get_archive('/tmp/test.log')
    results = open("config.log.tar", "wb")
    for chunk in strm:
        results.write(chunk)
    results.close()

    results_tar = tarfile.open("config.log.tar", "r")
    results_tar.extractall(path=share_dir)
    results_tar.close()

    print("Getting screenshots...")
    strm, stat = container.get_archive(f'/tmp/{screenshot}')
    results = open("screenshots.tar", "wb")
    for chunk in strm:
        results.write(chunk)
    results.close()

    results_tar = tarfile.open("screenshots.tar", "r")
    results_tar.extractall(path=share_dir)
    results_tar.close()

    print("Processing calls...")
    calls = condense_calls(share_dir + "/test.log", sample_name)

    outfile = open(share_dir + "/calls.log", "w")
    for line in calls:
        outfile.write(line + "\n")
    outfile.close()

main()