## Create virtual environment

virtualenv pyenv

source pyenv/bin/activate

cp util/config_local.py util/config.py

update `config.py` to point to the ip address of the oscilloscope. We only support Sigilent 1202X-E scopes. 

install all the packages in packages.list

this is optional

sudo apt-get install graphviz
