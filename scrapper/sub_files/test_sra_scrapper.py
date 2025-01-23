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
#current_date = datetime.now()
#formatted_date = current_date.strftime("%d-%m-%Y")
#publication_date = f"01-01-2024:{formatted_date}"
sys.stdout = open(os.devnull, 'w')
sra_search = SraSearch(
       verbosity=2,
       return_max=1000000,
       publication_date = f"01-01-2000:31-12-2000", 
       query=filter_query
)

# Search for matching SRA expriments
sra_search.search()
sys.stdout = sys.__stdout__
pre_sra_data = sra_search.df
if not pre_sra_data.empty:
    print("Hello")


"""
print(pre_sra_data)

sra_search = SraSearch(
       verbosity=2,
       return_max=1000000,
       publication_date = f"01-01-2010:01-01-2011", 
       query=filter_query
)

# Search for matching SRA expriments
sra_search.search()

pre_sra_data_2 = sra_search.df

print(pre_sra_data_2)

result = pandas.concat([pre_sra_data, pre_sra_data_2], ignore_index=True)

print(result)
"""