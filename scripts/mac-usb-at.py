"""Direct EG25 USB AT transport on macOS. Requires pyusb and Homebrew libusb.
No configuration changes at import. Commands are sent only by caller.
"""
import time,json
import usb.core,usb.util,usb.backend.libusb1
class Modem:
 def __init__(self):
  backend=usb.backend.libusb1.get_backend(find_library=lambda n:'/opt/homebrew/lib/libusb-1.0.dylib')
  self.d=usb.core.find(idVendor=0x2c7c,idProduct=0x0125,backend=backend)
  if self.d is None: raise RuntimeError('Quectel USB modem not detected')
  i=self.d.get_active_configuration()[(2,0)]
  self.rx=next(e for e in i if usb.util.endpoint_direction(e.bEndpointAddress)==usb.util.ENDPOINT_IN and usb.util.endpoint_type(e.bmAttributes)==usb.util.ENDPOINT_TYPE_BULK)
  self.tx=next(e for e in i if usb.util.endpoint_direction(e.bEndpointAddress)==usb.util.ENDPOINT_OUT and usb.util.endpoint_type(e.bmAttributes)==usb.util.ENDPOINT_TYPE_BULK)
  usb.util.claim_interface(self.d,2)
 def at(self,cmd,timeout=5):
  self.tx.write((cmd+'\r').encode(),timeout=1500)
  end=time.monotonic()+timeout;data=b''
  while time.monotonic()<end:
   try: data+=bytes(self.rx.read(4096,timeout=300))
   except usb.core.USBTimeoutError: continue
   if b'\r\nOK\r\n' in data or b'ERROR' in data: break
  response=data.decode(errors='replace')
  secret=cmd.startswith('AT+CPIN=')
  print('AT_RESULT',json.dumps({'command':'[SIM PIN redacted]' if secret else cmd,'response':response.replace(cmd,'[SIM PIN redacted]') if secret else response}),flush=True)
  return response
 def close(self):
  try: usb.util.release_interface(self.d,2)
  finally: usb.util.dispose_resources(self.d)
