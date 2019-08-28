
calibrate:
	python3 grendel.py --no-oscilloscope --calib-obj max_fit calibrate max_fit_calibrate.grendel 
	python3 grendel.py --no-oscilloscope --calib-obj min_error calibrate max_fit_calibrate.grendel 

profile:
	python3 grendel.py --no-oscilloscope --calib-obj max_fit profile max_fit_calibrate.grendel 
	python3 grendel.py --no-oscilloscope --calib-obj min_error profile max_fit_calibrate.grendel 

make-models:
	python3 model_builder.py infer --calib-obj max_fit --visualize
	python3 model_builder.py infer --calib-obj min_error --visualize

clean-models:
	rm -rf outputs/datasets
	rm -rf MODELS*
	rm -rf model.db
