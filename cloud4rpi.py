from time import sleep
import sys
import random
import cloud4rpi
import rpi
import spidev
import os

# Put your device token here. To get the token,
# sign up at https://cloud4rpi.io and create a device.
DEVICE_TOKEN = '******' # Your token

# Constants
DATA_SENDING_INTERVAL = 1  # secs
DIAG_SENDING_INTERVAL = 60  # secs
POLL_INTERVAL = 0.5  # 500 ms
flex_channel = 0

# Open SPI bus
spi = spidev.SpiDev()
spi.open(0,0)
spi.max_speed_hz=1000000

# Function to read SPI data from MCP3008 chip
# Channel must be an integer 0-7
def ReadChannel(channel):
  adc = spi.xfer2([1,(8+channel)<<4,0])
  data = ((adc[1]&3) << 8) + adc[2]
  return data
 
# Function to convert data to voltage level,
# rounded to specified number of decimal places.
def ConvertVolts(data,places):
  volts = (data * 3.3) / float(1023)
  volts = round(volts,places)
  return volts
 
def get_data():
    data = ReadChannel(flex_channel)
    return data

def get_volts():
    flex_level = ReadChannel(flex_channel)
    volts = ConvertVolts(flex_level,2)
    return volts

def get_status():
    flex_level = ReadChannel(flex_channel)
    volts = ConvertVolts(flex_level,2)
    if volts > 1.69 :
        return 'THRESHOLD CROSSED'
   else if volts < 1.3 :
        return 'THRESHOLD CROSSED'
    else:
        return 'TREE IS OK'
    
def main():
    # Put variable declarations here
    # Available types: 'bool', 'numeric', 'string'
    variables = {
        'VALUE': {
            'type': 'numeric',
            'bind': get_data
            },
        'VOLTAGE': {
            'type': 'numeric',
            'bind': get_volts
            },
        'STATUS': {
            'type': 'string',
            'bind': get_status
        }
    }

    diagnostics = {
        'IP Address': rpi.ip_address,
        'Host': rpi.host_name,
        'Operating System': rpi.os_name
    }
    device = cloud4rpi.connect(DEVICE_TOKEN)

    # Use the following 'device' declaration to enable the MQTT traffic encryption (TLS).

    try:
        device.declare(variables)
        device.declare_diag(diagnostics)

        device.publish_config()

        # Adds a 1 second delay to ensure device variables are created
        sleep(1)

        data_timer = 0
        diag_timer = 0

        while True:
            if data_timer <= 0:
                device.publish_data()
                data_timer = DATA_SENDING_INTERVAL

            if diag_timer <= 0:
                device.publish_diag()
                diag_timer = DIAG_SENDING_INTERVAL

            sleep(POLL_INTERVAL)
            diag_timer -= POLL_INTERVAL
            data_timer -= POLL_INTERVAL

    except KeyboardInterrupt:
        cloud4rpi.log.info('Keyboard interrupt received. Stopping...')

    except Exception as e:
        error = cloud4rpi.get_error_message(e)
        cloud4rpi.log.exception("ERROR! %s %s", error, sys.exc_info()[0])

    finally:
        sys.exit(0)

if __name__ == '__main__':
    main()
