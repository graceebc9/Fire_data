import sys
import os
import ee
ee.Initialize()
from geemap import geemap


#sys.path.append("C:/Users/tpfdo/OneDrive/Documents/GitHub/Polesia-Landcover/Routines/")
#sys.path.append("/home/markdj/repos/Polesia-Landcover/Routines/")

sys.path.append('/home/users/graceebc/Fire_data/Routines')

from Classification_tools import RF_model_and_train, accuracy_assessment_basic, map_target_area

print('\nClassification_MAIN(): hello!')

"""
User defined variables
"""
# Processing and output options
accuracy_eval_toggle = False

# File paths and directories for classification pipeline
#base_dir = '/home/markdj/Dropbox/artio/polesia'
base_dir = '/home/users/graceebc/Fire_data'

fp_train_ext = f"{base_dir}/Project_area.shp"
complex_training_fpath = f"{base_dir}/Training_data/Complex_points_2800.shp"
simple_training_fpath = f"{base_dir}/Training_data/Simple_points_5000.shp"
fp_target_ext = f"{base_dir}/whole_map.shp"
fp_export_dir = f"{base_dir}/Classified_2017/"

# Hard coded variables
label = "VALUE"
training_year = "2018"
scale = 20
trees_complex = 150
trees_simple = 75
years_to_map = [2017]

"""
Classification pipeline
"""
# Load training data area of interest
aoi = geemap.shp_to_ee(fp_train_ext)

# Set up folders
if not os.path.isdir(fp_export_dir):
    os.mkdir(fp_export_dir)

# Set up the classifiers
print('\nClassification_MAIN(): start complex model construction')
clf_complex, test_complex, max_min_values_complex = RF_model_and_train(training_year, scale, label, aoi,
                                                                       complex_training_fpath,
                                                                       trees_complex)
print('\nClassification_MAIN(): start simple model construction')
clf_simple, test_simple, max_min_values_simple = RF_model_and_train(training_year, scale, label, aoi,
                                                                    simple_training_fpath,
                                                                    trees_simple)

# Test classifiers accuracy if so desired
print('\nClassification_MAIN(): accuracy assessment')
if accuracy_eval_toggle:
    accuracy_assessment_basic(clf_complex, test_complex, 'Complex', label)
    accuracy_assessment_basic(clf_simple, test_simple, 'Simple', label)
else:
    print('Classification_MAIN(): No accuracy assessment carried out')

# Use the classifiers to map the whole of your target areas (tiled)
print('\nClassification_MAIN(): generate full map')
map_target_area(fp_target_ext, fp_export_dir, years_to_map, scale, clf_complex, clf_simple,
                max_min_values_complex, max_min_values_simple)

print('\nClassification_MAIN(): bye!')
