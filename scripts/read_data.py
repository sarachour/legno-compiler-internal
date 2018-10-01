import sys
import datetime
import os
import json

START = 0
META = 1
HEADER = 2
BODY = 3
NODATA = -1

def set_nested_dict(this_dict,key_path,value):
    curr_dict = this_dict
    for key in key_path[:-1]:
        if not key in curr_dict:
            curr_dict[key] = {}
        curr_dict = curr_dict[key]

    last_key = key_path[-1]
    curr_dict[last_key] = value


if len(sys.argv) < 3:
    print("process_data.py output_file result_dir")
    sys.exit(1)

filename = sys.argv[1]
outdir = sys.argv[2]

def write_data(metadata,header,values,index):
    print(metadata)
    trial = int(metadata['trial'])
    benchmark = metadata['benchmark']
    if not os.path.exists(outdir):
        os.mkdir(outdir)

    outfile = "%s/%s_%d_%d.json" % (outdir,benchmark,trial,index)

    json_data = {}
    json_data['meta'] = metadata
    json_data['meta']['benchmark'] = benchmark
    json_data['meta']['trial'] = trial


    json_data['values'] = {}
    json_data['time'] = []

    for field in header.values():
        if field == "time":
            continue
        json_data['values'][field] = []

    for row in values:
        for index,value in enumerate(row):
            field = header[index]
            if field == "time":
                json_data['time'].append(value)
            else:
                json_data['values'][field].append(value)


    for vs in json_data['values'].values():
        assert(len(vs) == len(json_data['time']))

    with open(outfile,'w') as fh:
        fh.write(json.dumps(json_data))




timecode = True
curr_time = None
data_state = -1
metadata = None
header = None
header_list = None
index = 0
values = []
value_row = []
times = []
base_time = None

n_fields = -1

with open(filename,'r') as fh:

    trial_indexes = {}
    for line in fh:
        if not timecode:
            timecode = not timecode

            #TRANSITIONS
            if "DATA_START" in line:
                data_state = START
                continue

            elif "start_meta" in line:
                data_state = META
                metadata = {}
                continue

            elif "end_meta" in line:
                data_state = NODATA
                continue

            elif "start_header" in line:
                data_state = HEADER
                header = {}
                continue

            elif "end_header" in line:
                data_state = NODATA
                continue

            elif "start_data" in line:
                data_state = BODY
                n_fields = len(header.keys())
                values = []
                value_row = []
                base_time = None
                continue

            elif "end_data" in line:
                trial = metadata['trial']
                if not trial in trial_indexes:
                    trial_indexes[trial] = 0
                write_data(metadata,header,values,trial_indexes[trial])
                print("-> Parsed Trial %s" % metadata['trial'])
                trial_indexes[trial] += 1
                data_state = NODATA
                metadata = None
                header = None
                values = None
                value_row = None
                continue


            # PARSING
            if data_state == META:
                  args = line.strip().split(",")
                  set_nested_dict(metadata,args[:-1],args[-1])

            elif data_state == HEADER:
                args = line.strip().split(",")
                if args[0] == "field":
                    header[int(args[1])] = args[2]

                elif args[1] == "num":
                    n_fields = int(args[1])

            elif data_state == BODY:
                value = float(line.strip())
                field = header[len(value_row)]
                if field == "time":
                    if base_time == None:
                        base_time = value

                    delta = value - base_time
                    value_row.append(delta)

                else:
                    value_row.append(value)

                if len(value_row) == n_fields:
                    values.append(value_row)
                    value_row = []


            else:
                continue


        else:
            timecode = not timecode
            timestr = line.strip()
            if "." in timestr:
                fmt = "%Y-%m-%d %H:%M:%S.%f"
            else:
                fmt = "%Y-%m-%d %H:%M:%S"

            curr_time = datetime.datetime.strptime(timestr,fmt)

