#!/usr/bin/python

"""
Author:  Christian Soto (chsoto@vmware.com)
"""

##### BEGIN IMPORTS #####

import os
import subprocess
import socket
import argparse

def get_args():
    parser = argparse.ArgumentParser(description='vRLI Toolkit.')

    parser.add_argument('-a', '--action', type=str, help='run specified command on ALL nodes')
    parser.add_argument('-cl', '--check_local', action="store_true", help='brief health check on local node')
    parser.add_argument('-ca', '--check_all', action="store_true", help='brief health check on ALL nodes')
    parser.add_argument('-rs', '--remove_ssh', action="store_true", help='delete keys')
    parser.add_argument('-s', '--start', action="store_true", help='create and copy the key')
    parser.add_argument('-n', '--nodes', action="store_true", help='show nodes IDs')

    args = parser.parse_args()

    return(args)

VMENV = os.environ

##### END IMPORTS #####

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(color, delim, title):
    print(f"{color}{delim}{title}{delim}{bcolors.ENDC}")

class host:
    def date_CMD(host_address):
        print(subprocess_cmd("date", host_address))

    def uptime_CMD(host_address):
        print(subprocess_cmd("uptime", host_address))

    def networking_CMD(host_address):
        print_header(bcolors.BOLD, "--", "HOSTNAME")
        print(subprocess_cmd("hostname -f", host_address))
        print_header(bcolors.BOLD, "--", "DNS SERVER(S)")
        print(subprocess_cmd("grep nameserver /etc/resolv.conf", host_address))
        print_header(bcolors.BOLD, "--", "GATEWAY")
        print(subprocess_cmd("ip r | grep default", host_address))
        print_header(bcolors.BOLD, "--", "IP ADDRESS")
        print(subprocess_cmd("ifconfig eth0", host_address))

    def vm_resources_CMD(host_address):
        print_header(bcolors.BOLD, "", "vCPUS:")
        
        num_of_vCPU=int(subprocess_cmd("grep -wc processor /proc/cpuinfo", host_address))
        switcher = {
        2: "(Extra Small)",
        4: "(Small)",
        8: "(Medium)",
        16: "(Large)"
        }
        print(num_of_vCPU, switcher.get(num_of_vCPU, "(Not a supported configuration for vCPUs!)"))
        
        print_header(bcolors.BOLD, "", "RAM:")  
        MemTotal_Conve=subprocess_cmd("grep 'MemTotal' /proc/meminfo", host_address)
        TotalRAM=host.conv_KB2GB(MemTotal_Conve)
        if (3.5 <= float(TotalRAM) <= 4):
            print("MemTotal:", TotalRAM, "GBs", "(Extra Small)")
        elif (7.5 <= float(TotalRAM) <= 8):
            print("MemTotal:", TotalRAM, "GBs", "(Small)")
        elif (15.5 <= float(TotalRAM) <= 16):
            print("MemTotal:", TotalRAM, "GBs", "(Medium)")
        elif (31.5 <= float(TotalRAM) <= 32):
            print("MemTotal:", TotalRAM, "GBs", "(Large)")
        else:
            print("MemTotal:", TotalRAM, "GBs", "Not a supported configuration for RAM!")
        MemFree_Conve=subprocess_cmd("grep 'MemFree' /proc/meminfo", host_address)
        print("MemFree:", host.conv_KB2GB(MemFree_Conve), "GBs")
        MemAvailable_Conve=subprocess_cmd("grep 'MemAvailable' /proc/meminfo", host_address)
        print("MemAvailable:", host.conv_KB2GB(MemAvailable_Conve), "GBs")
        SwapTotal_Conve=subprocess_cmd("grep 'SwapTotal' /proc/meminfo", host_address)
        print("SwapTotal:", host.conv_KB2GB(SwapTotal_Conve), "GBs")
        SwapFree_Conve=subprocess_cmd("grep 'SwapFree' /proc/meminfo", host_address)
        print("SwapFree:", host.conv_KB2GB(SwapFree_Conve), "GBs")

    def conv_KB2GB(strGrep):
        str_Conv=strGrep.split()
        GB_Conv=str(round(float(str_Conv[1])/1024**2, 2))
        return(GB_Conv) 
    
    def top_CMD(host_address):
        print(subprocess_cmd("top -n 1 -b | head -15", host_address))

    def vRLI_version_CMD(host_address):
        print(subprocess_cmd("rpm -qa | grep --color=never -i 'loginsight-configs-'", host_address))

    def local_OS_accountCMD(host_address):
        print_header(bcolors.BOLD, "--", "ROOT ACCOUNT")
        print(subprocess_cmd("chage -l root", host_address))
        print(subprocess_cmd("pam_tally2 -u root", host_address))

    def storage_CMD(host_address):
        print(subprocess_cmd("df -h", host_address))
        print_header(bcolors.WARNING , "--", "HEAPDUMPS")
        print(subprocess_cmd("ls -l /storage/var/loginsight/heapdump", host_address))

    def check_certs_CMD(host_address):
        print(subprocess_cmd("/opt/vmware/bin/li-ssl-cert.sh --check", host_address))

    def cluster_status_CMD(host_address):
        print(subprocess_cmd("/usr/lib/loginsight/application/lib/apache-cassandra-*/bin/nodetool status", host_address))

    def vRLI_service_statusCMD(host_address):
        print(subprocess_cmd("/etc/init.d/loginsight status", host_address))

commandsTitle=["DATE",
        "UPTIME",
        "vRLI VERSION",
        "NETWORKING",
        "VM RESOURCES",
        "TOP",
        "STORAGE",
        "LOCAL OS ACCOUNT",
        "CERTIFICATE",
        "CLUSTER STATUS",
        "VRLI SERVICE STATUS"]

commands=[host.date_CMD, 
        host.uptime_CMD, 
        host.vRLI_version_CMD, 
        host.networking_CMD,
        host.vm_resources_CMD,
        host.top_CMD,
        host.storage_CMD,
        host.local_OS_accountCMD,
        host.check_certs_CMD,
        host.cluster_status_CMD,
        host.vRLI_service_statusCMD]

def main():

    args = get_args()

    if args.action:
        comm_allNodes(args.action)
    elif args.check_local:
        local()
    elif args.check_all:
        ssh_all()
    elif args.start:
        start()
    elif args.remove_ssh:
        removeOld()
    elif args.nodes:
        print(get_nodes_ID())
    
def subprocess_cmd(command, host_address):
    if host_address == 'local':
        process = subprocess.Popen(command,stdout=subprocess.PIPE, shell=True)
    else:
        process = subprocess.Popen("ssh root@{host} {cmd}".format(host=host_address, cmd=command), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    proc_stdout = process.communicate()[0].strip()
    output=proc_stdout.decode('ascii')
    return(output)

def local():
    print_header(bcolors.OKCYAN, "▼▼▼", socket.gethostname())

    # BASIC INFO
    for comm, title in zip(commands,commandsTitle):
        print_header(bcolors.OKGREEN, "---", title)
        comm('local')
        if comm != commands[-1]:
            os.system('read -s -n 1 -p "Press any key to continue..."')
            print()

def ssh_all():
    hosts=get_nodes_ID()

    # BASIC INFO
    for comm, title in zip(commands,commandsTitle):
        print_header(bcolors.OKGREEN, "---", title)
        for h in hosts:
            print_header(bcolors.OKCYAN, "", h)
            comm(h)
        if comm != commands[-1]:
            os.system('read -s -n 1 -p "Press any key to continue..."')
            print()

def comm_allNodes(comm):
    hosts=get_nodes_ID()
    for h in hosts:
        print_header(bcolors.OKCYAN, '', h)
        print(subprocess_cmd(comm, h))

def start():
    hosts=get_nodes_ID()
    subprocess.Popen("ssh-keygen",stdout=subprocess.PIPE, shell=True)
    for h in hosts:
        print_header(bcolors.OKCYAN, "", h)
        process = subprocess.Popen("ssh-copy-id -i /root/.ssh/id_rsa.pub {host}".format(host=h), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        process.communicate()[0]

def removeOld():
    hosts=get_nodes_ID()
    for h in hosts:
        subprocess.Popen("ssh-keygen -R {host}".format(host=h), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

def get_nodes_ID():
    ConfigFile=subprocess_cmd("ls -ltr /storage/core/loginsight/config/loginsight-config.xml#* | tail -n 1 | awk '{print $NF}'", 'local')
    print("Current Configfile:", ConfigFile)
    grepped=subprocess_cmd("grep -i 'daemon host' {CF}".format(CF=ConfigFile), 'local').splitlines()
    return [ID.split('"')[1] for ID in grepped]

if __name__ == "__main__":
    main()