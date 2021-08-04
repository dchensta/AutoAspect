# AutoAspect
 
Use this webpage to create a virtual environment from the requirements.txt file: https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/

Once your virtual environment is activated, you can run AutoAspect.py to produce new annotations for all files in the “gold_files” folder. You must run semparse.py, split_jsons.py, and event_nominals.py on all gold files before you can run AutoAspect.py, otherwise the event nominals branch will not execute inside AutoAspect.py. 