#!/usr/bin/python3
"""Controlled EG25 UART speed test. Root; no SIM PIN operations. Rolls back on failure.
Successful test is volatile until the modem baud rate is explicitly saved with AT&W.
"""
import os, re, select, shutil, subprocess, sys, termios, time
from pathlib import Path
TARGET=921600
PROFILE="tmobile-pitalk"
RULE=Path("/etc/udev/rules.d/78-mm-pitalk-uart.rules")
PROFILE_FILE=Path("/etc/NetworkManager/system-connections/tmobile-pitalk.nmconnection")
BACKUP=Path("/root/pi-uart-speed-backup-20261003")

def run(args, timeout=45, check=True):
    r=subprocess.run(args,capture_output=True,text=True,timeout=timeout)
    print("$ "+" ".join(args), "exit="+str(r.returncode),flush=True)
    print(re.sub(r"\d{12,}","[identifier redacted]",r.stdout+r.stderr).strip(),flush=True)
    if check and r.returncode: raise RuntimeError("Command failed: "+args[0])
    return r

def stop():
    run(["nmcli","--wait","20","connection","down",PROFILE],check=False)
    run(["systemctl","stop","ModemManager"])
    if subprocess.run(["pgrep","-x","pppd"],stdout=subprocess.DEVNULL).returncode==0:
        raise RuntimeError("PPP is still running; refusing raw AT")

class Port:
    def __init__(self):
        self.fd=os.open("/dev/ttyS0",os.O_RDWR|os.O_NOCTTY|os.O_NONBLOCK)
    def close(self): os.close(self.fd)
    def speed(self,baud):
        a=termios.tcgetattr(self.fd)
        a[0]=a[1]=a[3]=0;a[2]=termios.CS8|termios.CREAD|termios.CLOCAL
        a[4]=a[5]=getattr(termios,"B"+str(baud));a[6][termios.VMIN]=a[6][termios.VTIME]=0
        termios.tcsetattr(self.fd,termios.TCSANOW,a)
    def read(self,wait):
        end=time.monotonic()+wait;data=b""
        while time.monotonic()<end:
            if select.select([self.fd],[],[],min(.1,max(0,end-time.monotonic())))[0]:
                data+=os.read(self.fd,65536)
        return data.decode("ascii",errors="replace").strip()
    def ask(self,cmd,wait=.7,check=True):
        termios.tcflush(self.fd,termios.TCIFLUSH)
        os.write(self.fd,(cmd+"\r").encode("ascii"))
        out=self.read(wait)
        print(cmd,repr(out),flush=True)
        if check and not re.search(r"(^|[\r\n])OK($|[\r\n])",out):
            raise RuntimeError("No OK for "+cmd)
        return out
    def find(self,rates):
        for baud in dict.fromkeys(rates):
            self.speed(baud)
            if "OK" in self.ask("AT",check=False): return baud
            time.sleep(1.3);termios.tcflush(self.fd,termios.TCIFLUSH)
            os.write(self.fd,b"+++");print("escape",repr(self.read(1.7)),flush=True)
            if "OK" in self.ask("AT",check=False):
                self.ask("ATH",check=False);return baud
        raise RuntimeError("No AT response at expected speeds")

def start():
    run(["udevadm","control","--reload-rules"])
    run(["udevadm","trigger","--action=change","/sys/class/tty/ttyS0"])
    run(["udevadm","settle"])
    run(["systemctl","start","ModemManager"])
    for i in range(30):
        r=subprocess.run(["nmcli","-t","-f","DEVICE,TYPE","device"],capture_output=True,text=True)
        if "ttyS0:gsm" in r.stdout:break
        time.sleep(1)
    run(["nmcli","--wait","40","connection","up",PROFILE],timeout=45)

def main():
    if os.geteuid()!=0: sys.exit("Run as root")
    BACKUP.mkdir(mode=0o700,exist_ok=True)
    for path in [RULE,PROFILE_FILE]:
        dest=BACKUP/path.name
        if not dest.exists(): shutil.copy2(path,dest)
    original_rule=RULE.read_text()
    if 'BAUDRATE}="115200"' not in original_rule: sys.exit("Expected baseline 115200; refusing repeated test")
    port=None
    try:
        stop();port=Port();port.find([115200])
        port.ask("AT+IPR=?");port.ask("AT+IFC?");port.ask("AT+CPIN?")
        port.ask("AT+IFC=0,0")
        port.ask("AT+IPR="+str(TARGET),check=False)
        port.speed(TARGET);time.sleep(.5)
        port.ask("AT");port.ask("AT+IPR?")
        port.close();port=None
        rule=original_rule.replace('BAUDRATE}="115200"','BAUDRATE}="'+str(TARGET)+'", ENV{ID_MM_TTY_FLOW_CONTROL}="none"')
        RULE.write_text(rule)
        run(["nmcli","connection","modify",PROFILE,"serial.baud",str(TARGET),"ppp.baud",str(TARGET),"ppp.crtscts","no"])
        start()
        run(["ping","-I","ppp0","-c","3","-W","3","1.1.1.1"],timeout=15)
        for url in ["https://example.com/","https://check.torproject.org/"]:
            run(["curl","-4","--interface","ppp0","--silent","--show-error","--fail","--connect-timeout","12","--max-time","30","--output","/dev/null","--write-out","http=%{http_code} bytes=%{size_download} dns=%{time_namelookup} tcp=%{time_connect} tls=%{time_appconnect} total=%{time_total} speed=%{speed_download}\n",url],timeout=35)
        run(["ip","-s","link","show","ppp0"])
        print(Path("/proc/tty/driver/serial").read_text(),flush=True)
        run(["vcgencmd","get_throttled"])
        print("SPEED_TEST_PASSED_VOLATILE",TARGET,flush=True)
    except Exception as exc:
        print("TEST_FAILED",type(exc).__name__,str(exc),flush=True)
        if port is not None:port.close();port=None
        stop()
        port=Port()
        try:
            current=port.find([TARGET,115200,460800,230400])
            if current!=115200:
                port.ask("AT+IPR=115200",check=False);port.speed(115200);time.sleep(.5);port.ask("AT")
            port.ask("AT+IFC=2,2");port.ask("AT+IPR?")
        finally: port.close()
        RULE.write_text(original_rule)
        run(["nmcli","connection","modify",PROFILE,"serial.baud","115200","ppp.baud","115200","ppp.crtscts","no"])
        start()
        print("ROLLED_BACK_TO_115200",flush=True)
        sys.exit(1)

if __name__=="__main__": main()
