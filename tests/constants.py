# DCC related
PAYLOAD_ISSUER, PAYLOAD_ISSUE_DATE, PAYLOAD_EXPIRY_DATE, PAYLOAD_HCERT = 1, 6, 4, -260
DCC_TYPES = {'v': "VAC", 't': "TEST", 'r': "REC"}
EXTENDED_KEY_USAGE_OIDs = {'t':'1.3.6.1.4.1.0.1847.2021.1.1','v':'1.3.6.1.4.1.0.1847.2021.1.2','r':'1.3.6.1.4.1.0.1847.2021.1.3',
                           'T':'1.3.6.1.4.1.1847.2021.1.1',  'V':'1.3.6.1.4.1.1847.2021.1.2',  'R':'1.3.6.1.4.1.1847.2021.1.3'}

# URLs
ACC_KID_LIST = 'https://dgca-verifier-service-eu-acc.cfapps.eu10.hana.ondemand.com/signercertificateStatus'
ACC_CERT_LIST = 'https://dgca-verifier-service-eu-acc.cfapps.eu10.hana.ondemand.com/signercertificateUpdate'
VALUESET_LIST = 'https://dgca-businessrule-service-eu-acc.cfapps.eu10.hana.ondemand.com/valuesets'
SCHEMA_BASE_URI = 'https://raw.githubusercontent.com/ehn-dcc-development/ehn-dcc-schema/release/'

# Headers 
X_RESUME_TOKEN = 'x-resume-token'
X_KID = 'X-KID'
