
calibrate:
	python3 grendel.py max_fit_calibrate.grendel --calibrate --no-oscilloscope --calib-obj max_fit

profile:
	python3 grendel.py max_fit_calibrate.grendel --profile --bootstrap --no-oscilloscope --calib-obj max_fit

make-models:
	python3 model_builder.py infer --calib-obj max_fit
	python3 model_builder.py infer --calib-obj min_obj

clean-models:
	rm -rf outputs/datasets
	rm -rf MODELS*
	rm -rf model.db
