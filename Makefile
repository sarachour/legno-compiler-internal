
calibrate:
	python3 -u grendel.py calibrate --no-oscilloscope --calib-obj max_fit device-state/calibrate/max_fit.grendel 
	python3 -u grendel.py calibrate --no-oscilloscope --calib-obj min_error device-state/calibrate/max_fit.grendel 

profile:
	python3 -u grendel.py profile --no-oscilloscope --calib-obj max_fit device-state/calibrate/max_fit.grendel 
	python3 -u grendel.py profile --no-oscilloscope --calib-obj min_error device-state/calibrate/max_fit.grendel 

make-models:
	python3 model_builder.py infer --calib-obj max_fit 
	python3 model_builder.py infer --calib-obj min_error 

clean-models:
	rm -rf device-state/datasets
	rm -rf device-state/models/*
	rm -rf device-state/model.db
