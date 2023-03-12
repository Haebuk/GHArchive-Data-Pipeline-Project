###
# Copyright 2013-2023 AFI, Inc. All Rights Reserved.
###

import os
import json
import gzip

for dir, _, file_list in os.walk("data/raw/2023/03"):
    for file in file_list:
        execution_date = file.split("/")[-1].split(".")[0]
        print(execution_date)
        year, month, day, hour = execution_date.split("-")
        # print(year, month, day, hour)

        print(f"{dir}/{file}")
        with gzip.open(f"{dir}/{file}", "rb") as f:
            data = f.read().decode()

        dicts = data.strip().split("\n")

        data_list = []
        for d in dicts:
            # remove payload key in dict
            d = json.loads(d)
            d.pop("payload")
            data_list.append(d)

        break
