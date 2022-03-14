import os
import argparse
import cdsapi
import pandas as pd
import time

c = cdsapi.Client()


def format_longitude(lon):
    if abs(lon - round(lon)) < 1e-3:
        lon = round(lon)
    return '{}{}'.format(abs(lon), '' if lon == 0 else 'E' if lon > 0 else 'W')


def format_latitude(lat):
    if abs(lat - round(lat)) < 1e-3:
        lat = round(lat)
    return '{}{}'.format(abs(lat), '' if lat == 0 else 'N' if lat > 0 else 'S')


def retrieve_era5_land_monthly(var_name, start_year, end_year, hour, area,
                               data_format):
    # get the CDS variable name
    era5_variables = pd.read_table('era5-land_variables.txt',
                                   index_col='var_name')
    var_details = era5_variables.loc[var_name]
    cds_var = var_details.CDS_name

    # CDS dataset
    cds_dataset = 'reanalysis-era5-land-monthly-means'

    # filename extension
    extensions = {'netcdf':'nc', 'grib':'grib'}
    extension = extensions[data_format]

    # download directory
    mean_description = 'mean' if hour is None else \
                       'mean_at_{:02d}Z'.format(hour[0])
    download_dir = ['..', mean_description]
    if area is not None:
        download_dir.append('{w}-{e}_{s}-{n}'.format(
                            n=format_latitude(area[0]),
                            w=format_longitude(area[1]),
                            s=format_latitude(area[2]),
                            e=format_longitude(area[3])))
    download_dir.append('download')
    download_dir = '/'.join(download_dir)

    # create the directory if required
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)

    target = "{}/era5-land_monthly_{}_{}_{:04d}-{:04d}.{}".format(
        download_dir, mean_description, var_name, start_year, end_year,
        extension)

    request = {'product_type': 'monthly_averaged_reanalysis' if hour is None \
                               else 'monthly_averaged_reanalysis_by_hour_of_day',
               'variable': cds_var,
               'year': ['{:04d}'.format(year) for year in
                        range(start_year, end_year+1)],
               'month': ['{:02d}'.format(month) for month in
                         range(1, 13)],
               'time': '00:00' if hour is None else
                       '{:02d}:00'.format(hour[0]),
               'format': data_format}

    if area is not None:
        request['area'] = area

    print('Performing retrieval:\n\nCDS data set: '
          '{}\nRequest: {}\nTarget: {}\n'.format(cds_dataset, request, target))

    c.retrieve(cds_dataset, request, target)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--format", help="Data format (netcdf/grib)",
                        default="grib")
    parser.add_argument("--area", help="Area (N W S E)", default=None, nargs=4,
                        type=float)
    parser.add_argument("--hour",
                        help="Hour of day (omit for full monthly mean)",
                        default=None, nargs=1, type=int)
    parser.add_argument("var", help="NetCDF variable name")
    parser.add_argument("start_year", help="start year", type=int)
    parser.add_argument("end_year", help="end year", type=int)
    args = parser.parse_args()

    print('At {}, started'.format(time.strftime('%Y-%m-%d %H:%M:%S')))

    retrieve_era5_land_monthly(args.var, args.start_year, args.end_year,
                               args.hour, args.area, args.format)

    print('At {}, finished'.format(time.strftime('%Y-%m-%d %H:%M:%S')))

