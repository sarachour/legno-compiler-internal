
import bmark.bmarks.biology as biology
import bmark.bmarks.columbia as columbia
import bmark.bmarks.audio as audio
import bmark.bmarks.quickstart as quickstart
import bmark.bmarks.other as other
import bmark.bmarks.kalman as kalman

# commented out any benchmarks that don't work.
BMARKS = biology.get_benchmarks() + \
         audio.get_benchmarks() + \
         columbia.get_benchmarks() + \
         other.get_benchmarks() + \
         kalman.get_benchmarks() + \
         quickstart.get_benchmarks()

# energy model: page 26 of thesis, chapter 2
def get_names():
    for _,bmark in BMARKS:
        yield bmark.name

def get_math_env(name):
    for menv,bmark in BMARKS:
        if bmark.name == name:
            return menv

    print("=== available benchmarks ===")
    for _,bmark in BMARKS:
        print("  %s" % bmark.name)
    raise Exception("unknown benchmark: <%s>" % name)

def get_prog(name):
    for _,bmark in BMARKS:
        if bmark.name == name:
            return bmark

    print("=== available benchmarks ===")
    for _,bmark in BMARKS:
        print("  %s" % bmark.name)


    raise Exception("unknown benchmark: <%s>" % name)
