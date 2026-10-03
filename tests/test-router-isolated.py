#!/usr/bin/python3
"""Functional test in temporary Linux network namespaces. Does not use the SIM or physical LAN."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time

assert os.geteuid() == 0, 'Run with sudo'
prefix = 'pi-test-'
names = {name: prefix + name for name in ('router', 'lan', 'wan', 'usb')}
created, children = [], []

def run(*args, **kwargs):
    return subprocess.run(args, text=True, capture_output=True, check=True, **kwargs)

def ns(name, *args, **kwargs):
    return run('ip', 'netns', 'exec', names[name], *args, **kwargs)

server = '''import socket,threading,time,sys
def serve(s):
 while True:
  c,a=s.accept(); c.sendall(a[0].encode()); c.close()
for p in sys.argv[1:]:
 s=socket.socket(); s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
 s.bind(('0.0.0.0',int(p))); s.listen()
 threading.Thread(target=serve,args=(s,),daemon=True).start()
print('READY',flush=True)
while True: time.sleep(60)
'''
client = '''import socket,sys
try:
 s=socket.create_connection((sys.argv[1],int(sys.argv[2])),timeout=1.3)
 print(s.recv(100).decode()); s.close()
except TimeoutError:
 print('BLOCKED'); sys.exit(3)
except ConnectionRefusedError:
 print('REJECTED'); sys.exit(4)
'''

def start_server(where, *ports):
    process = subprocess.Popen(['ip', 'netns', 'exec', names[where], 'python3', '-u', '-c', server, *map(str, ports)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    children.append(process)
    assert process.stdout.readline().strip() == 'READY'

def probe(where, target, port, expected, label):
    result = subprocess.run(['ip', 'netns', 'exec', names[where], 'python3', '-c', client, target, str(port)], text=True, capture_output=True)
    if expected == 'BLOCKED':
        # The known test server is listening; NetworkManager may reject before our drop chain.
        assert (result.returncode, result.stdout.strip()) in {(3, 'BLOCKED'), (4, 'REJECTED')}, (label, result.stdout, result.stderr)
    else:
        assert result.returncode == 0 and result.stdout.strip() == expected, (label, result.stdout, result.stderr)
    print('PASS:', label, flush=True)

dhcp_client = '''import socket,struct,random,json,subprocess
mac=bytes.fromhex(json.loads(subprocess.check_output(['ip','-j','link','show','net0']))[0]['address'].replace(':','')); xid=random.getrandbits(32)
s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); s.setsockopt(socket.SOL_SOCKET,socket.SO_BROADCAST,1); s.settimeout(3); s.bind(('',68))
rx=socket.socket(socket.AF_PACKET,socket.SOCK_RAW,socket.htons(0x0800)); rx.bind(('net0',0)); rx.settimeout(10)
head=struct.pack('!BBBBIHH4s4s4s4s16s64s128s',1,1,6,0,xid,0,0x8000,b'\\0'*4,b'\\0'*4,b'\\0'*4,b'\\0'*4,mac+b'\\0'*10,b'\\0'*64,b'\\0'*128)
def send(kind,extra=b''):
 s.sendto(head+b'\\x63\\x82\\x53\\x63'+bytes([53,1,kind,55,3,1,3,6])+extra+b'\\xff',('255.255.255.255',67))
def receive(kind):
 while True:
  frame,_=rx.recvfrom(4096)
  if len(frame)<42 or frame[23]!=17: continue
  offset=14+(frame[14]&15)*4
  if struct.unpack('!H',frame[offset+2:offset+4])[0]!=68: continue
  packet=frame[offset+8:]
  if len(packet)<240 or struct.unpack('!I',packet[4:8])[0]!=xid: continue
  options={}; pos=240
  while pos<len(packet):
   tag=packet[pos]; pos+=1
   if tag==255: break
   if tag==0: continue
   size=packet[pos]; pos+=1; options[tag]=packet[pos:pos+size]; pos+=size
  if options.get(53)==bytes([kind]): return packet,options
send(1); offer,options=receive(2)
send(3,bytes([50,4])+offer[16:20]+bytes([54,4])+options[54]); ack,options=receive(5)
assert socket.inet_ntoa(options[3][:4])=='192.168.76.1'
assert socket.inet_ntoa(options[6][:4])=='192.168.76.1'
assert socket.inet_ntoa(ack[16:20]).startswith('192.168.76.')
print(json.dumps({'lease':socket.inet_ntoa(ack[16:20]),'gateway':'192.168.76.1','dns':'192.168.76.1'}))
'''

try:
    existing = run('ip', 'netns', 'list').stdout
    assert not any(name in existing for name in names.values()), 'Test namespace already exists'
    for name in names.values():
        run('ip', 'netns', 'add', name); created.append(name)
        run('ip', '-n', name, 'link', 'set', 'lo', 'up')
    for index, (peer, router_if, router_ip, peer_ip) in enumerate([
        ('lan', 'eth0', '192.168.76.1/24', '192.168.76.50/24'),
        ('wan', 'wwan0', '198.18.0.1/24', '198.18.0.2/24'),
        ('usb', 'usb0', '10.12.194.1/28', '10.12.194.6/28'),
    ]):
        left, right = f'pt-r{index}', f'pt-p{index}'
        run('ip', 'link', 'add', left, 'type', 'veth', 'peer', 'name', right)
        run('ip', 'link', 'set', left, 'netns', names['router'])
        run('ip', 'link', 'set', right, 'netns', names[peer])
        run('ip', '-n', names['router'], 'link', 'set', left, 'name', router_if)
        run('ip', '-n', names[peer], 'link', 'set', right, 'name', 'net0')
        run('ip', '-n', names['router'], 'addr', 'add', router_ip, 'broadcast', '+', 'dev', router_if)
        run('ip', '-n', names[peer], 'addr', 'add', peer_ip, 'broadcast', '+', 'dev', 'net0')
        run('ip', '-n', names['router'], 'link', 'set', router_if, 'up')
        run('ip', '-n', names[peer], 'link', 'set', 'net0', 'up')
        run('ip', '-n', names[peer], 'route', 'add', 'default', 'via', router_ip.split('/')[0])
    ns('router', 'sysctl', '-w', 'net.ipv4.ip_forward=1')
    ns('router', 'nft', '-f', '/etc/nftables.conf')
    # Include the real NetworkManager USB table to test coexistence.
    shared = run('nft', 'list', 'table', 'ip', 'nm-shared-usb0').stdout
    ns('router', 'nft', '-f', '-', input=shared)
    ns('router', 'nft', 'add', 'element', 'inet', 'pi_router', 'wan_ifaces', '{ wwan0 }')
    start_server('router', 22, 8080)
    start_server('wan', 8080)
    start_server('lan', 8080)
    start_server('usb', 8080)
    probe('usb', '10.12.194.1', 22, '10.12.194.6', 'USB SSH permitted')
    probe('lan', '192.168.76.1', 22, 'BLOCKED', 'LAN SSH blocked')
    probe('wan', '198.18.0.1', 22, 'BLOCKED', 'WAN SSH blocked')
    probe('usb', '10.12.194.1', 8080, 'BLOCKED', 'Unpublished local service blocked')
    probe('lan', '198.18.0.2', 8080, '198.18.0.1', 'LAN to WAN allowed with verified source NAT and return traffic')
    probe('usb', '198.18.0.2', 8080, 'BLOCKED', 'USB Internet forwarding blocked despite NetworkManager shared rules')
    probe('wan', '192.168.76.50', 8080, 'BLOCKED', 'Unsolicited WAN to LAN blocked')
    probe('lan', '10.12.194.6', 8080, 'BLOCKED', 'LAN to USB management network blocked')
    ns('router', 'nft', 'flush', 'set', 'inet', 'pi_router', 'wan_ifaces')
    probe('lan', '198.18.0.2', 8080, 'BLOCKED', 'No modem means no forwarding')
    with tempfile.TemporaryDirectory(prefix='pi-router-test-') as temporary:
        path = Path(temporary); path.chmod(0o777)
        config = Path('/etc/pi-router/dnsmasq-lan.conf').read_text()
        config = config.replace('/var/lib/pi-router/dnsmasq.leases', str(path/'leases'))
        config = config.replace('/run/pi-lan-dnsmasq/dnsmasq.pid', str(path/'pid'))
        (path/'dnsmasq.conf').write_text(config)
        logfile = (path/'dnsmasq.log').open('w')
        daemon = subprocess.Popen(['ip','netns','exec',names['router'],'dnsmasq','--keep-in-foreground','--conf-file='+str(path/'dnsmasq.conf')],stdout=logfile,stderr=logfile)
        children.append(daemon)
        time.sleep(0.4)
        assert daemon.poll() is None, (path/'dnsmasq.log').read_text()
        answer = ns('lan','dig','@192.168.76.1','router.pi.home.arpa','+short','+time=2','+tries=1').stdout.strip()
        assert answer == '192.168.76.1', answer
        print('PASS: LAN DNS resolves router.pi.home.arpa',flush=True)
        capture = subprocess.Popen(['ip','netns','exec',names['router'],'tcpdump','-U','-n','-i','any','-w',str(path/'dhcp.pcap'),'udp and (port 67 or port 68)'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        children.append(capture)
        time.sleep(0.3)
        try:
            answer = ns('lan','python3','-c',dhcp_client).stdout.strip()
        except subprocess.CalledProcessError as error:
            capture.terminate(); capture.wait(timeout=5)
            print('DHCP CLIENT:', error.stdout, error.stderr, flush=True)
            print('DHCP SERVER:', (path/'dnsmasq.log').read_text(), flush=True)
            print('DHCP CAPTURE:', run('tcpdump','-nn','-vv','-r',str(path/'dhcp.pcap')).stdout, flush=True)
            raise RuntimeError('DHCP transaction failed') from None
        print('PASS: DHCP discover/offer/request/ACK with expected gateway and DNS:',answer,flush=True)
        daemon.terminate(); daemon.wait(timeout=5); logfile.close()
    print('ALL 11 TESTS PASSED. Cellular and physical iPhone connectivity still require hardware testing.',flush=True)
finally:
    for child in children:
        if child.poll() is None:
            child.terminate()
            try: child.wait(timeout=5)
            except subprocess.TimeoutExpired: child.kill(); child.wait()
    for name in reversed(created):
        subprocess.run(['ip','netns','delete',name],check=False)
