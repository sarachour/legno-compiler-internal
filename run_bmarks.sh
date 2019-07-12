CONFIG="standard_naive.cfg"
#CONFIG="extended_naive.cfg"
#CONFIG="unrestricted_naive.cfg"
#python3 legno_runner.py --search --arco --config configs/${CONFIG} cosc
#python3 legno_runner.py --search --arco --config configs/${CONFIG} micro-osc
python3 legno_runner.py --search --arco --config configs/${CONFIG} vanderpol
python3 legno_runner.py --search --arco --config configs/${CONFIG} forced-vanderpol
python3 legno_runner.py --search --arco --config configs/${CONFIG} pend
python3 legno_runner.py --search --arco --config configs/${CONFIG} pend-nl
python3 legno_runner.py --search --arco --config configs/${CONFIG} spring
python3 legno_runner.py --search --arco --config configs/${CONFIG} spring-nl
python3 legno_runner.py --search --arco --config configs/${CONFIG} robot
python3 legno_runner.py --search --arco --config configs/${CONFIG} heat1d-g4
python3 legno_runner.py --search --arco --config configs/${CONFIG} heat1d-g8
python3 legno_runner.py --search --arco --config configs/${CONFIG} heat1d-g17
