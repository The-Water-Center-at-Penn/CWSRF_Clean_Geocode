import pandas as pd
import numpy as np
import arcpy
from arcgis.gis import GIS
from arcgis.geocoding import geocode
import arcgis
import arcpy
import os

#Columns to keep for origional data
keep_cols = ['Region','State','Borrower Name','State Tracking Number','Type of Assistance','Supplemental Appropriation','Latest Agreement Action', \
      'Initial Agreement Date','Initial Agreement Amount','Date of Latest Agreement Action','Current Agreement Amount','Hardship/Disadvantaged Community?', \
      'Includes Additional Subsidy?','Additional Subsidy Amount','Facility Name','Project Name','Project Description','Population Served by Project','Project Needs Categories','Project Start','Project Completion Date']

#Path to raw data from 
file = r'.\Inputs\CWSRF_Projects_2018to2023.xlsx'

arcpy.env.workspace = r'C:\Users\richa\OneDrive\Documents\Professional\Water Center Work\FOIA_Data_Processing' #Path to arcpy workspace
arcpy.env.overwriteOutput = True #Allow file overwrite

de_basin = os.path.join(arcpy.env.workspace,'gis_data\DE_Basin.shp')

#Read data and just keep columns that are needed
df = pd.read_excel(file)
df = df[keep_cols]

#Add unique ID
df['id'] = df.index

#This section identifies all the different needs Cateogries identified in the Needs column 
split_d = df['Project Needs Categories'].str.split('<br>',expand=True)
df = df.join(split_d)

for col in range(0,4):
    col_name = 'Cat' + str(col + 1)
    df.rename({col:col_name},axis=1,inplace=True)
    col_type_name = col_name + '_Type'
    col_Amount_name = col_name + '_Amount'
    df[col_type_name] = df[col_name].str.split(':',expand=True)[0].str.strip()
    df[col_Amount_name] = df[col_name].str.replace(' : ','-').str.split(':',expand=True)[1].str.replace(',','').str.replace('$','').str.strip().astype(float)
    df.drop(col_name,inplace=True,axis=1)

melted_df = pd.melt(df, id_vars=['id'], value_vars=['Cat1_Type','Cat2_Type','Cat3_Type','Cat4_Type'], var_name='Category_Column', value_name='Category')
melted_df['Amount'] = pd.melt(df, id_vars=['id'], value_vars=['Cat1_Amount','Cat2_Amount','Cat3_Amount','Cat4_Amount'], var_name='Amount_Column', value_name='Amount')['Amount']

pivot_df = melted_df.pivot_table(index='id',columns='Category',values='Amount')
pivot_df.fillna(0,inplace=True)

cols = pivot_df.columns.values

print(pivot_df.info())
print(df.info())

new_cols = []
for c in cols:
    new_c = c.split('-')[1].strip().replace(" ", "_")
    new_cols.append(new_c)

pivot_df.columns = new_cols

final_df = df.merge(pivot_df,on='id',how='left') #Merge in collumns containing the funding amount, with category as the heading
# Delete collumns that are not needed
final_df.drop(['Cat1_Type','Cat1_Amount','Cat2_Type','Cat2_Amount','Cat3_Type','Cat3_Amount','Cat4_Type','Cat4_Amount','Project Needs Categories'],inplace=True,axis=1)

#Calcualate Total funding for Nature Based Solutions
final_df['Nature_Based'] = final_df['Hydromodification/Habitat_Restoration'] + \
    final_df['Land_Conservation'] + final_df['Silviculture'] + \
    final_df['Green_Infrastructure']

#Calculate total gray funding   
final_df['Gray'] = final_df['Current Agreement Amount'] - final_df['Nature_Based']

# Add an array of manual locations to update - set borrowers the geocoder will not recognize to the name of a more reconizable town.

replacements1 = {'Great Lakes Water Authority':'Water Board Building 735 Randolph Street Detroit',
                 'ABC Water and Stormwater District':'8299 Market St, Boardman',
                 'Lorain County Rural Wastewater District':'22898 West Rd. PO Box 158, Wellington',
                 'Greater Johnstown Water Authority':'Johnstown',
                 'Wanaque Valley RSA':'101 Warren Hagstrom Blvd, Wanaque',
                 'Chester Cty Conserv District':'Chester County',
                 'N7832 Lake View Ct, New Lisbon':'N7832 Lake View Ct, New Lisbon',
                 'Shamokin - Coal Township Jt SA':'114 Bridge St, Shamokin',
                 'Southern Clinton County Municipal Utilities Authority':'3671 W Herbison Rd, DeWitt',
                 'Ohio & Lee Water & Sewer Authority':'37414 OH-7, Sardis',
                 'Jackson East Taylor Sewer Authority':' 2603 William Penn Ave, Johnstown',
                 'Lancaster CCD':'Lancaster County',
                 'Lackawanna River Basin Sewer Authority':'101 Boulevard Ave, Throop',
                 'Eastern Snyder County Regional Authority':'870 S Front St, Selinsgrove',
                 'South Monmouth RSA':'1235 18th Ave, Wall Township',
                 'Palestine-Hollansburg JSD':'8314 State Route 121, Greenville',
                 'Heart of the Valley MSD':'801 Thilmany Rd, Kaukauna',
                 'Maple Grove Estates SD':'West Salem',
                 'Lemon Twp. & Tunkhannock Twp. JMSA':'Tunkhannock Township',
                 'Benz Creek Drain Drainage District':'Ann Arbor',
                 'Wyoming Vly San Auth':'179 S Wyoming Ave, Kingston',
                 'Rollin-Woodstock Sanitary Drain Improvements Drainage District':'6100 Sorby Hwy, Addison',
                 'Capital Region Water':'Harrisburg',
                 'Evergreen-Farmington Sanitary Drain Drainage District':'Farmington',
                 'Milk River Intercounty Drain Drainage District':'Grosse Pointe Woods',
                 'Chester CCD':'Chester County',
                 'Wellington City of':'Wellington',
                 'Two Rivers Water Reclamation Authority':'1 Highland Ave, Monmouth Beach',
                 'Lewes Board of Public Works':'107 Franklin Ave, Lewes',
                 'Rutgers, The State Univ. of NJ':'Rutgers, 57 US Highway 1, New Brunswick',
                 'Brockway Area Sewer Authority':'501 Main St, Brockway',
                 'Western Monmouth UA':'103 Pension Rd, Manalapan Township',
                 'Northwestern WSD':'12560 Middleton Pike, Bowling Green',
                 'Somerset Raritan Valley SA':'50 Polhemus Ln, Bridgewater',
                 'Lakengren Water Authority':'24 Lakengren Dr, Eaton',
                 'North Hudson SA':'1600 Adams St, Hoboken',
                 'Tri-Municipal Park':'2400 Upper Brush Valley Rd, Centre Hall',
                 'Millers Creek Ann Arbor Drain Drainage District':'Ann Arbor',
                 'Western Westmoreland MA':'12441 PA-993, North Huntingdon',
                 'Three Lakes SD #1':'6930 W School St Three Lakes',
                 'Passaic Valley SC':'600 Wilson Ave, Newark',
                 'Rahway Valley Sewerage Authority':'1050 E Hazelwood Ave, Rahway',
                 'Blacklick Valley Municipal Authority':'104 1st St, Twin Rocks',
                 'Ashley Village of':'Ashley',
                 'Freedom Sanitary District No. 1':'N4229 Garvey Ave, Kaukauna',
                 'Northwest Bergen Co UA':'30 Wyckoff Ave, Waldwick',
                 'Central Wayne Regional Authority':'574 Bucks Cove Rd, Honesdale',
                 'Swanton Village of':'Swanton',
                 'Sidney Village of':'Sidney',
                 'Pomeroy Village of':'Pomeroy',
                 'Piketon, Village of':'Piketon',
                 'Linden Roselle Sewerage Authority':'5005 S Wood Ave, Linden',
                 'Ottawa Village of':'Ottawa',
                 'Holgate, Village of':'Holgate',
                 'Gratis, village of':'Gratis',
                 'Genoa, Village of':'Genoa',
                 'Carey Village of':'Carey',
                 'Canfield, village of':'Canfield',
                 'Butler Village of':'Butler',
                 'Burton Village of':'Burton',
                 'Bremen, Village of':'Bremen',
                 'Beaver, Village of':'Beaver',
                 'Ashley Village of':'Ashley',
                 'Huron River Green Infrastructure Drainage District':'Ann Arbor',
                 'Northeast Ohio Regional Sewer District':'3900 Euclid Ave, Cleveland',
                 'Ohio City Village of':'Ohio City'}

# Handle Removing things from the borrower name that are not part of the "location". Need a town, county, or city name to geocode. 
# This is a dictinoary of specific text to remove. I figured this out by manually going through the data and finding things that are not part a geogrphiac location.
replacements2 = {'MUA':'',
                'Sanitary District #1':'',
                'SD #1':'',
                'General Authority of the ':'',
                ', Charter Township of':'',
                'Water and Sewer District':'',
                'Regional S.A.':'',
                'Interceptor Drain Drainage District':'',
                'Combined General Health District':'',
                'Township Municipal Services Authority':'',
                'Area Water and Sewer Authority':'',
                'Municipal Water and Sewer Authority':'',
                'Water and Sewer Authority':'',
                'Wastewater Treatment District':'',
                'Regional Sewer District':'',
                'Area Sewer Authority':'',
                'Regional Sewer Authority':'',
                'Joint Municipal Authority':'',
                'Madison County/':'',
                'Reg SA':'',
                'District Board of Health':'',
                'Drain Drainage District':'',
                'Municipal Sewer Authority':'',
                'Stormwater Authority of the ':'',
                'Area Joint Sewer Authority':'',
                'Regional Authority':'',
                'Municipal Utilities Authority':'',
                'Sanitary Authority':'',
                'Sewer District':'',
                'Department Health':'',
                'Board of Health':'',
                'Municipality of':'',
                'Municipal Authority':'',
                'Sanitation Authority':'',
                'Water Supply Authority':'',
                'Combined Health District':'',
                'Rail Trail Authority':'',
                'Community Utilities Authority':'',
                'MUNICIPAL AUTHORITY':'',
                'Consolidated':'',
                'Board of Health':'',
                'Public Health':'',
                'County Commissioners':'',
                'General Health District':'',
                'Stormwater Authority':'',
                'U.A.':'',
                ' Co UA':'',
                'MSD':'',
                'Bayshore Outfall Authority':'',
                'Sanitary District':'',
                'Green Infrastructure Drainage District':'',
                'Redevelopment Authority':'',
                'Madison-Chatham Joint Meeting - ':'',
                'District Board of Health':'',
                'Department of Health':'',
                'Soil and Water Conservation District':'',
                'Public Health':'',
                'Conservation District':'',
                'Department of Health':'',
                'Sanitary District No. 1':'',
                'Storm Water Authority':'',
                'Water Authority':'',
                'Sanitary District':'',
                'MUNICIPAL AUTH':'',
                'Health Department':'',
                'Utility Authority':'',
                'Georges Joint Municipal Authority':'',
                'Sewerage Authority':'',
                'IA':'',
                'SC':'',
                'WRA':'',
                'UA':'',
                ', City':'',
                'JMEUC':'',
                'Sewerage Commission':'',
                'Sewer Authority':'',
                'RSA':'',
                'Borough':'',
                'Sewer Authority (CSO)':'',
                '(CSO)':'',
                'SC':'',
                'Utilities Authority':'',
                'SA':'',
                'Essex Union Joint Meeting':'',
                ' of':'',
                'Health District':'',
                'Council':''}

final_df['Location'] = final_df['Borrower Name']

for string, replacement in replacements1.items():
    final_df['Location'] = final_df['Location'].str.replace(string,replacement)

for string, replacement in replacements2.items():
    final_df['Location'] = final_df['Location'].str.replace(string,replacement)

final_df['Location'] = final_df['Location'].str.strip()

final_df.loc[final_df['Borrower Name'] == 'New Jersey Water Supply Authority', 'Location'] = final_df['Facility Name']

final_df['Location_full'] = final_df['Location'] + ', ' + final_df['State'] + ', USA'

#Remove special characters from column names and reduce column name length to 64 characters, geodatabase column names must be less than 64 characters.
final_df.columns = final_df.columns.str.replace(' ','_').str.replace('/','_').str.replace('?','')
final_df.columns = final_df.columns.str[:64]
print(final_df.info())
# Connect to your ArcGIS Online account
gis = GIS("home")

# Geocode Data
for index, row in final_df.iterrows():
    geocode_result = geocode(row['Location_full'])[0]
    print(geocode_result)
    if geocode_result:
        final_df.at[index, 'location_final'] = geocode_result['attributes']['Match_addr']
        final_df.at[index, 'Latitude'] = geocode_result['location']['y']
        final_df.at[index, 'Longitude'] = geocode_result['location']['x']
        final_df.at[index, 'score'] = geocode_result['score']

final_df.drop(['Location_full','Location'],axis=1,inplace=True)

# Output df for just projects in Great Lakes Region
great_lakes_df = final_df[final_df['State'].isin(['Ohio','Michigan','Wisconsin'])]
great_lakes_df.to_excel(r'Geocoded_Data\Great_Lakes.xlsx',index=False)

#This section of code intersects projects in the Delaware River Basin with the Basin and flags projects that are located in the Basin
de_river_df = final_df[final_df['State'].isin(['Delaware','New Jersey','Pennsylvania'])]
de_river_df.to_excel(r'Geocoded_Data\De_river_states.xlsx',index=False)

output_fc = os.path.join('memory','de_projects')

arcpy.management.XYTableToPoint(in_table=r".\Geocoded_Data\De_river_states.xlsx\Sheet1$",
                                out_feature_class=output_fc,
                                x_field="Longitude",
                                y_field="Latitude")

arcpy.analysis.SpatialJoin(output_fc, de_basin, r'memory\test')

sdf = pd.DataFrame.spatial.from_featureclass(r'memory\test')

sdf.loc[sdf['Join_Count'] == 1, 'Basin'] = 'Yes'

sdf.drop(['OBJECTID','Shape_Leng','Shape_Area','SHAPE','Join_Count'],inplace=True,axis=1)

sdf.to_excel('Geocoded_Data\De_river_states.xlsx',index=False)

print('Script Complete')
