#!/usr/bin/env python
# coding: utf-8

# In[ ]:


"""Combine the MODIS data into one time block: pulls data from the CEDA archive on JASMIN 
Variable to be updates:
output_path : where your unzipped MODIS files go (reccomend not in your GIT folder)
whole_map: the location of the shp shapefiles that you want your MODIS data clipped to
output_path_final: location of your time stacked data set (put in your git file if you want to play around in local Jupyter notebook)
"""


# In[2]:


import rioxarray as rxr
from rioxarray import merge
import xarray as xr 
import glob
import tarfile

import os
import datetime
import fiona


# In[3]:


import routines
from routines import extract_vertices, crop_data_spatially 


# In[ ]:

#Set up paths and directories 
#file path for jasmin
path = '/neodc/esacci/fire/data/burned_area/MODIS/pixel/v5.1/compressed'  

#output paths
output_path_zip = '/home/users/graceebc/MODIS/'
output_path_final  = '/home/users/graceebc/Fire_data/MODIS/

if os.path.isdir(output_path_zip) is false:
    os.makedirs(output_path)   

if os.path.isdir(output_path_final) is false:
    os.makedirs(output_path_final)

print('Pulling and unzipping the MODIS files, start()... ')

#Access all files and unzip 
year_list = [ x for x in range(2001,2021) if (x!= 2007 and x!= 2019) ]
months = ['01', '02', '03', '04', '05', '06', '07', '08' ,'09' ,'10', '11', '12']
months1 = ['01', '02', '03', '04', '05', '06', '07', '08' ,'09']
months2 = [ '10', '11', '12']

#create list of files - 2007 has different folder structure + 2019
file_part1 = ['/neodc/esacci/fire/data/burned_area/MODIS/pixel/v5.1/compressed/{0}/{0}{1}01-ESACCI-L3S_FIRE-BA-MODIS-AREA_3-fv5.1.tar.gz'.format(year, month) for year in year_list for month in months]
file_part2 = ['/neodc/esacci/fire/data/burned_area/MODIS/pixel/v5.1/compressed/2007/new-corrected/2007{0}01-ESACCI-L3S_FIRE-BA-MODIS-AREA_3-fv5.1.tar.gz'.format(month) for month in months ]
file_part3 = ['/neodc/esacci/fire/data/burned_area/MODIS/pixel/v5.1/compressed/2019/2019{0}01-ESACCI-L3S_FIRE-BA-MODIS-AREA_3-fv5.1.tar.gz'.format(month) for month in months1]
file_part4 = ['/neodc/esacci/fire/data/burned_area/MODIS/pixel/v5.1/compressed/2019/new-corrected/2019{0}01-ESACCI-L3S_FIRE-BA-MODIS-AREA_3-fv5.1.tar.gz'.format(month) for month in months2]
files = file_part1 + file_part2 + file_part3 + file_part4



for file_name in files:
    #check if file already unzipped
    if file_name not in os.listdir(output_path_zip):
        # open file

        file = tarfile.open(file_name)

        # extracting file
        file.extractall(output_path_zip)

        file.close()

print('Unzip all MODIS files, end()')
# In[4]:


print('Create data stack, start().. ')

JD_files = sorted(glob.glob('/home/users/graceebc/MODIS/*JD.tif'))
CL_files = sorted(glob.glob('/home/users/graceebc/MODIS/*CL.tif'))

whole_map = '/home/users/graceebc/Fire_data/whole_map.shp'


# In[4]:



#n=12

for year in year_list :
    print('Starting ' + str(year))
    file = '/home/users/graceebc/MODIS/{0}*JD.tif'.format(year)
    JD_files = sorted(glob.glob(file))
    #chunked_files = [JD_files[i:i + n] for i in range(0, len(JD_files), n)]

    output_path =  output_path_final + '{0}_chunk.tif'.format(year)
    
    if os.path.isfile(output_path) is false:

        elements =[]
        for file in JD_files:
            #create date array to add to dataset 
            date_str = file[27:35]
            print(file)
            year, month, day  = int(date_str[:4]), int(date_str[4:6]), int(date_str[6:8])
            date = datetime.datetime(year, month, day)
            time_da = xr.Dataset({"date": date})

            #open dataset and add time , then store in elements 
            base = rxr.open_rasterio(file)
            base_days_clipped = crop_data_spatially(base, whole_map, -2) # set to non burnable 
            ds = base_days_clipped
            dst = ds.expand_dims(time=time_da.to_array()) 
            elements.append(dst)
            print('file done')
        stack = xr.concat(elements, dim='time')
        print('stack appended!')
        print('start downloading stack')
        da = stack.to_dataset(name='{0}_chunk'.format(year))
        da.to_netcdf(output_path)
        print('stack downloaded')


# In[ ]:


    
print('Completed data stack, bye!')
