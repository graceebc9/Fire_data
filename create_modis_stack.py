#!/usr/bin/env python
# coding: utf-8

# In[ ]:


#Combine the MODIS data into one time block 


# In[2]:


import rioxarray as rxr
from rioxarray import merge
import xarray as xr 
import glob

import os
import datetime
import fiona


# In[3]:


import routines
from routines import extract_vertices, crop_data_spatially 


# In[ ]:


#file path for jasmin 
path = '/neodc/esacci/fire/data/burned_area/MODIS/pixel/v5.1/compressed'


# In[ ]:


#Access all files and unzip 
year_list = range(2001,2003)
months = ['01', '02', '03', '04', '05', '06', '07', '08' ,'09' ,'10', '11', '12']
output_path = '/home/users/graceebc/MODIS/'


# In[ ]:


files = ['/neodc/esacci/fire/data/burned_area/MODIS/pixel/v5.1/compressed/{0}/{0}{1}01-ESACCI-L3S_FIRE-BA-MODIS-AREA_3-fv5.1.tar.gz'.format(year, month) for year in year_list for month in months]

for file_name in files:
    #check if file there
    if file_name not in os.listdir(output_path):
        # open file

        file = tarfile.open(file_name)

        # extracting file
        file.extractall(output_path)

        file.close()


# In[4]:




JD_files = sorted(glob.glob('/home/users/graceebc/MODIS/*JD.tif'))
CL_files = sorted(glob.glob('/home/users/graceebc/MODIS/*CL.tif'))

whole_map = '/home/users/gracebc/Fire_data/whole_map.shp'


# In[4]:



n=4
chunked_files = [JD_files[i:i + n] for i in range(0, len(JD_files), n)]


# In[ ]:


final = [] 

for i in range(len(chunked_files)):
    elements =[]
    for file in chunked_files[i]:
        #create date array to add to dataset 
        date_str = file[12:20]
        print(date_str)
        year, month, day  = int(date_str[:4]), int(date_str[4:6]), int(date_str[6:8])
        date = datetime.datetime(year, month, day)
        time_da = xr.Dataset({"date": date})

        #open dataset and add time , then store in elements 
        base = rxr.open_rasterio(file)
        base_days_clipped = crop_data_spatially(base, whole_map, -2) # set to non burnable 
        ds = base_days_clipped
        dst = ds.expand_dims(time=time_da.to_array()) 
        elements.append(dst)
    stack = xr.concat(elements, dim='time')
    print('Done!')
    final.append(stack)
    

