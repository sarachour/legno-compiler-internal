## Lab Bench Requirements

You need the following hardware:

1. HDACv2 Chip
2. Arduino Due 
	- SDA pin used as trigger for oscilloscope
        - Programmed to run the `arduino_due/arduino_driver/arduino_driver.ino` routine.
	- Plugged into your computer via the programming interface. (native not supported for now)

3. Sigilent 1020XE Oscilloscope (optional), or unsupported Oscilloscope.
4. Voltage converter circuit for converting Arduino DUE signals to HDACv2 signals.


## Installing Dependences

The `arduino_client.py` script requires the following packages be installed:

	pip3 pyserial numpy matplotlib scipy construct fastdtw sklearn
	
## Getting Started

You can run an example application on the lab setup with the following command:
 
	python3 arduino_client.py --ip <oscilloscope_ip> --script scripts/test_sin.grendel


You can also enter interpreter mode with the following command: 
	
	python3 arduino_client.py --ip <oscilloscope_ip>
	
### Setting up an Unsupported Oscilloscope:

You can use an unsupported oscilloscope with a grendel script as well. Simply connect the `SDA` pin on the board the the external trigger probe on the oscilloscope. Configure the edge trigger to trigger on alternating. When the `arduino_driver` starts the experiment, it toggles the external trigger on the SDA pin.

If you have a Sigilent1020XE Oscilloscope, the `arduino_client.py` script is able to remotely configure the voltage/time scale, reconfigure the trigger before each run and read data from the device.



