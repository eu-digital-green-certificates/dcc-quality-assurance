# LT - Lithuania

**JSON schema version**: 1.3.0

Used for productive DCCs issuance
* From: 02.07.2021
* Until: 

## Test files

### Vaccination

![VAC](VAC.png)

### Test

#### NAAT:

![TEST-NAAT](TEST-NAAT.png)

#### RAT:

![TEST-RAT](TEST-RAT.png)

### Recovery

![REC](REC.png)

### Special cases and deviations

* Test certificates have 'sc' date-time strings that ***ARE NOT*** tagged with CBOR TAG 0.
* Provided different certificates for NAAT (Nucleic acid amplification with probe detection) and RAT (Rapid Antigen Test) tests.