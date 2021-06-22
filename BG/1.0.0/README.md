# BG - Bulgaria

* **JSON schema version**: 1.0.0

Used for productive DCCs issuance
* from: 01.06.2021
* until:

## Test files

### Vaccination

![VAC](VAC.png)


### Test

![VAC](TEST.png)


### Recovery

![REC](REC.png)

### Special cases and deviations
A number of DCCs have been issued not adhering to the schema:
- datetime instead of date
- null values for non-existing properties

Snippet from decoded specialcases/REC-NULL-DATETIME.png
```
                  "r": [
                    {
                      "ci": "urn:uvci:01:BG:UFR5PLGKU8WDSZK7#0",
                      "co": "BG",
                      "df": "2021-05-11T00:00:00",
                      "du": "2021-10-28T00:00:00",
                      "fr": "2021-05-01T00:00:00",
                      "is": "Ministry of Health",
                      "tg": "840539006"
                    }
                  ],
                  "t": null,
                  "v": null,
```
![REC-NULL-DATETIME](specialcases/REC-NULL-DATETIME.png)


Snippet from decoded specialcases/VAC-NULL-DATETIME.png
```
                  "r": null,
                  "t": null,
                  "v": [
                    {
                      "ci": "urn:uvci:01:BG:UFR5PLGKU8WDSZK7#0",
                      "co": "BG",
                      "dn": 2,
                      "dt": "2021-03-09T00:00:00",
                      "is": "Ministry of Health",
                      "ma": "ORG-100030215",
                      "mp": "EU/1/20/1528",
                      "sd": 2,
                      "tg": "840539006",
                      "vp": "J07BX03"
                    }
                  ],
```

![VAC-NULL-DATETIME](specialcases/VAC-NULL-DATETIME.png)