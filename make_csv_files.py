"""' This is a rough proof of concept script for parsing the historical Enviratron growth chamber state data
that Percival Scientific stores in a MongoDb instance on the Enviratron intrastructure. """
import os
import datetime
from dateutil.tz import tzoffset
import pymongo
from pymongo import MongoClient
from bson.objectid import ObjectId
import arrow
import csv


def get_mongo_connection(ip_addr, port=27017, collection=None):
    client = MongoClient(ip_addr, port)
    db = client.intelluscloud

    if collection is not None:
        collection = db[collection]
        return collection

    return db


if __name__ == "__main__":

    mongo_ip_address = os.getenv("ENVIRATRON_MONGODB_IP")

    if mongo_ip_address is None:

        print("Please set the env var ENVIRATRON_MONGODB_IP before proceeding")
        import sys

        sys.exit(-1)

    # Pulled from MongoDb intelluscloud.chamber collection:
    chambers = {
        "Chamber 7 (0003AA0095F6)": "f466492cf72e9f428d50b092",
        "Chamber 8 (0003AA009600)": "7d9fd5ffa6ecb547bd6ea6a9",
        "Chamber 6 (0003AA0095F4)": "b5a2986a019fd241b268738c",
        "Chamber 5 (0003AA0095EC)": "16e39e954433a24793c3c06a",
        "Chamber 4 (0003AA0095F5)": "af6d1121f79c95499d04c00a",
        "Chamber 3 (0003AA0095F8)": "6e25512f31079343ac1e04cc",
        "Chamber 2 (0003AA0089B0)": "bdafd6f326d8664a8d874aa0",
        "Chamber 1 (0003AA0095FA)": "b8f681590cc4ac44ba21e2d3",
    }

    __tag_map = {
        # SENSOR READINGS:
        "PV_1": "temperature_actual",
        "PV_2": "humidity_actual",
        "PV_3": "co2_actual",
        "PV_4": "lighting_sensor",
        "PV_5": "watering_actual"
        # WRITE COMMAND TAGS:
        ,
        "CM_SP_1_Manual": "temperature_target",
        "CM_SP_2_Manual": "humidity_target",
        "CM_SP_3_Manual": "co2_target",
        "CM_SP_5_Manual": "watering_target"
        # LIGHTING SPECIFIC WRITE COMMANDS:
        ,
        "EO_1_On_Off": "lighting_1_on",
        "EO_2_On_Off": "lighting_2_on",
        "EO_1_Dim": "lighting_1",
        "EO_2_Dim": "lighting_2",
        "EO_3_Dim": "lighting_3",
        "EO_4_Dim": "lighting_4",
        "EO_5_Dim": "lighting_5",
        "EO_6_Dim": "lighting_6",
        "EO_7_Dim": "lighting_7",
    }

    # Set the start and end datetimes for the query here:
    # Let's naively assume all datetimes are UTC+0:
    start_datetime = datetime.datetime(
        2019, 1, 1, 0, 0, 0, 0, tzinfo=tzoffset("UTC+0", 0)
    )
    end_datetime = datetime.datetime(
        2019, 1, 4, 23, 59, 0, 0, tzinfo=tzoffset("UTC+0", 0)
    )

    start_datetime_str = start_datetime.strftime("%Y%m%dT%H:%M")
    end_datetime_str = end_datetime.strftime("%Y%m%dT%H:%M")

    db = get_mongo_connection(mongo_ip_address)
    chambers_collection = db.chamber
    chamber_data_collection = db.chamberdata

    for (chamber_name, chamber_id) in chambers.items():

        print(f"processing {chamber_name}")

        _chamber_id = int(chamber_name.split(" ")[1])

        with open(
            f"./output/chamber_{_chamber_id}_observation_data_from_{start_datetime_str}_to_{end_datetime_str}.csv",
            "w",
        ) as write_handle:

            writer = csv.writer(
                write_handle, delimiter=",", quotechar="'", quoting=csv.QUOTE_MINIMAL
            )
            # Header row:
            writer.writerow(
                [
                    "chamber",
                    "record ID",
                    "datetime",
                    "temperature setpoint",
                    "temperature actual",
                    "rh setpoint",
                    "rh actual",
                    "watering setpoint",
                    "watering actual",
                ]
            )

            chamber_id_obj = ObjectId(chamber_id)
            datas = chamber_data_collection.find(
                {
                    "ChamberId": chamber_id_obj,
                    "Timestamp": {"$lte": end_datetime, "$gte": start_datetime},
                }
            ).sort("Timestamp", pymongo.ASCENDING)

            for d in datas:

                obs_count = int(d.get("Count"))
                tstamp = arrow.get(d.get("Timestamp"))

                # Temperature:
                temp_data = d.get("Inputs").get("PV_1")
                temps_set_points = temp_data.get("SetPoints")
                temps_actual = temp_data.get("Values")

                # Relative humidity:
                rh_data = d.get("Inputs").get("PV_2")
                rhs_set_points = rh_data.get("SetPoints")
                rhs_actual = rh_data.get("Values")

                # Soil Moisture:
                watering_data = d.get("Inputs").get("PV_5")
                watering_set_points = watering_data.get("SetPoints")
                watering_actual = watering_data.get("Values")

                for i in range(0, obs_count):
                    # Because the chamberdata.Timestamp only reflect the datetime for the first of the many (probably 60)
                    # observations that the chamberdata entity wraps, we need to compare the synthetic timestamp for
                    # each wrapped observation to avoid returning data beyond our stated end_datetime:
                    if (end_datetime - tstamp).days < 0:
                        break

                    # I have found instances where the count of actual points doesn't match with the expected, so
                    # wrap all the reads with try-except blocks to handle index-out-of-range errors:

                    # Divide all values by 1000 to get a human-readable number

                    # Handle temperatures:
                    try:
                        temp_set_point = temps_set_points[i] / 1000.00
                    except IndexError:
                        temp_set_point = None

                    try:
                        temp_actual = temps_actual[i] / 1000.00
                    except IndexError:
                        temp_actual = None

                    # Handle relative humidity:
                    try:
                        rh_set_point = rhs_set_points[i] / 1000.00
                    except IndexError:
                        rh_set_point = None

                    try:
                        rh_actual = rhs_actual[i] / 1000.00
                    except IndexError:
                        rh_actual = None

                    # Soil moisture/watering:
                    try:
                        sm_set_point = watering_set_points[i] / 1000.00
                    except IndexError:
                        sm_set_point = None

                    try:
                        sm_actual = watering_actual[i] / 1000.00
                    except IndexError:
                        sm_actual = None

                    tstamp_str = tstamp.format("YYYY-MM-DD HH:mm")
                    writer.writerow(
                        [
                            _chamber_id,
                            str(d.get("_id")),
                            tstamp_str,
                            temp_set_point,
                            temp_actual,
                            rh_set_point,
                            rh_actual,
                            sm_set_point,
                            sm_actual,
                        ]
                    )
                    tstamp = tstamp.shift(minutes=1)
