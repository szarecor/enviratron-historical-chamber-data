# Enviratron Growth Chamber History Parser

This project is for extracting historical environmental data for the growth chambers in the Enviratron project. 

The Percival Scientific growth chambers log set point and observed values for temperature, relative humidity, CO2, soil moisture and lighting
to a MongoDB instance. This project extracts and reformats that logged data.


To run any the example code (`example.py`), you will first need to set the ip address of the MongoDb server for the terminal session: `export ENVIRATRON_MONGODB_IP=xxx.xxx.xxx.xxx`

Then, you can run `python example.py` or any of the other examples. See the definition of the `main()` function for available parameters.

 