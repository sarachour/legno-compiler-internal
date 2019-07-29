
def get_arduino_path():
  import os
  for root, dirs, files in os.walk("/dev/", topdown=False):
    for name in files:
      if "tty.usbmodem" in name:
        return "/dev/%s" % name

      elif "ttyACM" in name:
        return "/dev/%s" % name

  return None


OUTPUT_PATH="outputs/"
GPKIT_SOLVER="mosek_cli"
EXPERIMENT_DB="outputs/experiments.db"
STATE_DB="state.db"
OSC_IP=""
ARDUINO_FILE_DESC=get_arduino_path()
#GPKIT_SOLVER="cvxopt"
TIME_DIR="%s/times/" % OUTPUT_PATH
DATASET_DIR="%s/datasets/" % OUTPUT_PATH
