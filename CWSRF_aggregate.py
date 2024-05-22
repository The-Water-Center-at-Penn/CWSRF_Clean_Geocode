import pandas as pd
from arcgis.features import GeoAccessor
import os

Geocoded_Data = r'Geocoded_Data\Great_Lakes.xlsx'

output_location = r'C:\Users\richa\OneDrive\Documents\Professional\Water Center Work\Great Lakes\EPA_Mapping\Great_Lakes_Mapping.gdb'
output_file_name = 'Great_Lakes_EPA_Mapping'

data = pd.read_excel(Geocoded_Data)

filter_list = ['NPS Agriculture Program','NPS Septic Loan Program','Septic Program - 2018',\
               'Septic Program - 2019','Septic Program - 2020','Septic Program - 2023','Septic Program - 2022','Septic Program - 2021'\
                'Lyme Emporium Highlands II LLC']

data = data[~data['Borrower_Name'].isin(filter_list)]

agg_data = data.groupby(['State','location_final','Latitude','Longitude'])[['Green_Infrastructure',\
                        'Silviculture','Land_Conservation','Nature_Based','Gray']].sum().reset_index()

agg_data['Total'] = agg_data['Nature_Based'] + agg_data['Gray']

spatial_df = GeoAccessor.from_xy(agg_data, 'Longitude', 'Latitude')

output_file_name = os.path.join(output_location,output_file_name)

spatial_df.spatial.to_featureclass(output_file_name)

print("Script Complete")
