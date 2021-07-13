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

On a fresh *Ubuntu 21.04 Minimal* VM, the following receipe works for us: 
```
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-wheel python3-venv git libzbar0
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
This will run all tests against all examples **without** the
special cases. 

Special cases are purposefully excluded from the default run
because they are allowed to fail: A special case is a type of
DCC QR Code which has been issued in production but is known
to cause problems with verification or does not adhere to the
standard. 

To include the special case, add the following parameter: 
```
pytest --include-special
```

### Additional parameters

* **-C**=&lt;2-letter-code&gt;, **--country-code**=&lt;2-letter-code&gt; - 
    Only include DCCs from the given country (relies on
    directory structure, see below)
* **--include-special** - Also test the special cases
    (relies on directory structure)
* **--no-signature-check** - Do not verify the signature.
    Corresponding test cases will be skipped. This is 
    useful for testing production codes or codes from
    different test environments.
* **--allow-multi-dcc** (deprecated) - Do not yield an 
    error when more than one DCC is in one QR code
* **--warn-timedelta** (deprecated) - Show a warning when
    in recovery certificates the certificate validity 
    differs more than 14 days from the medical validity 
    date
* **-vs** (pytest standard parameters for verbose 
     and captured stdout) - will print detailed DCC info 
     into the console 
* **--html=**&lt;report-file-name&gt; - Write a test report
    in HTML format



### Directory structure

The checks on directory structure with country code and version
were included to assist with organizing the international call
for mutual testing. Of course this does not affect the validity
of the certificates and you are free to derive your own version
which does not perform the directory and file name checks. 

To use the test suite without changes, these rules must be 
followed:
* File names must begin with the certificate type: 
    TEST, VAC or REC and end with .png
* Files must be placed in a folder following the structure
    `<2-letter-code>/<schema-version>/<file>` or 
    `<2-letter-code>/<schema-version>/specialcases/<file>`

## Limitations

### Schema validation

The schema is currently taken from the github repo of the
DCC development. 

It is also rewritten during loading to make it more strict, 
so we can detect unnecessary fields. This will cause the 
schema check to fail on certificates which are technically
correct but contain extra fields.

### Signature validation

Key IDs (KID) and public keys are taken from the T-Systems/SAP 
DCC reference backend connected to the the DCC Acceptance 
Environment. Please note that the availability of this backend
is based on best effort.

If a key is not present in that environment, the signature
validation will fail. It can be skipped with the 
`--no-signature-check` parameter. 

