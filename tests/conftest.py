import pytest

def pytest_addoption(parser):
    parser.addoption("-C", "--country_code", action="store", default="*", help="Country code of tests to run.")
    parser.addoption("-F", "--file_name", action="store", default="*", help="Test file name, * wildcard is accepted.")
    parser.addoption("--no-signature-check", action="store_true", default=False, help="Do not verify the signature")
