# Import the required packages
import virtualenv
import pip
import os


def activate_venv(env):
    """ activate virtual env in jupyter jasmin
    env: env to activate 
    notes: update venv_dir for personal location of conda envs """ 
    
    venv_dir = '/home/users/graceebc/miniconda3/envs/'
    # Define the venv directory
    venv_dir_full = venv_dir + env
    activate_file = os.path.join(venv_dir_full, "bin", "activate_this.py")
    #test to see if the activate file is there
    try:
        # Activate the venv
        exec(open(activate_file).read(), dict(__file__=activate_file))
    except ValueError:
        print('view not active - is the activate file in your venv bin directory?') 


