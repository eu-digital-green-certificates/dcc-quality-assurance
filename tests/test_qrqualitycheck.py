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

import os
import re
import json
import json
import base64
import pytest
import jsonref
import requests
import warnings
import jsonschema 

from glob import glob
from io import BytesIO
from pathlib import Path
from zlib import decompress
from base45 import b45decode
from traceback import format_exc
from datetime import date, datetime, timezone
from PIL.Image import NONE, open as image_open
from filecache import HOUR, MINUTE, DAY, filecache
from pyzbar.pyzbar import decode as qrcode_decode

# COSE / CBOR related
import cbor2
from cose.keys import CoseKey
from cryptography import x509
from cose.keys.curves import P256
from cose.keys.keyops import VerifyOp
from cose.messages import Sign1Message
from cose.headers import Algorithm, KID
from cryptography.utils import int_to_bytes
from cose.keys.keytype import KtyEC2, KtyRSA
from cryptography.x509 import ExtensionNotFound
from cose.algorithms import Es256, Ps256, Sha256
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from cose.keys.keyparam import KpAlg, EC2KpX, EC2KpY, EC2KpCurve, RSAKpE, RSAKpN, KpKty, KpKeyOps

# ----- Constants -----
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
EXTENDED_KEY_USAGE_OIDs = {'t':'1.3.6.1.4.1.0.1847.2021.1.1','v':'1.3.6.1.4.1.0.1847.2021.1.2','r':'1.3.6.1.4.1.0.1847.2021.1.3',
                           'T':'1.3.6.1.4.1.1847.2021.1.1',  'V':'1.3.6.1.4.1.1847.2021.1.2',  'R':'1.3.6.1.4.1.1847.2021.1.3'}


def pytest_generate_tests(metafunc):
    if "dccQrCode" in metafunc.fixturenames:
        country_code = metafunc.config.getoption("country_code")
        test_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        test_files = glob(
            str(Path(test_dir, country_code, "*", "*.png")), recursive=False)
        if metafunc.config.getoption("include_special"):
            test_files.extend( glob(
                str(Path(test_dir, country_code, "*", "specialcases", "*.png")), recursive=False) )
        metafunc.parametrize("dccQrCode", test_files, indirect=True)

@pytest.fixture
def dccQrCode(request):
    "Create a DccQrCode object from the QR Code PNG file (and cache it)"
    if not request.param in dccQrCode.cache.keys():
        dccQrCode.cache[request.param] = DccQrCode(request.param)
    return dccQrCode.cache[request.param]
dccQrCode.cache = {}

class DccQrCode():
    "Represents a DCC QR code based on a file"

    def __init__(self, path):
        def datetime_to_string(decoder, value):
            'replace datetime objects with a string representation when loading the CBOR'
            return {k: v.astimezone(timezone.utc).strftime(TIMESTAMP_ISO8601_EXTENDED) \
                    if isinstance(v, (date, datetime)) else v for k, v in value.items()}

        self.file_path = path
        image = image_open( path )
        self.qr_code_data = qrcode_decode(image)[0].data.decode()
        if not self.qr_code_data.startswith('HC1:'):
            raise ValueError('Encoded data does not begin with magic number "HC1:"')
        self.decompressed = decompress(b45decode(self.qr_code_data[4:]))
        self.sign1Message = Sign1Message.decode(self.decompressed)
        self.payload = cbor2.loads(self.sign1Message.payload, object_hook=datetime_to_string)
        self._path_country = None
    
    def get_key_id_base64(self):     
        "returns the key ID of the COSE message"   
        if KID in self.sign1Message.phdr:
            kid = self.sign1Message.phdr[KID]
        else:
            kid = self.sign1Message.uhdr[KID]

        return base64.b64encode(kid).decode("ascii")        

    def get_path_schema_version(self): 
        """Returns the schema version that is encoded in the path (exactly 3 digits separated by dots)
           or None if no match is found."""
        _previous = None
        for subdir_name in self.file_path.split(os.sep):
            if re.match("^\\d\\.\\d\\.\\d$", subdir_name):
                self._path_country = _previous
                return subdir_name
            _previous = subdir_name
        return None # --> No path schema version

    def get_path_country(self): 
        """Returns the country code that is encoded in the path right before the schema version"""
        if self._path_country is None: 
            self.get_path_schema_version()
        return self._path_country

    def get_file_name(self):
        return self.file_path.split(os.sep)[-1]



@filecache(HOUR)
def certificates_from_environment():
    "Downloads and caches the certificates from the acceptance environment"
    def get_key_id_dict():
        response = requests.get(ACC_KID_LIST)
        if not response.ok:
            pytest.fail("KID list not reachable")
        kidDict = {key: None for key in json.loads(response.text)}
        return kidDict

    def download_certificates(kid_dict):
        response = requests.get(ACC_CERT_LIST)
        while X_RESUME_TOKEN in response.headers and response.ok:
            kid_dict[response.headers[X_KID]] = response.text
            response = requests.get(ACC_CERT_LIST, headers={
                            X_RESUME_TOKEN: response.headers[X_RESUME_TOKEN]})
        return kid_dict
    
    return download_certificates(get_key_id_dict())

def test_if_dsc_exists( dccQrCode, pytestconfig ):
    "Checks whether the DCC's key is listed on the national backend of the acceptance environment"
    if pytestconfig.getoption('no_signature_check'):
        pytest.skip('Signature check skipped by request')

    certs = certificates_from_environment()
    if not dccQrCode.get_key_id_base64() in certs:
        pytest.fail("KID exist not on acceptance environment")

def test_tags( dccQrCode ):
    "Tests if the decompressed contents of the QR code is a COSE.Sign1Message"
    firstByte = dccQrCode.decompressed[0]
    if firstByte == 132:
        msgType = "List"
    elif firstByte == 216:
        msgType == "CWT"
    elif firstByte == 210:
        msgType = "Sign1"
    else:
        msgType = "unknown"

    assert msgType == "Sign1"

def test_algorithm( dccQrCode ):
    "Tests if Ps256 or Es256 are used as cryptographic algorithm in the COSE message"
    alg = dccQrCode.sign1Message.phdr[Algorithm]
    if not alg.__name__ in ['Ps256', 'Es256']:
        pytest.fail(f"Wrong Algorithm used: {alg.__name__} Expected: Ps256 or Es256")

    if Algorithm in dccQrCode.sign1Message.uhdr:
        pytest.fail("Algorithm must be in Protected header")


def test_dcc_type_in_payload( dccQrCode, pytestconfig ): 
    """Checks whether the payload has exactly one of v, r or t content
       (vaccination, recovery, test certificate)"""
    dcc_types_in_payload = [ key for key in dccQrCode.payload[PAYLOAD_HCERT][1].keys() if key in ['v', 'r', 't'] ]

    if pytestconfig.getoption('verbose'):
        print(dccQrCode.payload)

    if not pytestconfig.getoption('allow_multi_dcc') and len(dcc_types_in_payload) > 1:
        pytest.fail('DCC contains multiple certificates')
    
    if len(dcc_types_in_payload) < 1: 
        pytest.fail('No DCC content (v, r, t) found')
    
    for dcc_type in dcc_types_in_payload:
        if not dccQrCode.get_file_name().lower().startswith( DCC_TYPES[dcc_type].lower()):
            pytest.fail(f'File name "{dccQrCode.get_file_name()}" indicates other DCC type. (DCC contains {DCC_TYPES[dcc_type]})')


def test_payload_version_matches_path_version( dccQrCode ):
    "Tests whether the payload has the same version as the file's path indicates"
    assert dccQrCode.payload[PAYLOAD_HCERT][1][VER] == dccQrCode.get_path_schema_version()


@filecache(DAY)
def get_json_schema(version):
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

@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_json_schema( dccQrCode ):
    "Performs a schema validation against the ehn-dcc-development/ehn-dcc-schema definition"
    schema = get_json_schema( dccQrCode.payload[PAYLOAD_HCERT][1][VER] )
    jsonschema.validate( dccQrCode.payload[PAYLOAD_HCERT][1], schema )


def test_verify_signature( dccQrCode, pytestconfig ):
    """Verifies the signature of the DCC.
       This requires download of the certificates from the acceptance environment"""

    if pytestconfig.getoption('no_signature_check'):
        pytest.skip('Signature check skipped by request')

    def key_from_cert(cert):
        if isinstance(cert.public_key(), ec.EllipticCurvePublicKey):
            return CoseKey.from_dict(
                {
                    KpKeyOps: [VerifyOp],
                    KpKty: KtyEC2,
                    EC2KpCurve: P256,  
                    KpAlg: Es256,      # ECDSA using P-256 and SHA-256
                    EC2KpX: int_to_bytes(cert.public_key().public_numbers().x),
                    EC2KpY: int_to_bytes(cert.public_key().public_numbers().y),
                }
            )
        elif isinstance(cert.public_key(), rsa.RSAPublicKey):
            return CoseKey.from_dict(
                {
                    KpKeyOps: [VerifyOp],
                    KpKty: KtyRSA,
                    KpAlg: Ps256,  # RSASSA-PSS using SHA-256 and MGF1 with SHA-256
                    RSAKpE: int_to_bytes(cert.public_key().public_numbers().e),
                    RSAKpN: int_to_bytes(cert.public_key().public_numbers().n),
                }
            )
        else:
            raise ValueError(f'Unsupported certificate agorithm: {cert.signature_algorithm_oid} for verification.')

    certs = certificates_from_environment()
    
    cert_base64 = certs[dccQrCode.get_key_id_base64()]
    cert = x509.load_pem_x509_certificate(
        f'-----BEGIN CERTIFICATE-----\n{cert_base64}\n-----END CERTIFICATE-----'.encode())
    extensions = { extension.oid._name:extension for extension in cert.extensions}

    if pytestconfig.getoption('verbose'):
        if 'extendedKeyUsage' in extensions.keys():
            allowed_usages = [oid.dotted_string for oid in extensions['extendedKeyUsage'].value._usages] 
        else
            allowed_usages = 'ANY'
        print(f'\nCert: {cert_base64}\nAllowed Cert Usages: {allowed_usages}\nKeyID: {dccQrCode.get_key_id_base64()}')


    key = key_from_cert( cert )
    fingerprint = cert.fingerprint(SHA256())        
    assert dccQrCode.get_key_id_base64() == base64.b64encode(fingerprint[0:8]).decode("ascii")

    dccQrCode.sign1Message.key = key_from_cert(cert)
    if not dccQrCode.sign1Message.verify_signature():
        pytest.fail(f"Signature could not be verified with signing certificate {cert_base64}")

    if 'extendedKeyUsage' in extensions.keys():
        allowed_usages = [oid.dotted_string for oid in extensions['extendedKeyUsage'].value._usages] 
        if len( set(EXTENDED_KEY_USAGE_OIDs.values()) & set(allowed_usages) ) > 0: # Only check if at least one known OID is used in DSC
            for cert_type in DCC_TYPES.keys():
                if cert_type in dccQrCode.payload[PAYLOAD_HCERT][1].keys():
                    # There are 2 versions of extended key usage OIDs in circulation. We simply logged them as upper and lower case 
                    # types, but they actually mean the same. So we treat t == T, v == V and r == R
                    if EXTENDED_KEY_USAGE_OIDs[cert_type] not in allowed_usages \
                    and EXTENDED_KEY_USAGE_OIDs[cert_type.upper()] not in allowed_usages: 
                        pytest.fail(f"DCC is of type {DCC_TYPES[cert_type]}, DSC allows {allowed_usages} "+\
                                    f"but not {EXTENDED_KEY_USAGE_OIDs[cert_type]} or {EXTENDED_KEY_USAGE_OIDs[cert_type.upper()]}")

  



def test_country_in_path_matches_issuer( dccQrCode ):
    'Checks whether the country code in the path matches the issuer country'
    if dccQrCode.get_path_country() in ['EL', 'GR'] and dccQrCode.payload[PAYLOAD_ISSUER] in ['EL','GR']:
        pass # EL and GR are interchangeable
    else:
        assert dccQrCode.get_path_country() == dccQrCode.payload[PAYLOAD_ISSUER]

def test_country_code_formats( dccQrCode ):
    'Checks that country codes are 2 upper case alphabetical characters'

    try:
        country_code = dccQrCode.payload[PAYLOAD_ISSUER] 
        assert len(country_code) == 2
        assert country_code.isalpha()
        assert country_code == country_code.upper()

        for cert_type in DCC_TYPES.keys():
            if cert_type in dccQrCode.payload[PAYLOAD_HCERT][1].keys():
                for inner_cert in dccQrCode.payload[PAYLOAD_HCERT][1][cert_type]:
                    country_code = inner_cert['co']
                    assert len(country_code) == 2
                    assert country_code.isalpha()
                    assert country_code == country_code.upper()
    except AssertionError:
        raise ValueError(f'Invalid country code: {country_code}')
