import constants
from datetime import datetime, timezone
from cryptography import x509
from test_qrqualitycheck import certificates_from_environment
from cryptography.hazmat.backends.openssl.backend import backend as OpenSSLBackend

LOCAL_TIMEZONE_DELTA = datetime.now(timezone.utc).astimezone().tzinfo.utcoffset(None)

def test_dcc_not_valid_before_dsc( dccQrCode ):
    "A DCC should not be valid before the signing DSC is valid"
    cert = x509_for_key_id(dccQrCode.get_key_id_base64())
    dcc_valid_from = datetime.fromtimestamp(dccQrCode.payload[constants.PAYLOAD_ISSUE_DATE])

    assert dcc_valid_from >= cert.not_valid_before + LOCAL_TIMEZONE_DELTA

def test_dcc_not_valid_after_dsc( dccQrCode ):
    "A DCC should not be valid after the signing DSC has expired"
    cert = x509_for_key_id(dccQrCode.get_key_id_base64())
    dcc_valid_until = datetime.fromtimestamp(dccQrCode.payload[constants.PAYLOAD_EXPIRY_DATE])

    assert dcc_valid_until <= cert.not_valid_after + LOCAL_TIMEZONE_DELTA

def test_dsc_info():
    """Print info about existing DSCs in the environment.
       This is not an actual test case and may be deleted in later versions"""

    certs = certificates_from_environment()
    
    for key_id in certs.keys():
        cert_base64 = certs[key_id] 
        cert = x509.load_pem_x509_certificate(
            f'-----BEGIN CERTIFICATE-----\n{cert_base64}\n-----END CERTIFICATE-----'.encode(), OpenSSLBackend)
        x509_for_key_id.cache[key_id] = cert # if we load the DSC anyway, we can fill the cache
        issuer_str = str(cert.issuer)
        issuer_country = issuer_str[issuer_str.find('C=')+2: issuer_str.find('C=')+4]
        print(  "\t".join([issuer_country, key_id , cert.not_valid_before.isoformat(), cert.not_valid_after.isoformat()]) )



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

