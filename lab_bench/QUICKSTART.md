## Lab Bench Requirements

You need the following hardware:

1. HDACv2 Chip
2. Arduino Due 
	- SDA pin used as trigger for oscilloscope
        - Programmed to run application from the `arduino/arduino_due` directory
	- Plugged into your computer via the programming interface. (native not supported for now)

3. Sigilent 1020XE Oscilloscope
4. Breadboard for Voltage Divider


## Getting Started

You can run an example application on the lab setup with the following command:
 
	python3 arduino_client.py --ip <oscilloscope_ip> --script scripts/test_sin.grendel


You can also enter interpreter mode with the following command: 
	
	python3 arduino_client.py --ip <oscilloscope_ip>
