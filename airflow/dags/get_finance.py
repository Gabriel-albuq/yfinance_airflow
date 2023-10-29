import yfinance
from airflow.decorators import dag, task
from airflow.macros import ds_add
from pathlib import Path
import pendulum
import os
import pandas as pd

TICKERS = [
            "AAPL",
            "MSFT",
            "GOOG",
            "TSLA"
            ]

@task() # Decorador para uma função Python se tornar uma instância de tarefa
def get_history(ticker, dest_path, ds=None, ds_nodash=None):
    dest_path = os.path.join(dest_path, f'stocks/{ticker}')
    if not os.path.exists(dest_path): os.makedirs(dest_path)
    yfinance.Ticker(ticker).history(
        period ="1d",
        interval = "5m",
        start = ds_add(ds, -1),
        end = ds,
        prepost = True
    ).to_csv(os.path.join(dest_path, f'{ticker}_{ds_add(ds, -1)}.csv'))

@task()
def transform_stocks(file_path, dest_path, ds=None, ds_nodash=None):
    df = []
    sub_folders = [sub_folder for sub_folder in os.listdir(file_path) if os.path.isdir(os.path.join(file_path, sub_folder))]
    if not os.path.exists(dest_path): os.makedirs(dest_path)

    for sub_folder in sub_folders:
        path = os.path.join(file_path, sub_folder)
        files = [arquivo for arquivo in os.listdir(path) if arquivo.endswith(f"{ds_add(ds, -1)}.csv")]

        for file in files:
            df_file = pd.read_csv(os.path.join(path, file))
            df_file['Ticker'] = file.split('_')[0]
            df.append(df_file)
        
    df = pd.concat(df, ignore_index=True)
    cols = df.columns
    column_order= ['Ticker'] + [col for col in cols if col != 'Ticker']
    df = df[column_order]

    df.to_csv(os.path.join(dest_path, f'Stocks_{ds_add(ds, -1)}.csv'), index=False)

@dag(schedule_interval = "0 0 * * 2-6", # Terça a sábado, pois o mercado funciona de segunda a sexta e o dag roda um dia depois pegando o anterior
        start_date = pendulum.datetime(2023, 10, 1, tz="UTC"),
        catchup = True # Para começar a rodar a partir do start_data, e não da data de hoje
)
def get_stocks_dag():
    list_get_history = []
    BASE_FOLDER = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '../..','datalake/{stage}')) #Para pegar duas pastas acima de onde o arquivo está e criar o caminho onde será colocado o datalake
    for ticker in TICKERS:
        list_get_history.append(get_history.override(task_id=ticker, pool ="finance_pool")(ticker=ticker, dest_path=BASE_FOLDER.format(stage='Bronze')))

    task_2 = transform_stocks.override(task_id="transform_stocks", pool = "finance_pool")(file_path= os.path.join(BASE_FOLDER.format(stage="Bronze"),'stocks'),\
                                                         dest_path = BASE_FOLDER.format(stage="Silver"))

    # Dependencias
    for i in range(0,len(list_get_history)):
        list_get_history[i] >> task_2


dag = get_stocks_dag()

