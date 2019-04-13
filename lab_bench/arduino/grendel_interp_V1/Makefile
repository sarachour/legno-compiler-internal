
all: interp upload

interp:
	arduino-cli compile --fqbn arduino:sam:arduino_due_x_dbg .
upload:
	arduino-cli upload -p /dev/tty.usbmodem14101 --fqbn arduino:sam:arduino_due_x_dbg .
