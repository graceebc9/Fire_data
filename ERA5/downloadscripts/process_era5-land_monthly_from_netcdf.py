import argparse
import iris
from iris.time import PartialDateTime
import numpy as np
import scipy.constants
from datetime import datetime
from dateutil.relativedelta import relativedelta
import os
import iris_grib
import iris_grib._grib_cf_map as grcf
from cf_units import CALENDAR_GREGORIAN, Unit
from iris.coords import AuxCoord, CellMethod, DimCoord
import pandas as pd


DEFAULT_CHUNK_SIZE = 4*1024*1024

def default_chunk_sizes(cube):
    '''
    Determine optimal default chunk sizes for multi-dimensional cubes to split each
    dimension approximately equally while yielding chunks that fit in DEFAULT_CHUNK_SIZE
    '''
    sizes = {}

    for coord in cube.coords(dim_coords=True):
        # code derived from lines 348:394 of https://github.com/Unidata/netcdf-c/blob/v4.6.1/libsrc4/nc4var.c
        suggested_size = int(((DEFAULT_CHUNK_SIZE / cube.data.nbytes) **
                          (1.0 / len(cube.shape))) * len(coord.points) - 0.5)
        if suggested_size < 1:
            suggested_size = 1
        elif suggested_size > len(coord.points):
            suggested_size = len(coord.points)
        num_chunks = (len(coord.points) + suggested_size - 1) // suggested_size
        if num_chunks > 0:
            overhang = (num_chunks * suggested_size) - len(coord.points)
            suggested_size -= overhang // num_chunks
        sizes[coord.name()] = suggested_size

    return sizes


def format_longitude(lon):
    if abs(lon - round(lon)) < 1e-3:
        lon = round(lon)
    return '{}{}'.format(abs(lon), '' if lon == 0 else 'E' if lon > 0 else 'W')


def format_latitude(lat):
    if abs(lat - round(lat)) < 1e-3:
        lat = round(lat)
    return '{}{}'.format(abs(lat), '' if lat == 0 else 'N' if lat > 0 else 'S')


def process_era5_land_monthly_means(var_name, start_year, end_year, hour, area):
    # download and output directories
    mean_path = 'mean' if hour is None else 'mean_at_{:02d}Z'.format(hour[0])
    data_dir = ['..', mean_path]
    if area is not None:
        data_dir.append('{w}-{e}_{s}-{n}'.format(
                        n=format_latitude(area[0]),
                        w=format_longitude(area[1]),
                        s=format_latitude(area[2]),
                        e=format_longitude(area[3])))
    output_dir = '/'.join(data_dir)
    data_dir.append('download')
    download_dir = '/'.join(data_dir)

    # the name of the grib data file
    source = '{}/era5-land_monthly_{}_{}_{:04d}-{:04d}.{}'.format(
        download_dir, mean_path, var_name, start_year, end_year,
        'nc')

    # read the specified variable
    cube = iris.load_cube(source)

    # fix the time coordinate values and add bounds
    time_coord = cube.coord(axis='t')
    tc_starts = time_coord.points
    tc_start_dts = time_coord.units.num2date(tc_starts)
    delta_days = 0 if hour is None else -1
    tc_end_dts = np.array([datetime(t.year, t.month, t.day, t.hour, t.minute, t.second,
                                    t.microsecond) + relativedelta(months=1, days=delta_days)
                           for t in tc_start_dts])
    tc_ends = time_coord.units.date2num(tc_end_dts)
    time_bounds = np.column_stack((tc_starts, tc_ends)).astype(np.int32)
    time_coord.points = (np.sum(time_bounds, axis=1) / 2).astype(np.int32)
    time_coord.bounds = time_bounds

    # identify the spatial coordinate system (spherical Earth, radius 6367.47 km)
    # see https://confluence.ecmwf.int/display/CKB/ERA5%3A+What+is+the+spatial+reference
    cs = iris.coord_systems.GeogCS(6367470.0)
    cube.coord(axis='x').coord_system = cs
    cube.coord(axis='y').coord_system = cs

    # cast the cube's data to float
    cube.data = cube.data.astype(np.float32)

    # if the cube is masked, make all the masked values equal its fill value
    fill_value = None
    if np.ma.is_masked(cube.data):
        fill_value = cube.data.fill_value
        cube.data.data[cube.data.mask] = fill_value

    # variable-specific processing
    # change units of snow depth to m
    if cube.var_name == 'sd':
        del cube.attributes['invalid_units']
        cube.units = 'm'

    # set the cell methods
    cube.cell_methods = None
    if hour is not None:
        cube.add_cell_method(CellMethod(method='point within days', coords='time'))
        cube.add_cell_method(CellMethod(method='mean over days', coords='time'))
    else:
        cube.add_cell_method(CellMethod(method='mean', coords='time'))

    # add a title attribute to identify the data
    long_name = cube.long_name
    if long_name[1] != ' ':
        long_name = long_name[0].lower() + long_name[1:]
    mean_desc = 'mean' if hour is None else 'mean of daily {:02d}:00'.format(hour[0])
    cube.attributes['title'] = 'ERA5-Land reanalysis monthly {} {}'.format(
        mean_desc, long_name)

    # work out the filename for the cube
    nc_base = '{}/era5-land_monthly_{}_{}_{:04d}-{:04d}'.format(
        output_dir, mean_path, var_name, start_year, end_year)

    # save the cube to a temporary (uncompressed) file
    tmp_nc_name = '{}_tmp.nc'.format(nc_base)
    print('Saving data to temporary file {}'.format(tmp_nc_name))
    iris.save(cube, tmp_nc_name, fill_value=fill_value)

    # compress the file
    nc_name = '{}.nc'.format(nc_base)
    chunkspec = ','.join(['{}/{}'.format(dim, chunk_size) for dim, chunk_size in 
                          default_chunk_sizes(cube).items()])
    compress_cmd = 'nccopy -d 9 -c {} {} {}'.format(chunkspec, tmp_nc_name, nc_name)
    print('Compressing file: {}'.format(compress_cmd))
    os.system(compress_cmd)
    os.remove(tmp_nc_name)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--area", help="Area (N W S E)", default=None, nargs=4,
                        type=float)
    parser.add_argument("--hour",
                        help="Hour of day (omit for full monthly mean)",
                        default=None, nargs=1, type=int)
    parser.add_argument("var", help="NetCDF variable name")
    parser.add_argument("start_year", help="start year", type=int)
    parser.add_argument("end_year", help="end year", type=int)
    args = parser.parse_args()

    process_era5_land_monthly_means(args.var, args.start_year, args.end_year,
                               args.hour, args.area)

