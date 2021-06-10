from os import path
from pathlib import Path
from io import BytesIO
from json import load
from PIL.Image import open as image_open
from base45 import b45decode
from cbor2 import loads, CBORTag
from cose.algorithms import Es256, Ps256
from cose.headers import KID
from cose.keys import CoseKey
from cose.keys.curves import P256
from cose.keys.keyops import VerifyOp
from cose.keys.keyparam import KpAlg, EC2KpX, EC2KpY, EC2KpCurve, RSAKpE, RSAKpN, KpKty, KpKeyOps
from cose.keys.keytype import KtyEC2, KtyRSA
from cose.messages import Sign1Message
from binascii import hexlify, unhexlify
from pytest import fixture, skip, fail
from pytest import mark
from glob import glob
from pyzbar.pyzbar import decode as bar_decode
from typing import Dict
from traceback import format_exc
from base45 import b45decode
from zlib import decompress
from cbor2 import loads, CBORTag
from datetime import date, datetime, timezone

TIMESTAMP_ISO8601_EXTENDED = "%Y-%m-%dT%H:%M:%S.%fZ"
CONFIG_ERROR = 'CONFIG_ERROR'

def pytest_generate_tests(metafunc):
 if "config_env" in metafunc.fixturenames:
  country_code = metafunc.config.getoption("country_code")
  # file_name = metafunc.config.getoption("file_name")
   # print(country_code, file_name)
  test_dir = path.dirname(path.dirname(path.abspath(__file__)))
  test_files = glob(str(Path(test_dir, country_code, "*.png")), recursive=True)
  metafunc.parametrize("config_env", test_files, indirect=True)

@fixture
def config_env(request):
    # noinspection PyBroadException
    try:
            config_env = _readobject(request.param)
            return config_env
    except Exception:
        return {CONFIG_ERROR: format_exc()}

def _readobject(png):
    file = open(png,mode='rb')
    # read all lines at once
    all_of_it = file.read()
    # close the file
    file.close()
    decoded=_get_code_content(all_of_it,png)
    return decoded

def _get_code_content(b,filepath):
    try:
     with BytesIO(b) as f:
        with image_open(f) as image:
            dec = bar_decode(image)[0]
     return dec.data.decode()
    except:
        fail(f'QR Code can not be decoded: {filepath}')

def _checkPrefix(decoded): 
    return decoded[0:4] == "HC1:"

def _object_hook(decoder, value):
    return {k: v.astimezone(timezone.utc).strftime(TIMESTAMP_ISO8601_EXTENDED) if isinstance(v, (date, datetime)) else v
            for k, v in value.items()}

def _checkTags(cose):
    firstbyte = cose[0]
    type = "Sign1"
    if(firstbyte==132):
      type="List"

    if(firstbyte==216):
      type="CWT"

    if(not firstbyte == 210) :
        fail(f'QR Code not tagged as Sign1 Message. Tagged with {firstbyte} ({type})')

def test_issuer_quality(config_env: Dict):
    _PREFIX=config_env

    if(not _checkPrefix(_PREFIX)) :
     fail("Prefix not correctly set")

    _BASE45=_PREFIX[4:]

    _COMPRESSION=b45decode(_BASE45)

    _COSE = decompress(_COMPRESSION)

    _checkTags(_COSE)

    _CBOR= Sign1Message.decode(_COSE)




