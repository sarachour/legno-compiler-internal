def get_arduino_path():
  import os
  for root, dirs, files in os.walk("/dev/", topdown=False):
    for name in files:
      if "tty.usbmodem" in name:
        return "/dev/%s" % name

      elif "ttyACM" in name:
        return "/dev/%s" % name

  return None

def mkdir_if_dne(dirname):
  import os
  if not os.path.exists(dirname):
    os.makedirs(dirname)

OUTPUT_PATH="outputs"
mkdir_if_dne(OUTPUT_PATH)
#GPKIT_SOLVER="mosek_cli"
GPKIT_SOLVER="cvxopt"
EXPERIMENT_DB="outputs/experiments.db"

OSC_IP="128.30.71.225"
ARDUINO_FILE_DESC=get_arduino_path()

DEVSTATE_PATH="device-state"
mkdir_if_dne(DEVSTATE_PATH)
CALIBRATE_DIR="%s/calibrate" % DEVSTATE_PATH
mkdir_if_dne(CALIBRATE_DIR)
STATE_DB="%s/state.db" % DEVSTATE_PATH
MODEL_DB="%s/model.db" % DEVSTATE_PATH
MODEL_PATH="%s/models" % DEVSTATE_PATH
DATASET_DIR="%s/datasets/" % DEVSTATE_PATH

