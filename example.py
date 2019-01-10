from datetime import datetime
from dateutil.tz import tzoffset
from enviratron_chamber_history import EnviratronChamberHistoryParser


def main():
    """ Pulls the historical data from mongodb for the chambers and date range defined below """
    import os

    mongo_ip_address = os.getenv("ENVIRATRON_MONGODB_IP")

    if mongo_ip_address is None:
        print("Please set/export the env var ENVIRATRON_MONGODB_IP before proceeding")
        import sys

        sys.exit(-1)

    history = EnviratronChamberHistoryParser(mongo_ip_address)
    assert history.db is not None, "No MongoDB connection established"

    # Set the start and end datetimes for the query here:
    # Let's naively assume all datetimes are UTC+0:
    start_datetime = datetime(2019, 1, 1, 0, 0, 0, 0, tzinfo=tzoffset("UTC+0", 0))
    end_datetime = datetime(2019, 1, 1, 23, 59, 0, 0, tzinfo=tzoffset("UTC+0", 0))

    start_datetime_str = start_datetime.strftime("%Y%m%dT%H:%M")
    end_datetime_str = end_datetime.strftime("%Y%m%dT%H:%M")

    time_resolution = 30

    for i in range(1, 9):

        chamber_id = i

        OUTPUT_PATH = f"./sample_output/chamber_{chamber_id}_observation_data_from_{start_datetime_str}_to_{end_datetime_str}_{time_resolution}_minute_resolution.csv"

        with open(OUTPUT_PATH, "w") as write_handle:
            history.write_csv(
                write_handle=write_handle,
                chamber_int=chamber_id,
                start_datetime=start_datetime,
                end_datetime=end_datetime,
                time_resolution_mins=time_resolution,
            )


if __name__ == "__main__":

    main()
