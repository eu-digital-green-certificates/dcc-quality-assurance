# TG - Togo

* **JSON schema version**: 1.3.0

## Validation round 2

### Test certificate
![TEST_TG](TEST_TG.png)

### Boost vaccine certificate 3/3
![TEST_TG_UE_COMPATIBILITY](VAC_TG.png)

### Invalid Vaccine certificate (2/3) on rule (dn >= sd')
![VAC_TG_INVALIDATED](VAC_TG_invalidated.png)

## Test files

### FULL COMPATIBILITY WITH EU SCHEMA

### VAC
![VAC_TG_UE_COMPATIBILITY](VAC_TG_UE_COMP.png)

- claim key 2 from RFC 8392 is the purpose of the CWT as requested by our national backend system (only for Togo)
- claim key 5 from RFC 8392  is the nbf as requested by our national backend system. should be override by  business rule if any (only for Togo)

### Test
![TEST_TG_UE_COMPATIBILITY](TEST_TG_UE_COMP.png)

- claim key 2 from RFC 8392 is the purpose of the CWT as requested by our national backend system (only for Togo)
- claim key 5 from RFC 8392  is the nbf as requested by our national backend system. should be override by  business rule if any (only for Togo)
- claim key 7 from RFC 8392  is the CTI as requested by our national backend system (only for Togo)

