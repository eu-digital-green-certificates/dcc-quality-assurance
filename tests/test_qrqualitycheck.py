# ---license-start
# eu-digital-green-certificates / dgc-testdata
# ---
# Copyright (C) 2021 Qryptal Pte Ltd
# Copyright (C) 2021 T-Systems International GmbH and all other contributors
# ---
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ---license-end

import json
from base64 import b64decode
import base64
import os
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
from cryptography import x509
from cryptography.x509 import ExtensionNotFound
import jsonschema 
import jsonref
from filecache import filecache, DAY
import re
import json

COSE = 'COSE'
TIMESTAMP_ISO8601_EXTENDED = "%Y-%m-%dT%H:%M:%S.%fZ"
CONFIG_ERROR = 'CONFIG_ERROR'
X_RESUME_TOKEN = 'x-resume-token'
X_KID = 'X-KID'
FILE_CONTENT = 'FILE_CONTENT'
FILE_PATH = 'FILE_PATH'
VER = 'ver'
ACC_KID_LIST = 'https://dgca-verifier-service-eu-acc.cfapps.eu10.hana.ondemand.com/signercertificateStatus'
ACC_CERT_LIST = 'https://dgca-verifier-service-eu-acc.cfapps.eu10.hana.ondemand.com/signercertificateUpdate'
SCHEMA_BASE_URI = 'https://raw.githubusercontent.com/ehn-dcc-development/ehn-dcc-schema/release/'
PAYLOAD_ISSUER, PAYLOAD_ISSUE_DATE, PAYLOAD_EXPIRY_DATE, PAYLOAD_HCERT = 1, 6, 4, -260
DCC_TYPES = {'v': "VAC", 't': "TEST", 'r': "REC"}


def pytest_generate_tests(metafunc):
    if "qr_code_list" in metafunc.fixturenames:
        country_code = metafunc.config.getoption("country_code")
        file_name = metafunc.config.getoption("file_name")
        test_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        test_files = glob(
            str(Path(test_dir, country_code, "*", "*.png")), recursive=False)
        if metafunc.config.getoption("include_special"):
            test_files.extend( glob(
                str(Path(test_dir, country_code, "*", "specialcases", "*.png")), recursive=False) )
        metafunc.parametrize("qr_code_list", test_files, indirect=True)


def _object_hook(decoder, value):
    return {k: v.astimezone(timezone.utc).strftime(TIMESTAMP_ISO8601_EXTENDED) if isinstance(v, (date, datetime)) else v
            for k, v in value.items()}


def _createKidDict():
    r = requests.get(ACC_KID_LIST)
    if not r.ok:
        fail("KID list not reachable")
    kidDict = {key: None for key in json.loads(r.text)}
    return kidDict


def _getCertificates(kid_dict):
    r = requests.get(ACC_CERT_LIST)
    while X_RESUME_TOKEN in r.headers and r.ok:
        kid_dict[r.headers[X_KID]] = r.text
        r = requests.get(ACC_CERT_LIST, headers={
                         X_RESUME_TOKEN: r.headers[X_RESUME_TOKEN]})
    return kid_dict


@filecache(HOUR)
def downloadCertificates():
    return _getCertificates(_createKidDict())


@fixture
def qr_code_list(request):
    print(f"Checking {request.param}")
    # noinspection PyBroadException
    try:
        return _readobject(request.param)
    except Exception:
        return {CONFIG_ERROR: format_exc()}


def _readobject(filepath):
    file = open(filepath, mode='rb')
    # read all lines at once
    all_of_it = file.read()
    # close the file
    file.close()
    decoded = _get_code_content(all_of_it, filepath)

    return {FILE_CONTENT: _get_code_content(all_of_it, filepath), FILE_PATH: filepath}


def _get_code_content(b, filepath):
    try:
        with BytesIO(b) as f:
            with image_open(f) as image:
                dec = bar_decode(image)[0]
        return dec.data.decode()
    except:
        fail(f'QR Code can not be decoded: {filepath}')


def _check_prefix(decoded):
    if(not decoded[0:4] == "HC1:"):
        fail("Prefix not correctly set")


def _object_hook(decoder, value):
    return {k: v.astimezone(timezone.utc).strftime(TIMESTAMP_ISO8601_EXTENDED) if isinstance(v, (date, datetime)) else v
            for k, v in value.items()}


def _check_tags(cose):
    firstbyte = cose[0]
    type = "Sign1"
    if(firstbyte == 132):
        type = "List"

    if(firstbyte == 216):
        type = "CWT"

    if(not firstbyte == 210):
        fail(
            f'QR Code not tagged as Sign1 Message. Tagged with {firstbyte} ({type})')


def _check_algorithm(cbor):
    alg = cbor.phdr[Algorithm]
    if not alg.__name__ in ['Ps256', 'Es256']:
        fail(f"Wrong Algorithm used: {alg.__name__} Expected: Ps256 or Es256")

    if Algorithm in cbor.uhdr:
        fail("Algorithm must be in Protected header")


def _get_kid(cose):
    if KID in cose.phdr:
        kid = cose.phdr[KID]
    else:
        kid = cose.uhdr[KID]

    return base64.b64encode(kid).decode("ascii")


def _get_key(cert):
    x = y = e = n = None
    if isinstance(cert.public_key(), rsa.RSAPublicKey):
        e = int_to_bytes(cert.public_key().public_numbers().e)
        n = int_to_bytes(cert.public_key().public_numbers().n)
    elif isinstance(cert.public_key(), ec.EllipticCurvePublicKey):
        x = int_to_bytes(cert.public_key().public_numbers().x)
        y = int_to_bytes(cert.public_key().public_numbers().y)
    else:
        raise Exception(
            f'Unsupported certificate agorithm: {cert.signature_algorithm_oid} for verification.'
        )

    key = None
    if x and y:
        key = CoseKey.from_dict(
            {
                KpKeyOps: [VerifyOp],
                KpKty: KtyEC2,
                EC2KpCurve: P256,  # Ought to be pk.curve - but the two libs clash
                KpAlg: Es256,  # ECDSA using P-256 and SHA-256
                EC2KpX: x,
                EC2KpY: y,
            }
        )
    elif e and n:
        key = CoseKey.from_dict(
            {
                KpKeyOps: [VerifyOp],
                KpKty: KtyRSA,
                KpAlg: Ps256,  # RSASSA-PSS using SHA-256 and MGF1 with SHA-256
                RSAKpE: e,
                RSAKpN: n,
            }
        )
    return key


def _check_signature(cose, kidlist):
    kid = _get_kid(cose)

    if not kid in kidlist:
        fail("KID exist not on acceptance environment")

    cert = _create_cert(kid, kidlist[kid])
    cose.key = _get_key(cert)
    if not cose.verify_signature():
        fail("Signature could not be verified with signing certificate {}".format(
            kidlist[kid]))


def _create_cert(kid, key):
    cert = x509.load_pem_x509_certificate(
        f'-----BEGIN CERTIFICATE-----\n{key}\n-----END CERTIFICATE-----'.encode())
    fingerprint = cert.fingerprint(SHA256())
    assert(kid == base64.b64encode(fingerprint[0:8]).decode("ascii"))
    return cert


@filecache(DAY)
def _get_json_schema(version):
    ''' Get the json schema depending on the version of the DCC data. 
        Schema code is obtained from https://raw.githubusercontent.com/ehn-dcc-development/ehn-dcc-schema/
    '''
    class RewritingLoader:
        '''Json schema in ehn-dcc-development has absolute references which don't match with the 
            base uri of their repo. The RewritingLoader is supposed to search and replace these uris with
            working links'''
        def __init__(self, rewrite, into):
            self.rewrite = rewrite
            self.into = into
    
        def __call__(self, uri, **kwargs):
            response = requests.get(uri, **kwargs)
            return json.loads(response.text.replace(self.rewrite, self.into))
    
    # Check if version is three numbers separated by dots 
    if re.match("^\\d\\.\\d\\.\\d$", version) is None: 
        raise ValueError(f'{version} is not a valid version string')

    # Before v1.2.1, the datatype was called DGC, now DCC
    main_file = 'DCC.schema.json' if version >= '1.2.1' else 'DGC.schema.json'
    versioned_path = f'{SCHEMA_BASE_URI}{version}/'
    # Rewrite the references to id.uvci.eu to the repository above
    rewritingLoader = RewritingLoader('https://id.uvci.eu/', versioned_path )
    
    print(f'Loading HCERT schema {version} ...')
    try: 
        schema = jsonref.load_uri(f'{versioned_path}{main_file}', loader=rewritingLoader )
    except: 
        raise LookupError(f'Could not load schema definition for {version}')
    return schema

def _verify_json_schema(hcert):
    schema = _get_json_schema(hcert['ver'])
    try:
        jsonschema.validate( hcert, schema )
        print('Schema validation passed')
    except:
        print('Schema validation failed')
        raise    

def test_issuer_quality(qr_code_list: Dict, pytestconfig):
    def get_path_schema_version(path, include_special=False): 
        split_path = path.split(os.sep)
        if re.match("^\\d\\.\\d\\.\\d$", split_path[-2]):
            return split_path[-2]
        elif include_special and split_path[-2].lower() == "specialcases" and re.match("^\\d\\.\\d\\.\\d$", split_path[-3]):
            return split_path[-3]
        else:
            return None

    _kidlist = downloadCertificates()

    # Prefix must be 'HC1:'
    _check_prefix(qr_code_list[FILE_CONTENT])

    base45 = qr_code_list[FILE_CONTENT][4:]
    decompressed_bytes = decompress(b45decode(base45))

    # First byte of COSE must be 210
    _check_tags(decompressed_bytes)

    cose = Sign1Message.decode(decompressed_bytes)

    # Signing algorithm must be 'Ps256' or 'Es256'
    _check_algorithm(cose)

    # DCC must be signed with key on ACC
    if not pytestconfig.getoption('no_signature_check'):
        _check_signature(cose, _kidlist)

    cose_payload = loads(cose.payload, object_hook=_object_hook)

    # If file path indicates JSON schema version, verify it against actual JSON schema version
    # E.g. "<countrycode>/1.0.0/VAC.png" will trigger schema version verification, whereas "<countrycode>/1.0.0/specialcases/VAC.png" will not
    path_schema_version = get_path_schema_version(qr_code_list[FILE_PATH], pytestconfig.getoption('include_special') )
    if path_schema_version is not None:         
        dcc_schema_version = cose_payload[PAYLOAD_HCERT][PAYLOAD_ISSUER][VER]
        if path_schema_version != dcc_schema_version:
            fail(f"File path indicates {path_schema_version} but DCC contains {dcc_schema_version} JSON schema version")

        hcert = cose_payload[PAYLOAD_HCERT][PAYLOAD_ISSUER]
        if not pytestconfig.getoption('allow_multi_dcc'):
            assert len([key for key in hcert.keys() if key in ['v', 'r', 't']]) == 1, \
                'DCC contains multiple certificates'

            # Check if DCC is of type as indicated by filename
            file_name = qr_code_list[FILE_PATH].split(os.sep)[-1]
            for dcc_type in DCC_TYPES.keys():
                if dcc_type in hcert.keys():
                    if not file_name.lower().startswith( DCC_TYPES[dcc_type].lower()):
                        fail(f'File name "{file_name}" indicates other DCC type. (DCC contains {DCC_TYPES[dcc_type]})')
    
        _verify_json_schema(hcert)


