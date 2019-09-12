
calibrate-minerr:
	python3 -u grendel.py calibrate --no-oscilloscope --calib-obj min_error device-state/calibrate/min_error.grendel 

calibrate-maxfit:
	python3 -u grendel.py calibrate --no-oscilloscope --calib-obj max_fit device-state/calibrate/max_fit.grendel 

profile-maxfit:
	python3 -u grendel.py profile --no-oscilloscope --calib-obj max_fit device-state/calibrate/max_fit.grendel 

profile-minerr:
	python3 -u grendel.py profile --no-oscilloscope --calib-obj min_error device-state/calibrate/min_error.grendel 

models:
	python3 model_builder.py infer --calib-obj min_error 
	python3 model_builder.py infer --calib-obj max_fit 

clean-models:
	rm -rf device-state/datasets
	rm -rf device-state/models/*
	rm -rf device-state/model.db
