
VISUALIZE=--visualize
VISUALIZE=
NOTIFY=afplay /System/Library/Sounds/Ping.aiff 

calibrate-minerr:
	python3 -u grendel.py calibrate --no-oscilloscope --calib-obj min_error outputs/calibrate/min_error.grendel 
	${NOTIFY}

calibrate-maxfit:
	python3 -u grendel.py calibrate --no-oscilloscope --calib-obj max_fit outputs/calibrate/max_fit.grendel 
	python3 -u grendel.py calibrate --no-oscilloscope --calib-obj min_error outputs/calibrate/max_fit.grendel 
	${NOTIFY}

profile-maxfit:
	python3 -u grendel.py profile --no-oscilloscope --calib-obj max_fit outputs/calibrate/max_fit.grendel 
	python3 -u grendel.py profile --no-oscilloscope --calib-obj min_error outputs/calibrate/max_fit.grendel 
	${NOTIFY}

profile-minerr:
	python3 -u grendel.py profile --no-oscilloscope --calib-obj min_error device-state/calibrate/min_error.grendel 
	${NOTIFY}

models-maxfit:
	python3 model_builder.py infer --calib-obj max_fit ${VISUALIZE}

models-minerr:
	python3 model_builder.py infer --calib-obj min_error ${VISUALIZE}

clean-executions:
	rm -f outputs/experiments.db
	rm -rf outputs/legno/*/*/grendel
	rm -rf outputs/legno/*/*/lscale-adp
	rm -rf outputs/legno/*/*/lscale-diag
	rm -rf outputs/legno/*/*/out-waveform
	rm -rf outputs/legno/*/*/plots
	rm -rf outputs/legno/*/*/sim
	rm -f outputs/legno/*/*/times/srcgen.txt
	rm -f outputs/legno/*/*/times/lscale.txt

clean-models:
	rm -rf device-state/datasets
	rm -rf device-state/models/*
	rm -rf device-state/model.db
