# RO - Romania

* **JSON schema version**: 1.3.0

Used for productive DCCs issuance
* From: 01.07.2021
* Until:

## Test files

### Vaccination

![VAC](VAC.png)

### Test

### Recovery

![REC](REC.png)


## Special cases and deviations

### Vaccination - dob, partial date

![specialcases/VAC](specialcases/VAC-11.png)

### Vaccination - dob, empty date

![specialcases/VAC](specialcases/VAC-12.png)


### Test

DCC is for PCR/NAA test but has rapid test manufacturer in content:

![TEST](specialcases/TEST.png)



Validity for QR-codes.
 - expiration:
    - vaccination: 365
    - recovery: 180
    - test: 3