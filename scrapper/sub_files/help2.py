import sys, os
current_folder = os.path.dirname(os.path.abspath(__file__))
python_classes_path = os.path.join(current_folder, "..", "python_classes")
sys.path.append(python_classes_path)
from geoScrapper_classes import virus_reader, select_sra_columns, compute_percentage, sra_container_extraction
sra_col_sel = select_sra_columns(f"../config_files/config_sra_cols.txt")

sra_columns = sra_col_sel.get_sra_columns()

has_no_further = True

with open("test.txt", "r") as file:
    for line in file:
        line = line.strip()
        lines = line.split("\t")
        
        for word in lines:
            word = word.strip()
            if word not in sra_columns:
                has_no_further = False
                break
        break

print(has_no_further)
        