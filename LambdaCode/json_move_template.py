import boto3
import botocore
import logging
from datetime import datetime
from botocore.vendored import requests
import os
import json
import os.path
from io import StringIO
import time
import zipfile
import sys
import os.path

def current_milli_time(): return int(round(time.time() * 1000))	

def lambda_handler(event, context):
	file_export_bucket = os.environ['BUCKET_NAME']

	logger = logging.getLogger()
	logger.setLevel(logging.INFO)
	
	timestamp = current_milli_time()
	table_name_variable = os.environ['TABLE_NAME']
	
	try:
		data = json.loads(requests.get(os.environ['URL']).text)
	except:
		logger.error("ERROR: Virhe haettaessa RESTin tietoja")
		
	try:
		file_name = f'table.{table_name_variable}.{timestamp}.batch.{timestamp}.fullscanned.true.json'
		file_load_key = f'{table_name_variable}/{file_name}'
	
		s3_resource = boto3.resource('s3')
		s3_resource.Object(file_export_bucket, file_load_key).put(Body=(bytes(json.dumps(data, indent=3).encode('UTF-8'))))
	except:
		return "ei toimi, virhe kun tehtiin S3 PUTia"
