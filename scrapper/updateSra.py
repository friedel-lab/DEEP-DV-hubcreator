import pandas, os, sys
import argparse
from pysradb.search import SraSearch
from pysradb.sraweb import SRAweb
from datetime import datetime
from tqdm import tqdm

current_folder = os.path.dirname(os.path.abspath(__file__))
python_classes_path = os.path.join(current_folder, "..", "python_classes")


config_file_path = os.path.join(current_folder, "..", "config_files")
data_files_path = os.path.join(current_folder, "..", "result_files")

parser = argparse.ArgumentParser(description="updateSRA.py extracts metadata from SRA by using the package 'pysradb'. It gets included/replaced in the existing dataframe.")
parser.add_argument("-config", help="Path to the directory containing the config files.", default=f"{config_file_path}")
parser.add_argument("-output_dir", help="Path to the directory were the result files should be saved.", default=data_files_path)
parser.add_argument("-input_dir", help="Path to the directory containing the result/meta data files.", default=data_files_path)
parser.add_argument("-time", help="Choose a time range to get updated and newly uploaded Series. 'lw' for last week, 'lm' for last month, 'l3m' for last 3 months or give an individual date in the following format: 'id=yyyy/mm/dd' e.g.: 'id=2015/05/05'", default = "auto")
parser.add_argument("-classes", help="Path to the directory were the python classes are saved.", default=python_classes_path)
args = parser.parse_args()

sys.path.append(args.classes)

from geoScrapper_classes import virus_reader, select_sra_columns, compute_percentage, sra_container_extraction, backUp_file_timer

vrd = virus_reader(f"{args.config}/config_virus.txt")
virus_list = vrd.get_virus_list()

# Get filter query from the virus config object. Remove last letters/the last OR
filter_query = vrd.get_filter()[:-4]

time = args.time

bupt = backUp_file_timer()
current_year = bupt.get_year()
current_month = bupt.get_month()
current_day = bupt.get_day()
current_date = bupt.get_today()
publication_date = ""

# Extracting last update of geo meta data
auto_start_date = ""
auto_end_date = f"{current_year}/{current_month}/{current_day}"
with open(f"{args.input_dir}/last.update_sra.txt", "r") as file:
    for line in file:
        line = line.strip()
        if line == "":
            continue
        else:
            time_array = line.split("-")
            auto_start_year = str(time_array[0]).strip()
            auto_start_month = str(time_array[1]).strip()
            auto_start_day = str(time_array[2]).strip()
            auto_start_date = f"{auto_start_year}/{auto_start_month}/{auto_start_day}"
            break

# Get SRAs from last week
if time == "lw":
    new_date = bupt.get_specific_date(7)
    publication_date = f"{new_date}:{current_date}"
# Get SRAs from last month
elif time == "lm":
    new_date = bupt.get_specific_date(30)
    publication_date = f"{new_date}:{current_date}"
# Get SRAs from last 3 months
elif time == "l3m":
    new_date = bupt.get_specific_date(90)
    publication_date = f"{new_date}:{current_date}"
# Get SRAs from an individual date on to now
elif "id" in time:
    selected_year = time.split("/")[0]
    selected_month = time.split("/")[1]
    selected_day = time.split("/")[2]
    times = time.split("=")
    publication_date = f"{selected_day}-{selected_month}-{selected_year}:{current_date}"
elif time == "auto":
    publication_date = f"{auto_start_day}-{auto_start_month}-{auto_start_year}:{current_date}"
else:
    raise ValueError("Please check your format.")

print(f"Last update on {auto_start_date}.")

sra_search = SraSearch(
       verbosity=2,
       return_max=1000000,
       publication_date = publication_date, 
       query=filter_query
)

# Search for matching SRA expriments
sra_search.search()

pre_sra_data = sra_search.df

# We only want SRA exmperiments that were not already mentioned in the extracted GEO metadata
# We will therefore extract all SRP IDs that are part of the extracted GEO metadata and drop all rows of sra_data that contain those SRP IDs

public_geo_data = pandas.read_csv(f"{args.input_dir}/geoSeries.txt")

srp_ids_geo = public_geo_data["SRP"]

# ~ is the negation ...
try:
    temp_sra_data = pre_sra_data[~pre_sra_data['study_accession'].isin(srp_ids_geo)]
except:
    print("\n\nNo new study has been found! Please increase the time range.\n\n")
    with open(f"{args.input_dir}/last.update_sra.txt", "r") as file:
        content = file.readlines()
    with open(f"{args.input_dir}/last.update_sra.txt", "w") as file:          
        file.write(str(bupt.get_time()).strip() + "\n")
        for old_line in content:
            file.write(old_line)
    sys.exit()

#srps = list(set(temp_sra_data["study_accession"]))
#print(len(srps))
###### Only once ######
#already_sra_data = pandas.read_csv(f"search_results.txt", sep="\t")
#temp_sra_data = already_sra_data[~already_sra_data['study_accession'].isin(srp_ids_geo)]
#srps = list(set(temp_sra_data["study_accession"]))
#print(len(srps))
###### Only once ######

srps = list(set(temp_sra_data["study_accession"]))

web = SRAweb()


sra_col_sel = select_sra_columns(f"{args.config}/config_sra_cols.txt")

sra_study_columns = sra_col_sel.get_study_columns()
sra_study_container = {}
sra_study_data = pandas.DataFrame(columns = sra_study_columns)

sra_run_columns = sra_col_sel.get_run_columns()
sra_run_container = {}
sra_run_data = pandas.DataFrame(columns = sra_run_columns)

failed_srps = []
con_ext = sra_container_extraction(virus_list, f"{args.config}/config_sra_relevance.txt")
progress_bar = tqdm(total=len(srps), desc="Processing", unit="iteration")

for srp in srps:
	try:
		progress_bar.update(1)
		df = web.sra_metadata(srp, detailed = True)  
	
		run_container_list = []

		for index, row in df.iterrows():
      
			new_srp = row["study_accession"]
   
			if pandas.isna(new_srp) or str(new_srp) == "nan":
				continue       
				
			for column, value in row.items():
				if str(value) == "<NA>" or pandas.isna(value) or str(value) == "missing" or str(value) == "Missing":
					value = "NA"
						
				if column in sra_run_columns:
					if column in sra_run_container.keys():
						sra_run_container[column].append(value)
					else:
						sra_run_container[column] = [value]
						
				if column in sra_study_columns:
					if column in sra_study_container.keys():
						sra_study_container[column].append(value)
						sra_study_container[column] = list(set(sra_study_container[column]))
					else:
						sra_study_container[column] = [value]
      
				if not column in sra_study_columns and not column in sra_run_columns:
					if value == "NA":
						continue
					if "SRA_characteristics" in sra_run_container.keys():
							sra_run_container["SRA_characteristics"].append(f"{column}:{value}")
					else:
							sra_run_container["SRA_characteristics"] = [f"{column}:{value}"]
										
			# Append to sra_data new_row = con_ext.get_new_series_row(series_container, gse)
			run_container_list.append(sra_run_container)
			sra_run_container = {}
   
		new_study_row = con_ext.get_new_sra_row(sra_study_container)
		new_run_row_list = []

		for con in run_container_list:
			run_row = con_ext.get_new_sra_row(con)
			run_virus = con_ext.contains_virus(con)
			if run_virus == "":
				run_virus = "NA "
			run_row["Virus"] = run_virus[:-1]
			new_run_row_list.append(run_row)
		
		common_container = sra_study_container.copy()
		for con in run_container_list:
			for key in con.keys():
				if key in common_container.keys():
					common_container[key] = common_container[key] + con[key]
					common_container[key] = list(set(common_container[key]))
				else:
					common_container[key] = con[key]

		virus = con_ext.contains_virus(common_container)

		if virus != "":
			new_study_row["Virus"] = virus[:-1]				
			sra_study_data = pandas.concat([sra_study_data, pandas.DataFrame([new_study_row])], ignore_index=True)
			for run_row in new_run_row_list:
				sra_run_data = pandas.concat([sra_run_data, pandas.DataFrame([run_row])], ignore_index=True)

		sra_study_container = {}
			
	except:
		sra_study_container = {}
		sra_run_container = {}
		failed_srps.append(srp)
		continue

progress_bar.close()
  
complete_sra_study_data = pandas.read_csv(f"{args.input_dir}/sraStudyData.txt", sep="\t", low_memory=False)
complete_sra_run_data = pandas.read_csv(f"{args.input_dir}/sraRunData.txt", sep="\t", low_memory=False)

accession_numbers = sra_study_data["study_accession"]

accession_numbers = list(set(list(accession_numbers)))

if len(accession_numbers) == 0:
    print("No SRP is relevant.")
else:
    for acc in accession_numbers:
        # If SRP is already in our original data, we want to replace it. Change the differing columns would cost too much time
        if acc in complete_sra_study_data["study_accession"].values:
            print(f"{acc} already in data: Will be replaced ...")
            # Delete columns correspondig to the SRP from original data
            complete_sra_study_data = complete_sra_study_data[complete_sra_study_data["study_accession"] != acc]
            complete_sra_run_data = complete_sra_run_data[complete_sra_run_data["study_accession"] != acc]

            # Add the SRP containing new data to the original data
            complete_sra_study_data = pandas.concat([complete_sra_study_data, sra_study_data[sra_study_data["study_accession"] == acc]], ignore_index = True)
            complete_sra_run_data = pandas.concat([complete_sra_run_data, sra_run_data[sra_run_data["study_accession"] == acc]], ignore_index = True)

            print(f"{acc} was successfully replaced.\n")
        # If SRP hasn't appeared in the original data yet
        else:
            print(f"{acc} not in data. Will be added ...")
            # Simply add to the original data
            complete_sra_study_data = pandas.concat([complete_sra_study_data, sra_study_data[sra_study_data["study_accession"] == acc]], ignore_index = True)
            complete_sra_run_data = pandas.concat([complete_sra_run_data, sra_run_data[sra_run_data["study_accession"] == acc]], ignore_index = True)

            print(f"{acc} got successfully added.\n")
            
    complete_sra_study_data = complete_sra_study_data.sort_values(by="study_accession", ascending=False)

    # Safe updated data
    complete_sra_study_data.to_csv(f"{args.output_dir}/sraStudyData.txt", index = False, na_rep = "NA", sep="\t")
    complete_sra_run_data.to_csv(f"{args.output_dir}/sraRunData.txt", index = False, na_rep = "NA", sep="\t")


if len(failed_srps) == 0:
    print("All updates were successful.")
else:
    print(f"Updates of these SRPs have failed: {failed_srps}")
    
with open(f"{args.input_dir}/last.update_sra.txt", "r") as file:
	content = file.readlines()
with open(f"{args.input_dir}/last.update_sra.txt", "w") as file:          
	file.write(str(bupt.get_time()).strip() + "\n")
	for old_line in content:
		file.write(old_line)
    