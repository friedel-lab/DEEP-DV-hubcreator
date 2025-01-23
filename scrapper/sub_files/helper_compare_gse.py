import pandas

geo = "../result_files/geoSeries.txt"
geo_new = "../result_files/geoSeriesNew.txt"

geo_data = pandas.read_csv(geo)
geo_data_new = pandas.read_csv(geo_new)

geo_gse = list(geo_data["Series_geo_accession"])
geo_gse_new = list(geo_data_new["Series_geo_accession"])

for gse in geo_gse_new:
    if gse not in geo_gse:
        print(gse)