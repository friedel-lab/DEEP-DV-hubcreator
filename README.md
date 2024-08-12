README

Required software:
* Conda, e.g. miniforge (https://github.com/conda-forge/miniforge)
* All other required software is automatically loaded using conda. 

To run the DEEP-DV hub creator you need to first create the conda environment: `conda env create -f conda_environment.yml`

To activate the environment you then have to activate the environment: `conda activate hubcreator`


1. Workflow

How this all works: 
    1. Meta data gets scrapped from the scrappers ("internalScrapper.py", "geoScrapper.py" and "sraScrapper.py"). The extracted meta data is saved by the scrappers in 
    comma or tab separated files ("internalSeries.txt", "internalSamples.txt", "geoSeries.txt", "geoSamples.txt", "sraStudyData.txt" and "sraRunData.txt"). 
    2. The python file "build_webpage.py" is then used to build the webpage(s). Therefore "build_webpage.py" reads in the CSV/TSV files containing the meta data and builds  
    the content of the webpage(s).
    3. At last the resulting webpages can be zipped and shared. 

    Info: The python files "updateGeo.py" and "updateSra.py" are highly recommended to use, since "geoScrapper.py" takes 4-5 hours of runtime and "sraScrapper.py" more than 10 hours.
    Also when re-running "geoScrapper.py" or "sraScrapper.py", it will  extract the exact same series and samples like before, apart of those, which are uploaded or updated on 
    "Gene expression omnibus" since the last invocation of "geoScrapper.py" or "sraScrapper.py" (so much of the work would unnecessarily be done twice). To save time, use 
    "updateGeo.py" or "updateSra.py" and use the default time setting or a specified time setting (see down below) to simply update the already existing  meta data files 
    (runtime ~ less than one minute for update of last week, runtime ~ 1 minute for update of last three months). There is no update file for "internalScrapper.py", since 
    "internalScrapper.py" has a runtime of less than one minute. Just run all series again, to update.

2. Structure and directories

All important files are in the directory "hiwi_project". This directory contains a few other sub-directories: "config_files", "python_classes", "result_files", "scrapper" and
"webpage". In the following sections, I will introduce all directories, their files and their usage.

2.1 Directory "config_files"

This directory contains all config files that can be used to flexibly adjust/modify the output. For more details, look at the discription (in the header) of the files.

    config_geo_cols.txt: You can select which columns should be shown for series and samples on the GEO data webpage.
    config_internal_cols.txt: You can select which columns should be shown for series and samples on the internal data webpage.
    config_sra_cols.txt: You can select which columns should be shown for studies and runs on the SRA data webpage.
    config_geo_relevance.txt: You can select which columns should be used, to check whether a series is relevant or which virus it corresponds to for the GEO data.
    config_internal_relevance.txt: You can select which columns should be used, to check for a series which virus it corresponds to for the internal data.
    config_sra_relevance.txt: You can select which columns should be used, to check whether a series is relevant or which virus it corresponds to for the SRA data.
    config_virus.txt: This file contains all viruses, categories and their synonyms which are used to filter and scrap public geo data.
    config_question.txt: This file contains questions and answers for the Q&A webpage, which is linked to the other data webpages.
    config_webpage.txt: You can choose, which of the webpages should get created or if all webpages should get created. Additionaly you can specify the number of
        parallel displayed series on one page. 

2.2 Directory "python_classes"

This directory contains python classes that are used by all python files from the project. These classes serve the purpose to reduce redundant code. Here is no python file,
which has to be invoked for the workflow.

    __pychache__: This is an automatically created directory. It is not important.
    excelScrapper_classes.py: Python file containing the classes, which are used by "excelScrapper.py" and "build_webpage.py"
    geoScrapper_classes.py: Python file containing the classes, which are used by "softScrapper.py", "update.py" and "build_webpage.py"


2.3 Directory "result_files", contains output files

This directory contains one additional directory and a few files (reduced example files are included).

    geoSeries.txt: CSV file containing series meta data from public GEO data.
    geoSamples.txt: CSV file containing sample meta data from public GEO data.
    internalSeries.txt: CSV file containing series meta data from local excel files.
    internalSamples.txt: CSV file containing sample meta data from local excel files.
    sraStudyData.txt: TSV file containing study meta data from SRA data.
    sraRunData.txt: TSV file containing run meta data from SRA data.
    directory "webpage_to_zip": Will be explained in 2.3.1

    2.3.1 Directory "webpage_to_zip"

    This directory contains the webpages, which are build by "build_webpage.py". When you want to zip the webpages, so you can share it, just zip this folder.
    -> zip -r yourZipName.zip webpage_to_zip


2.4 Directory "scrapper"

This directory contains the python files which scrap/extract the meta data. 

    internalScrapper.py: This python file accesses the folder "GEOTabellen", the location of the internal excel files. It then extracts the meta data from those excel files and
    saves it in "result_files" as "internalSeries.txt" and "internalSamples.txt". 
    -> python internalScrapper.py 
    (For additional parameters execute python internalScrapper.py --help or see 3. down below)

    geoScrapper.py: This python file downloads meta data from the "Genome expression omnibus" and extracts it from these files. The extracted meta data is then saved in 
    "result_files" as "geoSeries.txt" and "geoSamples.txt".
    -> python geoScrapper.py
    (For additional parameters execute python geoScrapper.py --help or see 3. down below)

    sraScrapper.py: This python file downloads meta data from the SRA by using the package pysradb and extracts it. The extracted meta data is then saved in 
    "result_files" as "sraSeries.txt" and "sraSamples.txt".
    -> python sraScrapper.py
    (For additional parameters execute python sraScrapper.py --help or see 3. down below)

    updateGeo.py: This python file updates the files "geoSeries.txt" and "geoSamples.txt" from the directory "result_files". You can specify the time-range for the update.
    In default settings, update.py will update the data with those GSE that where added or modified in the last week in "Gene expression omnibus".
    -> python updateGeo.py 
    (For additional parameters execute python updateGeo.py --help or see 3. down below)

    updateSra.py: This python file updates the files "sraSeries.txt" and "sraSamples.txt" from the directory "result_files". You can specify the time-range for the update.
    In default settings, updateSra.py will update the data with those SRP that where added or modified in the last week in SRA.
    -> python updateSra.py 
    (For additional parameters execute python updateSra.py --help or see 3. down below)


2.5 Directory "webpage"

    This directory contains the python file "build_webpage.py". This file creates the webpages you specified in the config file "config_webpage.txt" with the columns
    you specified in the config files "config_geo_cols.txt", "config_sra_cols" and "config_internal_cols.txt". The resulting webpages can the be found in 
    "result_files/webpage_to_zip/". Also the Q&A webpage is created.
    -> python build_webpage.py
    (For additional parameters execute python build_webpage.py --help or see 3. down below)


3. Execution of the python files:

    See down below, if you want to try the execution of the python files. I recommend to not run the geoScrapper.py and sraScrapper.py, since they need around 5 hours
    respectively 23 hours (!). I would instead try the corresponding update files, since they have the exact same code regarding the extraction of metadata. The only 
    difference is that they don't save the metadata in new dataframes. Instead they are inserting/replacing series/studies in the already existing dataframes. 

    3.1 Execution of updateGeo.py:

        python updateGeo.py \
            -config /home/proj/projekte/sequencing/Illumina/DEEP-DV/hub/hiwi_project/config_files \
            -classes /home/proj/projekte/sequencing/Illumina/DEEP-DV/hub/hiwi_project/python_classes \
            -output_dir output \
            -input_dir /home/proj/projekte/sequencing/Illumina/DEEP-DV/hub/hiwi_project/result_files \
            -time lm
        

        Parameters explained (see also python updateGeo.py --help):
            -config: Path to the conifg directory
            -classes: Path to the directory containing the python classes
            -output_dir: Path to the directory, where the output files should be saved
            -input_dir: Path to the directory containing the geoSeries.txt and geoSamples.txt files
            -time: Select a time range to get updates - lw for last week (you don't need to do this, since last week is the default setting), lm for last month, l3m for last 
            3 monts, ldx for last x days (e.g. ld9 for last 9 days).

    3.2 Execution of updateSra.py:

        python updateSra.py \
            -config /home/proj/projekte/sequencing/Illumina/DEEP-DV/hub/hiwi_project/config_files \
            -classes /home/proj/projekte/sequencing/Illumina/DEEP-DV/hub/hiwi_project/python_classes \
            -output_dir output \
            -input_dir /home/proj/projekte/sequencing/Illumina/DEEP-DV/hub/hiwi_project/result_files \
            -time lm
        

        Parameters explained (see also python updateSra.py --help):
            -config: Path to the conifg directory
            -classes: Path to the directory containing the python classes
            -output_dir: Path to the directory, where the output files should be saved
            -input_dir: Path to the directory containing the geoSeries.txt, sraRunData.txt and sraStudyData.txt files.
            -time: Select a time range to get updates - lw for last week (you don't need to do this, since last week is the default setting), lm for last month, l3m for last 
            3 monts, ldx for last x days (e.g. ld9 for last 9 days).
    
    3.3 Execution of internalScrapper.py:

        python internalScrapper.py \
            -config /home/proj/projekte/sequencing/Illumina/DEEP-DV/hub/hiwi_project/config_files \
            -classes /home/proj/projekte/sequencing/Illumina/DEEP-DV/hub/hiwi_project/python_classes \
            -tab_folder /home/proj/projekte/sequencing/Illumina/DEEP-DV/hub/GEOTabellen \
            -output_dir output
        

        Parameters explained (see also python internalScrapper.py --help):
            -config: Path to the conifg directory
            -classes: Path to the directory containing the python classes
            -tab_folder: Path to the directory containing the excel files ("GEOTabellen") for internal metadata
            -output_dir: Path to the directory, where the output files should be saved

    3.3 Execution of build_webpage.py:

        python build_webpage.py \
            -config /home/proj/projekte/sequencing/Illumina/DEEP-DV/hub/hiwi_project/config_files \
            -classes /home/proj/projekte/sequencing/Illumina/DEEP-DV/hub/hiwi_project/python_classes \
            -output_dir output \
            -input_dir /home/proj/projekte/sequencing/Illumina/DEEP-DV/hub/hiwi_project/result_files

        
        Parameters explained (see also python updateSra.py --help):
            -config: Path to the conifg directory
            -classes: Path to the directory containing the python classes
            -output_dir: Path to the directory, where the output files should be saved
            -input_dir: Path to the directory containing the metadata files from all scrappers.
