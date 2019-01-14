"""' This file is for parsing the historical Enviratron growth chamber state data
that Percival Scientific stores in a MongoDb instance on the Enviratron intrastructure. """
import csv
from bson.objectid import ObjectId
import arrow
import pymongo


class EnviratronChamberHistoryParser:
    def __init__(self, mongo_ip_addr=None):

        self.mongo_db_addr = mongo_ip_addr
        self.mongo_db_port = 27017
        self.db_name = "intelluscloud"
        self.db = None
        self.collection_name = "chamberdata"
        self.collection = None

        self.get_mongo_connection()

    def get_mongo_connection(self):
        client = pymongo.MongoClient(self.mongo_db_addr, self.mongo_db_port)
        self.db = client[self.db_name]

        if self.collection_name is not None:
            self.collection = self.db[self.collection_name]
            return self.collection

        return self.db

    def _get_chamber_id(self, chamber_int):
        """ Gets the internal mongo _id for the chamber associated with the given chamber_int (1-8) """

        # except AttributeError as err:
        if self.db is None:
            raise RuntimeError("No MongoDb connection available")

        # Need to use a different collection:
        _chamber_collection = self.db.chamber
        chamber = _chamber_collection.find_one(
            {"Name": {"$regex": f"Chamber {chamber_int}"}}
        )

        if chamber is None:
            raise RuntimeError(f"No Chamber object found for int '{chamber_int}'")

        return (str(chamber.get("_id")), chamber.get("Name"))

    def _parse_mongo_chamberdata_record(
        self, chamberdata, resolution_in_minutes=1, end_datetime=None
    ):
        """ Extracts the timepoint data wrapped in a chamberdata record

        The chamber data (set points and observed/actual is logged with one-minute resolution.

        The logged data is grouped in one-hour chunks wrapped in a single chamberdata instance.

        In most cases, there will be 60 entries for each set point and observation data type within each
        chamberdata instance. However, there are cases when the data gets sparse and there are < 60 entries.

        """

        d = chamberdata
        return_data = []

        obs_count = int(d.get("Count"))
        tstamp = arrow.get(d.get("Timestamp"))

        # Temperature:
        temp_data = d.get("Inputs").get("PV_1")
        assert temp_data is not None, "Did not find temperature (PV_1) data"
        temps_set_points = temp_data.get("SetPoints")
        temps_actual = temp_data.get("Values")

        assert (
            temps_set_points is not None
        ), "Did not find temperature (PV_1) set point data"
        assert temps_actual is not None, "Did not find temperature (PV_1) actual data"

        # Relative humidity:
        rh_data = d.get("Inputs").get("PV_2")
        assert rh_data is not None, "Did not find RH (PV_2) data"
        rhs_set_points = rh_data.get("SetPoints")
        rhs_actual = rh_data.get("Values")

        assert rhs_set_points is not None, "Did not find RH (PV_2) set point data"
        assert rhs_actual is not None, "Did not find RH (PV_2) observed data"

        # Soil Moisture:
        watering_data = d.get("Inputs").get("PV_5")
        assert watering_data is not None, "Did not find watering (PV_5) data"
        watering_set_points = watering_data.get("SetPoints")
        watering_actual = watering_data.get("Values")

        # For what it's worth, the black formatter keeps adding the parentheses here:
        assert (
            watering_set_points is not None
        ), "Did not find watering (PV_5) set point data"
        assert watering_actual is not None, "Did not find watering (PV_5) observed data"

        for i in range(0, obs_count, resolution_in_minutes):
            # Because the chamberdata.Timestamp only reflect the datetime for the first of the many (probably 60)
            # observations that the chamberdata entity wraps, we need to compare the synthetic timestamp for
            # each wrapped observation to avoid returning data beyond our stated end_datetime:
            if end_datetime is not None and (end_datetime - tstamp).days < 0:
                break

            # I have found instances where the count of actual points doesn't match with the expected, so
            # wrap all the reads with try-except blocks to handle index-out-of-range errors:

            # TODO: return empty/partial rows for missing/sparse data

            # Divide all values by 1000 to get a human-readable number

            def get_value_or_none(collection, index):
                ''' Simple helper to avoid IndexErrors when getting data from the lists.
                This is necessary because the "obs_count" value from the chamberdata object is not always
                correct. Alternatively, we could avoid the IndexErrors by simply using len() on the list.
                '''
                try:
                    value = collection[index] / 1000.00
                    return value
                except IndexError:
                    return None

            # Handle temperatures:
            temp_set_point = get_value_or_none(temps_set_points, i)
            temp_actual = get_value_or_none(temps_actual, i)
            # Handle relative humidity:
            rh_set_point = get_value_or_none(rhs_set_points, i)
            rh_actual = get_value_or_none(rhs_actual, i)
            # Soil moisture/watering:
            sm_set_point = get_value_or_none(watering_set_points, i)
            sm_actual = get_value_or_none(watering_actual, i)

            tstamp_str = tstamp.format("YYYY-MM-DD HH:mm")
            return_data.append(
                [
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
            tstamp = tstamp.shift(minutes=resolution_in_minutes)

        return return_data

    def get_chamber_history(
        self,
        chamber_int,
        start_datetime=None,
        end_datetime=None,
        time_resolution_mins=1,
    ):
        """ Returns a list of the historical data for the given chamber and date range and time_resolutions (in minutes) """

        # TODO: This is hacky, let's circle back and reconsider this:
        if time_resolution_mins > 60:
            raise RuntimeError(
                "Time resolution must be less than or equal to 60 minutes"
            )

        chamber_id, chamber_name = self._get_chamber_id(chamber_int)
        query = {"ChamberId": ObjectId(chamber_id)}

        # TODO: Consider not requiring both start_ and end_:
        if start_datetime is not None and end_datetime is not None:
            query["Timestamp"] = {"$lte": end_datetime, "$gte": start_datetime}

        timepoint_obs = self.collection.find(query).sort("Timestamp", pymongo.ASCENDING)

        environment_states = []

        for d in timepoint_obs:

            obs = self._parse_mongo_chamberdata_record(
                d, resolution_in_minutes=time_resolution_mins, end_datetime=end_datetime
            )
            # Add a chamber name element to each 'row' in the obs data:
            obs = [[chamber_name] + ob for ob in obs]
            environment_states += obs

        return environment_states

    def write_csv(
        self,
        write_handle,
        chamber_int,
        start_datetime=None,
        end_datetime=None,
        time_resolution_mins=1,
    ):

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

        obs_rows = self.get_chamber_history(
            chamber_int=chamber_int,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            time_resolution_mins=time_resolution_mins,
        )

        for row in obs_rows:
            writer.writerow(row)
