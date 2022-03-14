#!/bin/sh

source ~/.profile

conda activate iris3.0

for var in sd snowc swvl1 t2m; do python retrieve_era5-land_monthly.py --format netcdf --area 53.1 22.9 50.5 32.1 --hour 12 $var 2001 2020; done
for var in sd snowc swvl1 t2m; do python retrieve_era5-land_monthly.py --format netcdf --area 53.1 22.9 50.5 32.1 $var 2001 2020; done

