import argparse 
import docker
import random
import string
import os
import shutil 
import time
import subprocess 

def main():
    
    client = docker.from_env()

    cont_name = "inetsim-1"

    try:
        container = client.containers.get(cont_name)
        container.stop()
        container.remove()
    except docker.errors.NotFound:
        pass
    except docker.errors.APIError:
        pass

    
    
    container = client.containers.create('inetsim', detach=True, name=cont_name, network_mode="none")
    container.start()

    try:
        subprocess.check_output(["/usr/bin/sudo", "/usr/bin/ovs-docker", "del-ports", "vmbr0", cont_name])
    except:
        pass
    subprocess.check_output(["/usr/bin/sudo", "/usr/bin/ovs-docker", "add-port", "vmbr0", "eth0", cont_name, "--ipaddress={}".format('172.16.3.1/24')])

main()