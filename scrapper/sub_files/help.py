import pandas, re, numpy as np
config_df = pandas.read_csv("/home/proj/projekte/sequencing/Illumina/DEEP-DV/hub/hiwi_project/result_files/publicSeries.txt")
df = pandas.read_csv("/home/proj/projekte/sequencing/Illumina/DEEP-DV/hub/hiwi_project/scrapper/sraData.txt", sep="\t", low_memory=False)

def modify_value(value):
    
    srp_match = re.search(r'SRP\d+', str(value))
    
    if srp_match:
        srp = srp_match.group()
        return srp     
    else:
        return "NA"

#df.replace('<NA>', "NA", inplace=True, regex=False)
#df.replace('<NA>', np.nan, inplace=True)
#df.fillna('NA', inplace=True)

def replace_na(text):
    return str(text).replace('<NA>', 'NA')

# Anwendung der Funktion auf die Spalte
df['SRA_characteristics'] = df['SRA_characteristics'].apply(replace_na)
df.fillna('NA', inplace=True)
df.to_csv('sraData.txt', index=False, sep="\t")