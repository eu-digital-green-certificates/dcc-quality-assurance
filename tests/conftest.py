import pytest

def pytest_addoption(parser):
    parser.addoption("-C", "--country_code", action="store", default="*", help="Country code of tests to run.")
    parser.addoption("--no-signature-check", action="store_true", default=False, help="Do not verify the signature")
    parser.addoption("--include-special", action="store_true", default=False, help="Include special cases")
    parser.addoption("--allow-multi-dcc", action="store_true", default=False, help="Allow multiple DCC in one QR code")
    parser.addoption("--warn-timedelta", action="store_true", default=False, help="Warn about time deltas")
