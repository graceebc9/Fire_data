#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from tifffile import imread, imsave


# In[ ]:


chunks= glob.glob('/home/users/graceebc/Fire_data/MODIS/*.tif')
outputpath = '/home/users/graceebc/Fire_data/MODIS/zip/'

for file in chunks:
    out = outputpath + file    
    im = imread(file)
    imsave("out', im, compress=6) 

