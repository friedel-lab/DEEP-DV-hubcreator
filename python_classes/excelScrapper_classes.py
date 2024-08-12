#!/usr/bin/python3.11

class relevant_excel_columns_reader:

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

################################################################################################

class list_to_data:

    virus_list = {}
    relevant_columns = []

    # Extracts data of series- or sample container and returns it
    def get_data(self, variable, container):
        # Check if container contains data for the given variable. If yes, join all the lists containing data of this variable (there can be multiple lists, if data of one variable
        # goes over more than one line). If container contains no data to this variable, return NA
        if variable in container.keys() and len(container[variable]) > 0:
            if variable in "contributor":
                varibale_value = ""
                for entry in container[variable]:
                    if(entry != 'nan'):
                        varibale_value += f"{entry};"
            else:
                varibale_value = "".join(map(str, container[variable]))
                #varibale_value = "".join(value for value in container[variable] if value.lower() != "nan")
        else:
            varibale_value = "NA"
        return varibale_value
    
    def checkList(self, keyWord, container):
            if len(container[keyWord]) > 0:
                value_list = container[keyWord]
                # Could fail here? Doesn't matter, function isn't needed
                return "".join(str(value_list))
            else:
                return "NA"

    def __init__(self, virus_list, config_path):
        self.virus_list = virus_list
        rel_col = relevant_excel_columns_reader(config_path)
        self.relevant_columns = rel_col.get_relevant_columns()

    
    def get_new_series_row(self, series_container):

        virus_gse = ""
        new_row = {}
        checked_current_virus = False

        # Get content from relevant columns (columns where the corresponding virus get searched)
        relevant_content = []
        for col in self.relevant_columns:
            content = self.get_data(col, series_container)
            relevant_content.append(content)
        
        # Check for every virus and their corresponding synonyms if they appear in content (from above). 
        for key in self.virus_list.keys():
            checked_current_virus = False
            for syno in self.virus_list[key]:
                for cont in relevant_content:
                    if syno in cont:
                        # If a sysnonym of virus_x appears, skip the remaining synonyms of virus_x and start to check the synonyms of virus_x+1 (perhaps multiple viruses are relevant for one gse)
                        virus_gse += f"{key},"
                        checked_current_virus = True
                        break
                if checked_current_virus:
                    break
        
        if virus_gse == "":
            series_container["Virus"] = "NA"
        else:
            series_container["Virus"] = virus_gse[:-1]

        for identifier in series_container.keys():
            new_row[identifier] = self.get_data(identifier, series_container)
        
        return new_row

    def get_new_sample_row(self, sample_container):

        new_row = {}
        
        for identifier in sample_container.keys():
            #new_row[identifier] = self.checkList(identifier, sample_container)
            new_row[identifier] = sample_container[identifier]
        
        return new_row


################################################################################################

class excel_columns_selector:

    # All columns that are available
    series_columns = []
    sample_columns = []
    
    # Columns that will be shown on webpage
    selected_series_columns = []
    selected_sample_columns = []

    def __init__(self, filepath):
        
        # Open config file
        with open(filepath, "r") as file:

            series_reached = False
            samples_reached = False

            for line in file:
                # Empty lines or lines starting with "#" don't have relevant content
                if line.startswith("#") or line.strip() == "":
                    continue
                # ">" indicates a new part of the config file
                elif line.startswith(">"):
                    if "Series" in line:
                        series_reached = True
                    elif "Sample" in line:
                        series_reached = False
                        samples_reached = True
                # If we have reached the series part: Add all columns (idenpend of their selection/y or n) to the series_columns list and all selected columns (y after ":") to selected_series_columns
                elif series_reached:
                    line_values = line.split(":")
                    if line_values[1].strip() in "yes":
                        self.selected_series_columns.append(line_values[0])
                    self.series_columns.append(line_values[0])
                # If we have reached the samples part: Add all columns (idenpend of their selection/y or n) to the sample_columns list and all selected columns (y after ":") to selected_sample_columns
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
        
