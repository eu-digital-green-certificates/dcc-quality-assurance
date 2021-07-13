# Automated Test Suite

## Introduction

The automated test suite is based on the pytest framework and 
is automatically executed on all pull requests that are issued
towards this repo. 

It may also be used as an offline checking tool for issuers
or anyone who is working with digital covid certificates. 

## Installation

We suggest to use Python 3.9 or later and then use pip to 
install the dependencies. The latter can be done with the 
following statement: 

```
pip install -r tests/requirements.txt
```
Notice that on some systems you may need to replace `pip` with
`pip3` when the first points to a Python 2.7 version.

Some of the python packages may also depend on binary packages
that have to be installed (e.g. wheel and libzbar)

On a fresh *Ubuntu 20.10 Minimal* VM, the following receipe works for us: 
```
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-wheel git libzbar0
sudo pip install --upgrade pip

git clone https://github.com/eu-digital-green-certificates/dcc-quality-assurance.git
cd dcc-quality-assurance

# Setting up a virtual environment for the dependencies
python -m venv venv --prompt DCC-Test
source venv/bin/activate
pip install -r tests/requirements.txt
``` 

## Usage

Make sure that you are in the root directory of the repo
(in our case it is `~/dcc-quality-assurance`) and that your
virtual environment is active. 

Then simply run
```
pytest
```
To


