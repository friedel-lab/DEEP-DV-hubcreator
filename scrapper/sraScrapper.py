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

parser = argparse.ArgumentParser(description="sraScrapper.py extracts metadata from SRA by using the package 'pysradb'")
parser.add_argument("-config", help="Path to the directory containing the config files.", default=f"{config_file_path}")
parser.add_argument("-output_dir", help="Path to the directory were the result files should be saved.", default=data_files_path)
parser.add_argument("-input_dir", help="Path to the directory containing the result/meta data files from geoScrapper.py.", default=data_files_path)
parser.add_argument("-classes", help="Path to the directory were the python classes are saved.", default=python_classes_path)
args = parser.parse_args()

sys.path.append(args.classes)

from geoScrapper_classes import virus_reader, select_sra_columns, compute_percentage, sra_container_extraction

vrd = virus_reader(f"{args.config}/config_virus.txt")
virus_list = vrd.get_virus_list()

# Get filter query from the virus config object. Remove last letters/the last OR
filter_query = vrd.get_filter()[:-4]

# Just for testing
current_date = datetime.now()
formatted_date = current_date.strftime("%d-%m-%Y")
publication_date = f"01-01-2024:{formatted_date}"

sra_search = SraSearch(
       verbosity=2,
       return_max=1000000,
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

#perc_calc = compute_percentage(5, len(srps))

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
				failed_srps.append(f"{srp} is NA")
				continue       
				
			for column, value in row.iteritems():
				if str(value) == "<NA>" or pandas.isna(value) or str(value) == "missing":
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

if len(failed_srps) == 0:
    print("All SRPs were extracted successfully.")
else:
    print(f"Extraction of these SRPs has failed: {failed_srps}")
    
sra_study_data = sra_study_data.sort_values(by="study_accession", ascending=False)

sra_study_data.to_csv(f"{args.output_dir}/sraStudyData2.txt", sep = "\t", index=False, na_rep="NA")
sra_run_data.to_csv(f"{args.output_dir}/sraRunData2.txt", sep = "\t", index=False, na_rep="NA")