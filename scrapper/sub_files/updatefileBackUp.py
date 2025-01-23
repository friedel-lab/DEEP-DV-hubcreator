import pandas, os, sys
import argparse
from pysradb.search import SraSearch
from pysradb.sraweb import SRAweb
from datetime import datetime

current_folder = os.path.dirname(os.path.abspath(__file__))
python_classes_path = os.path.join(current_folder, "..", "python_classes")
sys.path.append(python_classes_path)

from geoScrapper_classes import virus_reader, select_sra_columns, compute_percentage, sra_container_extraction, backUp_file_timer

config_file_path = os.path.join(current_folder, "..", "config_files")
data_files_path = os.path.join(current_folder, "..", "result_files")

parser = argparse.ArgumentParser(description="sraScrapper.py extracts metadata from sra metadata by using the package 'pysradb'")
parser.add_argument("-config", help="Path to the directory containing the config files.", default=f"{config_file_path}")
parser.add_argument("-output_dir", help="Path to the directory were the result files should be saved.", default=data_files_path)
parser.add_argument("-input_dir", help="Path to the directory containing the result/meta data files.", default=data_files_path)
parser.add_argument("-time", help="Choose a time range to get updated and newly uploaded Series. 'lw' for last week, 'lm' for last month, 'l3m' for last 3 months or give an individual date in the following format: 'id=yyyy/mm/dd' e.g.: 'id=2015/05/05'", default = "lw")
args = parser.parse_args()

vrd = virus_reader(f"{args.config}/config_virus.txt")
virus_list = vrd.get_virus_list()

# Get filter query from the virus config object. Remove last letters/the last OR
filter_query = vrd.get_filter()[:-4]

time = args.time

bupt = backUp_file_timer()
current_date = bupt.get_today()
publication_date = ""

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
else:
    raise ValueError("Please check your format.")

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

perc_calc = compute_percentage(5, len(srps))

sra_col_sel = select_sra_columns(f"{args.config}/config_sra_cols.txt")

sra_columns = sra_col_sel.get_sra_columns()
sra_container = {}
sra_data = pandas.DataFrame(columns = sra_columns)

failed_srps = []
con_ext = sra_container_extraction(virus_list, f"{args.config}/config_sra_relevance.txt")
for srp in srps:
	try:
		percentage = perc_calc.get_percentage(srps.index(srp))
		if percentage != "":
				print(percentage)
		df = web.sra_metadata(srp, detailed = True)  
			
		for index, row in df.iterrows():
			for column, value in row.iteritems():
				if str(value) == "<NA>" or pandas.isna(value):
					value = "NA"
						
				if column in sra_columns:
					if column in sra_container.keys():
						sra_container[column].append(value)
					else:
						sra_container[column] = [value]
				else:
					if value == "NA":
						continue
					if "SRA_characteristics" in sra_container.keys():
							sra_container["SRA_characteristics"].append(f"{column}:{value}")
					else:
							sra_container["SRA_characteristics"] = [f"{column}:{value}"]
										
			# Append to sra_data new_row = con_ext.get_new_series_row(series_container, gse)
			new_row = con_ext.get_new_sra_row(sra_container)
					
			# Check if series/gse is relevant according to the config file
			if not new_row:
				sra_container = {}
				continue
			
			# Add new row to dataframe
			sra_data = pandas.concat([sra_data, pandas.DataFrame([new_row])], ignore_index=True)
			sra_container = {}
			
	except:
		failed_srps.append(srp)
		continue
    
complete_sra_data = pandas.read_csv(f"{args.input_dir}/sraData.txt", sep="\t", low_memory=False)

accession_numbers = sra_data["study_accession"]

accession_numbers = list(set(list(accession_numbers)))

if len(accession_numbers) == 0:
    print("No GSE is relevant.")
else:
    for acc in accession_numbers:
        # If SRA is already in our original data, we want to replace it. Change the differing columns would cost too much time
        if acc in complete_sra_data["study_accession"].values:
            print(f"{acc} already in data: Will be replaced ...")
            # Delete columns correspondig to the SRA from original data
            complete_sra_data = complete_sra_data[complete_sra_data["study_accession"] != acc]

            # Add the SRA containing new data to the original data
            complete_sra_data = pandas.concat([complete_sra_data, sra_data[sra_data["study_accession"] == acc]], ignore_index = True)

            print(f"{acc} got successfully replaced.\n")
        # If SRA hasn't appeared in the original data yet
        else:
            print(f"{acc} not in data. Will be added ...")
            # Simply add to the original data
            complete_sra_data = pandas.concat([complete_sra_data, sra_data[sra_data["study_accession"] == acc]], ignore_index = True)
            print(f"{acc} got successfully added.\n")

    # Safe updated data
    complete_sra_data.to_csv(f"{args.output_dir}/sraData.txt", index = False, na_rep = "NA", sep="\t")

if len(failed_srps) == 0:
    print("No SRP has failed.")
else:
    print(failed_srps)
    