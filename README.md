# Enviratron Growth Chamber History Parser

This project is for extracting historical environmental data for the growth chambers in the Enviratron project. 

The Percival Scientific growth chambers log set point and observed values for temperature, relative humidity, CO2, soil moisture and lighting
to a MongoDB instance. This project extracts and reformats that logged data.


To run the example code (`example.py`), you will first need to set the ip address of the MongoDb server for the terminal session: `export ENVIRATRON_MONGODB_IP=xxx.xxx.xxx.xxx`

Then, you can run `python example.py` or any of the other examples. See the definition of the `main()` function in `example.py` for available parameters.

Basic usage example:
```python
from datetime import datetime
from dateutil.tz import tzoffset
from envivatron_chamber_history import EnviratronChamberHistoryParser

# Provide your IP address here:
history = EnviratronChamberHistoryParser(<mongo_ip_address>)

chamber_id = 1

# start_datetime and end_datetime are not strictly required and without them the default will be all data:
start_datetime = datetime(2019, 1, 1, 0, 0, 0, 0, tzinfo=tzoffset("UTC+0", 0))
end_datetime = datetime(2019, 1, 1, 23, 59, 0, 0, tzinfo=tzoffset("UTC+0", 0))
# default time_resolution is 1 minute which is a lot of data:
time_resolution = 30

data = history.get_chamber_history(chamber_id, start_datetime, end_datetime, time_resolution)

for row in data:
    print(row)
    
# Or if you want to produce CSV output:
with open("my_file.csv", "w") as csv_handle:
    history.write_csv(csv_handle, chamber_id, start_datetime, end_datetime, time_resolution)
    
```

 