import constants
from datetime import datetime
from cryptography import x509
from test_qrqualitycheck import certificates_from_environment
from cryptography.hazmat.backends.openssl.backend import backend as OpenSSLBackend

def test_dcc_not_valid_before_dsc( dccQrCode ):
    "A DCC should not be valid before the signing DSC is valid"
    cert = x509_for_key_id(dccQrCode.get_key_id_base64())
    dcc_valid_from = datetime.fromtimestamp(dccQrCode.payload[constants.PAYLOAD_ISSUE_DATE])

    assert dcc_valid_from > cert.not_valid_before

def test_dcc_not_valid_after_dsc( dccQrCode ):
    "A DCC should not be valid after the signing DSC has expired"
    cert = x509_for_key_id(dccQrCode.get_key_id_base64())
    dcc_valid_until = datetime.fromtimestamp(dccQrCode.payload[constants.PAYLOAD_EXPIRY_DATE])

    assert dcc_valid_until < cert.not_valid_after


def x509_for_key_id( key_id ):
    "Returns an x509 certificate object by KID. Result is cached in memory"
    if key_id in x509_for_key_id.cache:
        return x509_for_key_id.cache[key_id]

    certs = certificates_from_environment()
    
    cert_base64 = certs[key_id] 
    cert = x509.load_pem_x509_certificate(
        f'-----BEGIN CERTIFICATE-----\n{cert_base64}\n-----END CERTIFICATE-----'.encode(), OpenSSLBackend)
    x509_for_key_id.cache[key_id] = cert 
    return cert
x509_for_key_id.cache = {}
