# Handling of Special Cases

This repository contains some QR codes which special cases which needs special handling during the CBOR Decoding/JSON Processing. 


| Description| Occurence| Verifier Action | Issuer Action| QR Code|
|---------|----|----- |----|---|
| Whitespaces in decoded JSON fields|
| Date of Birth with invalid pattern|
| Dates with invalid Pattern|
| t,v,r Entries have null values|
| Negative doses|
| "null/nil/undefined" values ommited|
| Standardized Name fields (fnt/gnt) with special signs|
| Escaped characters in CBOR content|
