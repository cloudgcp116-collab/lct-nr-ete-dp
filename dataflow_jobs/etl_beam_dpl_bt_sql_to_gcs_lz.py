# steps decide --
# step 1: Source Coneection testing 
# step 2: extracting the data from table 
# step 3: writing the data into gcs landing zone

import apache_beam as beam 
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.io.jdbc import ReadFromJdbc, WriteToJdbc

# variables declaration
driver_class = "com.mysql.cj.jdbc.Driver"
jdbc_url = "jdbc:mysql://34.47.255.97:3306/lavu_portal"
username = "Admin1"
password = "GCPCloud@123" 

# beam transformations 

with beam.Pipeline() as p:
    data = (
        p | 'reading sql data from onprem server' 
                >> ReadFromJdbc(
                    driver_class_name=driver_class,
                    jdbc_url=jdbc_url,
                    username=username,
                    password=password,
                    table_name='staff' # staff is dimention table in lavu_portal database

                )
          | 'converting namedtuple into csv format' >> beam.Map(lambda r: f"{r.id},{r.name}")
          | 'writing to GCS' >> beam.io.WriteToText(
                        "gs://employee_raw_data_bucket/us_region/employee_dim/date/rawdata",
                        file_name_suffix=".csv",
                        header="id,name"
          )
         
    )
