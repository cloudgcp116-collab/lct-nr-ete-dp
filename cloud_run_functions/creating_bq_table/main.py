import functions_framework
from google.cloud import bigquery
from config import PROJECT_ID, DATASETID

@functions_framework.http
def bq_table_creation_lct(request):
    request_json = request.get_json(silent=True)
    if request_json and 'table_name' in request_json:
        table_name = request_json['table_name'] 
        client = bigquery.Client(project=PROJECT_ID)
        table_id = f"{PROJECT_ID}.{DATASETID}.{table_name}"
        schema = [
            bigquery.SchemaField("name", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("age", "INTEGER", mode="REQUIRED"),
        ]
        table = bigquery.Table(table_id, schema=schema)
        table = client.create_table(table)
        
        return f"Table {table.table_id} was successfully created in dataset {DATASETID}!"
    else:
        
        return "No table name provided in the request JSON!" 
