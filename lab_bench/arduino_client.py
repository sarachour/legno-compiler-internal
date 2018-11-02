import lib.command as cmd
import sys

while True:
    line = input("ardc>> ")
    if line == "quit":
        sys.exit(0)
    command_obj = cmd.parse(line)
    if not command_obj is None:
        print(command_obj)


