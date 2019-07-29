## Create virtual environment

create a new virtual environment
	virtualenv pyenv

activate it

	source pyenv/bin/activate

copy the `config.py` template.

 	cp util/config_local.py util/config.py

update `config.py` to point to the ip address of the oscilloscope. We only support Sigilent 1202X-E scopes. 

install all the packages in `packages.list`

	pip install -r packages.list

for generating the circuit graphs:

	sudo apt-get install graphviz

for programming the arduino board:

	sudo apt-get install arduino-mk

