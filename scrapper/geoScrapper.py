#!/usr/bin/python3.11

import requests, pandas, gzip, sys, numpy, os, re
from geofetch import Finder
from io import BytesIO
import argparse
from tqdm import tqdm

current_folder = os.path.dirname(os.path.abspath(__file__))
python_classes_path = os.path.join(current_folder, "..", "python_classes")


config_file_path = os.path.join(current_folder, "..", "config_files")
data_files_path = os.path.join(current_folder, "..", "result_files")

parser = argparse.ArgumentParser(description="geoScrapper.py extracts metadata from public GEO Series and saves it in dataframes")
parser.add_argument("-config", help="Path to the directory containing the config files.", default=config_file_path)
parser.add_argument("-output_dir", help="Path to the directory were the result files should be saved.", default=data_files_path)
parser.add_argument("-classes", help="Path to the directory were the python classes are saved.", default=python_classes_path)
args = parser.parse_args()

sys.path.append(args.classes)

from geoScrapper_classes import virus_reader, extract_line, container_extraction, backUp_file_timer, select_columns, compute_percentage

def clear_sample_container():
    for key in sample_container.keys():
        sample_container[key] = []

def clear_series_container():
    for key in series_container.keys():
        series_container[key] = []

# Read in the viruses with their corresponding synonyms declared in the config file
vrd = virus_reader(f"{args.config}/config_virus.txt")

# Get filter for gse search and the virus list
filter = vrd.get_filter()
virus_list = vrd.get_virus_list()

virus_categories = vrd.get_virus_categories()
gse_list = []

for cat in virus_categories:
    current_filter = vrd.get_filter_for_category(cat)
    print(f"Scrapping all {cat}.")
    current_gse_obj = Finder(filters = current_filter)
    current_gse_list = current_gse_obj.get_gse_last_3_month()
    gse_list = gse_list + current_gse_list

gse_list = list(set(gse_list))

print(f"There are {len(gse_list)} series to get extracted.")

# Columns for series and sample dataframe
col_sel = select_columns(filepath=f"{args.config}/config_geo_cols.txt")

series_columns = col_sel.get_series_columns()
sample_columns = col_sel.get_sample_columns()

# Dictionaries containing the metadata to add it to the corresponding dataframe later on
series_container = {}
sample_container = {}

# Initializing dataframes
sample_data = pandas.DataFrame(columns = sample_columns)
series_data = pandas.DataFrame(columns = series_columns)

# Collect gse for which errors occured.
failed_gse = []

# Base for the complete url. url_base is equal for every gse
url_base = "https://ftp.ncbi.nlm.nih.gov/geo/series/"

line_ext = extract_line()
con_ext = container_extraction(virus_list, f"{args.config}/config_geo_relevance.txt")
bupt = backUp_file_timer()
progress_bar = tqdm(total=len(gse_list), desc="Processing", unit="iteration")

#perc_calc = compute_percentage(10, len(gse_list))
# Iterating over all gse
for gse in gse_list:
    skipper = False
    
    try:
        progress_bar.update(1)
        # Provide information about the progress
        #percentage = perc_calc.get_percentage(gse_list.index(gse))
        #if percentage != "":
            #print(percentage)

        # Check if series part of file is already reached. Stuff before that (e.g. "Database_email") isn't relevant
        reached_series = False
        # Check if samples part of file is already reached. This part follows directly after the series part in the file
        reached_samples = False
        # Check if we already reached one sample.
        reached_first_sample = False

        # Create gse-individual url. For more information visit: https://ftp.ncbi.nlm.nih.gov/geo/README.txt
        url = f"{url_base}{gse[:-3]}nnn/{gse}/soft/{gse}_family.soft.gz"

        # Send a request to the URL
        response = requests.get(url, stream=True)

        if response.status_code == 200:
            # Read the data from the request and store it in a BytesIO object
            data = BytesIO(response.content)
            
            # Unzip the BytesIO file with gzip
            with gzip.open(data, 'rt', encoding='utf-8', errors='replace') as file:
                
                for line in file:
                    
                    # Skip lines down below samples containing only numbers. Those lines always start with a number
                    if line[0].isdigit():
                        continue
                    
                    # ^ always indicates a new part of content in the file. Here it's checked if the series part is reached
                    elif line.startswith("^") and "SERIES" in line:
                        reached_series = True
                    
                    # ! always indicates metadata content. Here it's checked if we have series content to get extracted. 
                    elif line.startswith("!") and reached_series:
                                            
                        # Extracting metadata variable (identifier) and value from the content line
                        line_ext.extract(line)
                            
                        identifier = line_ext.get_identifier()
                        value = line_ext.get_value()

                        # If information is relevant, add to container
                        if identifier in series_columns:
                            
                            if identifier in series_container.keys():
                                series_container[identifier].append(value)
                            else:
                                series_container[identifier] = [value]

                    # ^ indicates the beginning of a new part in the file. 
                    elif reached_series and line.startswith("^"):
                        reached_series = False
                        # Check if sample part is reached
                        if "SAMPLE" in line:

                            # Add further analysis links that are not part of the soft file
                            series_container["NCBI_generated_data"] = [f"https://www.ncbi.nlm.nih.gov/geo/download/?acc={gse}"]
                            series_container["ARCHS4"] = [f"https://maayanlab.cloud/archs4/series/{gse}"]
                            
                            # Add SRP to compare with results from SRA scrapper. SRPs don't have columns in the meta data files, so we have to extract it from the Series_relation
                            if "Series_relation" in series_container.keys() and len(series_container["Series_relation"]) > 0:
                                for entry in series_container["Series_relation"]:
                                    entry = str(entry)
                                    srp_match = re.search(r'SRP\d+', entry)
                                    
                                    if srp_match:
                                        srp = srp_match.group()
                                        series_container["SRP"] = [srp]
                                    else:
                                        series_container["SRP"] = ["NA"]
                                    

                            # Extract series metadata from container
                            new_row = con_ext.get_new_series_row(series_container, gse)

                            # Check if series/gse is relevant according to the config file
                            if not new_row:
                                print(f"Skipped: {gse}")
                                skipper = True
                                break
                            
                            # Add new row to dataframe
                            series_data = pandas.concat([series_data, pandas.DataFrame([new_row])], ignore_index=True)

                            reached_samples = True
                            # We have now reached the first sample
                            reached_first_sample = True
                    
                    elif line.startswith("^") and "SAMPLE" in line:

                        reached_samples = True

                        if reached_first_sample:
                            
                            # It seems we have already reached the first sample. That means the sample container contains metadata to add in dataframe
                            #  Extract sample metadata from container
                            
                            new_row = con_ext.get_new_sample_row(sample_container, gse)
                            sample_data = pandas.concat([sample_data, pandas.DataFrame([new_row])], ignore_index=True)
                            
                            clear_sample_container()
                            
                        else:
                            # Add further analysis links that are not part of the soft file
                            series_container["NCBI_generated_data"] = [f"https://www.ncbi.nlm.nih.gov/geo/download/?acc={gse}"]
                            series_container["ARCHS4"] = [f"https://maayanlab.cloud/archs4/series/{gse}"]
                            
                            # Add SRP to compare with results from SRA scrapper. SRPs don't have columns in the meta data files, so we have to extract it from the Series_relation
                            if "Series_relation" in series_container.keys() and len(series_container["Series_relation"]) > 0:
                                for entry in series_container["Series_relation"]:
                                    entry = str(entry)
                                    srp_match = re.search(r'SRP\d+', entry)
                                    
                                    if srp_match:
                                        srp = srp_match.group()
                                        series_container["SRP"] = [srp]
                                    else:
                                        series_container["SRP"] = ["NA"]
                            
                            # This seems to be the first sample. So the series container contains metadata to add in dataframe
                            # Extract series metadata from container
                            new_row = con_ext.get_new_series_row(series_container, gse)
                                    
                            # Check if series/gse is relevant according to the config file
                            if not new_row:
                                skipper = True
                                print(f"Skipped: {gse}")
                                break

                            # Add metadata to dataframe
                            series_data = series_data.reset_index(drop=True)
                            series_data = pandas.concat([series_data, pandas.DataFrame([new_row])], ignore_index=True)
                            # We have now reached the first sample
                            reached_first_sample = True

                    # Extract sample metadata
                    elif line.startswith("!") and reached_samples:

                        # Extracting metadata variable (identifier) and value from the content line
                        line_ext.extract(line)
                            
                        identifier = line_ext.get_identifier()
                        value = line_ext.get_value()

                        # If information belongs to metadata we have look out for, add to container
                        if identifier in sample_columns:
                            
                            if identifier in sample_container.keys():
                                sample_container[identifier].append(value)
                            else:
                                sample_container[identifier] = [value]                            

                    else:
                        continue
                
                # Add last sample to data frame. Check if series/gse is relevant because if not it would break the for loop and gets down here
                if not skipper:

                    new_row = con_ext.get_new_sample_row(sample_container, gse)
                    sample_data = pandas.concat([sample_data, pandas.DataFrame([new_row])], ignore_index=True)
                
                # Clear container in all cases for a clean run of the next gse
                clear_sample_container()
                clear_series_container()

    except:
        failed_gse.append(gse)
        clear_sample_container()
        clear_series_container()
        continue
    
progress_bar.close()

# Drop duplicates: A few samples (Status december 29 2023: 58 samples) are doubled, since they are mentioned by two or more series
sample_data = sample_data.drop_duplicates(subset='Sample_geo_accession', keep='first')  

# Remove spaces after ":" in sample characteristics column for easier computation in build_webpage.py
def remove_spaces_after_dot(s):
    return s.replace(": ", ":") 

sample_data["Sample_characteristics_ch1"] = sample_data["Sample_characteristics_ch1"].apply(remove_spaces_after_dot)   

series_data = series_data.sort_values(by="Series_geo_accession")

series_data.to_csv(f"{args.output_dir}/geoSeries2.txt", index = False, na_rep = "NA")
sample_data.to_csv(f"{args.output_dir}/geoSamples2.txt", index = False, na_rep='NA')

formated_time = bupt.get_time()

if len(f"Extraction of these GSE has failed: {failed_gse}") > 0:
    print(failed_gse)
else:
    print("All GSE were extracted successfully.")

                

