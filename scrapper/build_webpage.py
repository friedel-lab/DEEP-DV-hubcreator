
import pandas, sys, argparse, re, os
from tqdm import tqdm

current_folder = os.path.dirname(os.path.abspath(__file__))
python_classes_path = os.path.join(current_folder, "..", "python_classes")

config_file_path = os.path.join(current_folder, "..", "config_files")

data_files_path = os.path.join(current_folder, "..", "result_files")

# Getting arguments. Default values are available
parser = argparse.ArgumentParser(description="build_webpage.py builds html code, which contains the webpages with all extracted metadata")
parser.add_argument("-config", help="Path to the directory containing the config files.", default=config_file_path)
parser.add_argument("-input_dir", help="Path to the directory containing the result/meta data files.", default=data_files_path)
parser.add_argument("-output_dir", help="Path to the directory were the result files should be saved.", default="../result_files/webpage_to_zip")
parser.add_argument("-classes", help="Path to the directory were the python classes are saved.", default=python_classes_path)
args = parser.parse_args()

sys.path.append(args.classes)

from excelScrapper_classes import excel_columns_selector
from geoScrapper_classes import select_columns, virus_reader, compute_percentage, select_sra_columns

# Remove existing files
def remove_files(filename):
    file_path = os.path.join(args.output_dir, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
file_names = ["geoData.html", "internalData.html", "sraData.html", "question_answer.html"]
for fn in file_names:
    remove_files(fn)

# Creating objects that contain information about selected columns
ecs = excel_columns_selector(f"{args.config}/config_internal_cols.txt")
sec = select_columns(f"{args.config}/config_geo_cols.txt")
sra_sel = select_sra_columns(f"{args.config}/config_sra_cols.txt")

# Load in data and save only selected columns
series_geo_columns = sec.get_selected_series_columns()
series_geo_df = pandas.read_csv(f"{args.input_dir}/geoSeries.txt")
series_geo_df = series_geo_df[series_geo_columns]

sample_geo_columns = sec.get_selected_sample_columns()
samples_geo_df = pandas.read_csv(f"{args.input_dir}/geoSamples.txt")
samples_geo_df = samples_geo_df[sample_geo_columns]

sra_study_columns = sra_sel.get_selected_study_columns()
sra_study_df = pandas.read_csv(f"{args.input_dir}/sraStudyData.txt", sep = "\t", low_memory=False)
sra_study_df = sra_study_df[sra_study_columns]

sra_run_columns = sra_sel.get_selected_run_columns()
sra_run_df = pandas.read_csv(f"{args.input_dir}/sraRunData.txt", sep = "\t", low_memory=False)
sra_run_df = sra_run_df[sra_run_columns]

series_excel_columns = ecs.get_selected_series_columns()
series_excel_df = pandas.read_csv(f"{args.input_dir}/internalSeries.txt")
series_excel_df = series_excel_df[series_excel_columns]
series_excel_df.columns = series_excel_df.columns.str.replace(" ", "_")

sample_excel_columns = ecs.get_selected_sample_columns()
sample_excel_df = pandas.read_csv(f"{args.input_dir}/internalSamples.txt")
sample_excel_df = sample_excel_df[sample_excel_columns]
sample_excel_df.columns = sample_excel_df.columns.str.replace(" ", "_")

vrd = virus_reader(f"{args.config}/config_virus.txt")
virus_list = vrd.get_virus_list()

categories_viruses = vrd.get_vir_cat_dic()

buildPublicPages = False
buildInternalPage = False
buildBoth = False

vis_num_geo = 20
vis_num_sra = 20
vis_num_int = -1

vis_num_sra_runs = 10
vis_num_geo_samples = 10


# Open config_webpage.txt and check, which columns should be build

with open(f"{args.config}/config_webpage.txt", "r") as file:
    for line in file:
        line = line.strip()
        if line.startswith("#") or line == "":
            continue
        line_splitted = line.split(":")
        if len(line_splitted) == 1:
            continue
        elif line_splitted[0].strip() == "public_data_pages" and line_splitted[1].strip() == "y":
            buildPublicPages = True
        elif line_splitted[0].strip() == "internal_data_page" and line_splitted[1].strip() == "y":
            buildInternalPage = True
        elif line_splitted[0].strip() == "number_visible_entries_geo":
            if line_splitted[1].strip() == "NA":
                vis_num_geo = -1
            else:
                vis_num_geo = int(line_splitted[1].strip())
        elif line_splitted[0].strip() == "number_visible_entries_sra":
            if line_splitted[1].strip() == "NA":
                vis_num_sra = -1
            else:
                vis_num_sra = int(line_splitted[1].strip())
        elif line_splitted[0].strip() == "number_visible_entries_internal":
            if line_splitted[1].strip() == "NA":
                vis_num_int = -1
            else:
                vis_num_int = int(line_splitted[1].strip())
        elif line_splitted[0].strip() == "number_visible_sra_runs":
            if line_splitted[1].strip() == "NA":
                vis_num_sra_runs = -1
            else:
                vis_num_sra_runs = int(line_splitted[1].strip())
        elif line_splitted[0].strip() == "number_visible_geo_samples":
            if line_splitted[1].strip() == "NA":
                vis_num_geo_samples = -1
            else:
                vis_num_geo_samples = int(line_splitted[1].strip())

file.close()

if buildPublicPages and buildInternalPage:
    buildBoth = True

##################################### GEO webpage #####################################
# Page for geo data

if len(categories_viruses.keys()) > 1:
    first_category = list(categories_viruses.keys())[0]
    last_category = list(categories_viruses.keys())[-1]



if(buildPublicPages):

    beg_geo_web = """

    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="UTF-8">
    <script>
    
    """
    
    total_rows_geo = series_geo_df.shape[0]
    if vis_num_geo == -1:
        dis_num_geo = total_rows_geo
    else:
        dis_num_geo = vis_num_geo
    
    beg_geo_web += f"var dis_num_geo = {dis_num_geo};\nvar vis_num_geo_samples = {vis_num_geo_samples};"
    
    beg_geo_web += """
    
    function showSamples(button, gse) {
        var tdElement = button.parentNode;
        var buttonElement = tdElement.querySelector("button");
        var sample_tablerow = document.getElementById(gse);

        if (buttonElement.textContent === "⯈") {
            buttonElement.textContent = "⯅";
            sample_tablerow.style.display = "table-row";
            sample_tablerow.style.height = "auto";
        } else {
            buttonElement.textContent = "⯈";
            sample_tablerow.style.display = "none";
        }
        getCurrentDate();
        }

    function showFullText(button) {
    var tdElement = button.parentNode; 
    var buttonElement = tdElement.querySelector("button");
    

    if (tdElement.style.whiteSpace === "normal") {
        tdElement.style.whiteSpace = "nowrap";
        buttonElement.innerHTML = "+";
    } else {
        tdElement.style.whiteSpace = "normal";
        buttonElement.innerHTML = "-";
    }
    }

    function toggleFilterPanel() {
            
        var filterPanel = document.getElementById('filter-panel');
        var filterButton = document.getElementById('OpenFilterPanelButton');
        if (filterPanel.style.display === 'none' || filterPanel.style.display === '') {
        filterPanel.style.display = 'block';
        } else {
        filterPanel.style.display = 'none';
        }
        event.stopPropagation();
    }

    
    function getIndexOfHeadColumn(head, head_column) {

        for (var i = 0; i < head.rows[0].cells.length; i++) {
            var cellText = head.rows[0].cells[i].innerText;
            
            if (cellText === head_column) {
                return i;
            }
        }

    }

    function getCurrentDate() {
        var currentDate = new Date();
        var options = { month: 'short', day: 'numeric', year: 'numeric' };
        var formattedDate = currentDate.toLocaleDateString('en-US', options);
        formattedDate = formattedDate.replace(",", "")

        return formattedDate;
    }

    function getProcessedDate(date_input) {
        date_to_number = {
            "Jan" : 1,
            "Feb" : 2,
            "Mar" : 3,
            "Apr" : 4,
            "May" : 5,
            "Jun" : 6,
            "Jul" : 7,
            "Aug" : 8,
            "Sep" : 9,
            "Oct" : 10,
            "Nov" : 11,
            "Dec" : 12
        }

        return date_to_number[date_input];
    }

    function dateCheckLeft (date_filter, date_td) {


        // yyyy-mm-dd
        dateFilterValues = date_filter.toString().split("-");
        //mmm dd yyyy
        dataTdValues = date_td.split(" ");


        if (parseInt(dateFilterValues[0], 10) < parseInt(dataTdValues[2], 10)) {
            return true;
        }
        else if(parseInt(dateFilterValues[0], 10) === parseInt(dataTdValues[2], 10)) {
            if (parseInt(dateFilterValues[1], 10) < getProcessedDate(dataTdValues[0])) {
                return true;
            }
            else if (parseInt(dateFilterValues[1], 10) === getProcessedDate(dataTdValues[0])) {
                if (parseInt(dateFilterValues[2], 10) <= parseInt(dataTdValues[1], 10)) {
                    return true;
                }
            }
        }
        return false;
    }

    function dateCheckRight (date_filter, date_td) {

        // yyyy-mm-dd
        dateFilterValues = date_filter.toString().split("-");
        //mmm dd yyyy
        dataTdValues = date_td.split(" ");


        if (parseInt(dateFilterValues[0], 10) > parseInt(dataTdValues[2], 10)) {
            return true;
        }
        else if(parseInt(dateFilterValues[0], 10) === parseInt(dataTdValues[2], 10)) {
            if (parseInt(dateFilterValues[1], 10) > getProcessedDate(dataTdValues[0])) {
                return true;
            }
            else if (parseInt(dateFilterValues[1], 10) === getProcessedDate(dataTdValues[0])) {
                if (parseInt(dateFilterValues[2], 10) >= parseInt(dataTdValues[1], 10)) {
                    return true;
                }
            }
        }
        return false;
        
    }

    function dateCheckRange (date_filter_left, date_filter_right, date_td) {


        // yyyy-mm-dd
        dateFilterValues_left = date_filter_left.toString().split("-");
        dateFilterValues_right = date_filter_right.toString().split("-");
        //mmm dd yyyy
        dataTdValues = date_td.split(" ");

        // Check if date_td > date_filter_left
        if (parseInt(dateFilterValues_left[0], 10) > parseInt(dataTdValues[2], 10)) {
            return false;
        }
        else if(parseInt(dateFilterValues_left[0], 10) === parseInt(dataTdValues[2], 10)) {
            if (parseInt(dateFilterValues_left[1], 10) > getProcessedDate(dataTdValues[0])) {
                return false;
            }
            else if (parseInt(dateFilterValues_left[1], 10) === getProcessedDate(dataTdValues[0])) {
                if (parseInt(dateFilterValues_left[2], 10) > parseInt(dataTdValues[1], 10)) {
                    return false;
                }
            }
        }

        // Check if date_td < date_filter_right
        if (parseInt(dateFilterValues_right[0], 10) < parseInt(dataTdValues[2], 10)) {
            return false;
        }
        else if(parseInt(dateFilterValues_right[0], 10) === parseInt(dataTdValues[2], 10)) {
            if (parseInt(dateFilterValues_right[1], 10) < getProcessedDate(dataTdValues[0])) {
                return false;
            }
            else if (parseInt(dateFilterValues_right[1], 10) === getProcessedDate(dataTdValues[0])) {
                if (parseInt(dateFilterValues_right[2], 10) < parseInt(dataTdValues[1], 10)) {
                    return false;
                }
            }
        }

        return true;
    }

    function check_reg_for_td(txtValue, reg_array) {

        next_and = false;
        next_or = false;
        next_not = false;
        first_entry = true;
        skip_next = false;

        overall_statisfied = true;

        for (var i = 0; i < reg_array.length; i++) {
            reg_array[i] = reg_array[i].trim();
            if (first_entry) {
                if (reg_array[i].startsWith("NOT")) {
                    if (txtValue.toUpperCase().indexOf(reg_array[i].slice(4).toUpperCase()) != -1) {
                        overall_statisfied = false;
                    }
                }
                else if (txtValue.toUpperCase().indexOf(reg_array[i].toUpperCase()) === -1) {
                    overall_statisfied = false;
                }
                first_entry = false;
            }
            else if (skip_next) {
                skip_next = false;
                continue;
            }
            else if (reg_array[i] === 'AND') {
                if (!overall_statisfied) {
                    skip_next = true;
                    continue;
                }
                next_and = true;
            }
            else if (reg_array[i] === 'OR'){
                if (overall_statisfied) {
                    skip_next = true;
                    continue;
                }
                next_or = true;
            }
            else {
                if (next_and) {
                    if (reg_array[i].startsWith("NOT")) {
                        if (txtValue.toUpperCase().indexOf(reg_array[i].slice(4).toUpperCase()) != -1) {
                            overall_statisfied = false;
                        }
                    }
                    else if (txtValue.toUpperCase().indexOf(reg_array[i].toUpperCase()) === -1) {
                        overall_statisfied = false;
                    }
                    next_and = false;
                }
                else if (next_or) {
                    if (reg_array[i].startsWith("NOT")) {
                        if (txtValue.toUpperCase().indexOf(reg_array[i].slice(4).toUpperCase()) === -1) {
                            overall_statisfied = true;
                        }
                    } 
                    else if (txtValue.toUpperCase().indexOf(reg_array[i].toUpperCase()) != -1) {
                        overall_statisfied = true;
                    }
                    next_or = false;
                }
            }
        }
        return overall_statisfied;
    }

    function closeAllSamples() {
        hiddenTableRows = document.getElementsByClassName("hidden_table_row");
        // Close all samples
        for(var i = 0; i < hiddenTableRows.length; i++) {
            hiddenTableRows[i].style.display = "none";
        }

        // Switch all sample buttons to standard

        showSamplesButtons = document.getElementsByClassName("show_sample_button");

        for(var i = 0; i < showSamplesButtons.length; i++) {

            showSamplesButtons[i].textContent = "⯈";
        }
    }

    /////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
    
    function submitChosenFilter() {

        closeAllSamples();

        var isAnyTerm = true;
        var isSeriesTerm = true;
        var isSampleTerm = true;

        var series_inputs = document.getElementsByClassName("input-for-filter");
        var sample_inputs = document.getElementsByClassName("input-sample-filter");
        var anyTermElement = document.getElementById("AnyTermFilter");
        var date_input = document.getElementsByClassName("input_dates");
        var date_sample_input = document.getElementsByClassName("input_sample_dates");

        var mainTable = document.getElementById("MainTable");
        var subTables = document.getElementsByClassName("sampleTable");

        var mainTableHead = document.getElementById("MainTableHead");
        var mainThElements = mainTableHead.querySelectorAll('th');
        var mainTableRows = document.getElementsByClassName("MainTable_rows");
        var subTableHeads = document.getElementsByClassName("SubTableHead");
        var subTableHead = subTableHeads[0];
        var subThElements = subTableHead.querySelectorAll('th');


        var checkboxes_virus = document.getElementsByClassName("virus_checkboxes");

        var gsm_column_index = getIndexOfHeadColumn(subTableHead, "Sample_geo_accession");
        var virus_column_index = getIndexOfHeadColumn(mainTableHead, "Virus");

        div_series = document.getElementById("SeriesFilterDiv");
        div_samples = document.getElementById("SampleFilterDiv");
        div_anyTerm = document.getElementById("AnyTermFilterDiv");

        const pattern = /\\b(AND|OR)\\b/g;

        if (div_series.style.display === "none") {
            isSeriesTerm = false;
        }
        if (div_samples.style.display === "none") {
            isSampleTerm = false;
        }
        if (div_anyTerm.style.display === "none") {
            isAnyTerm = false;
        }

        // Series term
        if (isSeriesTerm) {

            var text_dic = {}
            var reg_dic = {}

            var firstDate = true;

            for (var i = 0; i < series_inputs.length; i++) {

                input_id = series_inputs[i].id.split(":")[1];
                text_dic[input_id] = series_inputs[i].value.toUpperCase().trim();
                var reg_splitted = series_inputs[i].value.split(pattern)
                reg_dic[input_id] = reg_splitted.filter(item => item.trim() !== '');
            }
        
            for (var i = 0; i < date_input.length; i++) {
                input_id = date_input[i].id.split(":")[1];
                input_id = input_id.slice(0,-2);
                    if (firstDate) {
                        text_dic[input_id] = date_input[i].value;
                        text_dic[input_id] += "!&!";
                        firstDate = false;
                    }
                    else {
                        text_dic[input_id] += date_input[i].value;
                        firstDate = true;
                    }
            }
                        
            var matching_counter = 1;
            for (i = 0; i < mainTableRows.length; i++) {
                var rowShouldBeDisplayed = true; 
                var rowContainsVirus = false;

                tds = mainTableRows[i].getElementsByTagName("td");
                if (tds[virus_column_index]){
                    var anyIsChecked = false;
                    for (var j = 0; j < checkboxes_virus.length; j++) {
                        checkbox_name = ""
                        if (checkboxes_virus[j].checked) {
                            checkbox_name = checkboxes_virus[j].name.slice(0, -3);
                            anyIsChecked = true;
                        }
                        else{
                            continue;
                        }
                        if (tds[virus_column_index].textContent.indexOf(checkbox_name) > -1) {
                            rowContainsVirus = true;
                            break;
                        }
                    }
                    if (!rowContainsVirus && anyIsChecked) {
                        mainTableRows[i].style.display = "none";
                        continue;
                    }
                }
            
                for (j = 0; j < tds.length; j++) {
                    td = tds[j];
                    if (td) {
                        txtValue = td.textContent || td.innerText;
                        if (mainThElements[j]){
                            current_column = mainThElements[j].textContent;

                        if (current_column in reg_dic && reg_dic[current_column].length > 0 && !current_column.includes("_date") && !check_reg_for_td(txtValue, reg_dic[current_column])) {
                            rowShouldBeDisplayed = false;
                            break;
                        }
                        else if (current_column.includes("_date")) {

                            if (text_dic[current_column] != "!&!") {
                                dates = text_dic[current_column].split("&");

                                if (dates[0] === "!") {
                                    isValid = dateCheckRight(dates[1].slice(1, dates[1].length), txtValue);
                                    if (!isValid) {
                                        rowShouldBeDisplayed = false;
                                        break;
                                    }
                                }
                                else if (dates[1] === "!") {
                                    isValid = dateCheckLeft(dates[0].slice(0,-1), txtValue);
                                    if (!isValid) {
                                        rowShouldBeDisplayed = false;
                                        break;
                                    }
                                }
                                else {
                                    isValid = dateCheckRange(dates[0].slice(0,-1), dates[1].slice(1, dates[1].length), txtValue);
                                    if (!isValid) {
                                        rowShouldBeDisplayed = false;
                                        break;
                                    }
                                }

                            }

                        }

                        }
                    }
                }
                if (rowShouldBeDisplayed) {
                    mainTableRows[i].setAttribute("filter_number", matching_counter);
                    if (matching_counter < dis_num_geo+1) {
                            mainTableRows[i].style.display = "table-row";
                    }
                    else {
                        mainTableRows[i].style.display = "none";
                    }
                    matching_counter = matching_counter + 1;
                } else {
                    mainTableRows[i].style.display = "none";
                } 
            }
        }
        // Sample term
        else if (isSampleTerm) {

            var text_dic = {}
            var reg_dic = {}

            var firstDate = true;

            for (var i = 0; i < sample_inputs.length; i++) {

                input_id = sample_inputs[i].id.split(":")[1];
                text_dic[input_id] = sample_inputs[i].value.toUpperCase();
                var reg_splitted = sample_inputs[i].value.split(pattern);
                reg_dic[input_id] = reg_splitted.filter(item => item.trim() !== '');

            }
            
            if(reg_dic["Sample_characteristics_ch1"].length > 1) {
                alert("Conditional filtering isn't possible for sample characteristics.");
                return;
            }
        
            for (var i = 0; i < date_sample_input.length; i++) {
                input_id = date_sample_input[i].id.split(":")[1];
                input_id = input_id.slice(0,-2);
                    if (firstDate) {
                        text_dic[input_id] = date_sample_input[i].value;
                        text_dic[input_id] += "!&!";
                        firstDate = false;
                    }
                    else {
                        text_dic[input_id] += date_sample_input[i].value;
                        firstDate = true;
                    }
            }
        
        matching_counter = 1;

        for (var k = 0; k < subTables.length; k++) {
            
        tbody_subTable = subTables[k].getElementsByTagName("tbody")[0];

        tr = tbody_subTable.getElementsByTagName("tr");

        var currentSubTableHead = subTables[k].querySelector("thead")
        var currentSubThElements = currentSubTableHead.getElementsByTagName("th")

        for (i = 0; i < tr.length; i++) {
            var rowShouldBeDisplayed = true; 
            var rowContainsVirus = false;
            var rowDueToCharacteristic = false;


            tds = tr[i].getElementsByTagName("td");

            for (j = 0; j < tds.length; j++) {
                td = tds[j];
                if (td) {

                    txtValue = td.textContent || td.innerText;
                    
                    if (currentSubThElements[j]){

                        current_column = currentSubThElements[j].textContent;
                        if (current_column.includes("⯈") || current_column.includes("⯇")) {
                            current_column = current_column.replace(/⯈/g, ""); 
                            current_column = current_column.replace(/⯇/g, ""); 
                            current_column = current_column.trim();
                        }

                    if (current_column in reg_dic && reg_dic[current_column].length > 0 && !current_column.includes("_date") && !check_reg_for_td(txtValue, reg_dic[current_column])){
                        rowShouldBeDisplayed = false;              
                        break;
                    }
                    else if (current_column.includes("_date") && current_column in reg_dic) {

                        if (text_dic[current_column] != "!&!") {
                            dates = text_dic[current_column].split("&");

                            if (dates[0] === "!") {
                                isValid = dateCheckRight(dates[1].slice(1, dates[1].length), txtValue);
                                if (!isValid) {
                                    rowShouldBeDisplayed = false;
                                    break;
                                }
                            }
                            else if (dates[1] === "!") {
                                isValid = dateCheckLeft(dates[0].slice(0,-1), txtValue);
                                if (!isValid) {
                                    rowShouldBeDisplayed = false;
                                    break;
                                }
                            }
                            else {
                                isValid = dateCheckRange(dates[0].slice(0,-1), dates[1].slice(1, dates[1].length), txtValue);
                                if (!isValid) {
                                    rowShouldBeDisplayed = false;
                                    break;
                                }
                            }

                        }
                    }
                    else if(!(current_column in reg_dic) && reg_dic["Sample_characteristics_ch1"].length > 0) {

                        filterInput = reg_dic["Sample_characteristics_ch1"][0].toUpperCase().trim()

                        if(txtValue.toUpperCase().indexOf(filterInput) === -1 && !rowDueToCharacteristic) {
                            rowDueToCharacteristic = false;
                        }
                        else {
                            rowDueToCharacteristic = true;
                        }
                    }
                    }
                }
            }
            if(!rowDueToCharacteristic && reg_dic["Sample_characteristics_ch1"].length > 0) {
                rowShouldBeDisplayed = false;
            }
            // Virus verification
            if (rowShouldBeDisplayed){

                var anyIsChecked = false;
                corresponding_gse = tr[i].closest("table").id.split("_")[1];
                upper_gse_row = document.getElementById(corresponding_gse + "_MainTable");
                upper_tr = document.getElementById(corresponding_gse + "_tr");
                

                for (var j = 0; j < checkboxes_virus.length; j++) {
                    checkbox_name = ""
                    if (checkboxes_virus[j].checked) {
                        checkbox_name = checkboxes_virus[j].name.slice(0, -3);
                        anyIsChecked = true;
                    }
                    else{
                        continue;
                    }
                    if (upper_gse_row.getElementsByTagName("td")[virus_column_index].textContent.indexOf(checkbox_name) > -1) {
                        rowContainsVirus = true;
                        break;
                    }
                }
                if (!rowContainsVirus && anyIsChecked) {
                    upper_tr.style.display = "none";
                    upper_gse_row.style.display = "none";
                    continue;
                }
            }

            if (rowShouldBeDisplayed) {
                corresponding_gse = tr[i].closest("table").id.split("_")[1];
                upper_tr = document.getElementById(corresponding_gse + "_tr");
                upper_gse_row = document.getElementById(corresponding_gse + "_MainTable");
                upper_gse_row.setAttribute("filter_number", matching_counter);

                if (matching_counter < dis_num_geo+1) {
                    upper_gse_row.style.display = "table-row";
                    upper_tr.style.display = "table-row";
                    show_button = document.getElementById(corresponding_gse + "_showSamplesButton");
                    show_button.textContent = "⯅";
                }
                else {
                    upper_gse_row.style.display = "none";
                    upper_tr.style.display = "none";
                }
                matching_counter = matching_counter + 1;
                break;
                
            } else {
                corresponding_gse = tr[i].closest("table").id.split("_")[1];
                upper_tr = document.getElementById(corresponding_gse + "_tr");
                upper_tr.style.display = "none";
                upper_gse_row = document.getElementById(corresponding_gse + "_MainTable");
                upper_gse_row.style.display = "none";
            }
        }
        }
        }
        // Any term
        else if (isAnyTerm) {

            filter = anyTermElement.value;

            reg_dic = {}
            var reg_splitted = filter.split(pattern);
            reg_splitted = reg_splitted.filter(item => item.trim() !== '');
            
            if (reg_splitted.length > 1) {
                    alert("You can't use conditional filtering for this filter option!");
                    return;
                }

            matching_counter = 1;
            for (i = 0; i < mainTableRows.length; i++) {
                var rowShouldBeDisplayed = false; 
                var rowContainsVirus = false;
                var anyIsChecked = false;
                
                tds = mainTableRows[i].getElementsByTagName("td");
                gse = mainTableRows[i].id.split("_")[0];
                var upper_tr = document.getElementById(gse + "_tr");
                if(upper_tr === null) {
                                mainTableRows[i].style.display = "none";
                                continue;
                }
                if (tds[0]) {
                    
                    // Virus verification
                            
                    for (var j = 0; j < checkboxes_virus.length; j++) {
                        checkbox_name = ""
                        if (checkboxes_virus[j].checked) {
                            checkbox_name = checkboxes_virus[j].name.slice(0, -3);
                            anyIsChecked = true;
                        }
                        else{
                            continue;
                        }
                        if (mainTableRows[i].getElementsByTagName("td")[virus_column_index].textContent.indexOf(checkbox_name) > -1) {
                            rowContainsVirus = true;
                            break;
                        }
                    }
                    if (!rowContainsVirus && anyIsChecked) {
                        mainTableRows[i].style.display = "none";
                        continue;
                    }
                
                    if (check_reg_for_tr(tds, reg_splitted) | reg_splitted.length === 0) {
                        rowShouldBeDisplayed = true;
                    }
                    else {
                        smplTable = document.getElementById("sampleTable_" + gse);
                        trs_sample = smplTable.getElementsByTagName("tr");
                        
                        for (var k = 0; k < trs_sample.length; k++) {
                            tds_sample = trs_sample[k].getElementsByTagName("td");
                            if (check_reg_for_tr(tds_sample, reg_splitted)) {
                                rowShouldBeDisplayed = true;
                                break;
                            }
                        } 
                    }
                        
                    if (rowShouldBeDisplayed) {
                        mainTableRows[i].setAttribute("filter_number", matching_counter);
                        if (matching_counter < dis_num_geo+1) {
                            mainTableRows[i].style.display = "table-row";
                        }
                        else {
                            mainTableRows[i].style.display = "none";
                        }
                        matching_counter = matching_counter + 1;
                    }
                    else {
                        mainTableRows[i].style.display = "none";
                    }
                }
            
            
            }
        
        }

        var filterPanel = document.getElementById('filter-panel');
        filterPanel.style.display = 'none';
        
        var tableHeadMainRow = mainTableHead.getElementsByTagName("tr")[0];
        tableHeadMainRow.style.display = "table-row";

        for(var i = 0; i < subTableHeads.length; i++) {
            var subTableHeadRow = subTableHeads[i].getElementsByTagName("tr")[0];
            subTableHeadRow.style.display = "table-row";
        }
        
        var leftJumpButton = document.getElementById("left_jump");
        var rightJumpButton = document.getElementById("right_jump");

        leftJumpButton.disabled = true;

        matching_counter = matching_counter - 1;

        if (matching_counter < dis_num_geo) {
            end_index = matching_counter;
            rightJumpButton.disabled = true;
        }
        else {
            end_index = dis_num_geo; 
            rightJumpButton.disabled = false;
        }

        leftJumpButton.setAttribute("isFilter", "true");
        rightJumpButton.setAttribute("isFilter", "true");

        if(matching_counter === 0) {
            displayNumberResults(-1, -1, -1, true);
            leftJumpButton.setAttribute("start_number", "0");
            leftJumpButton.setAttribute("end_number", "0");
            leftJumpButton.setAttribute("total_number_filter", "0");

            rightJumpButton.setAttribute("start_number", "0");
            rightJumpButton.setAttribute("end_number", "0");
            rightJumpButton.setAttribute("total_number_filter", "0");
        }
        else {
            displayNumberResults(1, end_index, matching_counter, false);
            leftJumpButton.setAttribute("start_number", "1");
            leftJumpButton.setAttribute("end_number", end_index);
            leftJumpButton.setAttribute("total_number_filter", matching_counter);

            rightJumpButton.setAttribute("start_number", "1");
            rightJumpButton.setAttribute("end_number", end_index);
            rightJumpButton.setAttribute("total_number_filter", matching_counter);
        }
        }

        /////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

    function check_reg_for_tr(tds, reg_array) {

        next_and = false;
        next_or = false;
        next_not = false;
        first_entry = true;
        skip_next = false;

        overall_statisfied = false;

        for(var i = 0; i < reg_array.length; i++) {
            reg_array[i] = reg_array[i].trim();
            if (skip_next) {
                skip_next = false;
                continue;
            }
            else if (reg_array[i] === 'AND') {
                if (!overall_statisfied) {
                    skip_next = true;
                    continue;
                }
                next_and = true;
                continue;
            }
            else if (reg_array[i] === 'OR'){
                if (overall_statisfied) {
                    skip_next = true;
                    continue;
                }
                next_or = true;
                continue;
            }
            for(var j = 0; j < tds.length; j++) {
                if(tds[j]) {
                txtValue = tds[j].textContent;
            
                if (first_entry) {
                    if (reg_array[i].startsWith("NOT")) {
                        
                        if (txtValue.toUpperCase().indexOf(reg_array[i].slice(4).toUpperCase()) != -1) {
                            overall_statisfied = false;
                            break;
                        }
                        else {
                            overall_statisfied = true;
                        }
                    }
                    else if (txtValue.toUpperCase().indexOf(reg_array[i].toUpperCase()) != -1) {
                        overall_statisfied = true;
                        break;
                    }
                    else {
                        overall_statisfied = false;
                    }
            }
            else {
                if (next_and) {
                    if (reg_array[i].startsWith("NOT")) {
                        if (txtValue.toUpperCase().indexOf(reg_array[i].slice(4).toUpperCase()) != -1) {
                            
                            overall_statisfied = false;
                            break;
                        }
                        else {
                            overall_statisfied = true;
                        }
                    }
                    else if (txtValue.toUpperCase().indexOf(reg_array[i].toUpperCase()) != -1) {
                        overall_statisfied = true;
                        break;
                    }
                    else {
                        overall_statisfied = false;
                    }
                }
                else if (next_or) {
                    if (reg_array[i].startsWith("NOT")) {
                        if (txtValue.toUpperCase().indexOf(reg_array[i].slice(4).toUpperCase()) != -1) {
                            overall_statisfied = false;
                            break;
                        }
                        else {
                            overall_statisfied = true;
                        }

                    } 
                    else if (txtValue.toUpperCase().indexOf(reg_array[i].toUpperCase()) != -1) {
                        overall_statisfied = true;
                        break;
                    }
                    else {
                        overall_statisfied = false;
                    }
                }
            }
        }
        }
        if (first_entry) {
            first_entry = false;
        }
        if (next_or) {
            next_or = false;
        }
        if (next_and) {
            next_and = false;
        }
        }

        return overall_statisfied;
    }
    function resetFilter() {
        
        var anyFilter = document.getElementById("AnyTermFilter");
        anyFilter.value = "";
        anyFilter.disabled = false;
        
        var series_inputs = document.getElementsByClassName("input-for-filter");
        
        for (var i = 0; i < series_inputs.length; i++) {
            series_inputs[i].value = "";
        }
        
        var sample_inputs = document.getElementsByClassName("input-sample-filter");
        for (var i = 0; i < sample_inputs.length; i++) {
            sample_inputs[i].value = "";
        }

        var date_inuts = document.getElementsByClassName("input_dates");
        for (var i = 0; i < date_inuts.length; i++) {
            date_inuts[i].value = "";
        }

        var date_sample_inuts = document.getElementsByClassName("input_sample_dates");
        for (var i = 0; i < date_sample_inuts.length; i++) {
            date_sample_inuts[i].value = "";
        }

        var virus_cbs = document.getElementsByClassName("virus_checkboxes");
        for (var i = 0; i < virus_cbs.length; i++) {
            virus_cbs[i].checked = false;
        }
        
        caution_symbol = document.getElementById("cautionSymbol");
        caution_symbol.classList.remove('active');
        
        var leftJumpButton = document.getElementById("left_jump");
        var rightJumpButton = document.getElementById("right_jump");

        leftJumpButton.disabled = true;
        rightJumpButton.disabled = false;

        totalNumber = parseInt(leftJumpButton.getAttribute("total_number"));
        isFilter = leftJumpButton.getAttribute("isFilter");
        
        if (isFilter === "false") {
            start = parseInt(leftJumpButton.getAttribute("start_number"));
            end = parseInt(leftJumpButton.getAttribute("end_number"));
            
            for (var i = start; i < end+1; i++) {
            search_string = 'tr[overall_number="' + i + '"]'; 
            current_element = document.querySelector(search_string);
            current_element.style.display = "none";
            }
        }

        leftJumpButton.setAttribute("total_number_filter", "-1");
        leftJumpButton.setAttribute("isFilter", "false");
        leftJumpButton.setAttribute("start_number", "1");
        leftJumpButton.setAttribute("end_number", dis_num_geo.toString());

        rightJumpButton.setAttribute("total_number_filter", "-1");
        rightJumpButton.setAttribute("isFilter", "false");
        rightJumpButton.setAttribute("start_number", "1");
        rightJumpButton.setAttribute("end_number", dis_num_geo.toString());

        var filtered_trs = document.querySelectorAll('tr[filter_number]:not([filter_number="-1"])');

        for (var i = 0; i < filtered_trs.length; i++) {
            filtered_trs[i].style.display = "none";
            filtered_trs[i].setAttribute("filter_number", "-1");
        }

        for (var i = 1; i < dis_num_geo+1; i++) {
            search_string = 'tr[overall_number="' + i + '"]'; 
            current_element = document.querySelector(search_string);
            current_element.style.display = "table-row";
        }
    
    closeAllSamples();
    displayNumberResults(1, dis_num_geo, totalNumber, false);
    }

    function fillSecondDate(date_filter_option) {

        date_input_id_1 = "specificFilter:" + date_filter_option + "#1";
        date_input_id_2 = "specificFilter:" + date_filter_option + "#2";

        date_input_1 = document.getElementById(date_input_id_1);
        date_input_2 = document.getElementById(date_input_id_2);

        date_1 = date_input_1.value;

        date_input_2.value = date_1;
    }

    function downloadTableData() {

        var mainTableHead = document.getElementById("MainTableHead");
        var mainThElements = mainTableHead.querySelectorAll('th');
        
        var subTableHeads = document.getElementsByClassName("SubTableHead");
        var subTableHead = subTableHeads[0];
        var subThElements = subTableHead.querySelectorAll('th');

        var mainTableRows = document.getElementsByClassName("MainTable_rows");
        var gse_column_index = getIndexOfHeadColumn(mainTableHead, "Series_geo_accession");

        var series_file_content = "";
        var sample_file_content = "";
        
        characteristic_columns = document.getElementsByClassName("characteristicHead");
        characteristic_columns = Array.from(characteristic_columns);
        
        for(var i = 0; i < mainThElements.length; i++) {
            if(mainThElements[i]){
                series_file_content += mainThElements[i].textContent;
                series_file_content += "\\t"
            }
        }
        
        series_file_content = series_file_content.replace(/\t$/, '');
        series_file_content += "\\n";
        
        for(var j = 0; j < subThElements.length; j++) {
            if(subThElements[j] && characteristic_columns.indexOf(subThElements[j]) === -1){
                sub_content = subThElements[j].textContent;
                if (sub_content.includes("⯈") || sub_content.includes("⯇")) {
                        sub_content = sub_content.replace(/⯈/g, ""); 
                        sub_content = sub_content.replace(/⯇/g, ""); 
                        sub_content = sub_content.trim();
                }
                sample_file_content += sub_content;
                sample_file_content += "\\t"
            }
        } 
            
        sample_file_content += "Sample_characteristics\\n"
        
        var filtered_trs = document.querySelectorAll('tr[filter_number]:not([filter_number="-1"])');

        for (var i = 0; i < filtered_trs.length; i++) {
            sample_chars = "";
            tds = filtered_trs[i].getElementsByTagName("td");
            for(var j = 0; j < tds.length; j++) {
                if(tds[0]) {
                    if(tds[j].textContent.startsWith("⯈ ") | tds[j].textContent.startsWith("⯅ ") | tds[j].textContent.startsWith("+ ")) {
                        series_file_content += tds[j].textContent.slice(2);
                        series_file_content += "\\t";
                    }
                    else {
                        series_file_content += tds[j].textContent;
                        series_file_content += "\\t";
                    }
                }
            }
            
            series_file_content += "\\n";

            gse = filtered_trs[i].id.split("_")[0];
            var subTbl = document.getElementById("sampleTable_" + gse);
            
            var currentSampleTableHead = subTbl.querySelector("thead");
            var currentSampleThElements = currentSampleTableHead.getElementsByTagName("th");

            trs_samples = subTbl.getElementsByTagName("tr");
            
            
            for(var j = 0; j < trs_samples.length; j++) {
                tds_samples = trs_samples[j].getElementsByTagName("td");
                for(var k = 0; k < tds_samples.length; k++) {
                    if(tds_samples[0]) {
                        if(characteristic_columns.indexOf(currentSampleThElements[k]) === -1) {
                            if(tds_samples[k].textContent.startsWith("+ ") | tds_samples[k].textContent.startsWith("- ")) {
                                sample_file_content += tds_samples[k].textContent.slice(2);
                                sample_file_content += "\\t";
                            }
                            else {
                                sample_file_content += tds_samples[k].textContent;
                                sample_file_content += "\\t";
                            }
                        }
                        else {
                            if(tds_samples[k].textContent.startsWith("+ ") | tds_samples[k].textContent.startsWith("- ")) {
                                sample_chars += currentSampleThElements[k].textContent + ":" + tds_samples[k].textContent.slice(2) + "; ";
                            }
                            else {
                                sample_chars += currentSampleThElements[k].textContent + ":" + tds_samples[k].textContent + "; ";
                            } 
                        } 
                    }
                }
                sample_file_content += sample_chars;
                sample_chars = "";
                if(tds_samples[0]) {
                    sample_file_content += "\\n"
                }
                
            }
        }
        var blob = new Blob([series_file_content], { type: 'text/plain' });
        var series_file_name = 'Series_output.tsv';
        var a = document.createElement('a');

        a.href = window.URL.createObjectURL(blob);

        a.download = series_file_name;

        document.body.appendChild(a);

        a.click();

        document.body.removeChild(a);
        
        var blob = new Blob([sample_file_content], { type: 'text/plain' });
        var sample_file_name = 'Samples_output.tsv';
        var a = document.createElement('a');

        a.href = window.URL.createObjectURL(blob);

        a.download = sample_file_name;

        document.body.appendChild(a);

        a.click();

        document.body.removeChild(a);
        
        }
        
    function openNewVirusDiv(virus_category) {
        
        corresponding_virus_div = document.getElementById(virus_category + '_div');
        
        all_virus_divs = document.getElementsByClassName('viruses_divs');
        
        for(var i = 0; i < all_virus_divs.length; i++) {
            all_virus_divs[i].style.display = "none";
        }
        corresponding_virus_div.style.display = "block";
        
        change_virus_button_status(virus_category);
        caution_for_other_virus_divs(virus_category);
    }
    
    function change_virus_button_status(virus_category) {
        corresponding_virus_button = document.getElementById(virus_category + "_open_button");
        all_virus_buttons = document.getElementsByClassName("virus_open_buttons");

        for (var i = 0; i < all_virus_buttons.length; i++) {
            all_virus_buttons[i].classList.remove('active');
        }
        corresponding_virus_button.classList.add('active');
    }

    function caution_for_other_virus_divs(virus_category) {
        
        allVirusDivs = document.getElementsByClassName("viruses_divs");
        corresponding_virus_div = document.getElementById(virus_category + '_div');
        other_cbs_checked = false;
        caution_symbol = document.getElementById("cautionSymbol");
        caution_symbol.classList.remove('active');
        for(var i = 0; i < allVirusDivs.length; i++) {
            if(allVirusDivs[i] !== corresponding_virus_div ) {
                var currentVirusDiv = document.getElementById(allVirusDivs[i].id);
                var currentCheckboxes = currentVirusDiv.querySelectorAll('input[type="checkbox"]');
                for(var j = 0; j < currentCheckboxes.length; j++) {
                    if(currentCheckboxes[j].checked) {
                        other_cbs_checked = true;
                        break;
                    }
                }
                if(other_cbs_checked) {
                    break;
                }
            }
        }
        if(other_cbs_checked) {
            caution_symbol.classList.add('active');
        }   
    }

    function openNewFilterDivs(filter_name) {
        // filter_id := "Series" or "Sample" or "AnyTerm"
        resetFilter();
        
        filter_divs = document.getElementsByClassName("filterDivs");
        corresponding_filter_div = document.getElementById(filter_name + "FilterDiv");
        
        for(var i = 0; i < filter_divs.length; i++) {
            filter_divs[i].style.display = "none";
        }
        
        corresponding_filter_div.style.display = "block";
        
        change_open_buttons_status(filter_name);
    }
    
    function change_open_buttons_status(filter_name) {
        corresponding_filter_button = document.getElementById("open" + filter_name + "Filter");
        all_filter_buttons = document.getElementsByClassName("openButtons");

        for (var i = 0; i < all_filter_buttons.length; i++) {
            all_filter_buttons[i].classList.remove('active');
        }
        corresponding_filter_button.classList.add('active');
    }
    
    function deleteInput(object_id) {
        input_element = document.getElementById(object_id);
        input_element.value = "";
    }
    
    function displayNumberResults(start_num, end_num, numberTotal, noResults) {
            
            var numberInput = document.getElementById("numberSeries");
            numberInput.style.display = "inline-block";
            if(noResults) {
                numberInput.textContent = "No runs were found.";
            }
            else {
                leftJumpButton = document.getElementById("left_jump");
                total_count = parseInt(leftJumpButton.getAttribute("total_number"));
                if(total_count === dis_num_geo) {
                    numberInput.textContent = "Displaying " + end_num + "series of " + numberTotal;
                }
                else {
                    numberInput.textContent = "Series " + start_num + "-" + end_num + "/" + numberTotal;
                }
            }  
        }
        
         function nextLeftSamples() {
             
            closeAllSamples();

            leftJumpButton = document.getElementById("left_jump");
            rightJumpButton = document.getElementById("right_jump");

            leftJumpButton.disabled = false;
            rightJumpButton.disabled = false;

            start_index = parseInt(leftJumpButton.getAttribute("start_number"));
            end_index = parseInt(leftJumpButton.getAttribute("end_number"));
            total_count = parseInt(leftJumpButton.getAttribute("total_number"));
            total_count_filter = parseInt(leftJumpButton.getAttribute("total_number_filter"));
            
            if(end_index+1 - start_index < dis_num_geo) {
                new_start_index = start_index - dis_num_geo;
                new_end_index = end_index - (end_index+1 - start_index);
            }
            else {
                new_start_index = start_index - dis_num_geo;
                new_end_index = end_index - dis_num_geo;
            }
            
            if(new_start_index <= 1) {
                new_start_index = 1;
                new_end_index = new_start_index + dis_num_geo-1;
                leftJumpButton.disabled = true;
            }

            leftJumpButton.setAttribute("start_number", new_start_index);
            leftJumpButton.setAttribute("end_number", new_end_index);

            rightJumpButton.setAttribute("start_number", new_start_index);
            rightJumpButton.setAttribute("end_number", new_end_index);

            isFilter = leftJumpButton.getAttribute("isFilter");

            if (isFilter === "false") {
    
                for(var i = end_index; i > start_index-1; i--) {
                    search_string = 'tr[overall_number="' + i + '"]'; 
                    current_element = document.querySelector(search_string);
                    current_element.style.display = "none";
                }
    
                for(var i = new_end_index; i > new_start_index-1; i--) {
                    search_string = 'tr[overall_number="' + i + '"]'; 
                    current_element = document.querySelector(search_string);
                    current_element.style.display = "table-row";
                }
                displayNumberResults(new_start_index, new_end_index, total_count, false);

            }
            else {
                for(var i = end_index; i > start_index-1; i--) {
                    search_string = 'tr[filter_number="' + i + '"]'; 
                    current_element = document.querySelector(search_string);
                    current_element.style.display = "none";
                }
    
                for(var i = new_end_index; i > new_start_index-1; i--) {
                    search_string = 'tr[filter_number="' + i + '"]'; 
                    current_element = document.querySelector(search_string);
                    current_element.style.display = "table-row";
                }

                displayNumberResults(new_start_index, new_end_index, total_count_filter, false);
            }
            
        }
        
        function nextRightSamples() {
            
            closeAllSamples();
            
            leftJumpButton = document.getElementById("left_jump");
            rightJumpButton = document.getElementById("right_jump");

            leftJumpButton.disabled = false;
            rightJumpButton.disabled = false;

            start_index = parseInt(leftJumpButton.getAttribute("start_number"));
            end_index = parseInt(leftJumpButton.getAttribute("end_number"));
            total_count = parseInt(leftJumpButton.getAttribute("total_number"));
            total_count_filter = parseInt(leftJumpButton.getAttribute("total_number_filter"));
            
            new_start_index = start_index + dis_num_geo;
            new_end_index = end_index + dis_num_geo;

            isFilter = leftJumpButton.getAttribute("isFilter");

            if (isFilter === "false") {

                if(new_end_index >= total_count) {
                    new_end_index = total_count;
                    //new_start_index = new_end_index - (dis_num_geo-1);
                    rightJumpButton.disabled = true;
                }

                leftJumpButton.setAttribute("start_number", new_start_index);
                leftJumpButton.setAttribute("end_number", new_end_index);

                rightJumpButton.setAttribute("start_number", new_start_index);
                rightJumpButton.setAttribute("end_number", new_end_index);

                for(var i = start_index; i < end_index+1; i++) {
                    search_string = 'tr[overall_number="' + i + '"]'; 
                    current_element = document.querySelector(search_string);
                    current_element.style.display = "none";
                }

                for(var i = new_start_index; i < new_end_index+1; i++) {
                    search_string = 'tr[overall_number="' + i + '"]'; 
                    current_element = document.querySelector(search_string);
                    current_element.style.display = "table-row";
                }
                displayNumberResults(new_start_index, new_end_index, total_count, false);
            }
            else {

                if(new_end_index >= total_count_filter) {
                    new_end_index = total_count_filter;
                    //new_start_index = new_end_index - (dis_num_geo-1);
                    rightJumpButton.disabled = true;
                }

                leftJumpButton.setAttribute("start_number", new_start_index);
                leftJumpButton.setAttribute("end_number", new_end_index);

                rightJumpButton.setAttribute("start_number", new_start_index);
                rightJumpButton.setAttribute("end_number", new_end_index);

                for(var i = start_index; i < end_index+1; i++) {
                    search_string = 'tr[filter_number="' + i + '"]'; 
                    current_element = document.querySelector(search_string);
                    current_element.style.display = "none";
                }

                for(var i = new_start_index; i < new_end_index+1; i++) {
                    search_string = 'tr[filter_number="' + i + '"]'; 
                    current_element = document.querySelector(search_string);
                    current_element.style.display = "table-row";
                }
                displayNumberResults(new_start_index, new_end_index, total_count_filter, false);
            }
        }
        
        function nextLeftExperiments(gse) {
            
            leftBut = document.getElementById("jumpLeftSample_" + gse);
            rightBut = document.getElementById("jumpRightSample_" + gse);
            
            start_sample = parseInt(leftBut.getAttribute("startSample"));
            end_sample = parseInt(leftBut.getAttribute("endSample"));
            
            if(end_sample+1 - start_sample < vis_num_geo_samples) {
                new_start_sample = start_sample - vis_num_geo_samples;
                new_end_sample = end_sample - (end_sample+1 - start_sample);
            }
            else {
                new_start_sample = start_sample - vis_num_geo_samples;
                new_end_sample = end_sample - vis_num_geo_samples;
            }
                        
            leftBut.disabled = false;
            rightBut.disabled = false;
            
             if(new_start_sample <= 1) {
                new_start_sample = 1;
                new_end_sample = new_start_sample + (vis_num_geo_samples-1);
                leftBut.disabled = true;
            }

            leftBut.setAttribute("startSample", new_start_sample);
            leftBut.setAttribute("endSample", new_end_sample);
            
            corr_table = document.getElementById("sampleTable_" + gse);
            
            // Close current visible samples
            gsm_none = []
            for(var i = start_sample; i < end_sample+1; i++) {
                gsm_none.push("tr[sample_number='" + i + "']");
            }
            var selector_none = gsm_none.join(", ");
            samples_for_none = corr_table.querySelectorAll(selector_none);
            samples_for_none.forEach(function(tr) {
                tr.style.display = "none";
            });
            // Open new samples
            gsm_visible = []
            for(var i = new_start_sample; i < new_end_sample+1; i++) {
                gsm_visible.push("tr[sample_number='" + i + "']");
            }
            var selector_visible = gsm_visible.join(", ");
            samples_for_visible = corr_table.querySelectorAll(selector_visible);
            samples_for_visible.forEach(function(tr) {
                tr.style.display = "table-row";
            });
            
        }
        
        function nextRightExperiments(gse) {
            
            leftBut = document.getElementById("jumpLeftSample_" + gse);
            rightBut = document.getElementById("jumpRightSample_" + gse);
            
            start_sample = parseInt(leftBut.getAttribute("startSample"));
            end_sample = parseInt(leftBut.getAttribute("endSample"));
            
            new_start_sample = start_sample + vis_num_geo_samples;
            new_end_sample = end_sample + vis_num_geo_samples;
                        
            total_samples = parseInt(leftBut.getAttribute("totalSamples"));
            
            leftBut.disabled = false;
            rightBut.disabled = false;
            
            if(new_end_sample >= total_samples) {
                new_end_sample = total_samples;
                //new_start_sample = new_end_sample - (vis_num_geo_samples-1);
                rightBut.disabled = true;
            }

            leftBut.setAttribute("startSample", new_start_sample);
            leftBut.setAttribute("endSample", new_end_sample);
            
            corr_table = document.getElementById("sampleTable_" + gse);
            
            // Close current visible samples
            gsm_none = []
            for(var i = start_sample; i < end_sample+1; i++) {
                gsm_none.push("tr[sample_number='" + i + "']");
            }
            var selector_none = gsm_none.join(", ");
            samples_for_none = corr_table.querySelectorAll(selector_none);
            samples_for_none.forEach(function(tr) {
                tr.style.display = "none";
            });
            // Open new samples
            gsm_visible = []
            for(var i = new_start_sample; i < new_end_sample+1; i++) {
                gsm_visible.push("tr[sample_number='" + i + "']");
            }
            var selector_visible = gsm_visible.join(", ");
            samples_for_visible = corr_table.querySelectorAll(selector_visible);
            samples_for_visible.forEach(function(tr) {
                tr.style.display = "table-row";
            });
            
        }
    
    document.addEventListener('click', function(event) {
            var filter_panel = document.getElementById('filter-panel');
            var isClickInsideDiv = filter_panel.contains(event.target);
            if (!isClickInsideDiv && filter_panel.style.display !== "none") {
                filter_panel.style.display = 'none';
            }
        });
        
        document.addEventListener('keyup', function(event) {
            var filter_panel = document.getElementById('filter-panel');
            if (event.keyCode === 13 & filter_panel.style.display !== "none" ) {
                submitChosenFilter();
            }
        });
        
        document.addEventListener("DOMContentLoaded", function() {
            // Verstecke das Ladebildschirm-Div
            document.getElementById("loader").style.display = "none";
            // Zeige den eigentlichen Inhalt
            document.getElementById("content").style.display = "block";
        });
        
    
    </script>
        <title>DEEP-DV hub</title>
        <style>
    body {
                width: 100vw;
                background: #fff;
            }

            #MainTable {
                width: 100%;
                overflow: auto;
                border-collapse: collapse;
                border: 0;
                border-radius: 8px;
                }

            #MainTableHead th{
                padding: 20px;
                text-align: center;
                background-color: #1f7dac;
                max-width: 200px;
                min-width: 200px;
                max-height: 30px;
                color: #fff;
            }

            #MainTableHead th:first-child {
                border-radius: 8px 0 0 0;
            }

            #MainTableHead th:last-child {
                border-radius: 0 8px 0 0;
            }

            .MainTable_rows {
                border-bottom: 1px solid;
                border-color: rgb(104, 102, 102);
            }

            .sampleTable {
                width: 100%;
                overflow: hidden;
                border-collapse: collapse;
                border: 0;
                border-radius: 8px;
            }

            .SubTableHead th {
                padding: 20px;
                text-align: center;
                background-color: #b4ccd8;
                max-width: 200px;
                min-width: 200px;
                max-height: 30px;
                color: black;
            }

            .sampleTable tr{
                border-bottom: 1px solid;
                border-color: rgb(104, 102, 102);
            }
                
            .sampleTable td {
                padding: 20px;
                text-align: center;
                white-space: nowrap; 
                overflow: hidden; 
                text-overflow: ellipsis;
                max-width: 200px;
                min-width: 200px;
                max-height: 30px;
            }

            #MainTable td {
                padding: 20px;
                text-align: center;
                white-space: nowrap; 
                overflow: hidden; 
                text-overflow: ellipsis;
                max-width: 200px;
                min-width: 200px;
                max-height: 30px;
            }

            .top-heading {
                display: flex;
                align-items: center;
                margin-bottom: 30px;
                font-family: Tahoma, sans-serif;
                font-size: 36px;
                color: #fff;
                background-color: #1f7dac;
                height: 150px;
                width: 100%;
                border-bottom-left-radius: 15px; 
                border-bottom-right-radius: 15px;
                padding-left: 40px;

            }
    
            .button {
            bottom: 3px; 
            left: 2px; 
            width: 25px;
            background-color: #fff;
            border: 0;
            border-radius: 10px;
            cursor: pointer;
        }
        
        .show_sample_button {
            bottom: 3px; 
            left: 2px; 
            width: 25px;
            background-color: #fff;
            border: 0;
            border-radius: 10px;
            cursor: pointer;
        }

        .hidden_table_row {
            display: none;
        }
        
        #AnyTermFilterDiv {
            display: none;
        }

        #SampleFilterDiv {
            display: none;
        }
        
        #filter-panel {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 400px;
            height: 100%;
            background-color: #b4ccd8;
            padding: 20px;
            box-shadow: -5px 0 5px rgba(0, 0, 0, 0.1);
            overflow-y: auto;
            border-radius: 0 20px 20px 0;
        }

        #OpenFilterPanelButton {
            border-radius: 5px; 
            margin-bottom: 1%;
            margin-left: 3%;
            font-size: 20px;
            background-color: #1f7dac;
            color: #fff;
            border: 0;
            cursor: pointer;
            padding: 10px; 

        }
        
        #OpenFilterPanelButton:hover {
            background-color: gray; 
        }
        
        .input-for-filter {
            margin-bottom: 5px;
            width: 65%;
        }
        
        .input-sample-filter {
            margin-bottom: 5px;
            width: 65%;
        }

        #AnyTermFilter {
            margin-bottom: 5px;
            width: 65%;
        }
        
        .deleteCurrentInput {
            border-radius: 30%;
            background-color: #b4ccd8;
            border: none; 
            margin-left: 5px;
            margin-right: 5px;
            cursor: pointer;
            color: #B22222;
            font-size: 16px;

        }

        #SubmitFilterButton {
            margin-left: 75%;
            background-color: #1f7dac; 
            color: #fff; 
            padding: 10px 20px; 
            font-size: 16px;
            border: none; 
            border-radius: 5px; 
            cursor: pointer; 
            transition: background-color 0.3s ease; 
        }

        #buttonBar {
            overflow: hidden;
            background-color: #b4ccd8;
        }

        .openButtons {
        float: left;
        display: block;
        padding: 15px;
        text-align: center;
        cursor: pointer;
        transition: background-color 0.3s ease;
        background-color: #1f7dac;
        font-size: 16px;
        border: none;
        color: #fff; 
        }

        .openButtons:hover {
            background-color: gray; 
        }
        
        .openButtons.active {
        background-color: #4169E1;
        }

        #SubmitFilterButton:hover {
            background-color: gray;
        }
        
        #DownloadButton:hover {
            background-color: gray;
        }

        #openSeriesFilter {
            border-radius: 20px 0px 0px 20px;
        }

        #openAnyTermFilter {
            border-radius: 0 20px 20px 0;
        }

        #CloseFilterPanelButton {
            background-color: #b4ccd8;
            border: none;
            cursor: pointer;
            border-radius: 5px;
            font-size: 30px;
        }

        #CloseFilterPanelButton:hover {
            background-color: gray; 
        }

        #ResetFilterButton {
            background-color: #b4ccd8;
            border: none;
            cursor: pointer;
            border-radius: 5px;
            font-size: 20px;
            margin-left: 75%;
        }

        #ResetFilterButton:hover {
            background-color: gray;
        }

        .button:hover {
            background-color: gray;
        }
        
        .show_sample_button:hover {
            background-color: gray;
        }
        
        

        .input_dates {
            margin-bottom: 5px;
            width: 28%;
        }
        
        .input_sample_dates {
            margin-bottom: 5px;
            width: 28%;
        }
        
        .information_date_button {
            background-color: #b4ccd8;
            border: none;
            font-size: 20px;
        }
        
        #DownloadButton {
            border-radius: 5px; 
            margin-bottom: 1%;
            margin-left: 3%;
            font-size: 20px;
            background-color: #1f7dac;
            border: none;
            color: #fff;
            padding: 10px;
            cursor: pointer;
        }
        
        .virus_open_buttons {
            float: left;
            display: block;
            padding: 15px;
            text-align: center;
            cursor: pointer;
            transition: background-color 0.3s ease;
            background-color: #1f7dac;
            font-size: 14px;
            border: none;
            color: #fff; 
        }
        
        .virus_open_buttons:hover {
            background-color: gray;
        }
        
        .virus_open_buttons.active {
            background-color: #4169E1;
        }
        
        #virus_bar {
            overflow: hidden;
            background-color: #b4ccd8;
        }
        
        .virus_tds {
            padding: 5px;
        }
        
        .cautionSymbols {
            display: none;
        }
        
        .cautionSymbols.active {
            float: left;
            display: block;
            padding: 9px;
            text-align: center;
            background-color: #b4ccd8;
            font-size: 20px;
            border: none;
            color: red;
            
        }
        
        #numberSeries {
            display: none;
            border-radius: 5px;
            margin-bottom: 1%;
            font-size: 15px;
            background-color: #fff;
            border: 1px solid;
            padding: 10px;
            color: black;
        }
        
        .menuContentLinks {
            color: #fff;
            text-decoration: none;
            font-family: Tahoma, sans-serif;
            font-size: 20px;
            cursor: pointer;
        }

        #q_and_a_link {
            right: 5%;
            position: absolute;
        }

        #otherWebpage {
            right: 10%;
            position: absolute;
        }

        .menuContentLinks:hover {
            color: gray;
        }
        
        #public_sra_data {
                position: absolute;
                right: 10%;
            }

        #internal_data {
                position: absolute;
                right: 17%;
        }
        
        #left_jump {
            margin-left: 3%;
            font-size: 15px;
            background-color: #fff;
            color: black;
            border: none;
            cursor: pointer;
            border-radius: 5px;
        }

        #left_jump:hover{
            background-color: gray;
        }

        #right_jump {
            font-size: 15px;
            background-color: #fff;
            color: black;
            border: none;
            cursor: pointer;
            border-radius: 5px;
        }

        #right_jump:hover{
            background-color: gray;
        }

        #left_jump[disabled]:hover {
            background-color: #fff;
            cursor: default;
        }

        #left_jump[disabled] {
            color: lightgray;
        }

        #right_jump[disabled]:hover {
            background-color: #fff;
            cursor: default;
        }

        #right_jump[disabled] {
            color: lightgray;
        }
        
        .jumpSampleButtons {
            background-color: #b4ccd8;
            border: none;
            cursor: pointer;
            border-radius: 5px;
        }
        
        .jumpSampleButtons:hover{
            background-color: gray;
        }
        
        .jumpSampleButtons[disabled] {
            color: lightgray;
        }

        .jumpSampleButtons[disabled]:hover {
            background-color: #fff;
            cursor: default;
        }
        
        @-webkit-keyframes spin {
            0% { -webkit-transform: rotate(0deg); }
            100% { -webkit-transform: rotate(360deg); }
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        #loader {
        border: 16px solid #f3f3f3;
        border-radius: 50%;
        border-top: 16px solid #3498db;
        width: 120px;
        height: 120px;
        -webkit-animation: spin 2s linear infinite; /* Safari */
        animation: spin 2s linear infinite;
        margin-left: 50%;
        margin-top: 10%;
        }
        
        </style>
    </head>
    """
    beg_geo_web += f"""<body onload="displayNumberResults(1, {dis_num_geo}, {total_rows_geo}, false)">
        <div class="top-heading">
        Public GEO data
        <a href="question_answer.html" id="q_and_a_link" class="menuContentLinks" target="_blank">Q&A</a>
        <a href="sraData.html" id="public_sra_data" class="menuContentLinks" target="_blank">SRA data</a>
        """
        
    if(buildBoth):
        beg_geo_web += '<a href="internalData.html" id="internal_data" class="menuContentLinks" target="_blank">Internal data</a>'
        
    beg_geo_web += """
        </div>
        <button id="OpenFilterPanelButton" onclick="toggleFilterPanel()">Filter</button>
        <button id="DownloadButton" onclick="downloadTableData()"><b>&#11123;</b> Download</button>
    """
    if vis_num_geo == -1:
        beg_geo_web += f"""
            <button id="left_jump" onclick="nextLeftSamples()" start_number = "1" end_number= "{dis_num_geo}" total_number = "{total_rows_geo}" isFilter = "false" total_number_filter = "-1" disabled style="display: none;">&laquo; Previous</button>
            <button id="numberSeries" style="margin-left: 3%;">Label not relevant here</button>
            <button id="right_jump" onclick="nextRightSamples()" start_number = "1" end_number= "{dis_num_geo}" total_number = "{total_rows_geo}" isFilter = "false" total_number_filter = "-1" disabled style="display: none;">Next &raquo;</button>
            
        """
    else:
        beg_geo_web += f"""
            <button id="left_jump" onclick="nextLeftSamples()" start_number = "1" end_number= "{dis_num_geo}" total_number = "{total_rows_geo}" isFilter = "false" total_number_filter = "-1" disabled>&laquo; Previous</button>
            <button id="numberSeries">Label not relevant here</button>
            <button id="right_jump" onclick="nextRightSamples()" start_number = "1" end_number= "{dis_num_geo}" total_number = "{total_rows_geo}" isFilter = "false" total_number_filter = "-1">Next &raquo;</button>
            
        """
    
    beg_geo_web += """
        <div id="filter-panel">
            <button id="CloseFilterPanelButton" onclick="toggleFilterPanel()">&larrhk;</button>
            <button id="ResetFilterButton" onclick="resetFilter()">Reset</button>
            <h3>Filter options</h3>
            <div id="buttonBar">
            <button class="openButtons active" id="openSeriesFilter" onclick="openNewFilterDivs(\'Series\')">Series filter</button>
            <button class="openButtons" id="openSampleFilter" onclick="openNewFilterDivs(\'Sample\')">Sample filter</button>
            <button class="openButtons" id="openAnyTermFilter" onclick="openNewFilterDivs(\'AnyTerm\')">Any term</button>
            </div>
            <br>
            <div id="AnyTermFilterDiv" class="filterDivs"><p id=\"paraAnyTerm\">Filter all search terms: </p>
            <input type="text" id="AnyTermFilter" class="AnyTerm" placeholder="Search for any term"><button class="deleteCurrentInput" onclick="deleteInput('AnyTermFilter')">x</button></div>
        """
    
    beg_geo_web += '<div id="SeriesFilterDiv" class="filterDivs"><p id="paraSeries">Filter series data: </p>'
    for series_col in series_geo_df.columns:
        col_index = series_geo_df.columns.get_loc(series_col)
        if "_date" in str(series_col):
            beg_geo_web += f'<input type="date" title="Search for {series_col}" class="input_dates" id="specificFilter:{series_col}#1" onchange="fillSecondDate(\'{series_col}\')"><button class="deleteCurrentInput" onclick="deleteInput(\'specificFilter:{series_col}#1\')">x</button>'
            beg_geo_web += f'<input type="date" title="Search for {series_col}" class="input_dates" id="specificFilter:{series_col}#2"><button class="deleteCurrentInput" onclick="deleteInput(\'specificFilter:{series_col}#2\')">x</button>'
            beg_geo_web += f'<button title="Usage of date filters: Fill in only the first filter option to filter data from your choosen date until today. Fill in only the second filter option to filter data from the beginning until your choosen date. Fill in both filter options to filter data in the range of your choosen dates. For search of a specific date, fill in the same date in both options." class="information_date_button">&#9432;</button>'
        else:
            beg_geo_web += f'<input type="text" class="input-for-filter" id="specificFilter:{series_col}" placeholder="Search for {str(series_col)}"><button class="deleteCurrentInput" onclick="deleteInput(\'specificFilter:{series_col}\')">x</button><br>'

    beg_geo_web += '</div><div id="SampleFilterDiv" class="filterDivs"><p id="paraSamples">Filter sample data: </p>'
    for sample_col in samples_geo_df.columns:
        col_index = samples_geo_df.columns.get_loc(sample_col)
        if "_date" in str(sample_col):
            beg_geo_web += f'<input type="date" title="Search for {sample_col}" class="input_sample_dates" id="specificFilter:{sample_col}#1" onchange="fillSecondDate(\'{sample_col}\')"><button class="deleteCurrentInput" onclick="deleteInput(\'specificFilter:{sample_col}#1\')">x</button>'
            beg_geo_web += f'<input type="date" title="Search for {sample_col}" class="input_sample_dates" id="specificFilter:{sample_col}#2"><button class="deleteCurrentInput" onclick="deleteInput(\'specificFilter:{sample_col}#2\')">x</button>'
            beg_geo_web += f'<button title="Usage of date filters: Fill in only the first filter option to filter data from your choosen date until today. Fill in only the second filter option to filter data from the beginning until your choosen date. Fill in both filter options to filter data in the range of your choosen dates. For search of a specific date, fill in the same date in both options." class="information_date_button">&#9432;</button>'
        else:
            beg_geo_web += f'<input type="text" class="input-sample-filter" id="specificFilter:{sample_col}" placeholder="Search for {str(sample_col)}"><button class="deleteCurrentInput" onclick="deleteInput(\'specificFilter:{sample_col}\')">x</button><br>'

    beg_geo_web += '</div><div id="virusFilterDiv"><p id="paraVirus">Choose your virus(es): </p>'

    beg_geo_web += '<div id="virus_bar">'
    for cat in categories_viruses.keys():
        if cat == first_category:
            beg_geo_web += f'<button id="{cat}_open_button" class="virus_open_buttons active" style="border-radius: 20px 0px 0px 20px; " onclick="openNewVirusDiv(\'{cat}\')">{cat}</button>'
        elif cat == last_category:
            beg_geo_web += f'<button id="{cat}_open_button" class="virus_open_buttons" style="border-radius: 0px 20px 20px 0px; " onclick="openNewVirusDiv(\'{cat}\')">{cat}</button>'
        else:
            beg_geo_web += f'<button id="{cat}_open_button" class="virus_open_buttons" onclick="openNewVirusDiv(\'{cat}\')">{cat}</button>'
    beg_geo_web += '<button id="cautionSymbol" class="cautionSymbols" title="Caution! You have checked checkboxes from other virus genus. If you don\'t want to filter for them, uncheck these checkboxes.">&#9888;</button></div>'
    for cat in categories_viruses.keys():
        cb_counter = 0
        if cat == first_category:
            beg_geo_web += f'<div id="{cat}_div" class="viruses_divs" style="display: block;">'
        else:
            beg_geo_web += f'<div id="{cat}_div" class="viruses_divs" style="display: none;">'
        beg_geo_web += f'<table>'
        for v in categories_viruses[cat]:
            if cb_counter%3 == 0:
                beg_geo_web += "<tr>"
            beg_geo_web += f'<td class="virus_tds"><input type="checkbox" class="virus_checkboxes" id="{v}_cb" name="{v}_cb"><label class="virus_labels" for="{v}_cb">{v}</label></td>'
            if cb_counter%3 == 2:
                beg_geo_web += "</tr>"
            cb_counter += 1
        if cb_counter%3 != 2:
            beg_geo_web += f'</tr></table></div>'
        else:
            beg_geo_web += f'</table></div>'
    beg_geo_web += "<br>"

    geo_tab = '</div><button id="SubmitFilterButton" onclick="submitChosenFilter()">Filter</button><br><br><br></div><div id="loader"></div><div id="content" style="display: none;"><table id="MainTable"><thead id="MainTableHead"><tr>'

    # Add header for geo meta data
    for col in series_geo_df.columns:
        geo_tab += f"<th>{col}</th>"

    geo_tab += "</tr></thead>"
    # Add meta data
    progress_bar_geo = tqdm(total=total_rows_geo, desc="Processing", unit="iteration")

    visible_counter_geo = 1
    for index, row in series_geo_df.iterrows():
        
        progress_bar_geo.update(1)
        
        gse = str(series_geo_df.loc[index, "Series_geo_accession"])
        if visible_counter_geo < dis_num_geo+1:
            geo_tab += f'<tr id="{gse}_MainTable" class="MainTable_rows" style="display: table-row;" overall_number = "{visible_counter_geo}" filter_number = "-1">'
        else:
            geo_tab += f'<tr id="{gse}_MainTable" class="MainTable_rows" style="display: none;" overall_number = "{visible_counter_geo}" filter_number = "-1">'
        visible_counter_geo += 1
        for col in series_geo_df.columns:
            #value = str(series_geo_df.at[index, col])
            val = series_geo_df.at[index, col]
            if pandas.isna(val):
                value = 'NA'
            else:
                value = str(val)
            
            if len(value) < 25:
                if col == "Series_geo_accession":
                    geo_tab += f'<td title="{col}"><button class="show_sample_button" id="{gse}_showSamplesButton" onclick="showSamples({gse}_showSamplesButton, \'{gse}_tr\')">&#11208;</button><a href="https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={value}" target="_blank"> {value}</a></td>'               
                else:
                    geo_tab += f'<td title="{col}">{value}</td>'
            elif len(value.split(" ")) == 1:
                value_1 = value[0:(len(value))//2]
                value_2 = value[((len(value))//2):] 
                
                if col == "NCBI_generated_data":
                    geo_tab += f'<td title="{col}"><button class="button" id="{col}_{index}_showTextButton" onclick="showFullText({col}_{index}_showTextButton)">+</button><a href={value} target="_blank"> {value_1} {value_2}</a></td>'
                elif col == "ARCHS4":
                    geo_tab += f'<td title="{col}"><button class="button" id="{col}_{index}_showTextButton" onclick="showFullText({col}_{index}_showTextButton)">+</button><a href={value} target="_blank"> {value_1} {value_2}</a></td>'                    
                else:                      
                    geo_tab += f'<td title="{col}"><button class="button" id="{col}_{index}_showTextButton" onclick="showFullText({col}_{index}_showTextButton)">+</button> {value_1} {value_2}</td>'
            else:
                if col == "Series_relation":
                    
                    link_elements = value.split(";")
                    bio_pattern = r'https://www.ncbi.nlm.nih.gov/bioproject/\S+'
                    sra_pattern = r'https://www.ncbi.nlm.nih.gov/sra\?term=\S+'
                    
                    bio_match = False
                    sra_match = False
                    
                    for link_el in link_elements:
                        link_el = link_el.strip()
                        
                        if link_el.startswith("Bio"):
                            bio_match = re.search(bio_pattern, link_el)
                            bio_link = bio_match.group(0)
                        elif link_el.startswith("SRA"):
                            sra_match = re.search(sra_pattern, link_el)
                            sra_link = sra_match.group(0)
                            
                    if bio_match and sra_match:
                        geo_tab += f'<td title="{col}"><button class="button" id="{col}_{index}_showTextButton" onclick="showFullText({col}_{index}_showTextButton)">+</button><a href="{bio_link}" target="_blank"> Bioproject: {bio_link}</a><a href={sra_link} target="_blank"> SRA: {sra_link}</a></td>'
                    elif bio_match:
                        geo_tab += f'<td title="{col}"><button class="button" id="{col}_{index}_showTextButton" onclick="showFullText({col}_{index}_showTextButton)">+</button><a href="{bio_link}" target="_blank"> Bioproject: {bio_link}</a></td>'
                    elif sra_match:
                        geo_tab += f'<td title="{col}"><button class="button" id="{col}_{index}_showTextButton" onclick="showFullText({col}_{index}_showTextButton)">+</button><a href={sra_link} target="_blank"> SRA: {sra_link}</a></td>'
                    else:
                        geo_tab += f'<td title="{col}"><button class="button" id="{col}_{index}_showTextButton" onclick="showFullText({col}_{index}_showTextButton)">+</button> {value}</td>'               
                else:
                    geo_tab += f'<td title="{col}"><button class="button" id="{col}_{index}_showTextButton" onclick="showFullText({col}_{index}_showTextButton)">+</button> {value}</td>'
        geo_tab += "</tr>"
        
        geo_tab += f'<tr id="{gse}_tr" class="hidden_table_row"><td colspan="100%" style="overflow: auto;"><table class="sampleTable" id="sampleTable_{gse}">'
        
        geo_tab += '<thead class="SubTableHead"><tr>'
        
        temp_df = samples_geo_df[samples_geo_df["Sample_series_id"].str.contains(fr'\b{re.escape(gse)}(?:;|$)', regex=True, case=False, na=False)]

        sample_characteristics_column = temp_df['Sample_characteristics_ch1']
        sample_characteristics = []
        for entry in sample_characteristics_column:
            characteristics = str(entry).split(";")

            for char in characteristics:
                char.strip()
                if char != "" and char != "Na" and char != "NA" and char != "nan" and char != "NaN":
                    char_splitted = char.split(":")
                    if len(char_splitted) == 1:
                        sample_characteristics.append("Further_information")
                    else:                 
                        sample_characteristics.append(char.split(":")[0].strip())

        sample_characteristics = list(set(sample_characteristics))
        sample_characteristics = [s.replace(" ", "_").replace("(", "_").replace(")", "_") for s in sample_characteristics]        
        for col_sm in samples_geo_df.columns:
            if col_sm != "Sample_characteristics_ch1" and col_sm != "Sample_geo_accession":
                geo_tab += f"<th>{col_sm}</th>"
            elif col_sm == "Sample_geo_accession":
                if temp_df.shape[0] <= vis_num_geo_samples or vis_num_geo_samples == -1:
                    geo_tab += f'<th><button id="jumpLeftSample_{gse}" class="jumpSampleButtons" disabled style="display: none;"  startSample = "1" endSample = "{vis_num_geo_samples}" totalSamples = "{temp_df.shape[0]}">&#11207;</button>{col_sm}<button id="jumpRightSample_{gse}" disabled style="display: none;">&#11208;</button></th>'
                else:
                    geo_tab += f'<th><button id="jumpLeftSample_{gse}" class="jumpSampleButtons" onclick="nextLeftExperiments(\'{gse}\')" startSample = "1" endSample = "{vis_num_geo_samples}" totalSamples = "{temp_df.shape[0]}" disabled>&#11207; </button>{col_sm}<button id="jumpRightSample_{gse}" class="jumpSampleButtons" onclick="nextRightExperiments(\'{gse}\')">&#11208;</button></th>'
            else:
                for smpl_chr in sample_characteristics:
                    geo_tab += f'<th class="characteristicHead">{smpl_chr}</th>'
    
        geo_tab += "</tr></thead>" 
        sample_counter = 1
        tmp_vis_num = vis_num_geo_samples
        if vis_num_geo_samples == -1:
            tmp_vis_num = temp_df.shape[0]
        for index_sample, row_sample in temp_df.iterrows():
            if sample_counter < tmp_vis_num+1:
                geo_tab += f'<tr sample_number="{sample_counter}" style="display: table-row;">'
            else:
                geo_tab += f'<tr sample_number="{sample_counter}" style="display: none;">'
            sample_counter += 1
            gsm = "" 
            for col_sample in temp_df.columns:
                #value_sample = str(temp_df.at[index_sample, col_sample]) 
                val_sample = temp_df.at[index_sample, col_sample]
                
                if pandas.isna(val_sample):
                    value_sample = 'NA'
                else:
                    value_sample = str(val_sample)
                
                if col_sample == "Sample_characteristics_ch1":
                    characteristic_pairs = value_sample.split(";")
                    characteristic_names_values = {}
                    if "Further_information" in sample_characteristics:
                        characteristic_names_values["Further_information"] = ""
                    for char_pair in characteristic_pairs:
                        char_pair.strip()
                        if char_pair != "" and char_pair != "Na" and char_pair != "NA" and char_pair != "nan" and char_pair != "NaN":
                            
                            char_splitted = char_pair.split(":")
                            if len(char_splitted) == 1:
                                char_name = "Further_information"
                                char_value = char_splitted[0].strip()
                                characteristic_names_values["Further_information"] += f"{char_value};"
                            else:                 
                                char_name = char_splitted[0].strip().replace(" ", "_").replace("(", "_").replace(")", "_")
                                char_value = char_splitted[1].strip()                            
                                characteristic_names_values[char_name] = char_value
                    for sample_char in sample_characteristics:
                        split_strings = []
                        if sample_char in characteristic_names_values.keys():
                            if len(characteristic_names_values[sample_char].strip()) < 30:
                                if len(characteristic_names_values[sample_char].strip()) == 0:
                                    geo_tab += f'<td title="{sample_char}" class="characteristicData">Na</td>'
                                else:
                                    geo_tab += f'<td title="{sample_char}" class="characteristicData">{characteristic_names_values[sample_char]}</td>'
                                
                            elif len(characteristic_names_values[sample_char][0:25].split(" ")) == 1:
                                for i in range(0, len(characteristic_names_values[sample_char]), 20):
                                    if i == 0:
                                        split_strings.append(characteristic_names_values[sample_char][i:i+21])
                                    else:
                                        split_strings.append(characteristic_names_values[sample_char][i+1:i+21])
                                geo_tab += f'<td title="{sample_char}" class="characteristicData"><button class="button" id="{sample_char}_{index_sample}_sample_showTextButton" onclick="showFullText({sample_char}_{index_sample}_sample_showTextButton)">+</button> {" ".join(split_strings)}</td>'
                            else:
                                geo_tab += f'<td title="{sample_char}" class="characteristicData"><button class="button" id="{sample_char}_{index_sample}_sample_showTextButton" onclick="showFullText({sample_char}_{index_sample}_sample_showTextButton)">+</button> {characteristic_names_values[sample_char]}</td>'

                        else:
                            geo_tab += f'<td title="{sample_char}" class="characteristicData">NA</td>' 
                    continue                

                if len(value_sample) < 25:

                    if col_sample == "Sample_geo_accession":
                        geo_tab += f'<td title="{col_sample}"><a href="https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={value_sample}" target="_blank">{value_sample}</a></td>'
                        gsm = value_sample
                    else:
                        geo_tab += f'<td title="{col_sample}">{value_sample}</td>'
                        
                elif len(value_sample.split(" ")) == 1:
                    value_sample_1 = value_sample[0:(len(value_sample))//2]
                    value_sample_2 = value_sample[((len(value_sample))//2):]    
                    geo_tab += f'<td title="{col_sample}"><button class="button" id="{col_sample}_{index_sample}_showTextButton" onclick="showFullText({col_sample}_{index_sample}_showTextButton)">+</button> {value_sample_1} {value_sample_2}</td>'
                      
                else: 
                    if col_sample == "Sample_relation":
                        link_elements = value_sample.split(";")
                        bio_pattern = r'https://www.ncbi.nlm.nih.gov/biosample/\S+'
                        sra_pattern = r'https://www.ncbi.nlm.nih.gov/sra\?term=\S+'
                        
                        bio_match = False
                        sra_match = False
                        
                        for link_el in link_elements:
                            link_el = link_el.strip()
                            
                            if link_el.startswith("Bio"):
                                bio_match = re.search(bio_pattern, link_el)
                                bio_link = bio_match.group(0)
                            elif link_el.startswith("SRA"):
                                sra_match = re.search(sra_pattern, link_el)
                                sra_link = sra_match.group(0)
                        
                        if bio_match and sra_match:
                            geo_tab += f'<td title="{col_sample}"><button class="button" id="{col_sample}_{index_sample}_showTextButton" onclick="showFullText({col_sample}_{index_sample}_showTextButton)">+</button><a href="{bio_link}" target="_blank"> Biosample: {bio_link}</a><a href={sra_link} target="_blank"> SRA: {sra_link}</a></td>'
                        elif bio_match:
                            geo_tab += f'<td title="{col_sample}"><button class="button" id="{col_sample}_{index_sample}_showTextButton" onclick="showFullText({col_sample}_{index_sample}_showTextButton)">+</button><a href="{bio_link}" target="_blank"> Biosample: {bio_link}</a></td>'
                        elif sra_match:
                            geo_tab += f'<td title="{col_sample}"><button class="button" id="{col_sample}_{index_sample}_showTextButton" onclick="showFullText({col_sample}_{index_sample}_showTextButton)">+</button><a href={sra_link} target="_blank"> SRA: {sra_link}</a></td>'
                        else:
                            geo_tab += f'<td title="{col_sample}"><button class="button" id="{col_sample}_{index_sample}_showTextButton" onclick="showFullText({col_sample}_{index_sample}_showTextButton)">+</button> {value_sample}</td>'               
                    else:
                        geo_tab += f'<td title="{col_sample}"><button class="button" id="{col_sample}_{index_sample}_showTextButton" onclick="showFullText({col_sample}_{index_sample}_showTextButton)">+</button> {value_sample}</td>'
                        
                    #geo_tab += f'<td title="{col_sample}"><button class="button" id="{col_sample}_{index_sample}" onclick="showFullText({col_sample}_{index_sample})">+</button> {value_sample}</td>'
            geo_tab += "</tr>"
        geo_tab += "</table></td></tr>"
    geo_tab += "</table></div>"

    geo_tab += """
    </body>
    </html>
    """
    progress_bar_geo.close()  
    with open(f"{args.output_dir}/geoData.html", "w") as file:
        file.write(beg_geo_web + geo_tab)
    file.close()
    
    print("Finished build of geoData.hmtl.")
    
##################################### Public SRA data webpage #####################################
#if(False):
if(buildPublicPages):
    sra_page = """

        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="UTF-8">
        <script>
    """
    sra_study_df_size = sra_study_df.shape[0]
    if vis_num_sra == -1:
        dis_num_sra = sra_study_df_size
    else:
        dis_num_sra = vis_num_sra
    
    sra_page += f"var dis_num_sra = {dis_num_sra};\nvar vis_num_sra_runs = {vis_num_sra_runs};"
        
    sra_page += """    
           function showRuns(button, srr_row) {
            var tdElement = button.parentNode;
            var buttonElement = tdElement.querySelector("button");
            var srr_hidden_tbl_row = document.getElementById(srr_row);

            if (buttonElement.textContent === "⯈") {
                buttonElement.textContent = "⯅";
                srr_hidden_tbl_row.style.display = "table-row";
                srr_hidden_tbl_row.style.height = "auto";
            } else {
                buttonElement.textContent = "⯈";
                srr_hidden_tbl_row.style.display = "none";
            }
            getCurrentDate();
        }

        function showFullText(button) {
        var tdElement = button.parentNode; 
        var buttonElement = tdElement.querySelector("button");
        

        if (tdElement.style.whiteSpace === "normal") {
            tdElement.style.whiteSpace = "nowrap";
            buttonElement.innerHTML = "+";
        } else {
            tdElement.style.whiteSpace = "normal";
            buttonElement.innerHTML = "-";
        }
        }

        function toggleFilterPanel() {
                
            var filterPanel = document.getElementById('filter-panel');
            var filterButton = document.getElementById('OpenFilterPanelButton');
            if (filterPanel.style.display === 'none' || filterPanel.style.display === '') {
            filterPanel.style.display = 'block';
            } else {
            filterPanel.style.display = 'none';
            }
            event.stopPropagation();
        }

        
        function getIndexOfHeadColumn(head, head_column) {

            for (var i = 0; i < head.rows[0].cells.length; i++) {
                var cellText = head.rows[0].cells[i].innerText;
                
                if (cellText === head_column) {
                    return i;
                }
            }

        }

        function getCurrentDate() {
            var currentDate = new Date();
            var options = { month: 'short', day: 'numeric', year: 'numeric' };
            var formattedDate = currentDate.toLocaleDateString('en-US', options);
            formattedDate = formattedDate.replace(",", "")

            return formattedDate;
        }

        function getProcessedDate(date_input) {
            date_to_number = {
                "Jan" : 1,
                "Feb" : 2,
                "Mar" : 3,
                "Apr" : 4,
                "May" : 5,
                "Jun" : 6,
                "Jul" : 7,
                "Aug" : 8,
                "Sep" : 9,
                "Oct" : 10,
                "Nov" : 11,
                "Dec" : 12
            }

            return date_to_number[date_input];
        }

        function dateCheckLeft (date_filter, date_td) {


            // yyyy-mm-dd
            dateFilterValues = date_filter.toString().split("-");
            //mmm dd yyyy
            dataTdValues = date_td.split(" ");


            if (parseInt(dateFilterValues[0], 10) < parseInt(dataTdValues[2], 10)) {
                return true;
            }
            else if(parseInt(dateFilterValues[0], 10) === parseInt(dataTdValues[2], 10)) {
                if (parseInt(dateFilterValues[1], 10) < getProcessedDate(dataTdValues[0])) {
                    return true;
                }
                else if (parseInt(dateFilterValues[1], 10) === getProcessedDate(dataTdValues[0])) {
                    if (parseInt(dateFilterValues[2], 10) <= parseInt(dataTdValues[1], 10)) {
                        return true;
                    }
                }
            }
            return false;
        }

        function dateCheckRight (date_filter, date_td) {

            // yyyy-mm-dd
            dateFilterValues = date_filter.toString().split("-");
            //mmm dd yyyy
            dataTdValues = date_td.split(" ");


            if (parseInt(dateFilterValues[0], 10) > parseInt(dataTdValues[2], 10)) {
                return true;
            }
            else if(parseInt(dateFilterValues[0], 10) === parseInt(dataTdValues[2], 10)) {
                if (parseInt(dateFilterValues[1], 10) > getProcessedDate(dataTdValues[0])) {
                    return true;
                }
                else if (parseInt(dateFilterValues[1], 10) === getProcessedDate(dataTdValues[0])) {
                    if (parseInt(dateFilterValues[2], 10) >= parseInt(dataTdValues[1], 10)) {
                        return true;
                    }
                }
            }
            return false;
            
        }

        function dateCheckRange (date_filter_left, date_filter_right, date_td) {


            // yyyy-mm-dd
            dateFilterValues_left = date_filter_left.toString().split("-");
            dateFilterValues_right = date_filter_right.toString().split("-");
            //mmm dd yyyy
            dataTdValues = date_td.split(" ");

            // Check if date_td > date_filter_left
            if (parseInt(dateFilterValues_left[0], 10) > parseInt(dataTdValues[2], 10)) {
                return false;
            }
            else if(parseInt(dateFilterValues_left[0], 10) === parseInt(dataTdValues[2], 10)) {
                if (parseInt(dateFilterValues_left[1], 10) > getProcessedDate(dataTdValues[0])) {
                    return false;
                }
                else if (parseInt(dateFilterValues_left[1], 10) === getProcessedDate(dataTdValues[0])) {
                    if (parseInt(dateFilterValues_left[2], 10) > parseInt(dataTdValues[1], 10)) {
                        return false;
                    }
                }
            }

            // Check if date_td < date_filter_right
            if (parseInt(dateFilterValues_right[0], 10) < parseInt(dataTdValues[2], 10)) {
                return false;
            }
            else if(parseInt(dateFilterValues_right[0], 10) === parseInt(dataTdValues[2], 10)) {
                if (parseInt(dateFilterValues_right[1], 10) < getProcessedDate(dataTdValues[0])) {
                    return false;
                }
                else if (parseInt(dateFilterValues_right[1], 10) === getProcessedDate(dataTdValues[0])) {
                    if (parseInt(dateFilterValues_right[2], 10) < parseInt(dataTdValues[1], 10)) {
                        return false;
                    }
                }
            }

            return true;
        }

        function check_reg_for_td(txtValue, reg_array) {

            next_and = false;
            next_or = false;
            next_not = false;
            first_entry = true;
            skip_next = false;

            overall_statisfied = true;

            for (var i = 0; i < reg_array.length; i++) {
                reg_array[i] = reg_array[i].trim();
                if (first_entry) {
                    if (reg_array[i].startsWith("NOT")) {
                        if (txtValue.toUpperCase().indexOf(reg_array[i].slice(4).toUpperCase()) != -1) {
                            overall_statisfied = false;
                        }
                    }
                    else if (txtValue.toUpperCase().indexOf(reg_array[i].toUpperCase()) === -1) {
                        overall_statisfied = false;
                    }
                    first_entry = false;
                }
                else if (skip_next) {
                    skip_next = false;
                    continue;
                }
                else if (reg_array[i] === 'AND') {
                    if (!overall_statisfied) {
                        skip_next = true;
                        continue;
                    }
                    next_and = true;
                }
                else if (reg_array[i] === 'OR'){
                    if (overall_statisfied) {
                        skip_next = true;
                        continue;
                    }
                    next_or = true;
                }
                else {
                    if (next_and) {
                        if (reg_array[i].startsWith("NOT")) {
                            if (txtValue.toUpperCase().indexOf(reg_array[i].slice(4).toUpperCase()) != -1) {
                                overall_statisfied = false;
                            }
                        }
                        else if (txtValue.toUpperCase().indexOf(reg_array[i].toUpperCase()) === -1) {
                            overall_statisfied = false;
                        }
                        next_and = false;
                    }
                    else if (next_or) {
                        if (reg_array[i].startsWith("NOT")) {
                            if (txtValue.toUpperCase().indexOf(reg_array[i].slice(4).toUpperCase()) === -1) {
                                overall_statisfied = true;
                            }
                        } 
                        else if (txtValue.toUpperCase().indexOf(reg_array[i].toUpperCase()) != -1) {
                            overall_statisfied = true;
                        }
                        next_or = false;
                    }
                }
            }
            return overall_statisfied;
        }

        function closeAllChars() {
            hiddenTableRows = document.getElementsByClassName("hidden_table_row");
            // Close all samples
            for(var i = 0; i < hiddenTableRows.length; i++) {
                hiddenTableRows[i].style.display = "none";
            }

            // Switch all sample buttons to standard

            showSamplesButtons = document.getElementsByClassName("show_char_button");

            for(var i = 0; i < showSamplesButtons.length; i++) {

                showSamplesButtons[i].textContent = "⯈";
            }
        }

        /////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        
        function submitChosenFilter() {

            closeAllChars();

            var isAnyTerm = true;
            var isStudy = true;
            var isRun = true;

            var study_inputs = document.getElementsByClassName("input_study");
            var run_inputs = document.getElementsByClassName("input_run");
            var anyTermElement = document.getElementById("AnyTermFilter");
            var date_input = document.getElementsByClassName("input_dates");

            var mainTableRows = document.getElementsByClassName("MainTable_rows");
            var mainTable = document.getElementById("MainTable");
            var subTables = document.getElementsByClassName("runTable");

            var mainTableHead = document.getElementById("MainTableHead");
            var mainThElements = mainTableHead.querySelectorAll('th');
            var subTableHeads = document.getElementsByClassName("SubTableHead");
            var subTableHead = subTableHeads[0];
            var subThElements = subTableHead.querySelectorAll('th');


            var checkboxes_virus = document.getElementsByClassName("virus_checkboxes");

            var virus_column_index = getIndexOfHeadColumn(mainTableHead, "Virus");
            var srp_column_index = getIndexOfHeadColumn(mainTableHead, "study_accession")

            div_study_filter = document.getElementById("StudyFilterDiv");
            div_run_filter = document.getElementById("RunFilterDiv");
            div_anyTerm = document.getElementById("AnyTermFilterDiv");

            const pattern = /\\b(AND|OR)\\b/g;

            if (div_study_filter.style.display === "none") {
                isStudy = false;
            }
            if (div_run_filter.style.display === "none") {
                isRun = false;
            }
            if (div_anyTerm.style.display === "none") {
                isAnyTerm = false;
            }
            
            var filtered_trs = document.querySelectorAll('tr[filter_number]:not([filter_number="-1"])');

            for (var i = 0; i < filtered_trs.length; i++) {
                filtered_trs[i].style.display = "none";
                filtered_trs[i].setAttribute("filter_number", "-1");
            }

            // Study term
            if (isStudy) {
                var reg_dic = {}

                var firstDate = true;

                for (var i = 0; i < study_inputs.length; i++) {

                    input_id = study_inputs[i].id.split(":")[1];
                    var reg_splitted = study_inputs[i].value.split(pattern);
                    reg_dic[input_id] = reg_splitted.filter(item => item.trim() !== '');
                }

                var matching_counter = 1;

                for (i = 0; i < mainTableRows.length; i++) {
                    var rowShouldBeDisplayed = true; 
                    var rowContainsVirus = false;
                    var anyIsChecked = false;

                    tds = mainTableRows[i].getElementsByTagName("td");

                    if(tds[virus_column_index]) {
                    
                        // Control if correct viruses are checked
                        for (var j = 0; j < checkboxes_virus.length; j++) {
                            checkbox_name = ""
                            if (checkboxes_virus[j].checked) {
                                checkbox_name = checkboxes_virus[j].name.slice(0, -3);
                                anyIsChecked = true;
                            }
                            else{
                                continue;
                            }
                            if (tds[virus_column_index].textContent.indexOf(checkbox_name) > -1) {
                                rowContainsVirus = true;
                                break;
                            }
                        }
                        if (!rowContainsVirus && anyIsChecked) {
                            mainTableRows[i].style.display = "none";
                            continue;
                        }
                    }
                    
                    for (j = 0; j < tds.length; j++) {
                        td = tds[j];

                        if (td) {
                            txtValue = td.textContent || td.innerText;
                            if (mainThElements[j]) {
                                current_column = mainThElements[j].textContent;

                                if (current_column in reg_dic && reg_dic[current_column].length > 0 && !check_reg_for_td(txtValue, reg_dic[current_column])) {
                                    rowShouldBeDisplayed = false;
                                    break;
                                }
                            }
                        }
                    }
                    if (rowShouldBeDisplayed) {
                        mainTableRows[i].setAttribute("filter_number", matching_counter);
                        if (matching_counter < dis_num_sra+1) {
                            mainTableRows[i].style.display = "table-row";
                        }
                        else {
                            mainTableRows[i].style.display = "none";
                        }
                        matching_counter = matching_counter + 1;
                    } 
                    else {
                        mainTableRows[i].style.display = "none";
                    }
                }
            }     
            // Run term
            else if(isRun) {
                var reg_dic = {}

                for (var i = 0; i < run_inputs.length; i++) {

                    input_id = run_inputs[i].id.split(":")[1];
                    var reg_splitted = run_inputs[i].value.split(pattern);
                    reg_dic[input_id] = reg_splitted.filter(item => item.trim() !== '');

                }

                if(reg_dic["SRA_characteristics"].length > 1) {
                    alert("Conditional filtering isn't possible for SRA characteristics.");
                    return;
                }
                
                matching_counter = 1;
                
                for (var k = 0; k < subTables.length; k++) {
            
                    tbody_subTable = subTables[k].getElementsByTagName("tbody")[0];

                    tr = tbody_subTable.getElementsByTagName("tr");

                    var currentSubTableHead = subTables[k].querySelector("thead");
                    var currentSubThElements = currentSubTableHead.getElementsByTagName("th");

                    for (i = 0; i < tr.length; i++) {
                        var rowShouldBeDisplayed = true; 
                        var rowDueToCharacteristic = false
                        var rowContainsVirus = false;

                        tds = tr[i].getElementsByTagName("td");

                        for (j = 0; j < tds.length; j++) {
                            td = tds[j];
                            if (td) {

                                txtValue = td.textContent || td.innerText;
                                
                                if (currentSubThElements[j]){
                                    
                                    current_column = currentSubThElements[j].textContent;
                                    if (current_column.includes("⯈") || current_column.includes("⯇")) {
                                        current_column = current_column.replace(/⯈/g, ""); 
                                        current_column = current_column.replace(/⯇/g, ""); 
                                        current_column = current_column.trim();
                                    }

                                if (current_column in reg_dic && reg_dic[current_column].length > 0 && !check_reg_for_td(txtValue, reg_dic[current_column])){
                                    rowShouldBeDisplayed = false;              
                                    break;
                                }
                                else if(!(current_column in reg_dic) && reg_dic["SRA_characteristics"].length > 0) {

                                    filterInput = reg_dic["SRA_characteristics"][0].toUpperCase().trim();

                                    if(txtValue.toUpperCase().indexOf(filterInput) === -1 && !rowDueToCharacteristic) {
                                        rowDueToCharacteristic = false;
                                    }
                                    else {
                                        rowDueToCharacteristic = true;
                                    }
                                }
                                }
                            }
                        }

                        if(!rowDueToCharacteristic && reg_dic["SRA_characteristics"].length > 0) {
                            rowShouldBeDisplayed = false;
                        }
                        // Virus verification
                        if (rowShouldBeDisplayed){

                            var anyIsChecked = false;
                            corresponding_srp = tr[i].closest("table").id.split("_")[1];
                            upper_srp_row = document.getElementById(corresponding_srp + "_MainTable");
                            upper_tr = document.getElementById(corresponding_srp + "_tr");
                            
                            for (var j = 0; j < checkboxes_virus.length; j++) {
                                checkbox_name = ""
                                if (checkboxes_virus[j].checked) {
                                    checkbox_name = checkboxes_virus[j].name.slice(0, -3);
                                    anyIsChecked = true;
                                }
                                else{
                                    continue;
                                }
                                if (upper_srp_row.getElementsByTagName("td")[virus_column_index].textContent.indexOf(checkbox_name) > -1) {
                                    rowContainsVirus = true;
                                    break;
                                }
                            }
                            if (!rowContainsVirus && anyIsChecked) {
                                upper_tr.style.display = "none";
                                upper_srp_row.style.display = "none";
                                continue;
                            }
                        }

                        if (rowShouldBeDisplayed) {
                            corresponding_srp = tr[i].closest("table").id.split("_")[1];
                            upper_tr = document.getElementById(corresponding_srp + "_tr");
                            upper_srp_row = document.getElementById(corresponding_srp + "_MainTable");
                            upper_srp_row.setAttribute("filter_number", matching_counter);
                            if (matching_counter < dis_num_sra+1) {
                                upper_srp_row.style.display = "table-row";
                                upper_tr.style.display = "table-row";
                                show_button = document.getElementById(corresponding_srp + "_showRunButton");
                                show_button.textContent = "⯅";
                            }
                            else {
                                upper_srp_row.style.display = "none";
                                upper_tr.style.display = "none";
                            }
                            matching_counter = matching_counter + 1;
                            break;
                            
                        } else {
                            corresponding_srp = tr[i].closest("table").id.split("_")[1];
                            upper_tr = document.getElementById(corresponding_srp + "_tr");
                            upper_tr.style.display = "none";
                            upper_srp_row = document.getElementById(corresponding_srp + "_MainTable");
                            upper_srp_row.style.display = "none";
                        }
                    }
                    }
            }       
            // Any term
            else if (isAnyTerm) {
                filter = anyTermElement.value;

                reg_dic = {}
                var reg_splitted = filter.split(pattern);
                reg_splitted = reg_splitted.filter(item => item.trim() !== '');

                if (reg_splitted.length > 1) {
                    alert("You can't use conditional filtering for this filter option!");
                    return;
                }

                var matching_counter = 1;

                for (i = 0; i < mainTableRows.length; i++) {
                    var rowShouldBeDisplayed = false; 
                    var rowContainsVirus = false;
                    var anyIsChecked = false;

                    tds = mainTableRows[i].getElementsByTagName("td");

                    srp = tds[srp_column_index].textContent.slice(2);
                    var runRow = document.getElementById(srp + "_tr");
                    if(runRow === null) {
                                mainTableRows[i].style.display = "none";
                                continue;
                    }

                    if (tds[0]) {
                    
                        for (var j = 0; j < checkboxes_virus.length; j++) {
                            checkbox_name = ""
                            if (checkboxes_virus[j].checked) {
                                checkbox_name = checkboxes_virus[j].name.slice(0, -3);
                                anyIsChecked = true;
                            }
                            else{
                                continue;
                            }
                            if (tds[virus_column_index].textContent.indexOf(checkbox_name) > -1) {
                                rowContainsVirus = true;
                                break;
                            }
                        }
                        if (!rowContainsVirus && anyIsChecked) {
                            mainTableRows[i].style.display = "none";
                            continue;
                        }

                        if (check_reg_for_tr(tds, reg_splitted) | reg_splitted.length === 0) {
                            rowShouldBeDisplayed = true;
                        }
                        else {
                            
                            runTable = document.getElementById("runTable_" + srp);
                            trs_run = runTable.getElementsByTagName("tr");
                            
                            for (var k = 0; k < trs_run.length; k++) {
                                tds_run = trs_run[k].getElementsByTagName("td");
                                if (check_reg_for_tr(tds_run, reg_splitted)) {
                                    rowShouldBeDisplayed = true;
                                    break;
                                }
                            }
                            
                        }

                        if (rowShouldBeDisplayed) {
                            mainTableRows[i].setAttribute("filter_number", matching_counter);
                            if (matching_counter < dis_num_sra+1) {
                                mainTableRows[i].style.display = "table-row";
                            }
                            else {
                                mainTableRows[i].style.display = "none";
                            }
                            matching_counter = matching_counter + 1;
                        }
                        else {
                            mainTableRows[i].style.display = "none";
                        }

                    }
                }
            }
            
            var filterPanel = document.getElementById('filter-panel');
            filterPanel.style.display = 'none';
            
            var tableHeadMainRow = mainTableHead.getElementsByTagName("tr")[0];
            tableHeadMainRow.style.display = "table-row";

            for(var i = 0; i < subTableHeads.length; i++) {
                var subTableHeadRow = subTableHeads[i].getElementsByTagName("tr")[0];
                subTableHeadRow.style.display = "table-row";
            }

            var leftJumpButton = document.getElementById("left_jump");
            var rightJumpButton = document.getElementById("right_jump");

            leftJumpButton.disabled = true;

            matching_counter = matching_counter - 1;

            if (matching_counter < dis_num_sra) {
                end_index = matching_counter;
                rightJumpButton.disabled = true;
            }
            else {
                end_index = dis_num_sra; 
                rightJumpButton.disabled = false;
            }

            leftJumpButton.setAttribute("isFilter", "true");
            rightJumpButton.setAttribute("isFilter", "true");

            if(matching_counter === 0) {
                displayNumberResults(-1, -1, -1, true);
                leftJumpButton.setAttribute("start_number", "0");
                leftJumpButton.setAttribute("end_number", "0");
                leftJumpButton.setAttribute("total_number_filter", "0");

                rightJumpButton.setAttribute("start_number", "0");
                rightJumpButton.setAttribute("end_number", "0");
                rightJumpButton.setAttribute("total_number_filter", "0");
            }
            else {
                displayNumberResults(1, end_index, matching_counter, false);
                leftJumpButton.setAttribute("start_number", "1");
                leftJumpButton.setAttribute("end_number", end_index);
                leftJumpButton.setAttribute("total_number_filter", matching_counter);

                rightJumpButton.setAttribute("start_number", "1");
                rightJumpButton.setAttribute("end_number", end_index);
                rightJumpButton.setAttribute("total_number_filter", matching_counter);
            }
            
        }

            /////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

        function check_reg_for_tr(tds, reg_array) {

            next_and = false;
            next_or = false;
            next_not = false;
            first_entry = true;
            skip_next = false;

            overall_statisfied = false;

            for(var i = 0; i < reg_array.length; i++) {
                reg_array[i] = reg_array[i].trim();
                if (skip_next) {
                    skip_next = false;
                    continue;
                }
                else if (reg_array[i] === 'AND') {
                    if (!overall_statisfied) {
                        skip_next = true;
                        continue;
                    }
                    next_and = true;
                    continue;
                }
                else if (reg_array[i] === 'OR'){
                    if (overall_statisfied) {
                        skip_next = true;
                        continue;
                    }
                    next_or = true;
                    continue;
                }
                for(var j = 0; j < tds.length; j++) {
                    if(tds[j]) {
                    txtValue = tds[j].textContent;
                
                    if (first_entry) {
                        if (reg_array[i].startsWith("NOT")) {
                            
                            if (txtValue.toUpperCase().indexOf(reg_array[i].slice(4).toUpperCase()) != -1) {
                                overall_statisfied = false;
                                break;
                            }
                            else {
                                overall_statisfied = true;
                            }
                        }
                        else if (txtValue.toUpperCase().indexOf(reg_array[i].toUpperCase()) != -1) {
                            overall_statisfied = true;
                            break;
                        }
                        else {
                            overall_statisfied = false;
                        }
                }
                else {
                    if (next_and) {
                        if (reg_array[i].startsWith("NOT")) {
                            if (txtValue.toUpperCase().indexOf(reg_array[i].slice(4).toUpperCase()) != -1) {
                                
                                overall_statisfied = false;
                                break;
                            }
                            else {
                                overall_statisfied = true;
                            }
                        }
                        else if (txtValue.toUpperCase().indexOf(reg_array[i].toUpperCase()) != -1) {
                            overall_statisfied = true;
                            break;
                        }
                        else {
                            overall_statisfied = false;
                        }
                    }
                    else if (next_or) {
                        if (reg_array[i].startsWith("NOT")) {
                            if (txtValue.toUpperCase().indexOf(reg_array[i].slice(4).toUpperCase()) != -1) {
                                overall_statisfied = false;
                                break;
                            }
                            else {
                                overall_statisfied = true;
                            }

                        } 
                        else if (txtValue.toUpperCase().indexOf(reg_array[i].toUpperCase()) != -1) {
                            overall_statisfied = true;
                            break;
                        }
                        else {
                            overall_statisfied = false;
                        }
                    }
                }
            }
            }
            if (first_entry) {
                first_entry = false;
            }
            if (next_or) {
                next_or = false;
            }
            if (next_and) {
                next_and = false;
            }
            }

            return overall_statisfied;
        }
        
        function resetFilter() {
            
            var anyFilter = document.getElementById("AnyTermFilter");
            anyFilter.value = "";
            anyFilter.disabled = false;
            
            var study_inputs = document.getElementsByClassName("input_study");
            
            for (var i = 0; i < study_inputs.length; i++) {
                study_inputs[i].value = "";
            }
            
            var run_inputs = document.getElementsByClassName("input_run");
            for (var i = 0; i < run_inputs.length; i++) {
                run_inputs[i].value = "";
            }

            var date_inuts = document.getElementsByClassName("input_dates");
            for (var i = 0; i < date_inuts.length; i++) {
                date_inuts[i].value = "";
            }

            var date_sample_inuts = document.getElementsByClassName("input_sample_dates");
            for (var i = 0; i < date_sample_inuts.length; i++) {
                date_sample_inuts[i].value = "";
            }

            var virus_cbs = document.getElementsByClassName("virus_checkboxes");
            for (var i = 0; i < virus_cbs.length; i++) {
                virus_cbs[i].checked = false;
            }
            
            caution_symbol = document.getElementById("cautionSymbol");
            caution_symbol.classList.remove('active');

            var leftJumpButton = document.getElementById("left_jump");
            var rightJumpButton = document.getElementById("right_jump");

            leftJumpButton.disabled = true;
            rightJumpButton.disabled = false;

            totalNumber = parseInt(leftJumpButton.getAttribute("total_number"));
            isFilter = leftJumpButton.getAttribute("isFilter");
            
            if (isFilter === "false") {
                start = parseInt(leftJumpButton.getAttribute("start_number"));
                end = parseInt(leftJumpButton.getAttribute("end_number"));
                
                for (var i = start; i < end+1; i++) {
                search_string = 'tr[overall_number="' + i + '"]'; 
                current_element = document.querySelector(search_string);
                current_element.style.display = "none";
                }
            }

            leftJumpButton.setAttribute("total_number_filter", "-1");
            leftJumpButton.setAttribute("isFilter", "false");
            leftJumpButton.setAttribute("start_number", "1");
            leftJumpButton.setAttribute("end_number", dis_num_sra.toString());

            rightJumpButton.setAttribute("total_number_filter", "-1");
            rightJumpButton.setAttribute("isFilter", "false");
            rightJumpButton.setAttribute("start_number", "1");
            rightJumpButton.setAttribute("end_number", dis_num_sra.toString());

            var filtered_trs = document.querySelectorAll('tr[filter_number]:not([filter_number="-1"])');

            for (var i = 0; i < filtered_trs.length; i++) {
                filtered_trs[i].style.display = "none";
                filtered_trs[i].setAttribute("filter_number", "-1");
            }

            for (var i = 1; i < dis_num_sra+1; i++) {
                search_string = 'tr[overall_number="' + i + '"]'; 
                current_element = document.querySelector(search_string);
                current_element.style.display = "table-row";
            }
            
            closeAllChars();
            displayNumberResults(1, dis_num_sra, totalNumber, false);
        }

        function fillSecondDate(date_filter_option) {

            date_input_id_1 = "specificFilter:" + date_filter_option + "#1";
            date_input_id_2 = "specificFilter:" + date_filter_option + "#2";

            date_input_1 = document.getElementById(date_input_id_1);
            date_input_2 = document.getElementById(date_input_id_2);

            date_1 = date_input_1.value;

            date_input_2.value = date_1;
        }

        function downloadTableData() {

            var mainTableHead = document.getElementById("MainTableHead");
            var mainThElements = mainTableHead.querySelectorAll('th');
            
            var subTableHeads = document.getElementsByClassName("SubTableHead");
            var subTableHead = subTableHeads[0];
            var subThElements = subTableHead.querySelectorAll('th');

            var mainTableRows = document.getElementsByClassName("MainTable_rows");
            var srp_column_index = getIndexOfHeadColumn(mainTableHead, "study_accession");

            var srp_file_content = "";
            var srr_file_content = "";
            
            characteristic_columns = document.getElementsByClassName("characteristicHead");
            characteristic_columns = Array.from(characteristic_columns);
            
            for(var i = 0; i < mainThElements.length; i++) {
                if(mainThElements[i]){
                    srp_file_content += mainThElements[i].textContent;
                    srp_file_content += "\\t"
                }
            }
            
            srp_file_content = srp_file_content.replace(/\\t$/, '');
            srp_file_content += "\\n";
            
            for(var j = 0; j < subThElements.length; j++) {
                if(subThElements[j] && characteristic_columns.indexOf(subThElements[j]) === -1){
                    sub_content = subThElements[j].textContent;
                    if (sub_content.includes("⯈") || sub_content.includes("⯇")) {
                        sub_content = sub_content.replace(/⯈/g, ""); 
                        sub_content = sub_content.replace(/⯇/g, ""); 
                        sub_content = sub_content.trim();
                    }
                    srr_file_content += sub_content;
                    srr_file_content += "\\t"
                }
            } 
                
            srr_file_content += "SRA_characteristics\\n"
            
            

            var filtered_trs = document.querySelectorAll('tr[filter_number]:not([filter_number="-1"])');

            for (var i = 0; i < filtered_trs.length; i++) {
                tds = filtered_trs[i].getElementsByTagName("td");
                for(var j = 0; j < tds.length; j++) {
                    if(tds[0]) {
                        if(tds[j].textContent.startsWith("⯈ ") | tds[j].textContent.startsWith("⯅ ") | tds[j].textContent.startsWith("+ ")) {
                            srp_file_content += tds[j].textContent.slice(2);
                            srp_file_content += "\\t";
                        }
                        else {
                            srp_file_content += tds[j].textContent;
                            srp_file_content += "\\t";
                        }
                    }
                }
                
                srp_file_content += "\\n";

                srp = tds[srp_column_index].textContent.slice(2);

                var runTable = document.getElementById("runTable_" + srp);
                
                var currentrunTableHead = runTable.querySelector("thead");
                var currentrunThElements = currentrunTableHead.getElementsByTagName("th");

                trs_run = runTable.getElementsByTagName("tr");
                
                
                for(var j = 0; j < trs_run.length; j++) {
                    tds_run = trs_run[j].getElementsByTagName("td");
                    for(var k = 0; k < tds_run.length; k++) {
                        if(tds_run[0]) {
                            if(characteristic_columns.indexOf(currentrunThElements[k]) === -1) {
                                if(tds_run[k].textContent.startsWith("+ ") | tds_run[k].textContent.startsWith("- ")) {
                                    srr_file_content += tds_run[k].textContent.slice(2);
                                    srr_file_content += "\\t";
                                }
                                else {
                                    srr_file_content += tds_run[k].textContent;
                                    srr_file_content += "\\t";
                                }
                            }
                            else {
                                if(tds_run[k].textContent.startsWith("+ ") | tds_run[k].textContent.startsWith("- ")) {
                                    srr_file_content += currentrunThElements[k].textContent + ":" + tds_run[k].textContent.slice(2) + ";";
                                }
                                else {
                                    srr_file_content += currentrunThElements[k].textContent + ":" + tds_run[k].textContent + ";";
                                } 
                            } 
                        }
                    }
                    if(tds_run[0]) {
                        srr_file_content += "\\n"
                    }
                    
                }
            }
            var blob = new Blob([srp_file_content], { type: 'text/plain' });
            var srp_file_name = 'Study_output.tsv';
            var a = document.createElement('a');

            a.href = window.URL.createObjectURL(blob);

            a.download = srp_file_name;

            document.body.appendChild(a);

            a.click();

            document.body.removeChild(a);
            
            var blob = new Blob([srr_file_content], { type: 'text/plain' });
            var srr_file_name = 'Runs_output.tsv';
            var a = document.createElement('a');

            a.href = window.URL.createObjectURL(blob);

            a.download = srr_file_name;

            document.body.appendChild(a);

            a.click();

            document.body.removeChild(a);
            
        }
        
        function openNewVirusDiv(virus_category) {
            
            corresponding_virus_div = document.getElementById(virus_category + '_div');
            
            all_virus_divs = document.getElementsByClassName('viruses_divs');
            
            for(var i = 0; i < all_virus_divs.length; i++) {
                all_virus_divs[i].style.display = "none";
            }
            corresponding_virus_div.style.display = "block";
            
            change_virus_button_status(virus_category);
            caution_for_other_virus_divs(virus_category);
        }
        
        function change_virus_button_status(virus_category) {
            corresponding_virus_button = document.getElementById(virus_category + "_open_button");
            all_virus_buttons = document.getElementsByClassName("virus_open_buttons");

            for (var i = 0; i < all_virus_buttons.length; i++) {
                all_virus_buttons[i].classList.remove('active');
            }
            corresponding_virus_button.classList.add('active');
        }

        function caution_for_other_virus_divs(virus_category) {
            
            allVirusDivs = document.getElementsByClassName("viruses_divs");
            corresponding_virus_div = document.getElementById(virus_category + '_div');
            other_cbs_checked = false;
            caution_symbol = document.getElementById("cautionSymbol");
            caution_symbol.classList.remove('active');
            for(var i = 0; i < allVirusDivs.length; i++) {
                if(allVirusDivs[i] !== corresponding_virus_div ) {
                    var currentVirusDiv = document.getElementById(allVirusDivs[i].id);
                    var currentCheckboxes = currentVirusDiv.querySelectorAll('input[type="checkbox"]');
                    for(var j = 0; j < currentCheckboxes.length; j++) {
                        if(currentCheckboxes[j].checked) {
                            other_cbs_checked = true;
                            break;
                        }
                    }
                    if(other_cbs_checked) {
                        break;
                    }
                }
            }
            if(other_cbs_checked) {
                caution_symbol.classList.add('active');
            }   
        }

        function openNewFilterDivs(filter_name) {
            // filter_id := "Series" or "Sample" or "AnyTerm"
            resetFilter();
            
            filter_divs = document.getElementsByClassName("filterDivs");
            corresponding_filter_div = document.getElementById(filter_name + "FilterDiv");
            
            for(var i = 0; i < filter_divs.length; i++) {
                filter_divs[i].style.display = "none";
            }
            
            corresponding_filter_div.style.display = "block";
            
            change_open_buttons_status(filter_name);
        }
        
        function change_open_buttons_status(filter_name) {
            corresponding_filter_button = document.getElementById("open" + filter_name + "Filter");
            all_filter_buttons = document.getElementsByClassName("openButtons");

            for (var i = 0; i < all_filter_buttons.length; i++) {
                all_filter_buttons[i].classList.remove('active');
            }
            corresponding_filter_button.classList.add('active');
        }
        
        function deleteInput(object_id) {
            input_element = document.getElementById(object_id);
            input_element.value = "";
        }

        function displayNumberResults(start_num, end_num, numberTotal, noResults) {
            
            var numberInput = document.getElementById("numberSeries");
            numberInput.style.display = "inline-block";
            if(noResults) {
                numberInput.textContent = "No runs were found.";
            }
            else {
                leftJumpButton = document.getElementById("left_jump");
                total_count = parseInt(leftJumpButton.getAttribute("total_number"));
                if(total_count === dis_num_sra) {
                    numberInput.textContent = "Displaying " + end_num + "run of " + numberTotal;
                }
                else {
                    numberInput.textContent = "Run " + start_num + "-" + end_num + "/" + numberTotal;
                }
            }  
        }
        
         function nextLeftSamples() {
             
            closeAllChars();

            leftJumpButton = document.getElementById("left_jump");
            rightJumpButton = document.getElementById("right_jump");

            leftJumpButton.disabled = false;
            rightJumpButton.disabled = false;

            start_index = parseInt(leftJumpButton.getAttribute("start_number"));
            end_index = parseInt(leftJumpButton.getAttribute("end_number"));
            total_count = parseInt(leftJumpButton.getAttribute("total_number"));
            total_count_filter = parseInt(leftJumpButton.getAttribute("total_number_filter"));
            
            if(end_index+1 - start_index < dis_num_sra) {
                new_start_index = start_index - dis_num_sra;
                new_end_index = end_index - (end_index+1 - start_index);
            }
            else {
                new_start_index = start_index - dis_num_sra;
                new_end_index = end_index - dis_num_sra;
            }
            
            if(new_start_index <= 1) {
                new_start_index = 1;
                new_end_index = new_start_index + (dis_num_sra-1);
                leftJumpButton.disabled = true;
            }

            leftJumpButton.setAttribute("start_number", new_start_index);
            leftJumpButton.setAttribute("end_number", new_end_index);

            rightJumpButton.setAttribute("start_number", new_start_index);
            rightJumpButton.setAttribute("end_number", new_end_index);

            isFilter = leftJumpButton.getAttribute("isFilter");

            if (isFilter === "false") {
    
                for(var i = end_index; i > start_index-1; i--) {
                    search_string = 'tr[overall_number="' + i + '"]'; 
                    current_element = document.querySelector(search_string);
                    current_element.style.display = "none";
                }
    
                for(var i = new_end_index; i > new_start_index-1; i--) {
                    search_string = 'tr[overall_number="' + i + '"]'; 
                    current_element = document.querySelector(search_string);
                    current_element.style.display = "table-row";
                }
                displayNumberResults(new_start_index, new_end_index, total_count, false);

            }
            else {
                for(var i = end_index; i > start_index-1; i--) {
                    search_string = 'tr[filter_number="' + i + '"]'; 
                    current_element = document.querySelector(search_string);
                    current_element.style.display = "none";
                }
    
                for(var i = new_end_index; i > new_start_index-1; i--) {
                    search_string = 'tr[filter_number="' + i + '"]'; 
                    current_element = document.querySelector(search_string);
                    current_element.style.display = "table-row";
                }

                displayNumberResults(new_start_index, new_end_index, total_count_filter, false);
            }
            
        }
        
        function nextRightSamples() {
            
            closeAllChars();
            
            leftJumpButton = document.getElementById("left_jump");
            rightJumpButton = document.getElementById("right_jump");

            leftJumpButton.disabled = false;
            rightJumpButton.disabled = false;

            start_index = parseInt(leftJumpButton.getAttribute("start_number"));
            end_index = parseInt(leftJumpButton.getAttribute("end_number"));
            total_count = parseInt(leftJumpButton.getAttribute("total_number"));
            total_count_filter = parseInt(leftJumpButton.getAttribute("total_number_filter"));
            
            new_start_index = start_index + dis_num_sra;
            new_end_index = end_index + dis_num_sra;

            isFilter = leftJumpButton.getAttribute("isFilter");

            if (isFilter === "false") {

                if(new_end_index >= total_count) {
                    new_end_index = total_count;
                    //new_start_index = new_end_index - (dis_num_sra-1);
                    rightJumpButton.disabled = true;
                }

                leftJumpButton.setAttribute("start_number", new_start_index);
                leftJumpButton.setAttribute("end_number", new_end_index);

                rightJumpButton.setAttribute("start_number", new_start_index);
                rightJumpButton.setAttribute("end_number", new_end_index);

                for(var i = start_index; i < end_index+1; i++) {
                    search_string = 'tr[overall_number="' + i + '"]'; 
                    current_element = document.querySelector(search_string);
                    current_element.style.display = "none";
                }

                for(var i = new_start_index; i < new_end_index+1; i++) {
                    search_string = 'tr[overall_number="' + i + '"]'; 
                    current_element = document.querySelector(search_string);
                    current_element.style.display = "table-row";
                }
                displayNumberResults(new_start_index, new_end_index, total_count, false);
            }
            else {

                if(new_end_index >= total_count_filter) {
                    new_end_index = total_count_filter;
                    //new_start_index = new_end_index - (dis_num_sra-1);
                    rightJumpButton.disabled = true;
                }

                leftJumpButton.setAttribute("start_number", new_start_index);
                leftJumpButton.setAttribute("end_number", new_end_index);

                rightJumpButton.setAttribute("start_number", new_start_index);
                rightJumpButton.setAttribute("end_number", new_end_index);

                for(var i = start_index; i < end_index+1; i++) {
                    search_string = 'tr[filter_number="' + i + '"]'; 
                    current_element = document.querySelector(search_string);
                    current_element.style.display = "none";
                }

                for(var i = new_start_index; i < new_end_index+1; i++) {
                    search_string = 'tr[filter_number="' + i + '"]'; 
                    current_element = document.querySelector(search_string);
                    current_element.style.display = "table-row";
                }
                displayNumberResults(new_start_index, new_end_index, total_count_filter, false);
            }
        }
        
        function nextLeftRuns(srp) {
            
            leftBut = document.getElementById("jumpLeftRun_" + srp);
            rightBut = document.getElementById("jumpRightRun_" + srp);
            
            start_run = parseInt(leftBut.getAttribute("startRun"));
            end_run = parseInt(leftBut.getAttribute("endRun"));
            
            if(end_run+1 - start_run < vis_num_sra_runs) {
                new_start_run = start_run - vis_num_sra_runs;
                new_end_run = end_run - (end_run+1 - start_run);
            }
            else {
                new_start_run = start_run - vis_num_sra_runs;
                new_end_run = end_run - vis_num_sra_runs;
            }
                        
            leftBut.disabled = false;
            rightBut.disabled = false;
            
             if(new_start_run <= 1) {
                new_start_run = 1;
                new_end_run = new_start_run + (vis_num_sra_runs-1);
                leftBut.disabled = true;
            }

            leftBut.setAttribute("startRun", new_start_run);
            leftBut.setAttribute("endRun", new_end_run);
            
            corr_table = document.getElementById("runTable_" + srp);
            
            // Close current visible runs
            srr_none = []
            for(var i = start_run; i < end_run+1; i++) {
                srr_none.push("tr[run_number='" + i + "']");
            }
            var selector_none = srr_none.join(", ");
            runs_for_none = corr_table.querySelectorAll(selector_none);
            runs_for_none.forEach(function(tr) {
                tr.style.display = "none";
            });
            // Open new runs
            srr_visible = []
            for(var i = new_start_run; i < new_end_run+1; i++) {
                srr_visible.push("tr[run_number='" + i + "']");
            }
            var selector_visible = srr_visible.join(", ");
            runs_for_visible = corr_table.querySelectorAll(selector_visible);
            runs_for_visible.forEach(function(tr) {
                tr.style.display = "table-row";
            });
            
        }
        
        function nextRightRuns(srp) {
            
            leftBut = document.getElementById("jumpLeftRun_" + srp);
            rightBut = document.getElementById("jumpRightRun_" + srp);
            
            start_run = parseInt(leftBut.getAttribute("startRun"));
            end_run = parseInt(leftBut.getAttribute("endRun"));
            
            new_start_run = start_run + vis_num_sra_runs;
            new_end_run = end_run + vis_num_sra_runs;
            
            total_runs = parseInt(leftBut.getAttribute("totalRuns"));

            leftBut.disabled = false;
            rightBut.disabled = false;
            
             if(new_end_run >= total_runs) {
                new_end_run = total_runs;
                //new_start_run = new_end_run - (vis_num_sra_runs-1);
                rightBut.disabled = true;
            }

            leftBut.setAttribute("startRun", new_start_run);
            leftBut.setAttribute("endRun", new_end_run);
            
            corr_table = document.getElementById("runTable_" + srp);
            
            // Close current visible runs
            srr_none = []
            for(var i = end_run; i > start_run-1; i--) {
                srr_none.push("tr[run_number='" + i + "']");
            }
            var selector_none = srr_none.join(", ");
            runs_for_none = corr_table.querySelectorAll(selector_none);
            runs_for_none.forEach(function(tr) {
                tr.style.display = "none";
            });
            // Open new runs
            srr_visible = []
            for(var i = new_end_run; i > new_start_run-1; i--) {
                srr_visible.push("tr[run_number='" + i + "']");
            }
            var selector_visible = srr_visible.join(", ");
            runs_for_visible = corr_table.querySelectorAll(selector_visible);
            runs_for_visible.forEach(function(tr) {
                tr.style.display = "table-row";
            });
            
        }
        
        document.addEventListener('click', function(event) {
                var filter_panel = document.getElementById('filter-panel');
                var isClickInsideDiv = filter_panel.contains(event.target);
                if (!isClickInsideDiv && filter_panel.style.display !== "none") {
                    filter_panel.style.display = 'none';
                }
            });
            
            document.addEventListener('keyup', function(event) {
                var filter_panel = document.getElementById('filter-panel');
                if (event.keyCode === 13 & filter_panel.style.display !== "none" ) {
                    submitChosenFilter();
                }
            });
            
            document.addEventListener("DOMContentLoaded", function() {
            // Verstecke das Ladebildschirm-Div
            document.getElementById("loader").style.display = "none";
            // Zeige den eigentlichen Inhalt
            document.getElementById("content").style.display = "block";
            });
            
        
        </script>
            <title>DEEP-DV hub</title>
            <style>
        body {
                    width: 100vw;
                    background: #fff;
                }

                #MainTable {
                    width: 100%;
                    overflow: auto;
                    border-collapse: collapse;
                    border: 0;
                    border-radius: 8px;
                    }

                #MainTableHead th{
                    padding: 20px;
                    text-align: center;
                    background-color: #1f7dac;
                    max-width: 200px;
                    min-width: 200px;
                    max-height: 30px;
                    color: #fff;
                }

                #MainTableHead th:first-child {
                    border-radius: 8px 0 0 0;
                }

                #MainTableHead th:last-child {
                    border-radius: 0 8px 0 0;
                }

                .MainTable_rows {
                    border-bottom: 1px solid;
                    border-color: rgb(104, 102, 102);
                }

                .runTable {
                    width: 100%;
                    overflow: hidden;
                    border-collapse: collapse;
                    border: 0;
                    border-radius: 8px;
                }

                .SubTableHead th {
                    padding: 20px;
                    text-align: center;
                    background-color: #b4ccd8;
                    max-width: 200px;
                    min-width: 200px;
                    max-height: 30px;
                    color: black;
                }

                .runTable tr{
                    border-bottom: 1px solid;
                    border-color: rgb(104, 102, 102);
                }
                    
                .runTable td {
                    padding: 20px;
                    text-align: center;
                    white-space: nowrap; 
                    overflow: hidden; 
                    text-overflow: ellipsis;
                    max-width: 200px;
                    min-width: 200px;
                    max-height: 30px;
                }

                #MainTable td {
                    padding: 20px;
                    text-align: center;
                    white-space: nowrap; 
                    overflow: hidden; 
                    text-overflow: ellipsis;
                    max-width: 200px;
                    min-width: 200px;
                    max-height: 30px;
                }

                .top-heading {
                    display: flex;
                    align-items: center;
                    margin-bottom: 30px;
                    font-family: Tahoma, sans-serif;
                    font-size: 36px;
                    color: #fff;
                    background-color: #1f7dac;
                    height: 150px;
                    width: 100%;
                    border-bottom-left-radius: 15px; 
                    border-bottom-right-radius: 15px;
                    padding-left: 40px;

                }
        
                .button {
                bottom: 3px; 
                left: 2px; 
                width: 25px;
                background-color: #fff;
                border: 0;
                border-radius: 10px;
                cursor: pointer;
            }
            
            .show_char_button {
                bottom: 3px; 
                left: 2px; 
                width: 25px;
                background-color: #fff;
                border: 0;
                border-radius: 10px;
                cursor: pointer;
            }

            .hidden_table_row {
                display: none;
            }
            
            #AnyTermFilterDiv {
                display: none;
            }
            
            #RunFilterDiv {
                display: none;
            }
            
            #filter-panel {
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                width: 400px;
                height: 100%;
                background-color: #b4ccd8;
                padding: 20px;
                box-shadow: -5px 0 5px rgba(0, 0, 0, 0.1);
                overflow-y: auto;
                border-radius: 0 20px 20px 0;
            }

            #OpenFilterPanelButton {
                border-radius: 5px; 
                margin-bottom: 1%;
                margin-left: 3%;
                font-size: 20px;
                background-color: #1f7dac;
                color: #fff;
                border: 0;
                cursor: pointer;
                padding: 10px; 

            }
            
            #OpenFilterPanelButton:hover {
                background-color: gray; 
            }
            
            .input_study {
                margin-bottom: 5px;
                width: 65%;
            }
            
            .input_run {
                margin-bottom: 5px;
                width: 65%;
            }

            #AnyTermFilter {
                margin-bottom: 5px;
                width: 65%;
            }
            
            .deleteCurrentInput {
                border-radius: 30%;
                background-color: #b4ccd8;
                border: none; 
                margin-left: 5px;
                margin-right: 5px;
                cursor: pointer;
                color: #B22222;
                font-size: 16px;

            }

            #SubmitFilterButton {
                margin-left: 75%;
                background-color: #1f7dac; 
                color: #fff; 
                padding: 10px 20px; 
                font-size: 16px;
                border: none; 
                border-radius: 5px; 
                cursor: pointer; 
                transition: background-color 0.3s ease; 
            }

            #buttonBar {
                overflow: hidden;
                background-color: #b4ccd8;
            }

            .openButtons {
            float: left;
            display: block;
            padding: 15px;
            text-align: center;
            cursor: pointer;
            transition: background-color 0.3s ease;
            background-color: #1f7dac;
            font-size: 16px;
            border: none;
            color: #fff; 
            }

            .openButtons:hover {
                background-color: gray; 
            }
            
            .openButtons.active {
            background-color: #4169E1;
            }

            #SubmitFilterButton:hover {
                background-color: gray;
            }
            
            #DownloadButton:hover {
                background-color: gray;
            }

            #openStudyFilter {
                border-radius: 20px 0px 0px 20px;
            }

            #openAnyTermFilter {
                border-radius: 0 20px 20px 0;
            }

            #CloseFilterPanelButton {
                background-color: #b4ccd8;
                border: none;
                cursor: pointer;
                border-radius: 5px;
                font-size: 30px;
            }

            #CloseFilterPanelButton:hover {
                background-color: gray; 
            }

            #ResetFilterButton {
                background-color: #b4ccd8;
                border: none;
                cursor: pointer;
                border-radius: 5px;
                font-size: 20px;
                margin-left: 75%;
            }

            #ResetFilterButton:hover {
                background-color: gray;
            }

            .button:hover {
                background-color: gray;
            }
            
            .show_char_button:hover {
                background-color: gray;
            }
            
            .input_dates {
                margin-bottom: 5px;
                width: 28%;
            }
            
            .input_sample_dates {
                margin-bottom: 5px;
                width: 28%;
            }
            
            .information_date_button {
                background-color: #b4ccd8;
                border: none;
                font-size: 20px;
            }
            
            #DownloadButton {
                border-radius: 5px; 
                margin-bottom: 1%;
                margin-left: 3%;
                font-size: 20px;
                background-color: #1f7dac;
                border: none;
                color: #fff;
                padding: 10px;
                cursor: pointer;
            }
            
            .virus_open_buttons {
                float: left;
                display: block;
                padding: 15px;
                text-align: center;
                cursor: pointer;
                transition: background-color 0.3s ease;
                background-color: #1f7dac;
                font-size: 14px;
                border: none;
                color: #fff; 
            }
            
            .virus_open_buttons:hover {
                background-color: gray;
            }
            
            .virus_open_buttons.active {
                background-color: #4169E1;
            }
            
            #virus_bar {
                overflow: hidden;
                background-color: #b4ccd8;
            }
            
            .virus_tds {
                padding: 5px;
            }
            
            .cautionSymbols {
                display: none;
            }
            
            .cautionSymbols.active {
                float: left;
                display: block;
                padding: 9px;
                text-align: center;
                background-color: #b4ccd8;
                font-size: 20px;
                border: none;
                color: red;
                
            }
            
            #numberSeries {
                display: none;
                border-radius: 5px;
                margin-bottom: 1%;
                font-size: 15px;
                background-color: #fff;
                border: 1px solid;
                padding: 10px;
                color: black;
            }
            
            .menuContentLinks {
                color: #fff;
                text-decoration: none;
                font-family: Tahoma, sans-serif;
                font-size: 20px;
                cursor: pointer;
            }

             #recount3_link {
                position: absolute;
                right: 5%;
            }

            #q_and_a_link {
                right: 12%;
                position: absolute;
            }

            .menuContentLinks:hover {
                color: gray;
            }

            #public_geo_data {
                position: absolute;
                right: 17%;
            }

            #internal_data {
                position: absolute;
                right: 24%;
            }

            #left_jump {
                margin-left: 3%;
                font-size: 15px;
                background-color: #fff;
                color: black;
                border: none;
                cursor: pointer;
                border-radius: 5px;
            }

            #left_jump:hover{
                background-color: gray;
            }

            #right_jump {
                font-size: 15px;
                background-color: #fff;
                color: black;
                border: none;
                cursor: pointer;
                border-radius: 5px;
            }

            #right_jump:hover{
                background-color: gray;
            }

            #left_jump[disabled]:hover {
                background-color: #fff;
                cursor: default;
            }

            #left_jump[disabled] {
                color: lightgray;
            }

            #right_jump[disabled]:hover {
                background-color: #fff;
                cursor: default;
            }

            #right_jump[disabled] {
                color: lightgray;
            }
            
            .jumpRunButtons {
                background-color: #b4ccd8;
                border: none;
                cursor: pointer;
                border-radius: 5px;
            }
            
            .jumpRunButtons:hover{
                background-color: gray;
            }
            
            .jumpRunButtons[disabled] {
                color: lightgray;
            }

            .jumpRunButtons[disabled]:hover {
                background-color: #fff;
                cursor: default;
            }
            
             @-webkit-keyframes spin {
            0% { -webkit-transform: rotate(0deg); }
            100% { -webkit-transform: rotate(360deg); }
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
            
            #loader {
                border: 16px solid #f3f3f3;
                border-radius: 50%;
                border-top: 16px solid #3498db;
                width: 120px;
                height: 120px;
                -webkit-animation: spin 2s linear infinite; /* Safari */
                animation: spin 2s linear infinite;
                margin-left: 50%;
                margin-top: 10%;
                }
            
            </style>
        </head>
        """
        

    sra_page += f"""<body onload="displayNumberResults(1, {dis_num_sra}, {sra_study_df_size}, false)">
            <div class="top-heading">
            Public SRA data
            <a href="https://jhubiostatistics.shinyapps.io/recount3-study-explorer/" id="recount3_link" class="menuContentLinks" target="_blank">recount3</a>
            <a href="question_answer.html" id="q_and_a_link" class="menuContentLinks" target="_blank">Q&A</a>
            <a href="geoData.html" id="public_geo_data" class="menuContentLinks" target="_blank">GEO data</a>
            """

    if(buildBoth):
        sra_page += '<a href="internalData.html" id="internal_data" class="menuContentLinks" target="_blank">Internal data</a>'
        
            
    sra_page += f"""
        </div>
        <button id="OpenFilterPanelButton" onclick="toggleFilterPanel()">Filter</button>
        <button id="DownloadButton" onclick="downloadTableData()"><b>&#11123;</b> Download</button>
    """
    
    if vis_num_sra == -1:
        sra_page += f"""
            <button id="left_jump" onclick="nextLeftSamples()" start_number = "1" end_number= "{dis_num_sra}" total_number = "{sra_study_df_size}" isFilter = "false" total_number_filter = "-1" disabled style="display: none;">&laquo; Previous</button>
            <button id="numberSeries" style="margin-left: 3%;">Label not relevant here</button>
            <button id="right_jump" onclick="nextRightSamples()" start_number = "1" end_number= "{dis_num_sra}" total_number = "{sra_study_df_size}" isFilter = "false" total_number_filter = "-1" disabled style="display: none;">Next &raquo;</button>
            
        """
    else:
        sra_page += f"""
            <button id="left_jump" onclick="nextLeftSamples()" start_number = "1" end_number= "{dis_num_sra}" total_number = "{sra_study_df_size}" isFilter = "false" total_number_filter = "-1" disabled>&laquo; Previous</button>
            <button id="numberSeries">Label not relevant here</button>
            <button id="right_jump" onclick="nextRightSamples()" start_number = "1" end_number= "{dis_num_sra}" total_number = "{sra_study_df_size}" isFilter = "false" total_number_filter = "-1">Next &raquo;</button>
        """
        
    sra_page += f"""
        <div id="filter-panel">
            <button id="CloseFilterPanelButton" onclick="toggleFilterPanel()">&larrhk;</button>
            <button id="ResetFilterButton" onclick="resetFilter()">Reset</button>
            <h3>Filter SRA meta data</h3>
            <div id="buttonBar">
            <button class="openButtons active" id="openStudyFilter" onclick="openNewFilterDivs(\'Study\')">SRP filter</button>
            <button class="openButtons" id="openRunFilter" onclick="openNewFilterDivs(\'Run\')">SRR filter</button>
            <button class="openButtons" id="openAnyTermFilter" onclick="openNewFilterDivs(\'AnyTerm\')">Any term</button>
            </div>
            <br>
            <div id="AnyTermFilterDiv" class="filterDivs"><p id=\"paraAnyTerm\">Filter all search terms: </p>
            <input type="text" id="AnyTermFilter" class="AnyTerm" placeholder="Search for any term"><button class="deleteCurrentInput" onclick="deleteInput('AnyTermFilter')">x</button></div>
        """
        
    sra_page += '<div id="StudyFilterDiv" class="filterDivs"><p id="paraSRA">Filter SRPs: </p>'
    for sra_col in sra_study_df.columns:
        col_index = sra_study_df.columns.get_loc(sra_col)
        if "_date" in str(sra_col):
            sra_page += f'<input type="date" title="Search for {sra_col}" class="input_dates" id="specificFilter:{sra_col}#1" onchange="fillSecondDate(\'{sra_col}\')"><button class="deleteCurrentInput" onclick="deleteInput(\'specificFilter:{sra_col}#1\')">x</button>'
            sra_page += f'<input type="date" title="Search for {sra_col}" class="input_dates" id="specificFilter:{sra_col}#2"><button class="deleteCurrentInput" onclick="deleteInput(\'specificFilter:{sra_col}#2\')">x</button>'
            sra_page += f'<button title="Usage of date filters: Fill in only the first filter option to filter data from your choosen date until today. Fill in only the second filter option to filter data from the beginning until your choosen date. Fill in both filter options to filter data in the range of your choosen dates. For search of a specific date, fill in the same date in both options." class="information_date_button">&#9432;</button>'
        else:
            sra_page += f'<input type="text" class="input_study" id="specificFilter:{sra_col}" placeholder="Search for {str(sra_col)}"><button class="deleteCurrentInput" onclick="deleteInput(\'specificFilter:{sra_col}\')">x</button><br>'

    sra_page += '</div><div id="RunFilterDiv" class="filterDivs"><p id="paraSRA">Filter SRRs: </p>'
    
    for sra_col in sra_run_df.columns:
        col_index = sra_run_df.columns.get_loc(sra_col)
        sra_page += f'<input type="text" class="input_run" id="specificFilter:{sra_col}" placeholder="Search for {str(sra_col)}"><button class="deleteCurrentInput" onclick="deleteInput(\'specificFilter:{sra_col}\')">x</button><br>'


    sra_page += '</div><div id="virusFilterDiv"><p id="paraVirus">Choose your virus(es): </p>'

    sra_page += '<div id="virus_bar">'
    for cat in categories_viruses.keys():
        if cat == first_category:
            sra_page += f'<button id="{cat}_open_button" class="virus_open_buttons active" style="border-radius: 20px 0px 0px 20px; " onclick="openNewVirusDiv(\'{cat}\')">{cat}</button>'
        elif cat == last_category:
            sra_page += f'<button id="{cat}_open_button" class="virus_open_buttons" style="border-radius: 0px 20px 20px 0px; " onclick="openNewVirusDiv(\'{cat}\')">{cat}</button>'
        else:
            sra_page += f'<button id="{cat}_open_button" class="virus_open_buttons" onclick="openNewVirusDiv(\'{cat}\')">{cat}</button>'
    sra_page += '<button id="cautionSymbol" class="cautionSymbols" title="Caution! You have checked checkboxes from other virus genus. If you don\'t want to filter for them, uncheck these checkboxes.">&#9888;</button></div>'
    for cat in categories_viruses.keys():
        cb_counter = 0
        if cat == first_category:
            sra_page += f'<div id="{cat}_div" class="viruses_divs" style="display: block;">'
        else:
            sra_page += f'<div id="{cat}_div" class="viruses_divs" style="display: none;">'
        sra_page += f'<table>'
        for v in categories_viruses[cat]:
            if cb_counter%3 == 0:
                sra_page += "<tr>"
            sra_page += f'<td class="virus_tds"><input type="checkbox" class="virus_checkboxes" id="{v}_cb" name="{v}_cb"><label class="virus_labels" for="{v}_cb">{v}</label></td>'
            if cb_counter%3 == 2:
                sra_page += "</tr>"
            cb_counter += 1
        if cb_counter%3 != 2:
            sra_page += f'</tr></table></div>'
        else:
            sra_page += f'</table></div>'
    sra_page += "<br>"

    sra_page += '</div><button id="SubmitFilterButton" onclick="submitChosenFilter()">Filter</button><br><br><br></div><div id="loader"></div><div id="content" style="display: none;"><table id="MainTable"><thead id="MainTableHead"><tr>'

    # Add header for SRA meta data
    for col in sra_study_df.columns:
        sra_page += f"<th>{col}</th>"

    sra_page += "</tr></thead>"
    # Add meta data
    progress_bar_sra = tqdm(total=sra_study_df_size, desc="Processing", unit="iteration")

    visible_counter = 1
    for index, row in sra_study_df.iterrows():
        
        progress_bar_sra.update(1)
        
        srp = str(sra_study_df.loc[index, "study_accession"])
        if visible_counter < dis_num_sra+1:
            sra_page += f'<tr id="{srp}_MainTable" class="MainTable_rows" style="display: table-row;" overall_number = "{visible_counter}" filter_number = "-1">'
        else:
            sra_page += f'<tr id="{srp}_MainTable" class="MainTable_rows" style="display: none;" overall_number = "{visible_counter}" filter_number = "-1">'
        visible_counter += 1
        for col in sra_study_df.columns:
            
            val = sra_study_df.at[index, col]
            if pandas.isna(val):
                value = "NA"
            else:
                value = str(val)
            
            if len(value) < 40:
                if col == "study_accession":
                    if ";" in value:
                        value = value.split(";")[0].strip()
                    sra_page += f'<td title="{col}"><button class="show_char_button" id="{srp}_showRunButton" onclick="showRuns({srp}_showRunButton, \'{srp}_tr\')">&#11208;</button><a href="https://www.ncbi.nlm.nih.gov/sra/?term={value}" target="_blank"> {value}</a></td>'               
                elif col == "bioproject" and not pandas.isna(value) and value != "NA" and value != "nan":
                    sra_page += f'<td title="{col}"><a href="https://www.ncbi.nlm.nih.gov/bioproject/{value}" target="_blank">{value}</a></td>'               
                else:
                    sra_page += f'<td title="{col}">{value}</td>'
            elif len(value.strip().split(" ")) == 1:
                value_1 = value[0:(len(value))//2]
                value_2 = value[((len(value))//2):] 
                
                sra_page += f'<td title="{col}"><button class="button" id="{col}_{index}_showTextButton" onclick="showFullText({col}_{index}_showTextButton)">+</button> {value_1} {value_2}</td>'
            else:
                sra_page += f'<td title="{col}"><button class="button" id="{col}_{index}_showTextButton" onclick="showFullText({col}_{index}_showTextButton)">+</button> {value}</td>'
        sra_page += "</tr>"
        # <td colspan="100%" style="overflow: auto;">
        sra_page += f'<tr id="{srp}_tr" class="hidden_table_row"><td style="overflow: auto;"><table class="runTable" id="runTable_{srp}">'
        
        sra_page += f'<thead class="SubTableHead"><tr id="runTable_headRow_{srp}">'
        
        temp_df = sra_run_df[sra_run_df["study_accession"].str.contains(fr'\b{re.escape(srp)}(?:;|$)', regex=True, case=False, na=False)]
        
        run_characteristics_column = temp_df['SRA_characteristics']
        run_characteristics = []
        for entry in run_characteristics_column:
            characteristics = str(entry).split(";")

            for char in characteristics:
                char.strip()
                if char != "" and char != "Na" and char != "NA" and char != "nan" and char != "NaN" and not pandas.isna(char):
                    char_splitted = char.split(":")
                    if len(char_splitted) == 1:
                        run_characteristics.append("Further_information")
                    else:                 
                        run_characteristics.append(char.split(":")[0].strip())
        
        run_characteristics = list(set(run_characteristics))
        run_characteristics = [s.replace(" ", "_").replace("(", "_").replace(")", "_") for s in run_characteristics]     
           
        for col_run in sra_run_df.columns:
            if col_run != "SRA_characteristics" and col_run != "run_accession":
                sra_page += f"<th>{col_run}</th>"
            elif col_run == "run_accession":
                if temp_df.shape[0] <= vis_num_sra_runs or vis_num_sra_runs == -1:
                    sra_page += f'<th><button id="jumpLeftRun_{srp}" class="jumpRunButtons" disabled style="display: none;"  startRun = "1" endRun = "{vis_num_sra_runs}" totalRuns = "{temp_df.shape[0]}">&#11207;</button>{col_run}<button id="jumpRightRun_{srp}" disabled style="display: none;">&#11208;</button></th>'
                else:
                    sra_page += f'<th><button id="jumpLeftRun_{srp}" class="jumpRunButtons" onclick="nextLeftRuns(\'{srp}\')" startRun = "1" endRun = "{vis_num_sra_runs}" totalRuns = "{temp_df.shape[0]}" disabled>&#11207; </button>{col_run}<button id="jumpRightRun_{srp}" class="jumpRunButtons" onclick="nextRightRuns(\'{srp}\')">&#11208;</button></th>'
            else:
                for char_col in run_characteristics:
                    sra_page += f'<th class="characteristicHead">{char_col}</th>'
        sra_page += "</tr></thead>"
        
        run_counter = 1
        tmp_vis_num = vis_num_sra_runs
        if vis_num_sra_runs == -1:
            tmp_vis_num = temp_df.shape[0]
        for index_run, row_run in temp_df.iterrows():
            if run_counter < tmp_vis_num+1:
                sra_page += f'<tr run_number="{run_counter}" style="display: table-row;">'
            else:
                sra_page += f'<tr run_number="{run_counter}" style="display: none;">'
            srr = "" 
            for col_run in temp_df.columns:
                #value_sample = str(temp_df.at[index_sample, col_sample]) 
                val_run = temp_df.at[index_run, col_run]
                
                if pandas.isna(val_run) or val_run == "nan":
                    value_run = "NA"
                else:
                    value_run = str(val_run)
                
                if col_run == "SRA_characteristics":
                    characteristic_pairs = value_run.split(";")
                    characteristic_names_values = {}
                    if "Further_information" in run_characteristics:
                        characteristic_names_values["Further_information"] = ""
                    for char_pair in characteristic_pairs:
                        char_pair.strip()
                        if char_pair != "" and char_pair != "Na" and char_pair != "NA" and char_pair != "nan" and char_pair != "NaN" and not pandas.isna(char_pair):
                            
                            char_splitted = char_pair.split(":")
                            if len(char_splitted) == 1:
                                char_name = "Further_information"
                                char_value = char_splitted[0].strip()
                                characteristic_names_values["Further_information"] += f"{char_value};"
                            else:                 
                                char_name = char_splitted[0].strip().replace(" ", "_").replace("(", "_").replace(")", "_")
                                char_value = char_splitted[1].strip()                            
                                characteristic_names_values[char_name] = char_value
                    for run_char in run_characteristics:
                        split_strings = []
                        if run_char in characteristic_names_values.keys():
                            if len(characteristic_names_values[run_char].strip()) < 30:
                                if len(characteristic_names_values[run_char].strip()) == 0:
                                    sra_page += f'<td title="{run_char}" class="characteristicData">Na</td>'
                                else:
                                    sra_page += f'<td title="{run_char}" class="characteristicData">{characteristic_names_values[run_char]}</td>'
                                
                            elif len(characteristic_names_values[run_char][0:25].split(" ")) == 1:
                                for i in range(0, len(characteristic_names_values[run_char]), 20):
                                    if i == 0:
                                        split_strings.append(characteristic_names_values[run_char][i:i+21])
                                    else:
                                        split_strings.append(characteristic_names_values[run_char][i+1:i+21])
                                sra_page += f'<td title="{run_char}" class="characteristicData"><button class="button" id="{run_char}_{index_run}_sample_showTextButton" onclick="showFullText({run_char}_{index_run}_sample_showTextButton)">+</button> {" ".join(split_strings)}</td>'
                            else:
                                sra_page += f'<td title="{run_char}" class="characteristicData"><button class="button" id="{run_char}_{index_run}_sample_showTextButton" onclick="showFullText({run_char}_{index_run}_sample_showTextButton)">+</button> {characteristic_names_values[run_char]}</td>'

                        else:
                            sra_page += f'<td title="{run_char}" class="characteristicData">NA</td>' 
                    continue                
                elif col_run == "run_accession":
                    sra_page += f'<td title="{col_run}" class="characteristicData"><a href="https://www.ncbi.nlm.nih.gov/search/all/?term={value_run}" target="_blank">{value_run}</a></td>'
                else:
                    if len(value_run) < 30:
                        sra_page += f'<td title="{col_run}" class="characteristicData">{value_run}</td>'
                        
                    elif len(value_run) == 1:
                        for i in range(0, len(value_run), 20):
                            if i == 0:
                                split_strings.append(value_run)
                            else:
                                split_strings.append(value_run[i+1:i+21])
                        sra_page += f'<td title="{col_run}" class="characteristicData"><button class="button" id="{col_run}_{index_run}_sample_showTextButton" onclick="showFullText({col_run}_{index_run}_sample_showTextButton)">+</button> {" ".join(split_strings)}</td>'
                    else:
                        sra_page += f'<td title="{col_run}" class="characteristicData"><button class="button" id="{col_run}_{index_run}_sample_showTextButton" onclick="showFullText({col_run}_{index_run}_sample_showTextButton)">+</button> {value_run}</td>'

                    #sra_page += f'<td title="{col_run}"><button class="button" id="{col_run}_{index_run}_showTextButton" onclick="showFullText({col_run}_{index_run}_showTextButton)">+</button> {value_run}</td>'
            
            sra_page += "</tr>"
            run_counter += 1
        sra_page += "</table></td></tr>"
    sra_page += "</table></div>"

    sra_page += """
    </body>
    </html>
    """
    progress_bar_sra.close()    
    with open(f"{args.output_dir}/sraData.html", "w") as file:
        file.write(sra_page)
    file.close()
    
    print("Finished build of sraData.hmtl.")
##################################### Public SRA data webpage #####################################


##################################### Internal/excel data webpage #####################################
# Page for excel scrapped data/internal DEEP-DV data

if(buildInternalPage):
    
    excel_page = """
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="UTF-8">
    <script>
    """
    
    total_rows_excel = series_excel_df.shape[0]
    if vis_num_int == -1:
        dis_num_int = total_rows_excel
    else:
        dis_num_int = vis_num_int
    
    excel_page += f"var dis_num_int = {dis_num_int};"
    
    excel_page += """
    function showSamples(button, gse) {
        var tdElement = button.parentNode;
        var buttonElement = tdElement.querySelector("button");
        var sample_tablerow = document.getElementById(gse);

        if (buttonElement.textContent === "⯈") {
            buttonElement.textContent = "⯅";
            sample_tablerow.style.display = "table-row";
            sample_tablerow.style.height = "auto";
        } else {
            buttonElement.textContent = "⯈";
            sample_tablerow.style.display = "none";
        }
        getCurrentDate();
        }

    function showFullText(button) {
    var tdElement = button.parentNode; 
    var buttonElement = tdElement.querySelector("button");
    

    if (tdElement.style.whiteSpace === "normal") {
        tdElement.style.whiteSpace = "nowrap";
        buttonElement.innerHTML = "+";
    } else {
        tdElement.style.whiteSpace = "normal";
        buttonElement.innerHTML = "-";
    }
    }

    function toggleFilterPanel() {
            
        var filterPanel = document.getElementById('filter-panel');
        var filterButton = document.getElementById('OpenFilterPanelButton');
        if (filterPanel.style.display === 'none' || filterPanel.style.display === '') {
        filterPanel.style.display = 'block';
        } else {
        filterPanel.style.display = 'none';
        }
        event.stopPropagation();
    }

    
    function getIndexOfHeadColumn(head, head_column) {

        for (var i = 0; i < head.rows[0].cells.length; i++) {
            var cellText = head.rows[0].cells[i].innerText;
            
            if (cellText === head_column) {
                return i;
            }
        }

    }

    function getCurrentDate() {
        var currentDate = new Date();
        var options = { month: 'short', day: 'numeric', year: 'numeric' };
        var formattedDate = currentDate.toLocaleDateString('en-US', options);
        formattedDate = formattedDate.replace(",", "")

        return formattedDate;
    }

    function getProcessedDate(date_input) {
        date_to_number = {
            "Jan" : 1,
            "Feb" : 2,
            "Mar" : 3,
            "Apr" : 4,
            "May" : 5,
            "Jun" : 6,
            "Jul" : 7,
            "Aug" : 8,
            "Sep" : 9,
            "Oct" : 10,
            "Nov" : 11,
            "Dec" : 12
        }

        return date_to_number[date_input];
    }

    function dateCheckLeft (date_filter, date_td) {


        // yyyy-mm-dd
        dateFilterValues = date_filter.toString().split("-");
        //mmm dd yyyy
        dataTdValues = date_td.split(" ");


        if (parseInt(dateFilterValues[0], 10) < parseInt(dataTdValues[2], 10)) {
            return true;
        }
        else if(parseInt(dateFilterValues[0], 10) === parseInt(dataTdValues[2], 10)) {
            if (parseInt(dateFilterValues[1], 10) < getProcessedDate(dataTdValues[0])) {
                return true;
            }
            else if (parseInt(dateFilterValues[1], 10) === getProcessedDate(dataTdValues[0])) {
                if (parseInt(dateFilterValues[2], 10) <= parseInt(dataTdValues[1], 10)) {
                    return true;
                }
            }
        }
        return false;
    }

    function dateCheckRight (date_filter, date_td) {

        // yyyy-mm-dd
        dateFilterValues = date_filter.toString().split("-");
        //mmm dd yyyy
        dataTdValues = date_td.split(" ");


        if (parseInt(dateFilterValues[0], 10) > parseInt(dataTdValues[2], 10)) {
            return true;
        }
        else if(parseInt(dateFilterValues[0], 10) === parseInt(dataTdValues[2], 10)) {
            if (parseInt(dateFilterValues[1], 10) > getProcessedDate(dataTdValues[0])) {
                return true;
            }
            else if (parseInt(dateFilterValues[1], 10) === getProcessedDate(dataTdValues[0])) {
                if (parseInt(dateFilterValues[2], 10) >= parseInt(dataTdValues[1], 10)) {
                    return true;
                }
            }
        }
        return false;
        
    }

    function dateCheckRange (date_filter_left, date_filter_right, date_td) {


        // yyyy-mm-dd
        dateFilterValues_left = date_filter_left.toString().split("-");
        dateFilterValues_right = date_filter_right.toString().split("-");
        //mmm dd yyyy
        dataTdValues = date_td.split(" ");

        // Check if date_td > date_filter_left
        if (parseInt(dateFilterValues_left[0], 10) > parseInt(dataTdValues[2], 10)) {
            return false;
        }
        else if(parseInt(dateFilterValues_left[0], 10) === parseInt(dataTdValues[2], 10)) {
            if (parseInt(dateFilterValues_left[1], 10) > getProcessedDate(dataTdValues[0])) {
                return false;
            }
            else if (parseInt(dateFilterValues_left[1], 10) === getProcessedDate(dataTdValues[0])) {
                if (parseInt(dateFilterValues_left[2], 10) > parseInt(dataTdValues[1], 10)) {
                    return false;
                }
            }
        }

        // Check if date_td < date_filter_right
        if (parseInt(dateFilterValues_right[0], 10) < parseInt(dataTdValues[2], 10)) {
            return false;
        }
        else if(parseInt(dateFilterValues_right[0], 10) === parseInt(dataTdValues[2], 10)) {
            if (parseInt(dateFilterValues_right[1], 10) < getProcessedDate(dataTdValues[0])) {
                return false;
            }
            else if (parseInt(dateFilterValues_right[1], 10) === getProcessedDate(dataTdValues[0])) {
                if (parseInt(dateFilterValues_right[2], 10) < parseInt(dataTdValues[1], 10)) {
                    return false;
                }
            }
        }

        return true;
    }

    function check_reg_for_td(txtValue, reg_array) {

        next_and = false;
        next_or = false;
        next_not = false;
        first_entry = true;
        skip_next = false;

        overall_statisfied = true;

        for (var i = 0; i < reg_array.length; i++) {
            reg_array[i] = reg_array[i].trim();
            if (first_entry) {
                if (reg_array[i].startsWith("NOT")) {
                    if (txtValue.toUpperCase().indexOf(reg_array[i].slice(4).toUpperCase()) != -1) {
                        overall_statisfied = false;
                    }
                }
                else if (txtValue.toUpperCase().indexOf(reg_array[i].toUpperCase()) === -1) {
                    overall_statisfied = false;
                }
                first_entry = false;
            }
            else if (skip_next) {
                skip_next = false;
                continue;
            }
            else if (reg_array[i] === 'AND') {
                if (!overall_statisfied) {
                    skip_next = true;
                    continue;
                }
                next_and = true;
            }
            else if (reg_array[i] === 'OR'){
                if (overall_statisfied) {
                    skip_next = true;
                    continue;
                }
                next_or = true;
            }
            else {
                if (next_and) {
                    if (reg_array[i].startsWith("NOT")) {
                        if (txtValue.toUpperCase().indexOf(reg_array[i].slice(4).toUpperCase()) != -1) {
                            overall_statisfied = false;
                        }
                    }
                    else if (txtValue.toUpperCase().indexOf(reg_array[i].toUpperCase()) === -1) {
                        overall_statisfied = false;
                    }
                    next_and = false;
                }
                else if (next_or) {
                    if (reg_array[i].startsWith("NOT")) {
                        if (txtValue.toUpperCase().indexOf(reg_array[i].slice(4).toUpperCase()) === -1) {
                            overall_statisfied = true;
                        }
                    } 
                    else if (txtValue.toUpperCase().indexOf(reg_array[i].toUpperCase()) != -1) {
                        overall_statisfied = true;
                    }
                    next_or = false;
                }
            }
        }
        return overall_statisfied;
    }

    function closeAllSamples() {
        hiddenTableRows = document.getElementsByClassName("hidden_table_row");
        // Close all samples
        for(var i = 0; i < hiddenTableRows.length; i++) {
            hiddenTableRows[i].style.display = "none";
        }

        // Switch all sample buttons to standard

        showSamplesButtons = document.getElementsByClassName("show_sample_button");

        for(var i = 0; i < showSamplesButtons.length; i++) {

            showSamplesButtons[i].textContent = "⯈";
        }
    }

    /////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
    
    function submitChosenFilter() {

        closeAllSamples();

        var isAnyTerm = true;
        var isSeriesTerm = true;
        var isSampleTerm = true;

        var series_inputs = document.getElementsByClassName("input-for-filter");
        var sample_inputs = document.getElementsByClassName("input-sample-filter");
        var anyTermElement = document.getElementById("AnyTermFilter");

        var mainTableRows = document.getElementsByClassName("MainTable_rows");
        var subTables = document.getElementsByClassName("sampleTable");

        var mainTableHead = document.getElementById("MainTableHead");
        var mainThElements = mainTableHead.querySelectorAll('th');
        var subTableHeads = document.getElementsByClassName("SubTableHead");
        var subTableHead = subTableHeads[0];
        var subThElements = subTableHead.querySelectorAll('th');


        var checkboxes_virus = document.getElementsByClassName("virus_checkboxes");

        var gsm_column_index = getIndexOfHeadColumn(subTableHead, "Sample_geo_accession");
        var virus_column_index = getIndexOfHeadColumn(mainTableHead, "Virus");

        div_series = document.getElementById("SeriesFilterDiv");
        div_samples = document.getElementById("SampleFilterDiv");
        div_anyTerm = document.getElementById("AnyTermFilterDiv");

        const pattern = /\\b(AND|OR)\\b/g;

        if (div_series.style.display === "none") {
            isSeriesTerm = false;
        }
        if (div_samples.style.display === "none") {
            isSampleTerm = false;
        }
        if (div_anyTerm.style.display === "none") {
            isAnyTerm = false;
        }

        // Series term
        if (isSeriesTerm) {

            var reg_dic = {}

            var firstDate = true;

            for (var i = 0; i < series_inputs.length; i++) {

                input_id = series_inputs[i].id.split(":")[1];
                var reg_splitted = series_inputs[i].value.split(pattern);
                reg_dic[input_id] = reg_splitted.filter(item => item.trim() !== '');
            }
            
            var matching_counter = 1;
            for (i = 0; i < mainTableRows.length; i++) {
                var rowShouldBeDisplayed = true; 
                var rowContainsVirus = false;
                var anyIsChecked = false;

                tds = mainTableRows[i].getElementsByTagName("td");

                if(tds[virus_column_index]) {
                
                    // Control if correct viruses are checked
                    for (var j = 0; j < checkboxes_virus.length; j++) {
                        checkbox_name = ""
                        if (checkboxes_virus[j].checked) {
                            checkbox_name = checkboxes_virus[j].name.slice(0, -3);
                            anyIsChecked = true;
                        }
                        else{
                            continue;
                        }
                        if (tds[virus_column_index].textContent.indexOf(checkbox_name) > -1) {
                            rowContainsVirus = true;
                            break;
                        }
                    }
                    if (!rowContainsVirus && anyIsChecked) {
                        mainTableRows[i].style.display = "none";
                        continue;
                    }
                }
                
                for (j = 0; j < tds.length; j++) {
                    td = tds[j];
                    if (td) {
                        txtValue = td.textContent || td.innerText;
                        if (mainThElements[j]){
                            current_column = mainThElements[j].textContent;

                        if (current_column in reg_dic && reg_dic[current_column].length > 0 && !check_reg_for_td(txtValue, reg_dic[current_column])) {
                            rowShouldBeDisplayed = false;
                            break;
                        }

                        }
                    }
                }
                if (rowShouldBeDisplayed) {
                    mainTableRows[i].setAttribute("filter_number", matching_counter);
                    if (matching_counter < dis_num_int+1) {
                            mainTableRows[i].style.display = "table-row";
                    }
                    else {
                        mainTableRows[i].style.display = "none";
                    }
                    matching_counter = matching_counter + 1;
                } else {
                    mainTableRows[i].style.display = "none";
                }
            }
        }
        // Sample term
         else if (isSampleTerm) {

            var reg_dic = {}

            for (var i = 0; i < sample_inputs.length; i++) {

                input_id = sample_inputs[i].id.split(":")[1];
                var reg_splitted = sample_inputs[i].value.split(pattern);
                reg_dic[input_id] = reg_splitted.filter(item => item.trim() !== '');

            }

            if(reg_dic["Sample_characteristics"].length > 1) {
                alert("Conditional filtering isn't possible for sample characteristics.");
                return;
            }
            
        matching_counter = 1;

        for (var k = 0; k < subTables.length; k++) {
            
        tbody_subTable = subTables[k].getElementsByTagName("tbody")[0];

        tr = tbody_subTable.getElementsByTagName("tr");

        var currentSubTableHead = subTables[k].querySelector("thead");
        var currentSubThElements = currentSubTableHead.getElementsByTagName("th");

        for (i = 0; i < tr.length; i++) {
            var rowShouldBeDisplayed = true; 
            var rowDueToCharacteristic = false
            var rowContainsVirus = false;

            tds = tr[i].getElementsByTagName("td");

            for (j = 0; j < tds.length; j++) {
                td = tds[j];
                if (td) {

                    txtValue = td.textContent || td.innerText;
                    
                    if (currentSubThElements[j]){

                        current_column = currentSubThElements[j].textContent;

                    if (current_column in reg_dic && reg_dic[current_column].length > 0 && !check_reg_for_td(txtValue, reg_dic[current_column])){
                        rowShouldBeDisplayed = false;              
                        break;
                    }
                    else if(!(current_column in reg_dic) && reg_dic["Sample_characteristics"].length > 0) {

                        filterInput = reg_dic["Sample_characteristics"][0].toUpperCase().trim()

                        if(txtValue.toUpperCase().indexOf(filterInput) === -1 && !rowDueToCharacteristic) {
                            rowDueToCharacteristic = false;
                        }
                        else {
                            rowDueToCharacteristic = true;
                        }
                    }
                    }
                }
            }

            if(!rowDueToCharacteristic && reg_dic["Sample_characteristics"].length > 0) {
                rowShouldBeDisplayed = false;
            }
            // Virus verification
            if (rowShouldBeDisplayed){

                var anyIsChecked = false;
                corresponding_gse = tr[i].closest("table").id.split("_")[1];
                upper_gse_row = document.getElementById(corresponding_gse + "_MainTable");
                upper_tr = document.getElementById(corresponding_gse + "_tr");
                

                for (var j = 0; j < checkboxes_virus.length; j++) {
                    checkbox_name = ""
                    if (checkboxes_virus[j].checked) {
                        checkbox_name = checkboxes_virus[j].name.slice(0, -3);
                        anyIsChecked = true;
                    }
                    else{
                        continue;
                    }
                    if (upper_gse_row.getElementsByTagName("td")[virus_column_index].textContent.indexOf(checkbox_name) > -1) {
                        rowContainsVirus = true;
                        break;
                    }
                }
                if (!rowContainsVirus && anyIsChecked) {
                    upper_tr.style.display = "none";
                    upper_gse_row.style.display = "none";
                    continue;
                }
            }

            if (rowShouldBeDisplayed) {
                corresponding_gse = tr[i].closest("table").id.split("_")[1];
                upper_tr = document.getElementById(corresponding_gse + "_tr");
                upper_gse_row = document.getElementById(corresponding_gse + "_MainTable");
                upper_gse_row.setAttribute("filter_number", matching_counter);

                if (matching_counter < dis_num_int+1) {
                    upper_gse_row.style.display = "table-row";
                    upper_tr.style.display = "table-row";
                    show_button = document.getElementById(corresponding_gse + "_showSamplesButton");
                    show_button.textContent = "⯅";
                }
                else {
                    upper_gse_row.style.display = "none";
                    upper_tr.style.display = "none";
                }
                matching_counter = matching_counter + 1;
                break;
                
            } else {
                corresponding_gse = tr[i].closest("table").id.split("_")[1];
                upper_tr = document.getElementById(corresponding_gse + "_tr");
                upper_tr.style.display = "none";
                upper_gse_row = document.getElementById(corresponding_gse + "_MainTable");
                upper_gse_row.style.display = "none";
            }
        }
        }
        }
        // Any term
        else if (isAnyTerm) {

            filter = anyTermElement.value;

            reg_dic = {}
            var reg_splitted = filter.split(pattern);
            reg_splitted = reg_splitted.filter(item => item.trim() !== '');
            
            if (reg_splitted.length > 1) {
                    alert("You can't use conditional filtering for this filter option!");
                    return;
                }

            matching_counter = 1;
            for (i = 0; i < mainTableRows.length; i++) {
                var rowShouldBeDisplayed = false; 
                var rowContainsVirus = false;
                var anyIsChecked = false;
                
                tds = mainTableRows[i].getElementsByTagName("td");
                gse = mainTableRows[i].id.split("_")[0];
                var upper_tr = document.getElementById(gse + "_tr");
                if(upper_tr === null) {
                                mainTableRows[i].style.display = "none";
                                continue;
                }
                if (tds[0]) {
                    
                    // Virus verification
                            
                    for (var j = 0; j < checkboxes_virus.length; j++) {
                        checkbox_name = ""
                        if (checkboxes_virus[j].checked) {
                            checkbox_name = checkboxes_virus[j].name.slice(0, -3);
                            anyIsChecked = true;
                        }
                        else{
                            continue;
                        }
                        if (mainTableRows[i].getElementsByTagName("td")[virus_column_index].textContent.indexOf(checkbox_name) > -1) {
                            rowContainsVirus = true;
                            break;
                        }
                    }
                    if (!rowContainsVirus && anyIsChecked) {
                        mainTableRows[i].style.display = "none";
                        continue;
                    }
                
                    if (check_reg_for_tr(tds, reg_splitted) | reg_splitted.length === 0) {
                        rowShouldBeDisplayed = true;
                    }
                    else {
                        smplTable = document.getElementById("sampleTable_" + gse);
                        trs_sample = smplTable.getElementsByTagName("tr");
                        
                        for (var k = 0; k < trs_sample.length; k++) {
                            tds_sample = trs_sample[k].getElementsByTagName("td");
                            if (check_reg_for_tr(tds_sample, reg_splitted)) {
                                rowShouldBeDisplayed = true;
                                break;
                            }
                        } 
                    }
                        
                    if (rowShouldBeDisplayed) {
                        mainTableRows[i].setAttribute("filter_number", matching_counter);
                        if (matching_counter < dis_num_int+1) {
                            mainTableRows[i].style.display = "table-row";
                        }
                        else {
                            mainTableRows[i].style.display = "none";
                        }
                        matching_counter = matching_counter + 1;
                    }
                    else {
                        mainTableRows[i].style.display = "none";
                    }
                }
            
            
            }
        }
        var filterPanel = document.getElementById('filter-panel');
        filterPanel.style.display = 'none';
        
        var tableHeadMainRow = mainTableHead.getElementsByTagName("tr")[0];
        tableHeadMainRow.style.display = "table-row";

        for(var i = 0; i < subTableHeads.length; i++) {
            var subTableHeadRow = subTableHeads[i].getElementsByTagName("tr")[0];
            subTableHeadRow.style.display = "table-row";
        }
        
        var leftJumpButton = document.getElementById("left_jump");
        var rightJumpButton = document.getElementById("right_jump");

        leftJumpButton.disabled = true;

        matching_counter = matching_counter - 1;

        if (matching_counter < dis_num_int) {
            end_index = matching_counter;
            rightJumpButton.disabled = true;
        }
        else {
            end_index = dis_num_int; 
            rightJumpButton.disabled = false;
        }

        leftJumpButton.setAttribute("isFilter", "true");
        rightJumpButton.setAttribute("isFilter", "true");

        if(matching_counter === 0) {
            displayNumberResults(-1, -1, -1, true);
            leftJumpButton.setAttribute("start_number", "0");
            leftJumpButton.setAttribute("end_number", "0");
            leftJumpButton.setAttribute("total_number_filter", "0");

            rightJumpButton.setAttribute("start_number", "0");
            rightJumpButton.setAttribute("end_number", "0");
            rightJumpButton.setAttribute("total_number_filter", "0");
        }
        else {
            displayNumberResults(1, end_index, matching_counter, false);
            leftJumpButton.setAttribute("start_number", "1");
            leftJumpButton.setAttribute("end_number", end_index);
            leftJumpButton.setAttribute("total_number_filter", matching_counter);

            rightJumpButton.setAttribute("start_number", "1");
            rightJumpButton.setAttribute("end_number", end_index);
            rightJumpButton.setAttribute("total_number_filter", matching_counter);
        }
        }

        /////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

    function check_reg_for_tr(tds, reg_array) {

        next_and = false;
        next_or = false;
        next_not = false;
        first_entry = true;
        skip_next = false;

        overall_statisfied = false;

        for(var i = 0; i < reg_array.length; i++) {
            reg_array[i] = reg_array[i].trim();
            if (skip_next) {
                skip_next = false;
                continue;
            }
            else if (reg_array[i] === 'AND') {
                if (!overall_statisfied) {
                    skip_next = true;
                    continue;
                }
                next_and = true;
                continue;
            }
            else if (reg_array[i] === 'OR'){
                if (overall_statisfied) {
                    skip_next = true;
                    continue;
                }
                next_or = true;
                continue;
            }
            for(var j = 0; j < tds.length; j++) {
                if(tds[j]) {
                txtValue = tds[j].textContent;
            
                if (first_entry) {
                    if (reg_array[i].startsWith("NOT")) {
                        
                        if (txtValue.toUpperCase().indexOf(reg_array[i].slice(4).toUpperCase()) != -1) {
                            overall_statisfied = false;
                            break;
                        }
                        else {
                            overall_statisfied = true;
                        }
                    }
                    else if (txtValue.toUpperCase().indexOf(reg_array[i].toUpperCase()) != -1) {
                        overall_statisfied = true;
                        break;
                    }
                    else {
                        overall_statisfied = false;
                    }
            }
            else {
                if (next_and) {
                    if (reg_array[i].startsWith("NOT")) {
                        if (txtValue.toUpperCase().indexOf(reg_array[i].slice(4).toUpperCase()) != -1) {
                            
                            overall_statisfied = false;
                            break;
                        }
                        else {
                            overall_statisfied = true;
                        }
                    }
                    else if (txtValue.toUpperCase().indexOf(reg_array[i].toUpperCase()) != -1) {
                        overall_statisfied = true;
                        break;
                    }
                    else {
                        overall_statisfied = false;
                    }
                }
                else if (next_or) {
                    if (reg_array[i].startsWith("NOT")) {
                        if (txtValue.toUpperCase().indexOf(reg_array[i].slice(4).toUpperCase()) != -1) {
                            overall_statisfied = false;
                            break;
                        }
                        else {
                            overall_statisfied = true;
                        }

                    } 
                    else if (txtValue.toUpperCase().indexOf(reg_array[i].toUpperCase()) != -1) {
                        overall_statisfied = true;
                        break;
                    }
                    else {
                        overall_statisfied = false;
                    }
                }
            }
        }
        }
        if (first_entry) {
            first_entry = false;
        }
        if (next_or) {
            next_or = false;
        }
        if (next_and) {
            next_and = false;
        }
        }

        return overall_statisfied;
    }
    function resetFilter() {
        
        var anyFilter = document.getElementById("AnyTermFilter");
        anyFilter.value = "";
        anyFilter.disabled = false;
        
        var series_inputs = document.getElementsByClassName("input-for-filter");
        
        for (var i = 0; i < series_inputs.length; i++) {
            series_inputs[i].value = "";
        }
        
        var sample_inputs = document.getElementsByClassName("input-sample-filter");
        for (var i = 0; i < sample_inputs.length; i++) {
            sample_inputs[i].value = "";
        }

        var date_inuts = document.getElementsByClassName("input_dates");
        for (var i = 0; i < date_inuts.length; i++) {
            date_inuts[i].value = "";
        }

        var date_sample_inuts = document.getElementsByClassName("input_sample_dates");
        for (var i = 0; i < date_sample_inuts.length; i++) {
            date_sample_inuts[i].value = "";
        }

        var virus_cbs = document.getElementsByClassName("virus_checkboxes");
        for (var i = 0; i < virus_cbs.length; i++) {
            virus_cbs[i].checked = false;
        }
        
        caution_symbol = document.getElementById("cautionSymbol");
        caution_symbol.classList.remove('active');
        
        var leftJumpButton = document.getElementById("left_jump");
        var rightJumpButton = document.getElementById("right_jump");

        leftJumpButton.disabled = true;
        rightJumpButton.disabled = false;

        totalNumber = parseInt(leftJumpButton.getAttribute("total_number"));
        isFilter = leftJumpButton.getAttribute("isFilter");
        
        if (isFilter === "false") {
            start = parseInt(leftJumpButton.getAttribute("start_number"));
            end = parseInt(leftJumpButton.getAttribute("end_number"));
            
            for (var i = start; i < end+1; i++) {
            search_string = 'tr[overall_number="' + i + '"]'; 
            current_element = document.querySelector(search_string);
            current_element.style.display = "none";
            }
        }

        leftJumpButton.setAttribute("total_number_filter", "-1");
        leftJumpButton.setAttribute("isFilter", "false");
        leftJumpButton.setAttribute("start_number", "1");
        leftJumpButton.setAttribute("end_number", dis_num_int.toString());

        rightJumpButton.setAttribute("total_number_filter", "-1");
        rightJumpButton.setAttribute("isFilter", "false");
        rightJumpButton.setAttribute("start_number", "1");
        rightJumpButton.setAttribute("end_number", dis_num_int.toString());

        var filtered_trs = document.querySelectorAll('tr[filter_number]:not([filter_number="-1"])');

        for (var i = 0; i < filtered_trs.length; i++) {
            filtered_trs[i].style.display = "none";
            filtered_trs[i].setAttribute("filter_number", "-1");
        }

        for (var i = 1; i < dis_num_int+1; i++) {
            search_string = 'tr[overall_number="' + i + '"]'; 
            current_element = document.querySelector(search_string);
            current_element.style.display = "table-row";
        }
    
    closeAllSamples();
    displayNumberResults(1, dis_num_int, totalNumber, false);
    }

    function fillSecondDate(date_filter_option) {

        date_input_id_1 = "specificFilter:" + date_filter_option + "#1";
        date_input_id_2 = "specificFilter:" + date_filter_option + "#2";

        date_input_1 = document.getElementById(date_input_id_1);
        date_input_2 = document.getElementById(date_input_id_2);

        date_1 = date_input_1.value;

        date_input_2.value = date_1;
    }
    
    function downloadTableData() {

        var mainTableHead = document.getElementById("MainTableHead");
        var mainThElements = mainTableHead.querySelectorAll('th');
        
        var subTableHeads = document.getElementsByClassName("SubTableHead");
        var subTableHead = subTableHeads[0];
        var subThElements = subTableHead.querySelectorAll('th');

        var mainTableRows = document.getElementsByClassName("MainTable_rows");
        var gse_column_index = getIndexOfHeadColumn(mainTableHead, "Series_geo_accession");

        var series_file_content = "";
        var sample_file_content = "";
        
        characteristic_columns = document.getElementsByClassName("characteristicHead");
        characteristic_columns = Array.from(characteristic_columns);
        
        for(var i = 0; i < mainThElements.length; i++) {
            if(mainThElements[i]){
                series_file_content += mainThElements[i].textContent;
                series_file_content += "\\t"
            }
        }
        
        series_file_content = series_file_content.replace(/\t$/, '');
        series_file_content += "\\n";
        
        for(var j = 0; j < subThElements.length; j++) {
            if(subThElements[j] && characteristic_columns.indexOf(subThElements[j]) === -1){
                sample_file_content += subThElements[j].textContent;
                sample_file_content += "\\t"
            }
        } 
            
        sample_file_content += "Sample_characteristics\\n"
        
        

        var filtered_trs = document.querySelectorAll('tr[filter_number]:not([filter_number="-1"])');

        for (var i = 0; i < filtered_trs.length; i++) {
            sample_chars = "";
            tds = filtered_trs[i].getElementsByTagName("td");
            for(var j = 0; j < tds.length; j++) {
                if(tds[0]) {
                    if(tds[j].textContent.startsWith("⯈ ") | tds[j].textContent.startsWith("⯅ ") | tds[j].textContent.startsWith("+ ")) {
                        series_file_content += tds[j].textContent.slice(2);
                        series_file_content += "\\t";
                    }
                    else {
                        series_file_content += tds[j].textContent;
                        series_file_content += "\\t";
                    }
                }
            }
            
            series_file_content += "\\n";

            gse = filtered_trs[i].id.split("_")[0];
            var subTbl = document.getElementById("sampleTable_" + gse);
            
            var currentSampleTableHead = subTbl.querySelector("thead");
            var currentSampleThElements = currentSampleTableHead.getElementsByTagName("th");

            trs_samples = subTbl.getElementsByTagName("tr");
            
            
            for(var j = 0; j < trs_samples.length; j++) {
                tds_samples = trs_samples[j].getElementsByTagName("td");
                for(var k = 0; k < tds_samples.length; k++) {
                    if(tds_samples[0]) {
                        if(characteristic_columns.indexOf(currentSampleThElements[k]) === -1) {
                            if(tds_samples[k].textContent.startsWith("+ ") | tds_samples[k].textContent.startsWith("- ")) {
                                sample_file_content += tds_samples[k].textContent.slice(2);
                                sample_file_content += "\\t";
                            }
                            else {
                                sample_file_content += tds_samples[k].textContent;
                                sample_file_content += "\\t";
                            }
                        }
                        else {
                            if(tds_samples[k].textContent.startsWith("+ ") | tds_samples[k].textContent.startsWith("- ")) {
                                sample_chars += currentSampleThElements[k].textContent + ":" + tds_samples[k].textContent.slice(2) + "; ";
                            }
                            else {
                                sample_chars += currentSampleThElements[k].textContent + ":" + tds_samples[k].textContent + "; ";
                            } 
                        } 
                    }
                }
                sample_file_content += sample_chars;
                sample_chars = "";
                if(tds_samples[0]) {
                    sample_file_content += "\\n"
                }
                
            }
        }
        var blob = new Blob([series_file_content], { type: 'text/plain' });
        var series_file_name = 'Series_output.tsv';
        var a = document.createElement('a');

        a.href = window.URL.createObjectURL(blob);

        a.download = series_file_name;

        document.body.appendChild(a);

        a.click();

        document.body.removeChild(a);
        
        var blob = new Blob([sample_file_content], { type: 'text/plain' });
        var sample_file_name = 'Samples_output.tsv';
        var a = document.createElement('a');

        a.href = window.URL.createObjectURL(blob);

        a.download = sample_file_name;

        document.body.appendChild(a);

        a.click();

        document.body.removeChild(a);
        
        }

    function openNewVirusDiv(virus_category) {
        
        corresponding_virus_div = document.getElementById(virus_category + '_div');
        
        all_virus_divs = document.getElementsByClassName('viruses_divs');
        
        for(var i = 0; i < all_virus_divs.length; i++) {
            all_virus_divs[i].style.display = "none";
        }
        corresponding_virus_div.style.display = "block";
        
        change_virus_button_status(virus_category);
        caution_for_other_virus_divs(virus_category);
    }
    
    function change_virus_button_status(virus_category) {
        corresponding_virus_button = document.getElementById(virus_category + "_open_button");
        all_virus_buttons = document.getElementsByClassName("virus_open_buttons");

        for (var i = 0; i < all_virus_buttons.length; i++) {
            all_virus_buttons[i].classList.remove('active');
        }
        corresponding_virus_button.classList.add('active');
    }

    function caution_for_other_virus_divs(virus_category) {
        
        allVirusDivs = document.getElementsByClassName("viruses_divs");
        corresponding_virus_div = document.getElementById(virus_category + '_div');
        other_cbs_checked = false;
        caution_symbol = document.getElementById("cautionSymbol");
        caution_symbol.classList.remove('active');
        for(var i = 0; i < allVirusDivs.length; i++) {
            if(allVirusDivs[i] !== corresponding_virus_div ) {
                var currentVirusDiv = document.getElementById(allVirusDivs[i].id);
                var currentCheckboxes = currentVirusDiv.querySelectorAll('input[type="checkbox"]');
                for(var j = 0; j < currentCheckboxes.length; j++) {
                    if(currentCheckboxes[j].checked) {
                        other_cbs_checked = true;
                        break;
                    }
                }
                if(other_cbs_checked) {
                    break;
                }
            }
        }
        if(other_cbs_checked) {
            caution_symbol.classList.add('active');
        }   
    }

    function openNewFilterDivs(filter_name) {
        // filter_id := "Series" or "Sample" or "AnyTerm"
        resetFilter();
        
        filter_divs = document.getElementsByClassName("filterDivs");
        corresponding_filter_div = document.getElementById(filter_name + "FilterDiv");
        
        for(var i = 0; i < filter_divs.length; i++) {
            filter_divs[i].style.display = "none";
        }
        
        corresponding_filter_div.style.display = "block";
        
        change_open_buttons_status(filter_name);
    }
    
    function change_open_buttons_status(filter_name) {
        corresponding_filter_button = document.getElementById("open" + filter_name + "Filter");
        all_filter_buttons = document.getElementsByClassName("openButtons");

        for (var i = 0; i < all_filter_buttons.length; i++) {
            all_filter_buttons[i].classList.remove('active');
        }
        corresponding_filter_button.classList.add('active');
    }
    
    function deleteInput(object_id) {
        input_element = document.getElementById(object_id);
        input_element.value = "";
    }
    
    function displayNumberResults(start_num, end_num, numberTotal, noResults) {
            
            var numberInput = document.getElementById("numberSeries");
            numberInput.style.display = "inline-block";
            if(noResults) {
                numberInput.textContent = "No series were found.";
            }
            else {
                leftJumpButton = document.getElementById("left_jump");
                total_count = parseInt(leftJumpButton.getAttribute("total_number"));
                if(total_count === dis_num_int) {
                    numberInput.textContent = "Displaying series " + end_num + "/" + total_count;
                }
                else {
                    numberInput.textContent = "Series " + start_num + "-" + end_num + "/" + numberTotal;
                }
            }  
        }
        
         function nextLeftSamples() {
             
             closeAllSamples();

            leftJumpButton = document.getElementById("left_jump");
            rightJumpButton = document.getElementById("right_jump");

            leftJumpButton.disabled = false;
            rightJumpButton.disabled = false;

            start_index = parseInt(leftJumpButton.getAttribute("start_number"));
            end_index = parseInt(leftJumpButton.getAttribute("end_number"));
            total_count = parseInt(leftJumpButton.getAttribute("total_number"));
            total_count_filter = parseInt(leftJumpButton.getAttribute("total_number_filter"));
            
            if(end_index+1 - start_index < dis_num_int) {
                new_start_index = start_index - dis_num_int;
                new_end_index = end_index - (end_index+1 - start_index);
            }
            else {
                new_start_index = start_index - dis_num_int;
                new_end_index = end_index - dis_num_int;
            }

            if(new_start_index <= 1) {
                new_start_index = 1;
                new_end_index = new_start_index + dis_num_int-1;
                leftJumpButton.disabled = true;
            }

            leftJumpButton.setAttribute("start_number", new_start_index);
            leftJumpButton.setAttribute("end_number", new_end_index);

            rightJumpButton.setAttribute("start_number", new_start_index);
            rightJumpButton.setAttribute("end_number", new_end_index);

            isFilter = leftJumpButton.getAttribute("isFilter");

            if (isFilter === "false") {
    
                for(var i = end_index; i > start_index-1; i--) {
                    search_string = 'tr[overall_number="' + i + '"]'; 
                    current_element = document.querySelector(search_string);
                    current_element.style.display = "none";
                }
    
                for(var i = new_end_index; i > new_start_index-1; i--) {
                    search_string = 'tr[overall_number="' + i + '"]'; 
                    current_element = document.querySelector(search_string);
                    current_element.style.display = "table-row";
                }
                displayNumberResults(new_start_index, new_end_index, total_count, false);

            }
            else {
                for(var i = end_index; i > start_index-1; i--) {
                    search_string = 'tr[filter_number="' + i + '"]'; 
                    current_element = document.querySelector(search_string);
                    current_element.style.display = "none";
                }
    
                for(var i = new_end_index; i > new_start_index-1; i--) {
                    search_string = 'tr[filter_number="' + i + '"]'; 
                    current_element = document.querySelector(search_string);
                    current_element.style.display = "table-row";
                }

                displayNumberResults(new_start_index, new_end_index, total_count_filter, false);
            }
            
        }
        
        function nextRightSamples() {
            
            closeAllSamples();
            
            leftJumpButton = document.getElementById("left_jump");
            rightJumpButton = document.getElementById("right_jump");

            leftJumpButton.disabled = false;
            rightJumpButton.disabled = false;

            start_index = parseInt(leftJumpButton.getAttribute("start_number"));
            end_index = parseInt(leftJumpButton.getAttribute("end_number"));
            total_count = parseInt(leftJumpButton.getAttribute("total_number"));
            total_count_filter = parseInt(leftJumpButton.getAttribute("total_number_filter"));
            
            new_start_index = start_index + dis_num_int;
            new_end_index = end_index + dis_num_int;

            isFilter = leftJumpButton.getAttribute("isFilter");

            if (isFilter === "false") {

                if(new_end_index >= total_count) {
                    new_end_index = total_count;
                    //new_start_index = new_end_index - (dis_num_int-1);
                    rightJumpButton.disabled = true;
                }

                leftJumpButton.setAttribute("start_number", new_start_index);
                leftJumpButton.setAttribute("end_number", new_end_index);

                rightJumpButton.setAttribute("start_number", new_start_index);
                rightJumpButton.setAttribute("end_number", new_end_index);

                for(var i = start_index; i < end_index+1; i++) {
                    search_string = 'tr[overall_number="' + i + '"]'; 
                    current_element = document.querySelector(search_string);
                    current_element.style.display = "none";
                }

                for(var i = new_start_index; i < new_end_index+1; i++) {
                    search_string = 'tr[overall_number="' + i + '"]'; 
                    current_element = document.querySelector(search_string);
                    current_element.style.display = "table-row";
                }
                displayNumberResults(new_start_index, new_end_index, total_count, false);
            }
            else {

                if(new_end_index >= total_count_filter) {
                    new_end_index = total_count_filter;
                    //new_start_index = new_end_index - (dis_num_int-1);
                    rightJumpButton.disabled = true;
                }

                leftJumpButton.setAttribute("start_number", new_start_index);
                leftJumpButton.setAttribute("end_number", new_end_index);

                rightJumpButton.setAttribute("start_number", new_start_index);
                rightJumpButton.setAttribute("end_number", new_end_index);

                for(var i = start_index; i < end_index+1; i++) {
                    search_string = 'tr[filter_number="' + i + '"]'; 
                    current_element = document.querySelector(search_string);
                    current_element.style.display = "none";
                }

                for(var i = new_start_index; i < new_end_index+1; i++) {
                    search_string = 'tr[filter_number="' + i + '"]'; 
                    current_element = document.querySelector(search_string);
                    current_element.style.display = "table-row";
                }
                displayNumberResults(new_start_index, new_end_index, total_count_filter, false);
            }
        }
    
    document.addEventListener('click', function(event) {
            var filter_panel = document.getElementById('filter-panel');
            var isClickInsideDiv = filter_panel.contains(event.target);
            if (!isClickInsideDiv && filter_panel.style.display !== "none") {
                filter_panel.style.display = 'none';
            }
        });
        
        document.addEventListener('keyup', function(event) {
            var filter_panel = document.getElementById('filter-panel');
            if (event.keyCode === 13 & filter_panel.style.display !== "none" ) {
                submitChosenFilter();
            }
        });
        
    
    </script>
        <title>DEEP-DV hub</title>
        <style>
            body {
                width: 100vw;
                background: #fff;
            }

            #MainTable {
                width: 100%;
                overflow: auto;
                border-collapse: collapse;
                border: 0;
                border-radius: 8px;
                }

            #MainTableHead th{
                padding: 20px;
                text-align: center;
                background-color: #1f7dac;
                max-width: 200px;
                min-width: 200px;
                max-height: 30px;
                color: #fff;
            }

            #MainTableHead th:first-child {
                border-radius: 8px 0 0 0;
                max-width: 20px;
                min-width: 20px;
            }

            #MainTableHead th:last-child {
                border-radius: 0 8px 0 0;
            }

            .MainTable_rows {
                border-bottom: 1px solid;
                border-color: rgb(104, 102, 102);
            }

            .sampleTable {
                width: 100%;
                overflow: hidden;
                border-collapse: collapse;
                border: 0;
                border-radius: 8px;
            }

            .SubTableHead th {
                padding: 20px;
                text-align: center;
                background-color: #b4ccd8;
                max-width: 200px;
                min-width: 200px;
                max-height: 30px;
                color: black;
            }

            .sampleTable tr{
                border-bottom: 1px solid;
                border-color: rgb(104, 102, 102);
            }
                
            .sampleTable td {
                padding: 20px;
                text-align: center;
                white-space: nowrap; 
                overflow: hidden; 
                text-overflow: ellipsis;
                max-width: 200px;
                min-width: 200px;
                max-height: 30px;
            }

            #MainTable td {
                padding: 20px;
                text-align: center;
                white-space: nowrap; 
                overflow: hidden; 
                text-overflow: ellipsis;
                max-width: 200px;
                min-width: 200px;
                max-height: 30px;
            }

            .top-heading {
                display: flex;
                align-items: center;
                font-family: Tahoma, sans-serif;
                font-size: 36px;
                color: #fff;
                background-color: #1f7dac;
                height: 150px;
                width: 100%;
                border-bottom-left-radius: 15px; 
                border-bottom-right-radius: 15px;
                padding-left: 40px;

            }
    
            .button {
            bottom: 3px; 
            left: 2px; 
            width: 25px;
            background-color: #fff;
            border: 0;
            border-radius: 10px;
            cursor: pointer;
        }
        
        .show_sample_button {
            bottom: 3px; 
            left: 2px; 
            width: 25px;
            background-color: #fff;
            border: 0;
            border-radius: 10px;
            cursor: pointer;
        }

        .hidden_table_row {
            display: none;
        }
        
        #AnyTermFilterDiv {
            display: none;
        }

        #SampleFilterDiv {
            display: none;
        }
        
        #filter-panel {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 400px;
            height: 100%;
            background-color: #b4ccd8;
            padding: 20px;
            box-shadow: -5px 0 5px rgba(0, 0, 0, 0.1);
            overflow-y: auto;
            border-radius: 0 20px 20px 0;
        }

        #OpenFilterPanelButton {
            border-radius: 5px; 
            margin-bottom: 1%;
            margin-left: 3%;
            font-size: 20px;
            background-color: #1f7dac;
            color: #fff;
            border: 0;
            cursor: pointer;
            padding: 10px; 

        }
        
        #OpenFilterPanelButton:hover {
            background-color: gray; 
        }
        
        .input-for-filter {
            margin-bottom: 5px;
            width: 65%;
        }
        
        .input-sample-filter {
            margin-bottom: 5px;
            width: 65%;
        }

        #AnyTermFilter {
            margin-bottom: 5px;
            width: 65%;
        }
        
        .deleteCurrentInput {
            border-radius: 30%;
            background-color: #b4ccd8;
            border: none; 
            margin-left: 5px;
            margin-right: 5px;
            cursor: pointer;
            color: #B22222;
            font-size: 16px;

        }

        #SubmitFilterButton {
            margin-left: 75%;
            background-color: #1f7dac; 
            color: #fff; 
            padding: 10px 20px; 
            font-size: 16px;
            border: none; 
            border-radius: 5px; 
            cursor: pointer; 
            transition: background-color 0.3s ease; 
            margin-top: 30px;
            margin-bottom: 30px;
        }

        #buttonBar {
            overflow: hidden;
            background-color: #b4ccd8;
        }

        .openButtons {
        float: left;
        display: block;
        padding: 15px;
        text-align: center;
        cursor: pointer;
        transition: background-color 0.3s ease;
        background-color: #1f7dac;
        font-size: 16px;
        border: none;
        color: #fff; 
        }

        .openButtons:hover {
            background-color: gray; 
        }
        
        .openButtons.active {
        background-color: #4169E1;
        }

        #SubmitFilterButton:hover {
            background-color: gray;
        }
        
        #DownloadButton:hover {
            background-color: gray;
        }

        #openSeriesFilter {
            border-radius: 20px 0px 0px 20px;
        }

        #openAnyTermFilter {
            border-radius: 0 20px 20px 0;
        }

        #CloseFilterPanelButton {
            background-color: #b4ccd8;
            border: none;
            cursor: pointer;
            border-radius: 5px;
            font-size: 30px;
        }

        #CloseFilterPanelButton:hover {
            background-color: gray; 
        }

        #ResetFilterButton {
            background-color: #b4ccd8;
            border: none;
            cursor: pointer;
            border-radius: 5px;
            font-size: 20px;
            margin-left: 75%;
        }

        #ResetFilterButton:hover {
            background-color: gray;
        }

        .button:hover {
            background-color: gray;
        }
        
        .show_sample_button:hover {
            background-color: gray;
        }
        
        

        .input_dates {
            margin-bottom: 5px;
            width: 28%;
        }
        
        .input_sample_dates {
            margin-bottom: 5px;
            width: 28%;
        }
        
        .information_date_button {
            background-color: #b4ccd8;
            border: none;
            font-size: 20px;
        }
        
        #DownloadButton {
            border-radius: 5px; 
            margin-bottom: 1%;
            margin-left: 3%;
            font-size: 20px;
            background-color: #1f7dac;
            border: none;
            color: #fff;
            padding: 10px;
            cursor: pointer;
            margin-top: 30px;
            margin-bottom: 30px;
        }
        
        .virus_open_buttons {
            float: left;
            display: block;
            padding: 15px;
            text-align: center;
            cursor: pointer;
            transition: background-color 0.3s ease;
            background-color: #1f7dac;
            font-size: 14px;
            border: none;
            color: #fff; 
        }
        
        .virus_open_buttons:hover {
            background-color: gray;
        }
        
        .virus_open_buttons.active {
            background-color: #4169E1;
        }
        
        #virus_bar {
            overflow: hidden;
            background-color: #b4ccd8;
        }
        
        .virus_tds {
            padding: 5px;
        }
        
        .cautionSymbols {
            display: none;
        }
        
        .cautionSymbols.active {
            float: left;
            display: block;
            padding: 9px;
            text-align: center;
            background-color: #b4ccd8;
            font-size: 20px;
            border: none;
            color: red;
            
        }
        
        #numberSeries {
            display: none;
            border-radius: 5px;
            margin-bottom: 1%;
            font-size: 15px;
            background-color: #fff;
            border: 1px solid;
            padding: 10px;
            color: black;
        }
        
        .buttonSpot {
            max-width: 20px;
            min-width: 20px;
        }
        
        .buttonTd{
            max-width: 20px;
            min-width: 20px;
        }


        .menuContentLinks {
            color: #fff;
            text-decoration: none;
            font-family: Tahoma, sans-serif;
            font-size: 20px;
            cursor: pointer;
        }

        #q_and_a_link {
            right: 5%;
            position: absolute;
        }

        #otherWebpage {
            right: 10%;
            position: absolute;
        }

        .menuContentLinks:hover {
            color: gray;
        }
        
        #public_geo_data {
                position: absolute;
                right: 10%;
        }

        #public_sra_data {
            position: absolute;
            right: 17%;
        }
        
        #left_jump {
            margin-left: 3%;
            font-size: 15px;
            background-color: #fff;
            color: black;
            border: none;
            cursor: pointer;
            border-radius: 5px;
        }

        #left_jump:hover{
            background-color: gray;
        }

        #right_jump {
            font-size: 15px;
            background-color: #fff;
            color: black;
            border: none;
            cursor: pointer;
            border-radius: 5px;
        }

        #right_jump:hover{
            background-color: gray;
        }

        #left_jump[disabled]:hover {
            background-color: #fff;
            cursor: default;
        }

        #left_jump[disabled] {
            color: lightgray;
        }

        #right_jump[disabled]:hover {
            background-color: #fff;
            cursor: default;
        }

        #right_jump[disabled] {
            color: lightgray;
        }
    
        </style>
    </head>
    """
    excel_page += f"""
    <body onload="displayNumberResults(1, {dis_num_int}, {total_rows_excel}, false)">
        <div class="top-heading">
        Internal DEEP-DV data
        <a href="question_answer.html" id="q_and_a_link" class="menuContentLinks" target="_blank">Q&A</a> 
    """
    
    if(buildBoth):
        excel_page += '<a href="geoData.html" id="public_geo_data" class="menuContentLinks" target="_blank">GEO data</a>'
        excel_page += '<a href="sraData.html" id="public_sra_data" class="menuContentLinks" target="_blank">SRA data</a>'
    excel_page += f"""
        
        </div><button id="OpenFilterPanelButton" onclick="toggleFilterPanel()">Filter</button>
        <button id="DownloadButton" onclick="downloadTableData()"><b>&#11123;</b> Download</button>
        """
    if vis_num_int == -1:
        excel_page += f"""
            <button id="left_jump" onclick="nextLeftSamples()" start_number = "1" end_number= "{dis_num_int}" total_number = "{total_rows_excel}" isFilter = "false" total_number_filter = "-1" disabled style="display: none;">&laquo; Previous</button>
            <button id="numberSeries" style="margin-left: 3%;">Label not relevant here</button>
            <button id="right_jump" onclick="nextRightSamples()" start_number = "1" end_number= "{dis_num_int}" total_number = "{total_rows_excel}" isFilter = "false" total_number_filter = "-1" disabled style="display: none;">Next &raquo;</button>
            
        """
    else:
        excel_page += f"""
            <button id="left_jump" onclick="nextLeftSamples()" start_number = "1" end_number= "{dis_num_int}" total_number = "{total_rows_excel}" isFilter = "false" total_number_filter = "-1" disabled>&laquo; Previous</button>
            <button id="numberSeries">Label not relevant here</button>
            <button id="right_jump" onclick="nextRightSamples()" start_number = "1" end_number= "{dis_num_int}" total_number = "{total_rows_excel}" isFilter = "false" total_number_filter = "-1">Next &raquo;</button>
        """
    excel_page += f"""    
        <div id="filter-panel">
            <button id="CloseFilterPanelButton" onclick="toggleFilterPanel()">&larrhk;</button>
            <button id="ResetFilterButton" onclick="resetFilter()">Reset</button>
            <h3>Filter options</h3>
            <div id="buttonBar">
            <button class="openButtons active" id="openSeriesFilter" onclick="openNewFilterDivs(\'Series\')">Series filter</button>
            <button class="openButtons" id="openSampleFilter" onclick="openNewFilterDivs(\'Sample\')">Sample filter</button>
            <button class="openButtons" id="openAnyTermFilter" onclick="openNewFilterDivs(\'AnyTerm\')">Any term</button>
            </div>
            <br>
            <div id="AnyTermFilterDiv" class="filterDivs"><p id=\"paraAnyTerm\">Filter all search terms: </p>
            <input type="text" id="AnyTermFilter" class="AnyTerm" placeholder="Search for any term"><button class="deleteCurrentInput" onclick="deleteInput('AnyTermFilter')">x</button></div>
        """
    excel_page += '<div id="SeriesFilterDiv" class="filterDivs"><p id="paraSeries">Filter series data: </p>'
    for series_col in series_excel_df.columns:
        col_index = series_excel_df.columns.get_loc(series_col)
        excel_page += f'<input type="text" class="input-for-filter" id="specificFilter:{series_col}" placeholder="Search for {str(series_col)}"><button class="deleteCurrentInput" onclick="deleteInput(\'specificFilter:{series_col}\')">x</button><br>'

    excel_page += '</div><div id="SampleFilterDiv" class="filterDivs"><p id="paraSamples">Filter sample data: </p>'
    for sample_col in sample_excel_df.columns:
        col_index = sample_excel_df.columns.get_loc(sample_col)
        excel_page += f'<input type="text" class="input-sample-filter" id="specificFilter:{sample_col}" placeholder="Search for {str(sample_col)}"><button class="deleteCurrentInput" onclick="deleteInput(\'specificFilter:{sample_col}\')">x</button><br>'

    excel_page += '</div><div id="virusFilterDiv"><p id="paraVirus">Choose your virus(es): </p>'

    excel_page += '<div id="virus_bar">'
    for cat in categories_viruses.keys():
        if cat == first_category:
            excel_page += f'<button id="{cat}_open_button" class="virus_open_buttons active" style="border-radius: 20px 0px 0px 20px; " onclick="openNewVirusDiv(\'{cat}\')">{cat}</button>'
        elif cat == last_category:
            excel_page += f'<button id="{cat}_open_button" class="virus_open_buttons" style="border-radius: 0px 20px 20px 0px; " onclick="openNewVirusDiv(\'{cat}\')">{cat}</button>'
        else:
            excel_page += f'<button id="{cat}_open_button" class="virus_open_buttons" onclick="openNewVirusDiv(\'{cat}\')">{cat}</button>'
    excel_page += '<button id="cautionSymbol" class="cautionSymbols" title="Caution! You have checked checkboxes from other virus genus. If you don\'t want to filter for them, uncheck these checkboxes.">&#9888;</button></div>'
    for cat in categories_viruses.keys():
        cb_counter = 0
        if cat == first_category:
            excel_page += f'<div id="{cat}_div" class="viruses_divs" style="display: block;">'
        else:
            excel_page += f'<div id="{cat}_div" class="viruses_divs" style="display: none;">'
        excel_page += f'<table>'
        for v in categories_viruses[cat]:
            if cb_counter%3 == 0:
                excel_page += "<tr>"
            excel_page += f'<td class="virus_tds"><input type="checkbox" class="virus_checkboxes" id="{v}_cb" name="{v}_cb"><label class="virus_labels" for="{v}_cb">{v}</label></td>'
            if cb_counter%3 == 2:
                excel_page += "</tr>"
            cb_counter += 1
        if cb_counter%3 != 2:
            excel_page += f'</tr></table></div>'
        else:
            excel_page += f'</table></div>'
    excel_page += "<br>"

    excel_page += '</div><button id="SubmitFilterButton" onclick="submitChosenFilter()">Filter</button><br><br><br></div><table id="MainTable"><thead id="MainTableHead"><tr>'

    # Add header for geo meta data
    for col in series_excel_df.columns:
        excel_page += f"<th>{col}</th>"

    excel_page += "</tr></thead>"

    # Add meta data

    progress_bar_internal = tqdm(total=total_rows_excel, desc="Processing", unit="iteration")
    visible_counter_excel = 1
    for index, row in series_excel_df.iterrows():
        progress_bar_internal.update(1)
        gse = str(series_excel_df.loc[index, "Series_geo_accession"])
        if visible_counter_excel < dis_num_int+1:
            excel_page += f'<tr id="{gse}_MainTable" class="MainTable_rows" style="display: table-row;" overall_number = "{visible_counter_excel}" filter_number = "-1">'
        else:
            excel_page += f'<tr id="{gse}_MainTable" class="MainTable_rows" style="display: none;" overall_number = "{visible_counter_excel}" filter_number = "-1">'
        visible_counter_excel += 1
        for col in series_excel_df.columns:
            
            val = series_excel_df.at[index, col]
            
            if pandas.isna(val):
                value = "NA"
            else:
                value = str(val)
                
            if len(value) < 25:
                if col == "Series_geo_accession":
                    if value.startswith("GSE"):
                        excel_page += f'<td title="{col}"><button class="show_sample_button" id="{gse}_showSamplesButton" onclick="showSamples({gse}_showSamplesButton, \'{gse}_tr\')">&#11208;</button><a href="https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={value}" target="_blank"> {value}</a></td>'
                    else:
                        excel_page += f'<td title="{col}"><button class="show_sample_button" id="{gse}_showSamplesButton" onclick="showSamples({gse}_showSamplesButton, \'{gse}_tr\')">&#11208;</button> Not public yet</td>'                
                else:
                    excel_page += f'<td title="{col}">{value}</td>'
            elif len(value[0:25].split(" ")) == 1:
                
                split_strings = []
                for i in range(0, len(value), 20):
                    if i == 0:
                        split_strings.append(value[i:i+21])
                    else:
                        split_strings.append(value[i+1:i+21])
                        
                if col == "NCBI_generated_data":
                    excel_page += f'<td title="{col}"><button class="button" id="{col}_{index}_series_showTextButton" onclick="showFullText({col}_{index}_series_showTextButton)">+</button><a href={value} target="_blank"> {" ".join(split_strings)}</a></td>'
                elif col == "ARCHS4":
                    excel_page += f'<td title="{col}"><button class="button" id="{col}_{index}_series_showTextButton" onclick="showFullText({col}_{index}_series_showTextButton)">+</button><a href={value} target="_blank"> {" ".join(split_strings)}</a></td>'                    
                else:
                    excel_page += f'<td title="{col}"><button class="button" id="{col}_{index}_series_showTextButton" onclick="showFullText({col}_{index}_series_showTextButton)">+</button> {" ".join(split_strings)}</td>'
            else:
                excel_page += f'<td title="{col}"><button class="button" id="{col}_{index}_series_showTextButton" onclick="showFullText({col}_{index}_series_showTextButton)">+</button> {value}</td>'
        excel_page += "</tr>"
        
        excel_page += f'<tr id="{gse}_tr" class="hidden_table_row"><td colspan="100%" style="overflow: auto;"><table class="sampleTable" id="sampleTable_{gse}">'
        
        excel_page += '<thead class="SubTableHead"><tr>'
        
        temp_df = sample_excel_df[sample_excel_df["Sample_series_id"].str.contains(gse, case=False, na=False)]
        
        sample_characteristics_column = temp_df['Sample_characteristics']
        
        sample_characteristics = []
        
        for entry in sample_characteristics_column:
            characteristics = str(entry).split("&&")

            for char in characteristics:
                char.strip()
                if char != "" and char != "Na" and char != "NA" and char != "nan" and char != "NaN":
                    sample_characteristics.append(char.split(":")[0].strip())
        
        sample_characteristics = list(set(sample_characteristics))
        sample_characteristics = [s.replace(" ", "_").replace("(", "_").replace(")", "_") for s in sample_characteristics]

        for col_sm in sample_excel_df.columns:
            if col_sm != "Sample_characteristics":
                excel_page += f"<th>{col_sm}</th>"
            else:
                for smpl_chr in sample_characteristics:
                    excel_page += f'<th class="characteristicHead">{smpl_chr}</th>'
    
        excel_page += "</tr></thead>" 
        
        for index_sample, row_sample in temp_df.iterrows():
            excel_page += "<tr>"
            for col_sample in temp_df.columns:
                #value_sample = str(temp_df.at[index_sample, col_sample]) 
                val_sample = temp_df.at[index_sample, col_sample]
                if pandas.isna(val_sample):
                    value_sample = "NA"
                else:
                    value_sample = str(val_sample)
                
                if col_sample == "Sample_characteristics":
                    characteristic_pairs = value_sample.split("&&")
                    characteristic_names_values = {}
                    for char_pair in characteristic_pairs:
                        char_pair.strip()
                        if char_pair != "" and char_pair != "Na" and char_pair != "NA" and char_pair != "nan" and char_pair != "NaN":
                            char_name = char_pair.split(":")[0].strip().replace(" ", "_").replace("(", "_").replace(")", "_")
                            char_value = char_pair.split(":")[1].strip()
                            characteristic_names_values[char_name] = char_value
                    for sample_char in sample_characteristics:
                        split_strings = []
                        if sample_char in characteristic_names_values.keys():
                            if len(characteristic_names_values[sample_char].strip()) < 30:
                                excel_page += f'<td title="{sample_char}" class="characteristicData">{characteristic_names_values[sample_char]}</td>'
                            elif len(characteristic_names_values[sample_char][0:25].split(" ")) == 1:
                                for i in range(0, len(characteristic_names_values[sample_char]), 20):
                                    if i == 0:
                                        split_strings.append(characteristic_names_values[sample_char][i:i+21])
                                    else:
                                        split_strings.append(characteristic_names_values[sample_char][i+1:i+21])
                                excel_page += f'<td title="{sample_char}" class="characteristicData"><button class="button" id="{sample_char}_{index_sample}_sample_showTextButton" onclick="showFullText({sample_char}_{index_sample}_sample_showTextButton)">+</button> {" ".join(split_strings)}</td>'
                            else:
                                excel_page += f'<td title="{sample_char}" class="characteristicData"><button class="button" id="{sample_char}_{index_sample}_sample_showTextButton" onclick="showFullText({sample_char}_{index_sample}_sample_showTextButton)">+</button> {characteristic_names_values[sample_char]}</td>'

                        else:
                            excel_page += f'<td title="{sample_char}" class="characteristicData">NA</td>' 
                    continue

                if len(value_sample) < 25:

                    if col_sample == "Sample_series_id":
                        if value_sample.startswith("GSE"):
                            excel_page += f'<td title="{col_sample}"><a href="https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={value_sample}" target="_blank">{value_sample}</a></td>'
                        else:
                            excel_page += f'<td title="{col_sample}">Not public yet</td>'                            
                    else:
                        excel_page += f'<td title="{col_sample}">{value_sample}</td>'
                elif len(value_sample[0:25].split(" ")) == 1:
                    split_strings = []
                    for i in range(0, len(value_sample), 20):
                        if i == 0:
                            split_strings.append(value_sample[i:i+21])
                        else:
                            split_strings.append(value_sample[i+1:i+21])
                    excel_page += f'<td title="{col_sample}"><button class="button" id="{col_sample}_{index_sample}_sample_showTextButton" onclick="showFullText({col_sample}_{index_sample}_sample_showTextButton)">+</button> {" ".join(split_strings)}</td>'
                else: 
                    excel_page += f'<td title="{col_sample}"><button class="button" id="{col_sample}_{index_sample}_sample_showTextButton" onclick="showFullText({col_sample}_{index_sample}_sample_showTextButton)">+</button> {value_sample}</td>'
                        
            excel_page += "</tr>"
        excel_page += "</table></td></tr>"
    excel_page += "</table>"

    excel_page += """
    </body>
    </html>
    """
    progress_bar_internal.close()
    with open(f"{args.output_dir}/internalData.html", "w") as file:
        file.write(excel_page)
    file.close()
    
    print("Finished build of internalData.hmtl.")
    

##################################### Q&A page #####################################
# Page with questions and answers

question_page = """
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="UTF-8">
    <script src="https://code.jquery.com/jquery-3.6.4.min.js"></script>    
    <script>
    $(document).ready(function(){
      $('.question').click(function(){
        $(this).next('.answer').slideToggle();
      });
    });
    </script>
        <title>DEEP-DV hub</title>
        <style>
        .top-heading {
                display: flex;
                align-items: center;
                font-family: Tahoma, sans-serif;
                font-size: 36px;
                color: #fff;
                background-color: #1f7dac;
                height: 150px;
                width: 100%;
                border-bottom-left-radius: 15px; 
                border-bottom-right-radius: 15px;
                padding-left: 40px;
            }
            
        #questionContainer {
        width: 100%;
        margin: 0;
        text-align: left;
        margin-top: 30px;
        }

        .question {
        background-color: #b4ccd8;
        color: black;
        padding: 10px;
        margin: 5px 0;
        cursor: pointer;
        font-size: 20px;
        }

        .answer {
        display: none;
        background-color: #fff;
        padding: 10px;
        border: 1px solid #ddd;
        font-size: 20px;
    }
        </style>
    </head>
    <body>
    <div class="top-heading">Frequently asked questions</div>
    """

q_and_a_dic = {}    

with open(f"{args.config}/config_questions.txt", "r") as file:
    
    isQuestion = False
    isAnswer = False
    question = ""
    answer = ""
    
    for line in file:
        line = line.strip()
    
        if line.startswith("#") or line == "":
            continue
        elif line.startswith("Q:"):
            if answer != "":
                q_and_a_dic[question] = answer
            isQuestion = True
            question = line.split(":")[1].strip()
        elif isQuestion and not line.startswith("A"):
            question += f" {line}"
        elif line.startswith("A:"):
            isQuestion = False
            isAnswer = True
            answer_line = line.split(":")
            if len(answer_line) > 2:
                answer = " ".join(answer_line[1:])
            else:
                answer = answer_line[1].strip()
        elif isAnswer:
            answer_line = line.split(":")
            if len(answer_line) > 1:
                answer += " "
                answer += " ".join(answer_line)
            else:
                answer += f' {line}'
    
    q_and_a_dic[question] = answer       
    
question_page += '<div id="questionContainer">'    

for question in q_and_a_dic.keys():
    question_page += f'<div class="question">{question}</div>'
    question_page += f'<div class="answer">{q_and_a_dic[question]}</div>'
    
question_page += """
</div>
</body>
</html>
"""

with open(f"{args.output_dir}/question_answer.html", "w") as file:
        file.write(question_page)
file.close()
    