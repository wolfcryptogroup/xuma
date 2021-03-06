#!/usr/bin/python3
#created by https://t.me/WolfCryptoPub

import fcntl
import os
import socket
import struct
from subprocess import Popen, STDOUT, PIPE
import sys
import termios
import time

DEFAULT_COLOR = "\x1b[0m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
MAX_LEN=struct.unpack('HHHH',fcntl.ioctl(0, termios.TIOCGWINSZ,struct.pack('HHHH', 0, 0, 0, 0)))[1]-5

def run(cmd_list):
        for cmd in cmd_list:
                proc=Popen(cmd,stderr=STDOUT,stdout=PIPE,shell=True)
                output=[]
                while True:
                        line=proc.stdout.readline().strip().decode()[:MAX_LEN]
                        if sys.argv[-1]!="-v":
                                for i in range(len(output)):
                                        sys.stdout.write('\x1b[1A\r\x1b[2K')
                                sys.stdout.flush()
                        if not line: break
                        output.append("\r  "+line)
                        output=output[-5:]
                        if sys.argv[-1]!="-v": print(DEFAULT_COLOR+"\n".join(output))
                        else: print(DEFAULT_COLOR+output[-1])
                        time.sleep(0.05)
                proc.wait()

if os.getuid()!=0:
        sys.exit("This program must be run with root privledges:\n\nsudo python3 {}".format(" ".join(sys.argv)))

os.system('clear')
print("""{1}.------..------..------..------.
|X.--. ||U.--. ||M.--. ||A.--. |
| :/\: || (\/) || (\/) || (\/) |
| (__) || :\/: || :\/: || :\/: |
| '--'X|| '--'U|| '--'M|| '--'A|
`------'`------'`------'`------'

{0}XUMA Masternode Upgrader v0.1 - Upgrades Xuma from 1.0.5 to 1.1.0
By Wolf Crypto: {1}https://t.me/WolfCryptoPub{0}

Updating & Upgrading Ubuntu...""".format(BLUE,YELLOW))
run(["sudo apt-get update -y",
        'sudo DEBIAN_FRONTEND=noninteractive apt-get -y -o DPkg::options::="--force-confdef" -o DPkg::options::="--force-confold"  install grub-pc',
        "apt-get upgrade -y"])

print(BLUE+"Creating Swap and Securing Server...")
run(["fallocate -l 4G /swap",
         "chmod 600 /swap",
         "mkswap /swap",
         "swapon /swap"])
with open('/etc/fstab','r+') as f:
        line="/swap   none    swap    sw    0   0 \n"
        lines = f.readlines()
        if lines[-1]!=line:
                f.write(line)

run(["apt-get --assume-yes install ufw",
         "ufw allow OpenSSH",
         "ufw allow 19777",
         "ufw default deny incoming",
         "ufw default allow outgoing",
         "ufw --force enable"])

print(BLUE+"Installing Build Dependencies...")
run(["apt-get install git automake build-essential libtool autotools-dev autoconf pkg-config libssl-dev nano -y",
         "apt-get install libboost-all-dev software-properties-common -y",
         "add-apt-repository ppa:bitcoin/bitcoin -y",
         "apt-get update -y",
         "apt-get install libdb4.8-dev libdb4.8++-dev libminiupnpc-dev -y"])

print(BLUE+"Stopping Xuma Masternode...")
os.system('su - xuma -c "xuma-cli stop &> /dev/null" ')
os.system('systemctl stop xuma')

print(BLUE+"Cleaning Up Old Xuma Files...")
run(["rm -rf /root/xuma-core/mainnet/"
        "rm -rf /root/xuma-core/"
        "rm -rf /home/xuma/xuma-core/mainnet/",
        "rm -rf /home/xuma/xuma-core/"
        "rm -f /usr/local/bin/xuma*",])

print(BLUE+"Compiling New Xuma Version...")
print(YELLOW+"This will take approx 15-20 mins. Please be patient!")
run(["git clone https://github.com/xumacoin/xuma-core.git",
     "cd xuma-core && ./autogen.sh",
     "cd xuma-core && ./configure",
     "cd xuma-core && make all install",
     "cp -r /root/xuma-core /home/xuma",
     "chown xuma:xuma -R /home/xuma/xuma-core"])

if os.path.isfile('/lib/systemd/system/xuma.service'): print(BLUE+"Xuma Service File is Already Setup!")
else:
    print("\nSetting Up Xuma Service File...\n")
    with open('/lib/systemd/system/xuma.service', 'w') as f:
        f.write("""[Unit]

Description=Xuma Masternode Server
After=network.target
After=syslog.target

[Install]
WantedBy=multi-user.target
Alias=xumad.service

[Service]
User=xuma
Group=users
ExecStart=/usr/local/bin/xumad -conf=/home/xuma/.xuma/mainnet/xuma.conf -datadir=/home/xuma/xuma-core/
Type=forking
Restart=always
RestartSec=5
PrivateTmp=true
TimeoutStopSec=60s
TimeoutStartSec=5s
StartLimitInterval=120s
StartLimitBurst=15
PrivateTmp=false""")

print(BLUE+"Running Xuma...")
os.system('systemctl daemon-reload')
os.system('systemctl enable xuma')
os.system('systemctl start xuma')
os.system('systemctl --no-pager status xuma')

print(YELLOW+"Xuma Masternode Upgrade Finished! Your masternode version will bi displayed below.  If it displays anything other than 'Xuma Core RPC client version 1.1.0 something has gone wrong!.")
time.sleep(3)
os.system('su - xuma -c "xuma-cli | grep 1.1.0" ')
print(DEFAULT_COLOR+"All done!")
