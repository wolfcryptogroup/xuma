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

{0}XUMA Masternode Installer v0.2
By Wolf Crypto: {1}https://t.me/WolfCryptoPub{0}

Updating & Upgrading Ubuntu...""".format(BLUE,YELLOW))

run(["sudo apt-get update -y",
	'sudo DEBIAN_FRONTEND=noninteractive apt-get -y -o DPkg::options::="--force-confdef" -o DPkg::options::="--force-confold"  install grub-pc',
	"apt-get upgrade -y"])

print(BLUE+"Creating Swap...")

run(["fallocate -l 4G /swap",
	 "chmod 600 /swap",
	 "mkswap /swap",
	 "swapon /swap"])
with open('/etc/fstab','r+') as f:
	line="/swap   none    swap    sw    0   0 \n"
	lines = f.readlines()
	if lines[-1]!=line:
		f.write(line)

print(BLUE+"Securing Server...")
run(["apt-get --assume-yes install ufw",
	 "ufw allow OpenSSH",
	 "ufw allow 19777",
	 "ufw default deny incoming",
	 "ufw default allow outgoing",
	 "ufw --force enable"])

print(BLUE+"Creating Xuma User...")
run(["useradd --create-home -G sudo xuma"])


print(BLUE+"Installing Build Dependencies...")
run(["apt-get install git automake build-essential libtool autotools-dev autoconf pkg-config libssl-dev nano -y",
	 "apt-get install libboost-all-dev software-properties-common -y",
	 "add-apt-repository ppa:bitcoin/bitcoin -y",
	 "apt-get update -y",
	 "apt-get install libdb4.8-dev libdb4.8++-dev libminiupnpc-dev -y"])


if os.path.exists('/home/xuma/xuma-core'): print(BLUE+"Xuma is already installed!")
else:
	print(BLUE+"Downloading & Compiling Xuma...")
	run(["git clone https://github.com/xumacoin/xuma-core.git",
		 "cd xuma-core && ./autogen.sh",
		 "cd xuma-core && ./configure",
		 "cd xuma-core && make all install",
		 "cp -r /root/xuma-core /home/xuma",
		 "chown xuma:xuma -R /home/xuma/xuma-core"])

print(BLUE+"Running Xuma...")
run(['su - xuma -c "xumad &> /dev/null" '])

print(YELLOW+"Open your desktop wallet console (Help => Debug window => Console) and generate your masternode outputs by entering: masternode outputs")
txid=input(DEFAULT_COLOR+"  Transaction ID: ")
tx_index=input("  Transaction Index: ")

print(YELLOW+"Open your desktop wallet console (Help => Debug window => Console) and create a new masternode private key by entering: masternode genkey")
priv_key=input(DEFAULT_COLOR+"  masternodeprivkey: ")

print(YELLOW+"Open your desktop wallet config file (%appdata%/Xuma/mainnet/xuma.conf) and copy your rpc username and password! If it is not there create one! E.g.:\n\trpcuser=[SomeUserName]\n\trpcpassword=[DifficultAndLongPassword]")
rpc_user=input(DEFAULT_COLOR+"  rpcuser: ")
rpc_pass=input("  rpcpassword: ")

print(BLUE+"Saving config file...")
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
this_ip=s.getsockname()[0]
s.close()
with open('/home/xuma/.xuma/mainnet/xuma.conf', 'w') as f:
	f.write("""rpcuser={0}
rpcpassword={1}
rpcallowip=127.0.0.1
listen=1
server=1
daemon=1
logtimestamps=1
maxconnections=256
addnode=159.89.120.208
addnode=159.89.120.226
addnode=165.227.230.24
addnode=159.65.63.79
addnode=159.203.10.85
addnode=138.197.151.120
addnode=139.59.38.142
addnode=159.89.170.123
masternode=1
externalip={2}:17999
bind={2}
masternodeaddr={2}
masternodeprivkey={3}""".format(rpc_user, rpc_pass, this_ip, priv_key))
	
print(BLUE+"Setting Up Xuma Service File..."+DEFAULT_COLOR)
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

os.system('systemctl daemon-reload')
os.system('systemctl enable xuma')
os.system('systemctl start xuma')
os.system('systemctl --no-pager status xuma')
os.system('su - xuma -c "xuma-cli masternode status &> /dev/null" ')
print(BLUE+"Xuma Masternode Started...")

print(YELLOW+"""
Xuma Masternode Setup Finished!
Xuma Masternode Data:
IP: {0}:19777
Private key: {1}
Transaction ID: {2}
Transaction index: {3}
--------------------------------------------------
{4} {0}:19777 {1} {2} {3}
""".format(this_ip,priv_key,txid,tx_index,socket.gethostname().split('.')[0])+DEFAULT_COLOR)
