


import pandas as pd
import numpy as np
import yaml
import os
import time
import subprocess
#make directory the root of the project
if os.getcwd().split('\\')[-1] == 'src':
    os.chdir('..')
    print("Changed directory to root of project")

def remove_apostrophes_from_region_names(tmp_directory, path_to_results_config):

    with open(f'{path_to_results_config}') as f:
        contents_var = yaml.safe_load(f)
    for key in contents_var.keys():
        if contents_var[key]['type'] == 'result':
            fpath = f'{tmp_directory}/{key}.csv'
            #chekc if file exists
            if not os.path.exists(fpath):
                print(f'File {fpath} does not exist')#We need to double check we are handling data_config and results_config correctly
                continue
            #print(fpath)
            _df = pd.read_csv(fpath).reset_index(drop=True)
            #change the region names to remove apostrophes if they are at the start or end of the string
            _df['REGION'] = _df['REGION'].str.strip("'")
            _df.to_csv(fpath,index=False)
    return

def save_results_as_excel(tmp_directory, results_directory,path_to_results_config, economy, scenario, model_start):
        
    # Now we take the CSV files and combine them into an Excel file
    # First we need to make a dataframe from the CSV files
    # Note: if you add any new result parameters to osemosys_fast.txt, you need to update results_config.yml
    with open(f'{path_to_results_config}') as f:
        contents_var = yaml.safe_load(f)
    results_df={}
    for key in contents_var.keys():
        if contents_var[key]['type'] == 'result':
            fpath = f'{tmp_directory}/{key}.csv'
            #print(fpath)
            _df = pd.read_csv(fpath).reset_index(drop=True)
            results_df[key] = _df
    results_dfs = {}
    results_dfs = {k:v for (k,v) in results_df.items() if not v.empty}
    _result_tables = {}
    
    for key in results_dfs.keys():
        indices = contents_var[key]['indices']
        _df = results_dfs[key]
        if 'TIMESLICE' in indices:
            unwanted_members = {'YEAR', 'VALUE'}
            _indices = [ele for ele in indices if ele not in unwanted_members]
            df = pd.pivot_table(_df,index=_indices,columns='YEAR',values='VALUE',aggfunc=np.sum)
            df = df.loc[(df != 0).any(axis=1)] # remove rows if all are zero
            _result_tables[key] = df
        elif 'TIMESLICE' not in indices:
            if contents_var[key]['type'] == 'result':
                unwanted_members = {'YEAR', 'VALUE'}
                _indices = [ele for ele in indices if ele not in unwanted_members]
                df = pd.pivot_table(_df,index=_indices,columns='YEAR',values='VALUE')
                df = df.loc[(df != 0).any(axis=1)] # remove rows if all are zero
                _result_tables[key] = df
            elif contents_var[key]['type'] == 'param':
                unwanted_members = {'YEAR', 'VALUE'}
                _indices = [ele for ele in indices if ele not in unwanted_members]
                df = pd.pivot_table(_df,index=_indices,columns='YEAR',values='VALUE')
                df = df.loc[(df != 0).any(axis=1)] # remove rows if all are zero
                _result_tables[key] = df
            elif contents_var[key]['type'] == 'equ':
                unwanted_members = {'YEAR', 'VALUE'}
                _indices = [ele for ele in indices if ele not in unwanted_members]
                df = pd.pivot_table(_df,index=_indices,columns='YEAR',values='VALUE')
                #df = df.loc[(df != 0).any(axis=1)] # remove rows if all are zero
                _result_tables[key] = df
        _result_tables[key]=_result_tables[key].fillna(0)
    results_tables = {k: v for k, v in _result_tables.items() if not v.empty}
    
    # We take the dataframe of results and save to an Excel file
    print("Creating the Excel file of results. Results saved in the results folder.")
    scenario = scenario.lower()
    #if results tables not empty then save to excel
    if results_tables:
        with pd.ExcelWriter(f'{results_directory}/{economy}_results_{scenario}_{model_start}.xlsx') as writer:
            for k, v in results_tables.items():
                v.to_excel(writer, sheet_name=k, merge_cells=False)
    return

def save_results_as_long_csv(tmp_directory,results_directory, economy, scenario, model_start):

    # print('There are probably significant issues with this function because it is also saving the data config files to the long csv')
    
    #create_lsit of csvs in tmp_directory:
    csv_list = [x for x in os.listdir(tmp_directory) if x.split('.')[-1] == 'csv']

    #iterate through sheets in tmp
    for file in csv_list:
        #if file is not a csv or is in this list then skip it
        ignored_files = ['SelectedResults.csv']
        if file.split('.')[-1] != 'csv' or file in ignored_files:
            continue
        #load in sheet
        sheet_data = pd.read_csv(tmp_directory+'/'+file)

        #The trade file will have two Region columns. Set the second one to be 'REGION_TRADE'
        if file == 'Trade.csv':
            sheet_data.rename(columns={'REGION.1':'REGION_TRADE'}, inplace=True)

        #add file name as a column (split out .csv)
        sheet_data['SHEET_NAME'] = file.split('\\')[-1].split('.')[0]
        #if this is the first sheet then create a dataframe to hold the data
        if file == csv_list[0]:
            combined_data = sheet_data
        #if this is not the first sheet then append the data to the combined data
        else:
            combined_data = pd.concat([combined_data, sheet_data], ignore_index=True)

    #remove any coluymns with all na's
    combined_data = combined_data.dropna(axis=1, how='all')

    #count number of na's in each column and then order the cols in a list by the number of na's. We'll use this to order the cols in the final dataframe
    na_counts = combined_data.isna().sum().sort_values(ascending=True)
    ordered_cols = list(na_counts.index)

    #reorder the columns so the year cols are at the end, the ordered first cols are at start and the rest of the cols are in the middle
    new_combined_data = combined_data[ordered_cols]

    #CREATE TWO TALL DFS. ONE WHERE THE YEARS ARE COLUMNS AND THE OTHER WHERE THE SHEET_NAME'S ARE COLUMNS:
    #YEAR COLUMNS
    #pivot so each unique vlaue in sheet name is a column and value is the value in the value column
    other_cols = new_combined_data.columns.difference(['YEAR','VALUE'])
    new_combined_data_year_tall = new_combined_data.pivot(index=other_cols, columns='YEAR', values='VALUE').reset_index()
    #SHEET_NAME COLUMNS
    other_cols = new_combined_data.columns.difference(['SHEET_NAME','VALUE'])
    new_combined_data_sheet_name_tall = new_combined_data.pivot(index=other_cols, columns='SHEET_NAME', values='VALUE').reset_index()

    #save combined data to csv
    new_combined_data_year_tall.to_csv(f'{results_directory}/tall_years_{economy}_results_{scenario}_{model_start}.csv', index=False)
    new_combined_data_sheet_name_tall.to_csv(f'{results_directory}/tall_sheet_names_{economy}_results_{scenario}_{model_start}.csv', index=False)
    
    return


def create_res_visualisation(path_to_results_config,scenario,economy,path_to_input_data_file,results_directory):
    #run visualisation tool
    #https://otoole.readthedocs.io/en/latest/

    #PLEASE NOTE THAT THE VIS TOOL REQUIRES THE PACKAGE pydot TO BE INSTALLED. IF IT IS NOT INSTALLED, IT WILL THROW AN ERROR. TO INSTALL IT, RUN THE FOLLOWING COMMAND IN THE TERMINAL: pip install pydot OR conda install pydot

    #For some reason we cannot make the terminal command work in python, so we have to run it in the terminal. The following command will print the command to run in the terminal:

    # path_to_data_config = f'{root_dir}/config/{data_config_file}'
    path_to_visualisation = f'{results_directory}/energy_system_visualisation_{scenario}_{economy}.png'

    # path_to_data_config = f'{root_dir}/config/{data_config_file}'
    command = f'otoole viz res datafile {path_to_input_data_file} {path_to_visualisation} {path_to_results_config}'
    print('Please run the following command in the terminal to create the visualisation:\n')
    print(command)
    return

def extract_osmosys_cloud_results_to_csv(tmp_directory, path_to_results_config):
    #load in the result.txt file from osmosys cloud and make it into csvs like we would if we ran osemosys locally. Note that this is the result.txt file you get when you downlaod result_####.zip from osmosys cloud and extract the result.txt file
    #we will just run the file through the f"otoole results cbc csv {tmp_directory}/cbc_results_{economy}_{scenario}.txt {tmp_directory} {path_to_results_config}" script to make the csvs. That script is from the model_solving_functions.solve_model() function
    #remember to put the results file in the tmp directory

    #convert to csv
    start = time.time()
    #check the result.txt file is in the tmp directory
    if 'result.txt' not in os.listdir(tmp_directory):
        print('The result.txt file is not in the tmp directory. Please get it from osemosys-cloud.com, put it in the tmp directory and try again. There is documentation in the documentation folder if you want to know how to do this.')
        return False
    
    command=f"otoole results cbc csv {tmp_directory}/result.txt {tmp_directory} {path_to_results_config}"
    result = subprocess.run(command,shell=True, capture_output=True, text=True)
    print("\n Printing command line output from converting OsMOSYS CLOUD output to csv \n")#results_cbc_{economy}_{scenario}.txt
    print(command+'\n')
    print(result.stdout+'\n')
    print(result.stderr+'\n')
    print('\n Time taken: {} for converting OsMOSYS CLOUD output to csv \n\n########################\n '.format(time.time()-start))
    return True

