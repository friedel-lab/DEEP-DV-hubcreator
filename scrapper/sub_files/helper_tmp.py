import pandas, re
geo_series_file = "../result_files/geoSeries.txt"

complete_series_data = pandas.read_csv(geo_series_file)
bioprojects = []

for index, row in complete_series_data.iterrows():
    links = row["Series_relation"]
    
    if "BioProject" in str(links):
        match = re.search(r'(PRJ\w{2}\d+)', links)

        if match:
            bioproject_id = match.group(1)
            bioprojects.append(bioproject_id)
    else:
        bioprojects.append("NA")

complete_series_data["BioProject"] = bioprojects

complete_series_data.to_csv(f"../result_files/geoSeries2.txt", index = False, na_rep = "NA")
    