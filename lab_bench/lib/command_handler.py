import lab_bench.lib.command as cmd
import sys


def execute(state,line):
    if line.startswith("#"):
        print(line)
        print("<comment, skipping..>")
        return True

    command_obj = cmd.parse(line)
    if command_obj is None:
        print("<unknown command: (%s)>" % line)
        return False

    if not command_obj.test():
        print("[error] %s" % command_obj.error_msg())
        return False


    if isinstance(command_obj,cmd.Command):
        command_obj.execute(state)
        return True

    else:
        print("unhandled..")
        print(command_obj)
        return False

def main_stdout(state):
    while True:
        line = input("ardc>> ")
        if line == "quit":
            sys.exit(0)
        elif line.strip() == "":
            continue

        execute(state,line)


def main_script_calibrate(state,filename):
    successes = 0
    failures = 0
    with open(filename,'r') as fh:
        for idx,line in enumerate(fh):
            if line == "quit":
                sys.exit(0)
            elif line.strip() == "":
                continue

            if line.startswith("#"):
                print(line)
                print("<comment, skipping..>")

            command_obj = cmd.parse(line)
            succ = cmd.calibrate(state,command_obj)
            if succ is None:
                continue

            if succ:
                successes += 1
            else:
                failures += 1


    print("SUCCESSES: %d" % successes)
    print("FAILURES: %d" % failures)

def main_script(state,filename):
    with open(filename,'r') as fh:
        for idx,line in enumerate(fh):
            print("ardc>> %s" % line.strip())
            if line == "quit":
                sys.exit(0)
            elif line.strip() == "":
                continue
            if not (execute(state,line.strip())):
                sys.exit(1)

