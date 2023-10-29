import os
from pathlib import Path
import pandas as pd

df = []
stage = "Bronze"
ds_nodash = "20231003"
BASE_FOLDER = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '../..','datalake/{stage}/stocks'))
file_path = BASE_FOLDER.format(stage="Bronze")
subpastas = [subpasta for subpasta in os.listdir(file_path) if os.path.isdir(os.path.join(file_path, subpasta))]
sub_folders = [sub_folder for sub_folder in os.listdir(file_path) if os.path.isdir(os.path.join(file_path, sub_folder))]

for sub_folder in sub_folders:
    path = os.path.join(file_path, sub_folder)
    files = [arquivo for arquivo in os.listdir(path) if arquivo.endswith(f"{ds_nodash}.csv")]

    for file in files:
        df_file = pd.read_csv(os.path.join(path, file))
        df_file['Ticker'] = file.split('_')[0]
        df.append(df_file)

df = pd.concat(df, ignore_index=True)
cols = df.columns
column_order= ['Ticker'] + [col for col in cols if col != 'Ticker']
df = df[column_order]
print(df)
