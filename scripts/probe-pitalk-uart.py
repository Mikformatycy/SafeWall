#!/usr/bin/python3
"""Read modem identity, SIM lock and network status over GPIO UART. No PIN or write commands."""
import fcntl,os,re,select,termios,time,subprocess,sys
if subprocess.run(["systemctl","is-active","--quiet","ModemManager"]).returncode==0:
    sys.exit("Stop ModemManager before direct UART diagnostics; use mmcli for normal checks.")
port='/dev/serial0'
fd=os.open(port,os.O_RDWR|os.O_NOCTTY|os.O_NONBLOCK)
fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
original=termios.tcgetattr(fd)
def ask(command,wait=2):
    termios.tcflush(fd,termios.TCIFLUSH)
    os.write(fd,(command+'\r').encode('ascii'))
    end=time.monotonic()+wait;data=b''
    while time.monotonic()<end:
        if select.select([fd],[],[],min(.2,max(0,end-time.monotonic())))[0]:
            data+=os.read(fd,4096)
            if b'\r\nOK\r\n' in data or b'\r\nERROR\r\n' in data: break
    text=data.decode('ascii',errors='replace').strip()
    return re.sub(r'\d{12,}', '[identifier redacted]',text)
try:
    found=False
    for baud in (115200,9600):
        settings=termios.tcgetattr(fd)
        settings[0]=0;settings[1]=0;settings[2]=termios.CS8|termios.CREAD|termios.CLOCAL;settings[3]=0
        settings[4]=settings[5]=getattr(termios,'B'+str(baud));settings[6][termios.VMIN]=0;settings[6][termios.VTIME]=0
        termios.tcsetattr(fd,termios.TCSANOW,settings)
        answer=ask('AT')
        print('BAUD',baud,'AT:',repr(answer),flush=True)
        if re.search(r'(^|[\r\n])OK($|[\r\n])',answer):
            found=True;break
    if found:
        for command in ('AT+CGMI','AT+CGMM','AT+CPIN?','AT+CSQ','AT+COPS?','AT+CREG?','AT+CEREG?','AT+CGATT?'):
            print(command+':',repr(ask(command)),flush=True)
    else: print('NO AT RESPONSE: verify model, power state and UART jumpers.')
finally:
    termios.tcsetattr(fd,termios.TCSANOW,original)
    os.close(fd)
