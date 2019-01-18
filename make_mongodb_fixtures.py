import os
from datetime import datetime
import pymongo
from bson.objectid import ObjectId
from bson.json_util import dumps

def main():
    mongo_ip_addr = os.getenv("ENVIRATRON_MONGODB_IP")
    mongo_db_port = 27017
    db_name = "intelluscloud"

    client = pymongo.MongoClient(mongo_ip_addr, mongo_db_port)
    db = client[db_name]

    # Write the "chamber" objects:
    with open('./tests/mongodb_fixtures/chambers.json', 'w') as write_fixture_handle:
        collection = db.chamber
        data = collection.find({})
        write_fixture_handle.write(dumps(data, indent=3))


    # Write the "chamberdata" objects:
    with open('./tests/mongodb_fixtures/chamberdata.json', 'w') as write_fixture_handle:

        collection = db.chamberdata
        start_datetime = datetime(2019, 1, 1, 0, 0)
        end_datetime = datetime(2019, 1, 10, 0, 0)

        query = {
            "ChamberId": ObjectId("bdafd6f326d8664a8d874aa0"),
            "Timestamp": {"$lte": end_datetime, "$gte": start_datetime}
        }

        data = collection.find(query)
        write_fixture_handle.write(dumps(data, indent=3))



if __name__ == '__main__':

    main()
