import boto3
import botocore
import logging
from datetime import datetime
import json
from botocore.vendored import requests
import os.path
from io import StringIO
import time
import hashlib
import zipfile
import sys
import os.path
import pandas as pd
from pandas.io.json import json_normalize


def current_milli_time(): return int(round(time.time() * 1000))

def lambda_handler(event, context):
	mybucket = os.environ['FILE_LOAD_BUCKET']
	
	logger = logging.getLogger()
	logger.setLevel(logging.INFO)
	raideosuudet_infra_idt = []
	df_raideosuudet = pd.DataFrame({'A' : []})
	csv_buffer = StringIO()
	table_name_variable = os.environ['TABLE_NAME_VARIABLE']
	
    try:
        #raideosuudet = json.loads(requests.get("https://rata.digitraffic.fi/infra-api/0.3/raideosuudet.json?srsName=crs:84&time=2018-11-12T00%3A00%3A00Z%2F2018-11-12T00%3A00%3A00Z").text)
        
        raideosuudet = json.loads(requests.get(os.environ['URL']).text)

        for key in raideosuudet.keys():
            raideosuudet_infra_idt.append(key)
    except:
        logger.error("ERROR: Virhe haettaessa RESTin tietoja")
        
    try:
        for i in range(len(raideosuudet_infra_idt)):
            #print(i)
            vaihteet_temp = json_normalize(raideosuudet[raideosuudet_infra_idt[i]][0])
            df_raideosuudet = pd.concat([df_raideosuudet, vaihteet_temp], ignore_index=True)

        #Deletoidaan turhat kamat, esimerkiksi geometria turhaa tietoa kun se jo omissa kentissä
        del df_raideosuudet['A']
        
        #Metatietojen lisäys
        timestamp = current_milli_time()
        df_raideosuudet = addSDTColumns(df_raideosuudet, timestamp)
        file_name = f'table.{table_name_variable}.{timestamp}.batch.{timestamp}.fullscanned.true.delim.pipe.skiph.1.csv'
        file_load_key = f'{table_name_variable}/{file_name}'
        #print(file_load_key)
        
        #df_raideosuudet.to_csv(file_name, sep='|', encoding='UTF-8')
        #print(len(df_raideosuudet))
        df_raideosuudet.to_csv(csv_buffer, sep='|', encoding='utf-8')
        s3_resource = boto3.resource('s3')
        s3_resource.Object(mybucket, file_load_key).put(Body=csv_buffer.getvalue())
        csv_buffer.close()
        return "tiedostot menivät S3:seen"
    except:
        return "ei toimi, virhe kun tehtiin S3 PUTia"
        
        
def addSDTColumns(df, batch_id):
    #print("------  addSDTColumns ------")
    # sdt_stage_id: hashCode() + startTime. Exist mainly because of legacy reasons.
    # sdt_stage_create_time:    Current timestamp
    # sdt_stage_batch_id:   Unique for a data source. A number. This can be current time in milliseconds for example.
    # sdt_stage_source: The name of the source system in crawler's metadata database.
    # sdt_stage_source_type:    Always "db" in crawler's source code,
    # sdt_stage_source_tech:    Always "TYPE" in crawler's source code.
    # sdt_sort_order: An index number for sorting the data
    def reOrder(df):
        cols = df.columns.tolist()
        df = df.loc[:, [cols[-1]] + cols[:-1]]
        return df
    # add sdt_sort_order
    #df[len(df.columns)] = 0
    #df = reOrder(df)                # reorder from last column to first one
	# add sdt_stage_source_type
    length = len(df.columns)
    df.loc[:, length] = 'json'
    df = reOrder(df)                # reorder from last column to first one
    # add sdt_stage_source_tech
    length = len(df.columns)
    df.loc[:, length] = 'rest-api'
    df = reOrder(df)                # reorder from last column to first one
    # add sdt_stage_source
    length = len(df.columns)
    df.loc[:, length] = 'avoin-data'
    df = reOrder(df)                # reorder from last column to first one
	# add sdt_stage_id
    hash_code = hashlib.md5(str(batch_id).encode('utf-8')).hexdigest()
    length = len(df.columns)
    df.loc[:, length] = f'{hash_code}{batch_id}'
    df = reOrder(df)                # reorder from last column to first one
	# add sdt_stage_create_time
    # creation time is same as batch_id which is timestamp
    length = len(df.columns)
    df.loc[:, length] = batch_id
    df = reOrder(df)                # reorder from last column to first one
    # add sdt_stage_batch_id
    length = len(df.columns)
    df.loc[:, length] = batch_id
    df = reOrder(df)                # reorder from last column to first one


    #print(df.head())
    return df