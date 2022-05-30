import os

# DCC related
PAYLOAD_ISSUER, PAYLOAD_ISSUE_DATE, PAYLOAD_EXPIRY_DATE, PAYLOAD_HCERT = 1, 6, 4, -260
DCC_TYPES = {'v': "VAC", 't': "TEST", 'r': "REC"}
EXTENDED_KEY_USAGE_OIDs = {'t':'1.3.6.1.4.1.0.1847.2021.1.1','v':'1.3.6.1.4.1.0.1847.2021.1.2','r':'1.3.6.1.4.1.0.1847.2021.1.3',
                           'T':'1.3.6.1.4.1.1847.2021.1.1',  'V':'1.3.6.1.4.1.1847.2021.1.2',  'R':'1.3.6.1.4.1.1847.2021.1.3'}
EU_COUNTRIES = ['BE', 'EL', 'GR', 'LT', 'PT', 'BG', 'ES', 'LU', 'RO', 'CZ', 'FR', 'HU', 'SI', 'DK', 'HR', 'MT', 'SK',
                'DE', 'IT', 'NL', 'FI', 'EE', 'CY', 'AT', 'SE', 'IE', 'LV', 'PL'] # Greece included as EL and GR

# URLs

# Former hard coded URLs are now deprecated and may be taken out of order in the future
#ACC_KID_LIST = os.environ['DCC_KID_LIST']
#ACC_CERT_LIST = os.environ['DCC_CERT_LIST']
DSC_LIST = os.environ['DSC_LIST']
VALUESET_LIST = os.environ['DCC_VALUESET_LIST']
VALUESET_LIST_ALTERNATIVE = os.environ['DCC_VALUESET_LIST_ALT']
SCHEMA_BASE_URI = os.environ['DCC_SCHEMA_BASE_URI']

# Headers
X_RESUME_TOKEN = 'x-resume-token'
X_KID = 'X-KID'
