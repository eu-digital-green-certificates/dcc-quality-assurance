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
import constants
import jsonschema

from glob import glob
from io import BytesIO
from pathlib import Path
from DccQrCode import DccQrCode
from traceback import format_exc
from datetime import date, datetime, timezone
from filecache import HOUR, MINUTE, DAY, filecache

# COSE / CBOR related
from cose.keys import CoseKey
from cryptography import x509
from cose.keys.curves import P256
from cose.keys.keyops import VerifyOp
from cose.headers import Algorithm, KID
from cryptography.utils import int_to_bytes
from cose.keys.keytype import KtyEC2, KtyRSA
from cryptography.x509 import ExtensionNotFound
from cose.algorithms import Es256, Ps256, Sha256
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from cose.keys.keyparam import KpAlg, EC2KpX, EC2KpY, EC2KpCurve, RSAKpE, RSAKpN, KpKty, KpKeyOps
from cryptography.hazmat.backends.openssl.backend import backend as OpenSSLBackend

@filecache(HOUR)
def valuesets_from_environment():
    "Downloads and caches valuesets from acceptance environment"
    valuesets = {}
    if requests.get(constants.VALUESET_LIST).ok:
         source_url = constants.VALUESET_LIST
    else:
        source_url = constants.VALUESET_LIST_ALTERNATIVE

    hashes = requests.get(source_url).json()
    for vs in hashes:
        try:
            valuesets[vs['id']] = requests.get(f'{source_url}/{vs["hash"]}').json()['valueSetValues']
        except KeyError:
            warnings.warn('Could not download value-sets. Skipping tests.')
            pytest.skip('Could not download value-sets.')

    return valuesets

@filecache(HOUR)
def certificates_from_environment():
    "Downloads and caches the certificates from the acceptance environment"
    def get_key_id_dict():
        response = requests.get(constants.ACC_KID_LIST)
        if not response.ok:
            pytest.fail("KID list not reachable")
        kidDict = {key: None for key in json.loads(response.text)}
        return kidDict

    def download_certificates(kid_dict):
        response = requests.get(constants.ACC_CERT_LIST)
        while constants.X_RESUME_TOKEN in response.headers and response.ok:
            kid_dict[response.headers[constants.X_KID]] = response.text
            response = requests.get(constants.ACC_CERT_LIST, headers={
                            constants.X_RESUME_TOKEN: response.headers[constants.X_RESUME_TOKEN]})
        return kid_dict

    return download_certificates(get_key_id_dict())


def test_plausibility_checks( dccQrCode ):
    '''Perform various plausibility checks:
        - RAT tests should not have "nm" field
        - NAA/PCR tests should not have "ma" field
    '''
    hcert = dccQrCode.payload[constants.PAYLOAD_HCERT][1]

    if 't' in hcert.keys():
        assert 'tt' in hcert['t'][0].keys(), 'Test type is not present in TEST-DCC'
        if hcert['t'][0]['tt'] == 'LP6464-4': 
            assert 'ma' not in hcert['t'][0].keys() or hcert['t'][0]['ma'] == '', "PCR/NAA tests should not have a ma-field"
        if hcert['t'][0]['tt'] == 'LP217198-3': 
            assert 'nm' not in hcert['t'][0].keys() or hcert['t'][0]['nm'] == '', "Rapid tests should not have a nm-field"

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
    dcc_types_in_payload = [ key for key in dccQrCode.payload[constants.PAYLOAD_HCERT][1].keys() if key in ['v', 'r', 't'] ]

    if pytestconfig.getoption('verbose'):
        print(dccQrCode.payload)

    if not pytestconfig.getoption('allow_multi_dcc') and len(dcc_types_in_payload) > 1:
        pytest.fail('DCC contains multiple certificates')

    if len(dcc_types_in_payload) < 1:
        pytest.fail('No DCC content (v, r, t) found')

    for dcc_type in dcc_types_in_payload:
        if not dccQrCode.get_file_name().lower().startswith( constants.DCC_TYPES[dcc_type].lower()):
            pytest.fail(f'File name "{dccQrCode.get_file_name()}" indicates other DCC type. (DCC contains {constants.DCC_TYPES[dcc_type]})')


def test_payload_version_matches_path_version( dccQrCode ):
    "Tests whether the payload has the same version as the file's path indicates"
    assert dccQrCode.payload[constants.PAYLOAD_HCERT][1]['ver'] == dccQrCode.get_path_schema_version()


@filecache(DAY)
def get_json_schema(version, extra_eu):
    ''' Get the json schema depending on the version of the DCC data.
        Schema code is obtained from https://raw.githubusercontent.com/ehn-dcc-development/ehn-dcc-schema/
    '''
    class RewritingLoader:
        '''Json schema in ehn-dcc-development has absolute references which don't match with the
            base uri of their repo. The RewritingLoader is supposed to search and replace these uris with
            working links'''
        def __init__(self, rewrites ):
            self.rewrites = rewrites

        def __call__(self, uri, **kwargs):
            response = requests.get(uri, **kwargs)
            raw = response.text
            for rw_from, rw_to in self.rewrites.items():
                raw = raw.replace( rw_from, rw_to )
            return json.loads(raw)

    # Check if version is three numbers separated by dots
    if re.match("^\\d\\.\\d\\.\\d$", version) is None:
        raise ValueError(f'{version} is not a valid version string')

    # Before v1.2.1, the datatype was called DGC, now DCC
    main_file = 'DCC.schema.json' if version >= '1.2.1' else 'DGC.schema.json'
    versioned_path = f'{constants.SCHEMA_BASE_URI}{version}/'
    # Rewrite the references to id.uvci.eu to the repository above
    # Rewrite to not allow additional properties
    rewritingLoader = RewritingLoader({'https://id.uvci.eu/' : versioned_path,
                                       "\"properties\"":  "\"additionalProperties\": false, \"properties\""} )

    rewritingLoaderExtraEU = RewritingLoader({'https://id.uvci.eu/' : versioned_path,
                                       "\"properties\"":  "\"additionalProperties\": true, \"properties\""} )

    print(f'Loading HCERT schema {version} ...')
    try:
        schema = jsonref.load_uri(f'{versioned_path}{main_file}', loader=rewritingLoader )
        schemaExtraEU = jsonref.load_uri(f'{versioned_path}{main_file}', loader=rewritingLoaderExtraEU )
    except:
        raise LookupError(f'Could not load schema definition for {version}')

    if extra_eu:
        return schemaExtraEU
    return schema

@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_json_schema( dccQrCode ):
    "Performs a schema validation against the ehn-dcc-development/ehn-dcc-schema definition"
    extra_eu = dccQrCode.get_path_country() not in constants.EU_COUNTRIES
    schema = get_json_schema( dccQrCode.payload[constants.PAYLOAD_HCERT][1]['ver'], extra_eu)

    jsonschema.validate( dccQrCode.payload[constants.PAYLOAD_HCERT][1], schema )


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
        f'-----BEGIN CERTIFICATE-----\n{cert_base64}\n-----END CERTIFICATE-----'.encode(), OpenSSLBackend)
    extensions = { extension.oid._name:extension for extension in cert.extensions}

    if pytestconfig.getoption('verbose'):
        if 'extendedKeyUsage' in extensions.keys():
            allowed_usages = [oid.dotted_string for oid in extensions['extendedKeyUsage'].value._usages]
        else:
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
        if len( set(constants.EXTENDED_KEY_USAGE_OIDs.values()) & set(allowed_usages) ) > 0: # Only check if at least one known OID is used in DSC
            for cert_type in constants.DCC_TYPES.keys():
                if cert_type in dccQrCode.payload[constants.PAYLOAD_HCERT][1].keys():
                    # There are 2 versions of extended key usage OIDs in circulation. We simply logged them as upper and lower case
                    # types, but they actually mean the same. So we treat t == T, v == V and r == R
                    if constants.EXTENDED_KEY_USAGE_OIDs[cert_type] not in allowed_usages \
                    and constants.EXTENDED_KEY_USAGE_OIDs[cert_type.upper()] not in allowed_usages:
                        pytest.fail(f"DCC is of type {constants.DCC_TYPES[cert_type]}, DSC allows {allowed_usages} "+\
                                    f"but not {constants.EXTENDED_KEY_USAGE_OIDs[cert_type]} or {constants.EXTENDED_KEY_USAGE_OIDs[cert_type.upper()]}")





def test_country_in_path_matches_issuer( dccQrCode ):
    'Checks whether the country code in the path matches the issuer country'
    if dccQrCode.get_path_country() in ['EL', 'GR'] and dccQrCode.payload[constants.PAYLOAD_ISSUER] in ['EL','GR']:
        pass # EL and GR are interchangeable
    else:
        assert dccQrCode.get_path_country() == dccQrCode.payload[constants.PAYLOAD_ISSUER]

def test_country_code_formats( dccQrCode ):
    'Checks that country codes are 2 upper case alphabetical characters'

    try:
        country_code = dccQrCode.payload[constants.PAYLOAD_ISSUER]
        assert len(country_code) == 2
        assert country_code.isalpha()
        assert country_code == country_code.upper()

        for cert_type in constants.DCC_TYPES.keys():
            if cert_type in dccQrCode.payload[constants.PAYLOAD_HCERT][1].keys():
                for inner_cert in dccQrCode.payload[constants.PAYLOAD_HCERT][1][cert_type]:
                    country_code = inner_cert['co']
                    assert len(country_code) == 2
                    assert country_code.isalpha()
                    assert country_code == country_code.upper()
    except AssertionError:
        raise ValueError(f'Invalid country code: {country_code}')


def test_claim_dates( dccQrCode, pytestconfig ):
    'Performs some plausibility checks against date related claims'

    assert dccQrCode.payload[constants.PAYLOAD_ISSUE_DATE] < dccQrCode.payload[constants.PAYLOAD_EXPIRY_DATE]
    assert datetime.fromtimestamp(dccQrCode.payload[constants.PAYLOAD_ISSUE_DATE]).year >= 2021

    if 'r' in  dccQrCode.payload[constants.PAYLOAD_HCERT][1].keys() and pytestconfig.getoption('warn_timedelta') :
        expiry_from_claim = datetime.fromtimestamp(dccQrCode.payload[constants.PAYLOAD_EXPIRY_DATE])
        expiry_from_payload = datetime.fromisoformat(dccQrCode.payload[constants.PAYLOAD_HCERT][1]['r'][0]['du'])
        if abs(expiry_from_claim - expiry_from_payload).days > 14:
            warnings.warn('Expiry dates in payload and envelope differ more than 14 days:\n'+
                        f'Claim key 4: {expiry_from_claim.isoformat()}\n'+
                        f'Payload: {expiry_from_payload.isoformat()}')

def test_valuesets( dccQrCode ):
    "Test if the only entries from valuesets are used for corresponding fields"

    def test_field( data, field_name, valueset_name ):
        valuesets = valuesets_from_environment()
        if not data[field_name] in valuesets[valueset_name].keys():
            pytest.fail(f'"{data[field_name]}" is not a valid value for {field_name} ({valueset_name})')

    hCert = dccQrCode.payload[constants.PAYLOAD_HCERT][1]

    if 'v' in hCert.keys():
        test_field( hCert['v'][0], 'vp','sct-vaccines-covid-19' )
        test_field( hCert['v'][0], 'ma','vaccines-covid-19-auth-holders' )
        test_field( hCert['v'][0], 'mp','vaccines-covid-19-names' )
        test_field( hCert['v'][0], 'tg','disease-agent-targeted' )

    elif 't' in dccQrCode.payload[constants.PAYLOAD_HCERT][1].keys():
        test_field( hCert['t'][0], 'tr','covid-19-lab-result' )
        if 'ma' in hCert['t'][0].keys():  # Only rapid tests have these
            test_field( hCert['t'][0], 'ma','covid-19-lab-test-manufacturer-and-name' )
        test_field( hCert['t'][0], 'tt','covid-19-lab-test-type' )
        test_field( hCert['t'][0], 'tg','disease-agent-targeted' )

    elif 'r' in dccQrCode.payload[constants.PAYLOAD_HCERT][1].keys():
        test_field( hCert['r'][0], 'tg','disease-agent-targeted' )

