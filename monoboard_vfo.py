# Si5351 VFO with rotary encoder and OLED display for RP2040 Zero
# Updated: 20250416
# Peter, VK3TPM, https://blog.marxy.org
#
# Uses i2c bus 1 which is SCL=3, SDA=2
# 
# Encoder Edge pins
# GND, VCC, Switch, A, B
# Note that the large font ssd1306 takes a while to load up on start

from machine import Pin, I2C, Timer
import time
import math
#import ssd1306 # https://github.com/kwankiu/ssd1306wrap/
import sh1106 # https://github.com/robert-hh/SH1106
import si5351 # https://github.com/hwstar/Si5351_Micropython

# GPIO Pins for Rotary Encoder
# GND, VCC, Switch, A, B
CLKPin = Pin(27, Pin.IN, Pin.PULL_UP)  # A channel
DTPin = Pin(26, Pin.IN, Pin.PULL_UP)   # B channel
SWPin = Pin(28, Pin.IN, Pin.PULL_UP)   # Button (optional)

# Define debounce time (in milliseconds)
DEBOUNCE_TIME = 500 # 200

# Set up a flag to handle debounce state
last_pressed_time = 0
debounce_timer = Timer(-1)

SDAPin = Pin(2)
SCLPin = Pin(3)
# For RP2040 Zero use pins 2 and 3 for I2C bus 1
i2c = machine.I2C(1, scl=SCLPin, sda=SDAPin, freq=400000) # 400kHz
#i2c = machine.I2C(1)

# Instantiate i2c objects
oled = sh1106.SH1106_I2C(128, 64, i2c, rotate=180)
clkgen = si5351.SI5351(i2c)

# Variables to track position
encoder_position = 0
last_state = CLKPin.value()

start_frequency = 7100000
min_step_power = 1
max_step_power = 6
initial_step_power = 3
step = int(math.pow(10, initial_step_power)) # gets changed by button pushes
step_power = initial_step_power

frequency = start_frequency

def main():
    #print("started")
    global CLKPin, SWPin
    clkgen.init(si5351.CRYSTAL_LOAD_0PF, 25000000, -4000)
    setFrequency(frequency)
    clkgen.output_enable(si5351.CLK0, True)
    clkgen.drive_strength(si5351.CLK0, si5351.DRIVE_2MA) # up to DRIVE_8MA
    oled_display(str(frequency))
    # Attach interrupt to CLK pin (rising/falling edge)
    # https://docs.micropython.org/en/latest/library/machine.Pin.html#machine.Pin.irq
    # options: Pin.IRQ_RISING | Pin.IRQ_FALLING | Pin.IRQ_LOW_LEVEL | Pin.IRQ_HIGH_LEVEL
    CLKPin.irq(trigger=Pin.IRQ_FALLING, handler=rotary_callback)
    SWPin.irq(trigger=Pin.IRQ_FALLING, handler=button_callback)

    # Main loop
    while True:
        #print("Encoder Position:", encoder_position)
        time.sleep(0.5)  # Reduce CPU usage
    
def change_step():
    global step, min_step_power, max_step_power, step_power
    step_power += 1
    if step_power > max_step_power:
        step_power = min_step_power
    step = math.pow(10, step_power)
    
    #print(f"pow = {step_power}, step = {step}")
    
def oled_display(message):
    oled.fill(0)#clear
    oled.text(message,0,0)  #x, y, size
    draw_step(step)
    oled.show()
    print(f"{message}")
    
def draw_step(step):
    """Draw a line under the step digit"""
    # https://docs.micropython.org/en/v1.15/library/framebuf.html
    char_width = 8
    underline_y = 10
    text_width = char_width * (len(str(frequency)))
    line_start_x = text_width - (char_width * step_power) - char_width
    oled.hline(line_start_x, underline_y, char_width, 1) # x, y, w, c
                    
def rotary_callback(pin):
    """Interrupt handler for rotary encoder falling edge"""
    global encoder_position, frequency
    if DTPin.value() == 1:
        encoder_position += 1  # Clockwise
        frequency += int(math.pow(10, step_power))
    else:
        encoder_position -= 1  # Counterclockwise
        frequency -= int(math.pow(10, step_power))
    setFrequency(frequency)
    oled_display(str(frequency))
    print(f"Encoder Position: {encoder_position}, Frequency: {frequency}")


# Optional: Detect button press
def button_callback(pin):
    global frequency
    global last_pressed_time

    current_time = time.ticks_ms()
    if time.ticks_diff(current_time, last_pressed_time) > DEBOUNCE_TIME:
        last_pressed_time = current_time
        print("Switch Pressed")
        change_step()
        oled_display(str(frequency))

def setFrequency(newFrequency):
    #print(newFrequency)
    clkgen.set_freq(si5351.CLK0, newFrequency * 100) # 10Mhz 1000000000
        
if __name__ == "__main__":
    main()
