import smbus
import time
import array
import requests

# This code are using 0 i2c bus on Orange pi poard
bus = smbus.SMBus(0)  # Rev 1 Pi uses 0

def send_score(a, b):
  # call rest api tu push scores to web interface which put this score to video
  try:
    header = {'Authorization' : 'TOKEN', 'Content-type': 'application/json'}
    response = requests.post('http://XXX.XXX.XXX.XXX:5080/KlaskApp/app/api/score', json = {"a": a,"b": b, "id": "uuid123"},  headers=header)
    print("sent: a:{}, b:{}, repsponse:{}", a, b, response.json())  
  except:
    print("Message send error")

# wrapper function to make sned out easiest and this will conains any onther checks
def write_out(DEVICE, PORT, VALUE):
  bus.write_byte_data(DEVICE, PORT, VALUE)

# LCD and leds visiblitiy check function
def lcd_init():
  for i in range(0,10):
    # check all lcd and led at start time
    write_out(DEVICE_LCD,OLATA,a[i])
    write_out(DEVICE_LCD,OLATB,b[i])
    write_out(DEVICE_A,OLATB,pow(2,i))
    write_out(DEVICE_B,OLATB,pow(2,i))
    print("num:", i, " binary value:", a[i])
    time.sleep(0.2)

#init lcd numbers which represend all numbers in binary number. This is depend on 7 segment LCD and MCP23017 (or any relevant IC) port connections.
a = []
a.append(132) # 0
a.append(190) # 1
a.append(200) # 2
a.append(152) # 3
a.append(178) # 4
a.append(145) # 5
a.append(129) # 6
a.append(180) # 7
a.append(128) # 8
a.append(144) # 9

# oterh LCD numbers mapping
b=[]
b.append(33)  # 0
b.append(125) # 1
b.append(19)  # 2
b.append(25)  # 3
b.append(77)  # 4
b.append(137) # 5
b.append(129) # 6
b.append(45)  # 7
b.append(1)   # 8
b.append(9)   # 9

#set up constans
DEVICE_LCD = 0x20 # LCD
DEVICE_A   = 0x21 # light scrores and button for A player
DEVICE_B   = 0x22 # light srores and buttons for B player

IODIRA = 0x00 # Pin direction register
IODIRB = 0x01
OLATA  = 0x01 # Register for outputs 1.st side
OLATB  = 0x14 # REgister for output 2.nd side
GPIOA  = 0x12 # Register for a inputs
GPIOB  = 0x12 # register for b input

#Deult we doesn't have LCD 
lcd = False

a_score = 0
b_score = 0
max_score = 5
end = 0

# Set all GPA pins as outputs by setting
# all bits of IODIRA register to 0

#detect LCD_devices
try:
  bus.write_byte_data(DEVICE_LCD,IODIRA,0x00)
  bus.write_byte_data(DEVICE_LCD,IODIRB,0x00)
  lcd = True
except:
  print("Please attach LCD module to 000 bus")

#detect A and B players led output and button input IC 
try:
  bus.write_byte_data(DEVICE_A,IODIRA,0x00)
  bus.write_byte_data(DEVICE_B,IODIRA,0x00)
  lcd = True
except:
  print("Please attach BUTTON module to 010 bus")


# Set output all 7 output bits to 0
write_out(DEVICE_LCD,OLATA,255)
write_out(DEVICE_LCD,OLATB,255)

# run initializer to check all lcd segment and led
lcd_init()

 
# Set all bits to zero
bus.write_byte_data(DEVICE_LCD,OLATA,255)
bus.write_byte_data(DEVICE_LCD,OLATB,255)
write_out(DEVICE_A,OLATB,1)
write_out(DEVICE_B,OLATB,1)
write_out(DEVICE_LCD,OLATA,a[a_score])
write_out(DEVICE_LCD,OLATB,b[b_score])
send_score(a_score, b_score)

# let's start the game ...
while True:
  # we protect this flow to can run if we have any exception (like lost LCD or any IC connection)
  try:
    # read input form 2 buttons
    Switcha = bus.read_byte_data(DEVICE_A,GPIOA)
    Switchb = bus.read_byte_data(DEVICE_B,GPIOA)

    # if A nd B player press buttons at same time then reset current game
    if Switcha & 0b10000000 == 0b10000000 and Switchb & 0b10000000 == 0b10000000:
      a_score = 0
      b_score = 0
      end = 0
      write_out(DEVICE_LCD,OLATA,a[a_score])
      write_out(DEVICE_LCD,OLATB,b[b_score])
      write_out(DEVICE_A,OLATB,1)
      write_out(DEVICE_B,OLATB,1)
      send_score(a_score, b_score)
      time.sleep(1)

    # if pushed A players button
    if Switcha & 0b10000000 == 0b10000000 and end == 0:
      a_score += 1
      write_out(DEVICE_LCD,OLATA,a[a_score])
      write_out(DEVICE_A,OLATB,pow(2,a_score))
      send_score(a_score,b_score)

    #if pushed B players button
    if Switchb & 0b10000000 == 0b10000000 and end == 0:
      b_score += 1
      write_out(DEVICE_LCD,OLATB,b[b_score])
      write_out(DEVICE_B,OLATB,pow(2,b_score))
      send_score(a_score, b_score)
    
    # if A player win set game end and hide B player score on LCD panel
    if a_score > max_score:
      a_score=0
      bus.write_byte_data(DEVICE_LCD,OLATB,255)
      end = 1

    # if B player win set game end and hide B player score on LCD panel
    if b_score > max_score:
      b_score=0
      bus.write_byte_data(DEVICE_LCD,OLATA,255)
      end = 1

    # if any button pressed then sleep to prevent duplicate press
    if Switcha & 0b10000000 == 0b10000000 or Switchb & 0b10000000 == 0b10000000:
      time.sleep(0.5)

    # default sleep to free up any other threads
    time.sleep(0.05)
  except:
    print("unknow error")
