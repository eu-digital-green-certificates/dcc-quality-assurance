# LU - Luxembourg

- **JSON schema version**: 1.3.0

Used for productive DCCs issuance

- From: 22.06.2021
- Until: -

## Test files

### Vaccinations

#### Cycle with 1 mandatory dose

| 1/1 | 2/1 | 3/1 |
|-----|-----|-----|
| ![Vaccination 1/1](VAC_11Standard.png)| ![Vaccination 2/1](VAC_21Booster.png)| ![Vaccination 3/1](VAC_31Booster.png) |
| valid from: **17 Jan 2022** | valid from: **17 Jan 2022** | valid from: **17 Jan 2022** |

#### Cycle with 2 mandatory doses

| 2/2 | 3/3 | 4/4 |
|-----|-----|-----|
| ![Vaccination 2/2](VAC_22Standard.png)| ![Vaccination 3/3](VAC_33Booster.png)| ![Vaccination 4/4](VAC_44Booster.png) |
| valid from: **17 Jan 2022** | valid from: **17 Jan 2022** | valid from: **17 Jan 2022** |

### Tests

| NAAT | RAT |
|------|-----|
| ![NAAT certificate](TEST_NAAT.png) | ![RAT certificate](TEST_RAT.png) |
| valid from: **31 Jan 2022** | valid from: **31 Jan 2022** |

### Recovery

![Recovery certificate](REC_standard.png)

valid from: **17 Jan 2022**

## Special cases and deviations

Date of birth can be provided partially or be empty.

### Vaccination certificate - date of birth without the day

![specialcases/VAC_noday](specialcases/VAC_noday.png)

### Vaccination certificate - date of birth without the day and the month

![specialcases/VAC_nonomonth](specialcases/VAC_nomonth.png)

### Vaccination certificate - empty date of birth

![specialcases/VAC_noyear](specialcases/VAC_noyear.png)

### Recovery certificate - date of birth without the day and the month

![specialcases/REC_nomonth](specialcases/REC_nomonth.png)
