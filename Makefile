
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

clean-models:
	rm -rf device-state/datasets
	rm -rf device-state/models/*
	rm -rf device-state/model.db
