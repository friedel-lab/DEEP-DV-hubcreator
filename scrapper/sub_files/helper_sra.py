import pandas

geo = "../result_files/geoSeries.txt"
sra = "../result_files/sraStudyData3.txt"

geo_data = pandas.read_csv(geo)
sra_data = pandas.read_csv(sra, sep="\t")

geo_bio = geo_data["BioProject"]
sra_bio = sra_data["bioproject"]

common_ids = sra_bio.isin(geo_bio)

# Anzahl der gemeinsamen IDs
num_common_ids = common_ids.sum()

print(num_common_ids)

common_ids = geo_bio[geo_bio.isin(sra_bio)]

# Ausgabe der gemeinsamen IDs
print("Gemeinsame BioProject-IDs:")
print(common_ids)

