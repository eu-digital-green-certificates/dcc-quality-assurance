import json
from base64 import b64decode
import base64
from os import path
from pathlib import Path
from io import BytesIO
from json import load
from PIL.Image import NONE, open as image_open
from base45 import b45decode
from cbor2 import loads, CBORTag
from cose.algorithms import Es256, Ps256, Sha256
from cose.headers import Algorithm, KID
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
import requests
from filecache import HOUR, MINUTE, filecache
from json import load
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from cryptography.utils import int_to_bytes

TIMESTAMP_ISO8601_EXTENDED = "%Y-%m-%dT%H:%M:%S.%fZ"
CONFIG_ERROR = 'CONFIG_ERROR'
X_RESUME_TOKEN = 'x-resume-token'
X_KID = 'X-KID'
ACC_KID_LIST = 'https://dgca-verifier-service-eu-acc.cfapps.eu10.hana.ondemand.com/signercertificateStatus'
ACC_CERT_LIST = 'https://dgca-verifier-service-eu-acc.cfapps.eu10.hana.ondemand.com/signercertificateUpdate'


def pytest_generate_tests(metafunc):
    if "config_env" in metafunc.fixturenames:
        country_code = metafunc.config.getoption("country_code")
        file_name = metafunc.config.getoption("file_name")
        print(country_code, file_name)
        test_dir = path.dirname(path.dirname(path.abspath(__file__)))
        test_files = glob(
            str(Path(test_dir, country_code, "*", "*.png")), recursive=True)
        metafunc.parametrize("config_env", test_files, indirect=True)


def getKidList():
    response = requests.get(ACC_KID_LIST)
    if not response.ok:
        fail("KID List not reachable")
    kidlist = dict()
    for x in json.loads(response.text):
        kidlist[x] = ''
    return kidlist


def getCertificates(kidlist):
    r = requests.get(ACC_CERT_LIST)
    while X_RESUME_TOKEN in r.headers and r.status_code == 200:
        print(r.headers[X_RESUME_TOKEN])
        bytes = Sha256.compute_hash(base64.b64decode(r.text))
        kid = base64.b64encode(bytes[0:8]).decode("ascii")
        kidlist[r.headers[X_KID]] = bytes
        r = requests.get(ACC_CERT_LIST, headers={
                         X_RESUME_TOKEN: r.headers[X_RESUME_TOKEN]})
    return kidlist


@filecache(HOUR)
def downloadCertificates():
    kidlist = getKidList()
    kidlist = getCertificates(kidlist)
    return kidlist


@fixture
def config_env(request):
    # noinspection PyBroadException
    try:
        config_env = _readobject(request.param)
        return config_env
    except Exception:
        return {CONFIG_ERROR: format_exc()}


def _readobject(png):
    file = open(png, mode='rb')
    # read all lines at once
    all_of_it = file.read()
    # close the file
    file.close()
    decoded = _get_code_content(all_of_it, png)
    return decoded


def _get_code_content(b, filepath):
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
    if(firstbyte == 132):
        type = "List"

    if(firstbyte == 216):
        type = "CWT"

    if(not firstbyte == 210):
        fail(
            f'QR Code not tagged as Sign1 Message. Tagged with {firstbyte} ({type})')


def test_issuer_quality(config_env: Dict):
    kidlist = downloadCertificates()

    _PREFIX = config_env

    if(not _checkPrefix(_PREFIX)):
        fail("Prefix not correctly set")

    _BASE45 = _PREFIX[4:]

    _COMPRESSION = b45decode(_BASE45)

    _COSE = decompress(_COMPRESSION)

    _checkTags(_COSE)

    _CBOR = Sign1Message.decode(_COSE)

    alg = _CBOR.phdr[Algorithm]
    if not alg.__name__ in ["Ps256", "Es256"]:
        fail(f"Wrong Algorithm used: {alg.__name__} Expected: Ps256 or Es256")

    if Algorithm in _CBOR.uhdr:
        fail("Algorithm must be in Protected header")

    kid = base64.b64encode(_CBOR.uhdr[KID]).decode("ascii")

    if not kid in kidlist:
        fail("KID exist not on acceptance environment")