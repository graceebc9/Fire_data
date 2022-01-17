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


#file path for jasmin 
path = '/neodc/esacci/fire/data/burned_area/MODIS/pixel/v5.1/compressed'


print('Pulling and unzipping the MODIS files, start()... ')
#Access all files and unzip 
year_list = [ x for x in range(2001,2021) if x!= 2007 ]
months = ['01', '02', '03', '04', '05', '06', '07', '08' ,'09' ,'10', '11', '12']
output_path = '/home/users/graceebc/MODIS/'


# In[ ]:


files = ['/neodc/esacci/fire/data/burned_area/MODIS/pixel/v5.1/compressed/{0}/{0}{1}01-ESACCI-L3S_FIRE-BA-MODIS-AREA_3-fv5.1.tar.gz'.format(year, month) for year in year_list for month in months]

for file_name in files:
    #check if file already unzipped
    if file_name not in os.listdir(output_path):
        # open file

        file = tarfile.open(file_name)

        # extracting file
        file.extractall(output_path)

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

    final = [] 
    output_path_final = '/home/users/graceebc/Fire_data/MODIS/{0}_chunk.tif'.format(year)
    

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
    da.to_netcdf(output_path_final)
    print('stack downloaded')


# In[ ]:


    
print('Completed data stack, bye!')
