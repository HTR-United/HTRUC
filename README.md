<img src="./img/HTRUC.png" width=300 align=right>

HTRUC
=====

[![Test](https://github.com/HTR-United/HTRUC/actions/workflows/tests.yml/badge.svg)](https://github.com/HTR-United/HTRUC/actions/workflows/tests.yml)


Pronunced `EuchTruc` (*ce truc*), this contains most of the tooling for the catalog records: 
- Parses catalog records
- Test the validity of the catalog according to different schemas
- Builds agglomerated catalog records with optional dataviz
- Retrieve catalog information from all repositories of a user or an organization.

## Install 

Either clone and run `python setup.py install` **or** use the pip version `pip install htruc`

## Use

### Testing a catalog record

Simply run `htruc test YourYamlFile.yml`

### Upgrade a previously existing catalog record

Run `htruc upgrade yourYamlFile.yml`

### Upgrade a previously existing catalog record to the newest schema

Run `htruc upgrade yourYamlFile.yml`

### Upgrade metrics using [HTR-United Metadata Generator (HUMg)](https://github.com/HTR-United/htr-united-metadata-generator)

Run `htruc update-volumes YourYamlFile.yml MetricFileFromHUMG.jons --inplace`

---

Logo by [Alix Chagué](https://alix-tz.github.io).
