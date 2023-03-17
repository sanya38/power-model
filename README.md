# power-model

These files are for running the power model (OSeMOSYS).

## 1. Get set up first
The recommended way to get these files on your computer is to clone using Git:

`git clone https://github.com/asia-pacific-energy-research-centre/power-model.git`

Make sure you run this command in the folder you want.

You need to create a conda environment. To install, move to your working directory and copy and paste the following in your command line:

`conda env create --prefix ./env --file ./config/environment.yml`

`conda activate ./env`

Install cbc solver by following instructions below:

# Installing coin cbc solver
This will help to run the model faster. However it's installation is a little tricky. Go to the word document in ./documentation/ called "Installing CBC solver.docx" and follow the instructions. If you dont use this you will need to set 'use_coincbc' to False in the main.py file, and use use_glpsol to True.

Please note that on APERC computers the coin cbc sovler doesnt currently work. This is because of a ucrtbased.dll error. 
APPARENTLY: This is a windows error and is not related to the coin cbc solver. To fix this you need to install the latest version of visual studio. This can be done by going to the following link: https://visualstudio.microsoft.com/downloads/ and downloading the latest version of visual studio. Once this is installed you should be able to run the coin cbc solver.
BUT i havent managed to work out how to do this yet. So for now, just use the glpsol solver or OSemOSYS cloud.

## 2. To run the model 
Make sure you did Step 1 (only need to do it once).

1. Make sure you are in the working directory:
    In the command prompt you can check with `pwd`

2. Edit the data input sheet. Configure your model run using the START tab.

3. Run the model by typing in `python ./src/main.py <input_data_sheet_file> <data_config_file> <osemosys_cloud> <solving_method>"
    a. where <input_data_sheet_file> is the name of the input data sheet file in ./data (e.g., data.xlsx)
    b. where <data_config_file> is the name of the data config file in ./config (e.g., config.yml)
    c. where <osemosys_cloud> is a boolean (True or False) to indicate whether to use OSeMOSYS CLOUD or not
    d. where <solving_method> is the solving method to use if you arent using OSemosys Cloud (glpsol or coin-cbc)
    e. For example, `python ./src/main.py data.xlsx config.yml False glpsol`
    f. If you want to use OSeMOSYS CLOUD, set <osemosys_cloud> to True and <solving_method> can be anything. For example, `python ./src/main.py data.xlsx config.yml True None`
    g. You can also use > output.txt 2>&1 to save the output to a text file. For example, `python ./src/main.py data.xlsx config.yml False glpsol > output.txt 2>&1`

4. The model will run. Pay attention to the OSeMOSYS statements. There should not be any issues with the python script. 

## 3. Debugging model runs
When the script runs, the following temporary files are saved in `./tmp/ECONOMY NAME/SCENARIO`:
- combined_data_ECONOMYNAME_SCENARIO.xlsx
- datafile_from_python_ECONOMYNAME_SCENARIO.txt
- model_ECONOMYNAME_SCENARIO.txt
- process_log_{economy}_{scenario}.txt
The above files are created before OSeMOSYS runs. If you notice that OSeMOSYS gives you an error, check these files. The combined data Excel file is easy to check. You can see if there is missing data, typos, etc. This Excel file is converted to the text version (datafile_from_python). Finally, check the model text file. This is the file with sets, parameters, and equations that contains the OSeMOSYS model.

If the model solves successfully, a bunch of CSV files will be written to the same tmp folder. These are then combined and saved in the `results` folder as an Excel file.

If there is an error message saying the model is infeasible, check your model data. You can also double check the process_log_{economy}_{scenario}.txt file for outputs from the solving process. If the model is infeasible, the results files will not be written and you will get a "file not found" error message. This is your clue that the model did not solve. You always want to see a message in the solver output saying "OPTIMAL LP SOLUTION FOUND".

## Running OsEMOSYS CLOUD
It may be better to use OsEMOSYS CLOUD. In this case refer to the ./documentation/Running_osemosys_cloud.docx file for instructions.

## 4. Adding results to config yml files
To add results (e.g., capacity factor) you need to edit the following files:
- osemosys_fast.txt
- results_config.yml

The `osemosys_fast.txt` file is where the calculations occur. Following the pattern from the other results. The `results_config.yml` file tells the script to include that result and add it to the combined results Excel file.

## 5. Using results
Saved in the results folder will be a few different files. The ones with name ~ tall_...xlsx, will be a combination of all the results.

## Creating visualisation of RES
You can create a visualisaton of the RES as stated within the config/config.yml files. The script to run this will be outputted at the end of each model run, but you will need to run it in command line yourself.

## Avoiding errors when running the system:
I have included a few checks to make sure things in the input data are as they should be, however it is hard to cover for all of the possible ones, and a bit of a waste of time to cover for ones which will eventually be caught by otoole/cbc/osemosys. So if you find some error you dont expect take a look below:

### Known issues:
 - AttributeError: Can only use .str accessor with string values!
    - this seems to happen when running the model using coin-cbc and the osemosys.txt model. It occurs in the osemosys results call of model_solving_fuctions.solve_model(). I cannot work out why it occurs but i haven't tried very hard, because it doesnt seem to occur with osemosys_fast.txt.
 - Primal infs and other infs when running cbc solve.
    - perhaps these also occur with glpsol. I expect this is because of bad input data, i.e. the numbers being unrealistic, but its hard to tell since there are a lot of inputs. 
 - Something like EmissionActivityRatio['19_THA',POW_1_x_coal_thermal,1,'1_x_coal_thermal_CO2',2017] MathProg model processing error:
    - i fixed this one by changing the indices for EmissionActivityRatio from [REGION,TECHNOLOGY,MODE_OF_OPERATION,EMISSION,YEAR] to [REGION,TECHNOLOGY,EMISSION,MODE_OF_OPERATION,YEAR] in the config file. It seems this is because that is the order they are stated in osemosys.txt/osemosys_fast.txt (the model file)
 - blank output csvs
    - i cant tell for sure why this is but i think its related to the primal infs issue and can also happen if the supplied input data for calculating the variable for that sheet are not available, i.e. not supplied. 
 - SystemExit Errors. 
    - These should be occuring because of some check i have introduced to the code to make sure the input data is closer to what it should be for the model.
 - ./power-model/env/Library/bin/cbc.exe: error while loading shared libraries: ucrtbased.dll: cannot open shared object file: No such file or directory
    - This is a windows error. It doesnt occur on my home computer so i expect it is to do with the APERC laptops. I've tried a few things but no success. If this happens then you can try running the model using glpsol (is much slower), or you can try running the model on your own computer, or perhaps the OSeMOSYS CLOUD solution.
 
### What can you do to avoid errors in the first place:
 - When introducing new paramaters to the model, check they arent already stated in the osemosys_official_config.yaml as this should contain every variable calcualted or used in the osemosys.txt model file. That way you can make sure you dont make any annoying mistakes like misordering indices, supplying the wrong values etc. 
 - If you are introducing something that isnt even in the model file then you're kind of on your own but someone who knows code might be able to help. 
  - When removing variables from the config.yaml file be aware that this could affect other varaibles if they are calculated using them or so on. 

### Validation:
https://otoole.readthedocs.io/en/latest/functionality.html#otoole-validate