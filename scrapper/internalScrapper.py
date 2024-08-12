#!/usr/bin/python3.11

import pandas, os, sys
import argparse
# Path to external classes
current_folder = os.path.dirname(os.path.abspath(__file__))
python_classes_path = os.path.join(current_folder, "..", "python_classes")


# Argument parser for config file and GEO table file paths (default settings are available)
config_file_path = os.path.join(current_folder, "..", "config_files")
data_files_path = os.path.join(current_folder, "..", "result_files")

parser = argparse.ArgumentParser(description="internalScrapper.py extracts metadata from local excel files and saves it in dataframes")
parser.add_argument("-tab_folder", help="Filepath to the folder 'GEOTabellen', which contains all xls-files", default=f"/home/proj/projekte/sequencing/Illumina/DEEP-DV/hub/GEOTabellen")
parser.add_argument("-config", help="Path to the directory containing the config files.", default=f"{config_file_path}")
parser.add_argument("-output_dir", help="Path to the directory were the result files should be saved.", default=data_files_path)
parser.add_argument("-classes", help="Path to the directory were the python classes are saved.", default=python_classes_path)
args = parser.parse_args()

sys.path.append(args.classes)

from geoScrapper_classes import virus_reader
from excelScrapper_classes import list_to_data, excel_columns_selector

# Get viruses and their corresponding synonyms
vrd = virus_reader(f"{args.config}/config_virus.txt")
virus_list = vrd.get_virus_list()

# Get all GEO excel files
folder_path = args.tab_folder
file_list = os.listdir(folder_path)

# Get all available columns for excel tables
ecs = excel_columns_selector(f"{args.config}/config_internal_cols.txt")
series_meta_data_list = ecs.get_series_columns()
sample_meta_data_list = ecs.get_sample_columns()

# Create dataframes
series_table_data = pandas.DataFrame(columns = series_meta_data_list)
sample_table_data = pandas.DataFrame(columns = sample_meta_data_list)

# Read config file for GEO tables
config_df = pandas.read_csv(f"{args.config}/config_internal_info.txt", sep='\t')
ltd = list_to_data(virus_list, f"{args.config}/config_internal_relevance.txt")

# IID counter (IID := If there is no GSE assigned for a series, assign self created IID with the counter)
IID_counter = 0


# Iterate over all GEO excel files

for filename in file_list:

    file_path = os.path.join(folder_path, filename)

    # Only extract from excel files
    if os.path.isfile(file_path) and file_path.lower().endswith(('.xls', '.xlsx')):
         
        # Container for series and sample meta data, which will be uploaded to the corresponding data frame later on
        series_meta_data_container = {}
        sample_meta_data_container = {}
        
        # Get current GSE by filename
        if filename in list(config_df["File"]):
            
            gse = config_df.loc[config_df["File"] == filename, "Accession"].values[0]
            # Status information only contained in config file. Will extract it right now
            series_meta_data_container["status"] = [config_df.loc[config_df["File"] == filename, "Status"].values[0]]
            series_meta_data_container["contact"] = [config_df.loc[config_df["File"] == filename, "Contact"].values[0]]
            if str(gse).startswith("GSE"):
                series_meta_data_container["NCBI_generated_data"] = [f"https://www.ncbi.nlm.nih.gov/geo/download/?acc={config_df.loc[config_df['File'] == filename, 'Accession'].values[0]}"]
                series_meta_data_container["ARCHS4"] = [f"https://maayanlab.cloud/archs4/series/{config_df.loc[config_df['File'] == filename, 'Accession'].values[0]}"]

            if not str(gse).startswith("GSE"):
                gse = f"IID{IID_counter}"
                IID_counter += 1
        # If file isn't listed in config file, assign "own" GSE (IID number)
        else:
            gse = f"IID{IID_counter}"
            IID_counter += 1


        # Load GSE in the data container
        series_meta_data_container["Series_geo_accession"] = [gse]
        sample_meta_data_container["Sample_series_id"] = gse

        # First sheet name for old version, second for new version
        sheet_names = ["2. Metadata Template", "METADATA TEMPLATE ", "Tabelle1"]

        # Try different sheet names for different versions and load excel file
        for sheet_name in sheet_names:
            try: # I added engine='xlrd' for conda
                # For conda installation
                excel_file = pandas.read_excel(file_path, sheet_name = sheet_name, engine='openpyxl')
                # For normal execution
                #excel_file = pandas.read_excel(file_path, sheet_name = sheet_name)
                break
            except:
                continue
        
        # Variables that indicate which part of the file has already been reached
        reached_series_part = False
        reached_samples_part = False
        # Iterate over all lines of the excel file
        for index, row in excel_file.iterrows():
            
            # Tells us information about in which part of the file we actually are 
            row_identifier = str(row.iloc[0]).strip()
            # Extracts the value, if row_identifier suggests meta data information
            row_value = str(row.iloc[1]).strip()
            
            # All lines starting with '#' are comments and not interesting
            if row_identifier.startswith("#"):
                continue
            
            # 'SERIES' (or 'STUDY') indicate that the series part of the old version file (or new version file) starts
            elif row_identifier == "SERIES" or row_identifier == "STUDY":
                reached_series_part = True
                continue
            
            # 'SAMPLES' indicates that the samples part has started (identical for both versions)
            elif row_identifier == "SAMPLES":
                reached_series_part = False
                reached_samples_part = True
            
            # If we already are in the series part, do ...
            elif reached_series_part:
                
                if row_identifier in series_meta_data_list:
                    # Extract meta data into the series container. Lists as values are needed here, because 
                    # there are multiple columns for e.g. contributors
                    if row_identifier not in series_meta_data_container.keys():
                        series_meta_data_container[row_identifier] = [row_value]
                    else:
                        series_meta_data_container[row_identifier].append(row_value)
                # Dirty fix :)
                elif row_identifier in "experimental design":
                    if row_identifier not in series_meta_data_container.keys():
                        series_meta_data_container["overall design"] = [row_value]
                    else:
                        series_meta_data_container["overall design"].append(row_value)
                
                elif row_identifier in "summary (abstract)":
                    if row_identifier not in series_meta_data_container.keys():
                        series_meta_data_container["summary"] = [row_value]
                    else:
                        series_meta_data_container["summary"].append(row_value)

            # If we already are in the samples part, do ...
            elif reached_samples_part:
                
                # Calculate index for next row down below
                new_index = index + 1
                
                # Get row identifier for next row down below. 'nan' would indicate us that the samples part has ended
                still_samples = str(excel_file.iloc[new_index,0]).strip()
                
                # If we are in samples part and get directly a 'nan', this suggest that there is a empty row
                # between header (e.g. 'Sample name') and the corresponding values (e.g. 'Mock_1')
                # If that happens skip this line by increasing the new_index (so now 2 lines down below the header)
                if still_samples == "nan":
                    new_index += 1
                    still_samples = str(excel_file.iloc[new_index,0]).strip()
                
                # Extract all column names/header     
                sample_columns = excel_file.iloc[index].tolist()
                
                # 'Sample name' is a column from the old version file. We'll rename it into the corresponding name
                # from the new version: 'library name'
                if "Sample name" in sample_columns:
                    col_index = sample_columns.index("Sample name")
                    sample_columns[col_index] = "library name"
                
                # Iterate over all samples until no sample is left (indicated by 'nan')
                while still_samples != "nan":
                    
                    # Reset sample container for next sample
                    for col in sample_columns:
                        sample_meta_data_container[col] = ""
                    # Now extract the values. They will have the same column index as their corresponding headers
                    values = excel_file.iloc[new_index].tolist()
                    value_pos = 0
                    # Extract meta data for all columns/values of the samples
                    for value in values:
                        # Pay attention! There are often two columns with the same name containing different 
                        # data (e.g. raw_file). We obviously want to store the information of both columns. 
                        # Let's save the in one column in the sample data frame and seperate them by ';'
                        if value_pos > 1 and sample_columns[value_pos] == sample_columns[value_pos-1]:
                            if str(value) != "nan" and str(value).strip() != "":
                                sample_meta_data_container[sample_columns[value_pos]] += f";{value}"
                        else:
                            sample_meta_data_container[sample_columns[value_pos]] = value
                        value_pos += 1
                    # Build new sample row for each sample and add it to sample dataframe
                    new_sample_row = ltd.get_new_sample_row(sample_meta_data_container)
                    sample_table_data = pandas.concat([sample_table_data, pandas.DataFrame([new_sample_row])], ignore_index=True)
                    
                    # Increase index for next sample and check if we are still in samples part 
                    new_index += 1
                    still_samples = str(excel_file.iloc[new_index,0]).strip()
                    
                reached_samples_part = False
                        
                           
        # Add to series meta data table
        new_series_row = ltd.get_new_series_row(series_meta_data_container)
        series_table_data = pandas.concat([series_table_data, pandas.DataFrame([new_series_row])], ignore_index=True)

        print(f"{filename} has been extracted.")
    else:
        print(f"{filename} won't be extracted.")
        continue
    
# Now we have to join all sample characteristic columns:
characteristic_columns = []
for col in sample_table_data.columns:
    if col not in sample_meta_data_list:
        characteristic_columns.append(col)
        
# Bunch all characteristics for each sample in one argument seperated by ';', so it fits in one column
for acc in series_table_data["Series_geo_accession"]:
    for title in sample_table_data[sample_table_data["Sample_series_id"] == acc]["title"]:
        characteristics = ""
        # Iterate over all characteristics for each sample individually
        for col in characteristic_columns:
            value = str(sample_table_data.loc[(sample_table_data['Sample_series_id'] == acc) & (sample_table_data["title"] == title), col].values[0]).strip()
            # Check if characteristic is relevant
            if value != "NaN" and value != "nan" and value != "Na" and value != "" and value != "NA":
                characteristics += f"{col}:{value}&&"
        # If no characteristic has been documented for the sample, give back 'Na'
        if characteristics == "":
            characteristics = "NA"
        # If characteristics are available for sample, remove all 'characteristics: ' from the String (old version)
        else:
            if "characteristics" in characteristics:
                characteristics = characteristics.replace("characteristics: ", "")
                characteristics = characteristics.replace("characteristics:", "")
        sample_table_data.loc[(sample_table_data['Sample_series_id'] == acc) & (sample_table_data['title'] == title), 'Sample characteristics'] = characteristics

# Only original columns in our final dataframe
sample_table_data = sample_table_data[sample_meta_data_list]

# Sort data frame by GSE
series_table_data = series_table_data.sort_values(by="Series_geo_accession")

# Save dataframes as files
series_table_data.to_csv(f"{args.output_dir}/internalSeries.txt", index = False, na_rep = "NA")
sample_table_data.to_csv(f"{args.output_dir}/internalSamples.txt", index = False, na_rep = "NA")


