import os
benchmarks = ["cos", \
        "cosc", \
        "spring", \
        "pend", \
        "vanderpol", \
        "forced", \
        "bont", \
        "gentoggle", \
        "pid", \
        "kalconst", \
        "smmrxn", \
        "heat1d"]

modes = ["default_maxfit_naive", \
        "default_minerr_naive", \
        "default_maxfit", \
        "default_minerr", \
]

for bmark in benchmarks:
    for idx,mode in enumerate(modes):
        flag = ""
        if idx == 0:
            flag="--lgraph"

        cmd = "time python3 legno_runner.py --config configs/{config}.cfg {bmark} {flag} --ignore-missing"
        conc_cmd = cmd.format(config=mode,bmark=bmark,flag=flag)
        print("echo %s" % conc_cmd);
        print("%s  > /dev/null 2>&1" % conc_cmd);



