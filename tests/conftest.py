import os
import pytest
from glob import glob
from pathlib import Path
from DccQrCode import DccQrCode

def pytest_addoption(parser):
    parser.addoption("-C", "--country-code", action="store", default="*", help="Country code of tests to run.")
    parser.addoption("--no-signature-check", action="store_true", default=False, help="Do not verify the signature")
    parser.addoption("--forbid-extra-fields", action="store_true", default=False, help="Only allow fields defined in schema")
    parser.addoption("--include-special", action="store_true", default=False, help="Include special cases")
    parser.addoption("--allow-multi-dcc", action="store_true", default=False, help="Allow multiple DCC in one QR code")

def pytest_generate_tests(metafunc):
    def glob_files(country_code='*', include_special=False):
        "Find matching files"
        test_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        test_files = glob(
            str(Path(test_dir, country_code, "*", "*.png")), recursive=False)
        if include_special:
            test_files.extend( glob(
                str(Path(test_dir, country_code, "*", "specialcases", "*.png")), recursive=False) )
        return test_files
        
    qr_code_files = glob_files( metafunc.config.getoption("country_code"), metafunc.config.getoption("include_special") )
    
    if "dccQrCode" in metafunc.fixturenames:
        metafunc.parametrize("dccQrCode", qr_code_files, indirect=True)

@pytest.fixture
def dccQrCode(request):
    "Create a DccQrCode object from the QR Code PNG file (and cache it)"
    if not request.param in dccQrCode.cache.keys():
        dccQrCode.cache[request.param] = DccQrCode(request.param)
    return dccQrCode.cache[request.param]
dccQrCode.cache = {}