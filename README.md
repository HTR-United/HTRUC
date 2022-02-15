<img src="./img/HTRUC.png" width=300 align=right>

HTRUC
=====

[![Test](https://github.com/HTR-United/HTRUC/actions/workflows/tests.yml/badge.svg)](https://github.com/HTR-United/HTRUC/actions/workflows/tests.yml)


Pronunced `EuchTruc` (*ce truc*), this contains most of the tooling for the catalog files: 
- Parses catalog files
- Test the validity of the catalog according to different schemas
- Builds agglomerated catalog files with optional dataviz
- Retrieve catalog information from all repositories of a user or an organization.

## Install 

Either clone and run `python setup.py install` **or** use the pip version `pip install htruc`

## Use

### Testing a catalog file

Simply run `htruc test YourYamlFile.yml`

