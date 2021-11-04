import psycopg2
import numpy as np
import pandas as pd
import type_correction as tc
import reconcilation as rec

conn = psycopg2.connect(
    host="codd01.research.northwestern.edu",
    database="postgres",
    user="cpdbstudent",
    password="DataSci4AI")

df_trr_refresh = pd.read_sql_query("select * from trr_trr_refresh", con=conn)
df_trr_weapondischarge_refresh = pd.read_sql_query('select * from trr_weapondischarge_refresh', con=conn)
df_trr_trrstatus_refresh = pd.read_sql_query('select * from trr_trrstatus_refresh', con=conn)
df_trr_trr = pd.read_sql_query("select * from trr_trr", con=conn)
df_data_officer = pd.read_sql_query("select * from data_officer", con=conn)

# Replace 'Redacted' values to None
df_trr_refresh.replace(to_replace = 'Redacted', value = None, inplace = True)
df_trr_weapondischarge_refresh.replace(to_replace = 'Redacted', value = None, inplace = True)
df_trr_trr.replace(to_replace = 'Redacted', value = None, inplace = True)
df_trr_trrstatus_refresh.replace(to_replace = 'Redacted', value = None, inplace = True)

# List with columns by type
trr_boolean_tables = ['officer_on_duty','officer_injured','officer_in_uniform', 'subject_armed','subject_injured', 'subject_alleged_injury',
                      'notify_oemc','notify_district_sergeant', 'notify_op_command','notify_det_division']
trr_boolean_weapon_tables =['firearm_reloaded','sight_used']
trr_integer_tables =['officer_age', 'beat', 'subject_birth_year', 'subject_age', 'officer_birth_year']

"************** TYPE CORRECTION **************"
#Convert booleans
for table in trr_boolean_tables:
    tc.convert_boolean(df_trr_refresh,table)

for table in trr_boolean_weapon_tables:
    tc.convert_boolean(df_trr_weapondischarge_refresh,table)

#Convert integers
for table in trr_integer_tables:
    tc.convert_integer(df_trr_refresh,table)

#Convert timestamp (STILL STRING OUTPUT)
timestamp_created = tc.convert_timestamp(df_trr_refresh,'trr_created')
timestamp_datetime = tc.convert_timestamp(df_trr_refresh,'trr_datetime')
timestamp_status = tc.convert_timestamp(df_trr_trrstatus_refresh,'status_datetime')

#Convert dates
date_trr_app_date = tc.convert_date(df_trr_refresh,'officer_appointed_date')
date_trr_status_app_date = tc.convert_date(df_trr_trrstatus_refresh,'officer_appointed_date')


"************** RECONCILIATION **************"

# Reconciliation race
rec.reconcile_subject_race(df_trr_refresh,'subject_race')
rec.reconcile_officer_race(df_trr_refresh,'officer_race')
rec.reconcile_officer_race(df_trr_trrstatus_refresh,'officer_race')

# Reconciliation gender
rec.reconcile_gender(df_trr_refresh,'subject_gender')
rec.reconcile_gender(df_trr_refresh,'officer_gender')
rec.reconcile_gender(df_trr_trrstatus_refresh,'officer_gender')

# Reconciliation birth_year
rec.reconcile_birth_year(df_trr_refresh,'subject_birth_year')
rec.reconcile_birth_year(df_trr_refresh,'officer_birth_year')
rec.reconcile_birth_year(df_trr_trrstatus_refresh,'officer_birth_year')

# Reconciliation first name
rec.reconcile_first_name(df_trr_refresh,'officer_first_name')
rec.reconcile_first_name(df_trr_trrstatus_refresh,'officer_first_name')

# Reconciliation last name
rec.reconcile_last_name(df_trr_refresh,'officer_last_name')
rec.reconcile_last_name(df_trr_trrstatus_refresh,'officer_last_name')

# Reconciliation streets
rec.reconcile_street(df_trr_refresh,'street')

# Reconciliation locations
rec.reconcile_location(df_trr_refresh, 'location')

# Reconciliation indoor_or_outdoor
rec.reconcile_in_outdoor(df_trr_refresh, 'indoor_or_outdoor')

# Reconciliation party_fired_first [No change]

# Reconciliation subject weapon [No change]

#print(df_trr_refresh['officer_birth_year'])
#print(df_data_officer['birth_year'])
#print(df_trr_refresh['officer_birth_year'].isna().sum(), " Number of nulls")
#print(df_trr_refresh['officer_birth_year'].count()," Total columns of refresh birthday")
#print(df_data_officer['birth_year'].count(), " Total columns of officer birthday")

"************** LINK OFFICER ID **************"

# Define the columns we want to match from each table
left = ['officer_first_name','officer_last_name', 'officer_gender', 'officer_race','officer_appointed_date', 'officer_middle_initial','officer_birth_year']
right = ['first_name','last_name', 'gender', 'race', 'appointed_date', 'middle_initial','birth_year']

# Merge both tables trying to match de 8 fields
merged_df_refresh = pd.merge(df_trr_refresh, df_data_officer, how = 'left', left_on = left, right_on = right)
merged_df_status = pd.merge(df_trr_trrstatus_refresh, df_data_officer, how = 'left', left_on = left, right_on = right)

match_rate_refresh = (len(merged_df_refresh) - merged_df_refresh['id_y'].isna().sum())/len(merged_df_refresh)
match_rate_status = (len(merged_df_status) - merged_df_status['id'].isna().sum())/len(merged_df_status)

print(match_rate_refresh, " Refresh match initial rate")
print(match_rate_status, " Status match initial rate")

# Make a subset with the officer_id = NULL and not NULL
subset_merged_remaining = merged_df_refresh[merged_df_refresh['id_y'].isna()]
subset_merged_matched = merged_df_refresh[merged_df_refresh['id_y'].notna()]

# We remove the birth year and middle initial
left_2 = ['officer_first_name','officer_last_name', 'officer_gender', 'officer_race','officer_appointed_date']
right_2 = ['first_name','last_name', 'gender', 'race', 'appointed_date']

# Merge again trying to match 5 fields
merged_df_refresh_2 = pd.merge(df_trr_refresh, df_data_officer, how = 'left', left_on = left_2, right_on = right_2)
match_rate_refresh_2 = (len(merged_df_refresh_2) - merged_df_refresh_2['id_y'].isna().sum())/len(merged_df_refresh_2)

merged_df_status_2 = pd.merge(df_trr_trrstatus_refresh, df_data_officer, how = 'left', left_on = left_2, right_on = right_2)
match_rate_status_2 = (len(merged_df_status_2) - merged_df_status_2['id'].isna().sum())/len(merged_df_status_2)

print(match_rate_refresh_2, " Refresh match rate v2")
print(match_rate_status_2, " Status match rate v2")

# We combine the first and the second tables with the matches
'''
for i, row in merged_df_refresh.iterrows():
    value_id_x = row['id_x']
    value_id_y = row['id_y']
    if value_id_y != None:
        merged_df_refresh_2.iloc[i] = merged_df_refresh.iloc[i]

for i, row in merged_df_status.iterrows():
    value_id_y = row['id']

    if value_id_y != None:
        merged_df_status_2.iloc[i] = merged_df_status.iloc[i]
'''

# Delete rows: first_name, middle_initial, last_name, suffix_name, gender, race, appointed_date, birth year
merged_df_refresh_2 = merged_df_refresh_2.drop(['first_name', 'middle_initial', 'last_name','suffix_name', 'gender', 'race', 'appointed_date', 'birth_year'], axis=1)
merged_df_status_2 = merged_df_status_2.drop(['first_name', 'middle_initial', 'last_name','suffix_name', 'gender', 'race', 'appointed_date', 'birth_year'], axis=1)

# Save the final merged table in a CSV
merged_df_refresh_2.to_csv('Integration_trr_refresh.csv', header=True, index= False, sep=',')
merged_df_status_2.to_csv('Integration_trr_status.csv', header=True, index= False, sep=',')


"************** LINK POLICE UNITS ID **************"


conn.close()