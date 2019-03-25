# Enviratron Growth Chamber History Parser

__The code in this repo is rough and in-progress__

This project is for extracting historical environmental data for the growth chambers in the Enviratron project. 

The Percival Scientific growth chambers log set point and observed values for temperature, relative humidity, CO2, soil moisture and lighting
to a MongoDB instance. This project extracts and reformats that logged data.


To run the example code (`example.py`), you will first need to set the ip address of the MongoDb server for the terminal session: `export ENVIRATRON_MONGODB_IP=xxx.xxx.xxx.xxx`

Then, you can run `python example.py`. See the definition of the `main()` function in `example.py` or the usage example below for available parameters.


Sample output of the `EnviratronChamberHistoryParser.write_csv()` method is available in the `./sample_output/` directory.


The `get_chamber_history()` method returns a list of `ChamberObservationTimepoint` namedtuples where each namedtuple represents a single timepoint and the data for that timepoint.
The `ChamberObservationTimepoint` namedtuples have the following form:

* __chamber__ string representation of chamber ID
* __record_id__ string representation of the ID of the source chamberdata record in the DB
* __datetime__ string representation of the datetime
* __temperature_setpoint__ float representation of the specified temperature in Celcius
* __temperature_actual__ float representation of the observed temperature in Celcius
* __rh_setpoint__ float representation of the specified humidty as a percentage
* __rh_actual__ float representation of the observed humidity as a percentage
* __watering_setpoint__ float representation of the specified soil moisture as a percentage
* __watering_actual__ float representation of the observed soil moisture as a percentage





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
    # row is a ChamberObservationTimepoint namedtuple like this:
    # ChamberObservationTimepoint(
    #   chamber='Chamber 8 (0003AA009600)', 
    #   record_id='5b2675faa2b3c744addba6b5', 
    #   datetime='2019-01-01 11:04', 
    #   temperature_setpoint=32.0, 
    #   temperature_actual=32.0, 
    #   rh_setpoint=60.0, 
    #   rh_actual=58.0, 
    #   watering_setpoint=50.0, 
    #   watering_actual=51.0
    # )
    print(row)
    
# Or if you want to produce CSV output:
with open("my_file.csv", "w") as csv_handle:
    history.write_csv(csv_handle, chamber_id, start_datetime, end_datetime, time_resolution)
    
```

 