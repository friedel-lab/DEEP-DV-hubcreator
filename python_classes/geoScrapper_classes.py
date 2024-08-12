#!/usr/bin/python3.11

import sys, datetime
#sys.path.append("/home/proj/projekte/sequencing/Illumina/DEEP-DV/hub/projectFiles/python_classes")
#from relevanceCol import read_in_relevant_columns


class virus_reader:
    
    """
    Variables explanation:

    - filepath: String; contains the path to the config file ("config_start.txt")
    - filter: String; the virus abbreviations and their synonyms will get merged in a format, so that the Finder-Class from package geofetch can search for gse
    - virus_list: Dictionary; contains the virus abbreviations as keys and a list containing their corresponding synonyms as values
    - dotted_box: Boolean; checks if the dotted box in config file is already reached. This is necessary that the example in config file won't be added to virus_list

    """

    filter = ""
    virus_list = {}
    virus_categories = []
    cat_vir = {}

    def __init__(self, filepath):
        
        with open(filepath, "r") as file:

            virus = ""
            dotted_box_synonyms = False
            dotted_box_categories = False
            categories_already_statisfied = False
            current_category = ""

            for line in file:
                
                if line.startswith("----") and not dotted_box_categories and not categories_already_statisfied:
                    dotted_box_categories = True
                elif dotted_box_categories and line.strip() != "" and not line.startswith("----"):
                    virus_category = line[1:].strip()
                    self.virus_categories.append(virus_category)
                elif line.startswith("----") and dotted_box_categories:
                    categories_already_statisfied = True
                    dotted_box_categories = False
                elif line.startswith("----") and categories_already_statisfied:
                    dotted_box_synonyms = True
                elif dotted_box_synonyms and line.strip() != "" and not line.startswith("----"):
                    if line.startswith("<"):
                        current_category = line[1:-2].strip()
                    elif line.startswith(">"):
                        virus = line[1:].strip()
                        self.virus_list[virus] = []
                        self.virus_list[virus].append(virus)
                        
                        if current_category in self.cat_vir.keys():
                            self.cat_vir[current_category].append(virus)
                        else:
                            self.cat_vir[current_category] = [virus]
                    else:
                        synonyms = line.split(",")
                        for syn in synonyms:
                            self.virus_list[virus].append(syn.strip())
                
                
                """
                if line.startswith(">") and dotted_box_synonyms:
                    virus = line[1:].strip()
                    self.virus_list[virus] = []
                    self.virus_list[virus].append(virus)
                elif dotted_box_synonyms and line.strip() != "" and not line.startswith("-"):
                    synonyms = line.split(",")
                    for syn in synonyms:
                        self.virus_list[virus].append(syn.strip())
                elif line.startswith("-"):
                    dotted_box_synonyms = True
                """

        for value in self.virus_list.values():
            for syn in value:
                self.filter += f"{syn} OR "

    def get_filter(self):
        return self.filter
    
    def get_virus_list(self):
        return self.virus_list

    def get_virus_categories(self):
        return self.virus_categories
    
    def get_vir_cat_dic(self):
        return self.cat_vir
    
    def get_filter_for_category(self, category):
        category_filter = ""
        for v in self.cat_vir[category]:
            for syn in self.virus_list[v]:
                category_filter += f"{syn} OR "
        
        return category_filter

####################################################################################################################

class extract_line:

    identifier = ""
    value = ""

    def __init__(self):
        pass
    
    def extract(self, line):
        # Extract values and variable. Format in file: variable_name = value. E.g.: !Series_contributor = Georg,,Weber
        values = line[1:].split(" = ")

        if len(values) == 2:
            self.identifier = values[0].strip()
            self.value = values[1].strip()
        # If len(values) > 2, it means there is at least one mor " = " in the line, which shouldn't be seperated because it belongs to the value. So the "value parts" have to be combined.
        elif len(values) > 2:
            self.identifier = values[0].strip()
            self.value = ""
            for i in range(1, len(values)):
                self.value += values[i].strip()
        # Treating remaining cases. Not relevant
        elif len(values) == 1:
            self.identifier = values[0].strip()
            self.value = "NA"
        else:
            self.identifier = "NA"
            self.value = "NA"
    
    def get_identifier(self):
        return self.identifier

    def get_value(self):
        return self.value
    
####################################################################################################################

class read_in_relevant_columns:

    relevant_columns = []

    def __init__(self, filepath):

        with open(filepath, "r") as file:
            
            for line in file:

                if line.startswith("#") or line.strip() == "":
                    continue
                else:
                    line_values = line.split(":")
                    if line_values[1].strip() in "yes":
                        self.relevant_columns.append(line_values[0].strip())
    
    def get_relevant_columns(self):
        return self.relevant_columns
    
####################################################################################################################

class select_sra_columns:
    
    # All columns that are available
    study_columns = []
    run_columns = []
    
    # Columns that will be shown on webpage
    selected_study_columns = []
    selected_run_columns = []

    def __init__(self, filepath):

        with open(filepath, "r") as file:

            study_reached = False
            run_reached = False

            for line in file:
                line = line.strip()
                if line.startswith("#") or line == "":
                    continue
                elif line.startswith(">"):
                    if "Study" in line:
                        study_reached = True
                    elif "Run" in line:
                        study_reached = False
                        run_reached = True
                elif study_reached:
                    line_values = line.split(":")
                    if line_values[1].strip() in "yes":
                        self.selected_study_columns.append(line_values[0])
                    self.study_columns.append(line_values[0])
                elif run_reached:
                    line_values = line.split(":")
                    if line_values[1].strip() in "yes":
                        self.selected_run_columns.append(line_values[0])
                    self.run_columns.append(line_values[0])
    
    def get_selected_study_columns(self):
        return self.selected_study_columns
    
    def get_selected_run_columns(self):
        return self.selected_run_columns
    
    def get_study_columns(self):
        return self.study_columns
    
    def get_run_columns(self):
        return self.run_columns
    
    #def get_sra_columns(self):
    
    #def get_sra_sel_columns(self):

####################################################################################################################

class sra_container_extraction:

    virus_list = {}
    relevant_columns = []

    # Extracts data of series- or samplecontainer and returns it
    def get_data(self, variable, container):
        # Check if container contains data for the given variable. If yes, join all the lists containing data of this variable (there can be multiple lists, if data of one variable
        # goes over more than one line). If container contains no data to this variable, return Na
        if len(container[variable]) > 0:
            varibale_value = ";".join(map(str, container[variable]))
        else:
            varibale_value = "NA"
        return varibale_value

    def __init__(self, virus_list, config_path):

        # Initialize the virus list globaly for whole class, because those won't change for the program
        self.virus_list = virus_list

        # Read in relevant columns. These columns are used to decide if a given gse/series is relevant or not

        read_rel_col = read_in_relevant_columns(config_path)
        self.relevant_columns = read_rel_col.get_relevant_columns()
    
    def contains_virus(self, sra_container):
        virus_sra = ""
        checked_current_virus = False

        relevant_content = []
        for col in self.relevant_columns:
            if col in sra_container.keys():
                content = self.get_data(col, sra_container)
                relevant_content.append(content)
        
        # Check for every virus and their corresponding synonyms if they appear in title, summary and design (from above). 
        for key in self.virus_list.keys():
            checked_current_virus = False
            for syno in self.virus_list[key]:
                for cont in relevant_content:
                    if syno.upper() in cont.upper():
                        # If a sysnonym of virus_x appears, skip the remaining synonyms of virus_x and start to check the synonyms of virus_x+1 (perhaps multiple viruses are relevant for one gse)
                        virus_sra += f"{key};"
                        checked_current_virus = True
                        break
                if checked_current_virus:
                    break

        # If virus_sra is still empty/"" then no virus synonym has been matched -> SRP isn't relevant, return False
        if virus_sra == "":
            return ""
        else:
            return virus_sra
            
    def get_new_study_row(self, sra_container):

        # String which decides if gse is relevant and if so it's the entry for the virus column in the series dataframe
        virus_sra = ""
        new_row = {}
        checked_current_virus = False

        # Get content from relevant columns
        relevant_content = []
        for col in self.relevant_columns:
            if col in sra_container.keys():
                content = self.get_data(col, sra_container)
                relevant_content.append(content)

        # Check for every virus and their corresponding synonyms if they appear in title, summary and design (from above). 
        for key in self.virus_list.keys():
            checked_current_virus = False
            for syno in self.virus_list[key]:
                for cont in relevant_content:
                    if syno.upper() in cont.upper():
                        # If a sysnonym of virus_x appears, skip the remaining synonyms of virus_x and start to check the synonyms of virus_x+1 (perhaps multiple viruses are relevant for one gse)
                        virus_sra += f"{key};"
                        checked_current_virus = True
                        break
                if checked_current_virus:
                    break

        # If virus_sra is still empty/"" then no virus synonym has been matched -> SRP isn't relevant, return empty row (empty dictionary)
        if virus_sra == "":
            return new_row
        else:
            sra_container["Virus"] = [virus_sra[:-1]]

        # If virus_sra isn't empty then at least one virus synonym hab been matched -> fill in the row with the data contained in the series_container    

        for identifier in sra_container.keys():
            new_row[identifier] = self.get_data(identifier, sra_container)
        
        return new_row 
    
    def get_new_sra_row(self, sample_container):

        new_row = {}

        # Return sample row, containing data from the samples_container

        for identifier in sample_container.keys():
            new_row[identifier] = self.get_data(identifier, sample_container)
        
        return new_row   

####################################################################################################################


class container_extraction:

    virus_list = {}
    relevant_columns = []

    # Extracts data of series- or samplecontainer and returns it
    def get_data(self, variable, container):
        # Check if container contains data for the given variable. If yes, join all the lists containing data of this variable (there can be multiple lists, if data of one variable
        # goes over more than one line). If container contains no data to this variable, return Na
        if len(container[variable]) > 0:
            varibale_value = ";".join(map(str, container[variable]))
        else:
            varibale_value = "NA"
        return varibale_value

    def __init__(self, virus_list, config_path):

        # Initialize the virus list globaly for whole class, because those won't change for the program
        self.virus_list = virus_list

        # Read in relevant columns. These columns are used to decide if a given gse/series is relevant or not

        read_rel_col = read_in_relevant_columns(config_path)
        self.relevant_columns = read_rel_col.get_relevant_columns()


            
    def get_new_series_row(self, series_container, gse):

        # String which decides if gse is relevant and if so it's the entry for the virus column in the series dataframe
        virus_gse = ""
        new_row = {}
        checked_current_virus = False

        # Get content from relevant columns
        relevant_content = []
        for col in self.relevant_columns:
            content = self.get_data(col, series_container)
            relevant_content.append(content)

        # Check for every virus and their corresponding synonyms if they appear in title, summary and design (from above). 
        for key in self.virus_list.keys():
            checked_current_virus = False
            for syno in self.virus_list[key]:
                for cont in relevant_content:
                    if syno.upper() in cont.upper():
                        # If a sysnonym of virus_x appears, skip the remaining synonyms of virus_x and start to check the synonyms of virus_x+1 (perhaps multiple viruses are relevant for one gse)
                        virus_gse += f"{key};"
                        checked_current_virus = True
                        break
                if checked_current_virus:
                    break

        # If virus_gse is still empty/"" then no virus synonym has been matched -> gse isn't relevant, return empty row (empty dictionary)
        if virus_gse == "":
            return new_row
        else:
            series_container["Virus"] = [virus_gse[:-1]]
            
        # Delete SuperSeries from data (they're just doubling the samples)
        if "Series_summary" in series_container.keys():
            for sum in series_container["Series_summary"]:
                if "SuperSeries" in sum:
                    return new_row

        # If virus_gse isn't empty then at least one virus synonym hab been matched -> fill in the row with the data contained in the series_container    

        for identifier in series_container.keys():
            new_row[identifier] = self.get_data(identifier, series_container)
        
        return new_row    


    def get_new_sample_row(self, sample_container, gse):

        new_row = {}

        # Return sample row, containing data from the samples_container

        for identifier in sample_container.keys():
            new_row[identifier] = self.get_data(identifier, sample_container)
        
        return new_row

####################################################################################################################

class select_columns:

    # All columns that are available
    series_columns = []
    sample_columns = []
    
    # Columns that will be shown on webpage
    selected_series_columns = []
    selected_sample_columns = []

    def __init__(self, filepath):

        with open(filepath, "r") as file:

            series_reached = False
            samples_reached = False

            for line in file:
                if line.startswith("#") or line.strip() == "":
                    continue
                elif line.startswith(">"):
                    if "Series" in line:
                        series_reached = True
                    elif "Sample" in line:
                        series_reached = False
                        samples_reached = True
                elif series_reached:
                    line_values = line.split(":")
                    if line_values[1].strip() in "yes":
                        self.selected_series_columns.append(line_values[0])
                    self.series_columns.append(line_values[0])
                elif samples_reached:
                    line_values = line.split(":")
                    if line_values[1].strip() in "yes":
                        self.selected_sample_columns.append(line_values[0])
                    self.sample_columns.append(line_values[0])
    
    def get_selected_series_columns(self):
        return self.selected_series_columns
    
    def get_selected_sample_columns(self):
        return self.selected_sample_columns
    
    def get_series_columns(self):
        return self.series_columns
    
    def get_sample_columns(self):
        return self.sample_columns
                
####################################################################################################################

class backUp_file_timer:

    current_time = ""
    format = ""
    formated_time = ""

    def __init__(self):
        self.current_time = datetime.datetime.now()
        self.format = "%Y-%m-%d-%H:%M"
        self.formated_time = self.current_time.strftime(self.format)
    
    def get_time(self):
        return self.formated_time

    def get_year(self):
        format = "%Y"
        return self.current_time.strftime(format)

    def get_month(self):
        format = "%m"
        return self.current_time.strftime(format)
    
    def get_day(self):
        format = "%d"
        return self.current_time.strftime(format)
    
    def get_specific_date(self, n_days):
        current_date = datetime.date.today()
        new_date = current_date - datetime.timedelta(days=n_days)
        new_date = new_date.strftime("%d-%m-%Y")
        return new_date

    def get_today(self): 
        current_date = datetime.date.today()
        return current_date.strftime("%d-%m-%Y")

    

class compute_percentage:
    
    step = -1
    step_list = []
    list_length = -1
    
    def __init__(self, step, list_length):
        print("0%")
        number_steps = int(100/step)
        self.step_list = [i * step for i in range(1, number_steps+1)]
        self.list_length = list_length
    
    def get_percentage(self, index):
        
        percentage = (float(index)/float(self.list_length))*100
        for percent in self.step_list:
            if percent < percentage:
                percent_string = f"{percent:.2f}%"
                self.step_list.remove(percent)
                return percent_string
            else:
                return ""
    
        


    

