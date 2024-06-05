import pandas as pd
from arcgis.features import GeoAccessor
import os

'''
This script is used to aggregated geocoded CWSRF data by geographic location, and calculate funding by location. This script ouputs a featureclass.
The included collumns in the feature class include:
    1) Latitude and Longitude information and location information.
    2) The Amount of funding for Green Infrastructure, Siliviculture, Land Conservation, and Hydromodification/Habitat_Restoration
    3) Total funding for nature Based Solutions (includes four categories listed above)
    4) Total funding for gray infrastructure (total funding - NBS)
    5) Total funding
    6) Subsidized funding
    7) Number of projects recieving subsized funding
'''

#File Paths to geocoded data created by CWSRF_processing script
Geocoded_Data_GL = r'Geocoded_Data\Great_Lakes.xlsx'
Geocoded_Data_DE = r'Geocoded_Data\DE_River_states.xlsx' 

#File paths to location of Geodatabase where GIS data should be outputed
output_location_GL = r'C:\Users\richa\OneDrive\Documents\Professional\Water Center Work\Great Lakes\EPA_Mapping\Great_Lakes_Mapping.gdb'
output_location_DE = r'C:\Users\richa\OneDrive\Documents\Professional\Water Center Work\Delaware Basin\GIS EJ Mapping\EPA_CWSRF_Mapping\EPA_CWSRF_Mapping.gdb'

#Name of Featureclass to be outpuuted to Geodatabase
output_file_name_GL = 'Great_Lakes_EPA_Mapping'
output_file_name_DE = 'DE_EPA_Mapping'

#Projects to filter out, these projects are not associated with a specific location and thus can not be maps. This was agreed with American Rivers
filter_list = ['NPS Agriculture Program','NPS Septic Loan Program','Septic Program - 2018',\
               'Septic Program - 2019','Septic Program - 2020','Septic Program - 2023','Septic Program - 2022','Septic Program - 2021'\
                'Lyme Emporium Highlands II LLC']

#Collumns to aggregate on, these are the location collumns
agg_columns = ['State','location_final','Latitude','Longitude']

def aggregate_data(input_data,output_location,output_file_name,agg_columns):
    data = pd.read_excel(input_data)
    data = data[~data['Borrower_Name'].isin(filter_list)]
    agg_data = data.groupby(agg_columns)[['Nature_Based','Gray','Additional_Subsidy_Amount']].sum().reset_index()
    subsidy_data = data[data['Includes_Additional_Subsidy'] == 'Yes']
    subsidy_count = subsidy_data.groupby(agg_columns)[['Gray']].count().reset_index().rename({'Gray':'disadvantaged_projects'},axis=1)
    agg_data = agg_data.merge(subsidy_count,how='left',on=agg_columns)
    agg_data['Total'] = agg_data['Nature_Based'] + agg_data['Gray']
    agg_data['Non_Subidized'] = agg_data['Total'] - agg_data['Additional_Subsidy_Amount']
    spatial_df = GeoAccessor.from_xy(agg_data, 'Longitude', 'Latitude')
    output_file_name = os.path.join(output_location,output_file_name)
    spatial_df.spatial.to_featureclass(output_file_name)

aggregate_data(Geocoded_Data_GL,output_location_GL,output_file_name_GL,agg_columns)

aggregate_data(Geocoded_Data_DE,output_location_DE,output_file_name_DE,agg_columns)

print("Script Complete")
