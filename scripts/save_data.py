import serial
import sys
import datetime


assert(len(sys.argv) == 2)
outfile = sys.argv[1]

print("output file: %s" % outfile)

#serial_port = '/dev/ttyACM0';
serial_port = '/dev/tty.usbmodem1411';
baud_rate = 115200;


ser = serial.Serial(serial_port, baud_rate)
line = ser.readline().decode("utf-8");

WAITING = "waiting for serial input.."
RECEIVED = "received serial input.."
DONE = "<<EOF>>"
output_file = None

if WAITING in line:
    print("[[ Arduino is waiting for input ]]")
    input("   Press key when ready: ")
    # writing to serial
    ser.write("x\r\n".encode());
    # overwrite file
    write_to_file_path = outfile;
    output_file = open(write_to_file_path, "w+");

    line = ser.readline().decode("utf-8");
    while WAITING in line:
        line = ser.readline().decode("utf-8");
    assert(RECEIVED in line)

elif DONE in line:
    print("[[ Arduino is finished running experiments.]]")
    sys.exit(0)
else:
    print("[[ Arduino is desynchronized. Please reprogram the device]]")
    sys.exit(1)

try:
    while True:
        line = ser.readline();
        line = line.decode("utf-8") #ser.readline returns a binary, convert to string
        if DONE in line:
            break;

        time = datetime.datetime.now()
        print("%s: %s" % (time,line.strip()));
        output_file.write("%s\n" % time);
        output_file.write(line);

    print("<FINISHED>")
    output_file.close()

except KeyboardInterrupt:
    print("closing file..")
    output_file.close()
