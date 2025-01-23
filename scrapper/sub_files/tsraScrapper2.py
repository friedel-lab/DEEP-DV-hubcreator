import pandas, os, sys
import argparse
from pysradb.search import SraSearch
from pysradb.sraweb import SRAweb
from datetime import datetime

current_folder = os.path.dirname(os.path.abspath(__file__))
python_classes_path = os.path.join(current_folder, "..", "python_classes")
sys.path.append(python_classes_path)

from geoScrapper_classes import virus_reader, select_sra_columns, compute_percentage, sra_container_extraction

config_file_path = os.path.join(current_folder, "..", "config_files")
data_files_path = os.path.join(current_folder, "..", "result_files")

parser = argparse.ArgumentParser(description="sraScrapper.py extracts metadata from sra metadata by using the package 'pysradb'")
parser.add_argument("-config", help="Path to the directory containing the config files.", default=f"{config_file_path}")
parser.add_argument("-output_dir", help="Path to the directory were the result files should be saved.", default=data_files_path)
parser.add_argument("-input_dir", help="Path to the directory containing the result/meta data files.", default=data_files_path)
args = parser.parse_args()

vrd = virus_reader(f"{args.config}/config_virus.txt")
virus_list = vrd.get_virus_list()

# Get filter query from the virus config object. Remove last letters/the last OR
filter_query = vrd.get_filter()[:-4]

# Just for testing
current_date = datetime.now()
formatted_date = current_date.strftime("%d-%m-%Y")
publication_date = f"10-10-2024:{formatted_date}"

sra_search = SraSearch(
       verbosity=2,
       return_max=1000000,
       publication_date = f"01-01-2024:{formatted_date}", 
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
temp_sra_data = pre_sra_data[~pre_sra_data['study_accession'].isin(srp_ids_geo)]

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

if len(failed_srps) == 0:
    print("No SRP has failed.")
else:
    print(failed_srps)

sra_data.to_csv(f"{args.output_dir}/sraData3.txt", sep = "\t", index=False, na_rep="NA")