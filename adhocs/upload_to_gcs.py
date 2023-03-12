###
# Copyright 2013-2023 AFI, Inc. All Rights Reserved.
###

import os
import json
import gzip
from tqdm import tqdm

for dir, _, file_list in os.walk("data/raw/2023/03"):
    for file in tqdm(file_list):
        execution_date = file.split("/")[-1].split(".")[0]
        # print(execution_date)
        year, month, day, hour = map(int, execution_date.split("-"))
        # print(year, month, day, hour)

        # print(f"{dir}/{file}")
        with gzip.open(f"{dir}/{file}", "rb") as f:
            data = f.read().decode()

        dicts = data.strip().split("\n")

        data_list = []
        for d in dicts:
            # remove payload key in dict
            d = json.loads(d)
            d.pop("payload")
            data_list.append(d)

        os.makedirs(f"data/{year}/{month:02d}/{day:02d}", exist_ok=True)
        file_name = f"data/{year}/{month:02d}/{day:02d}/{hour:02d}.json.gz"

        with gzip.open(file_name, "wt", encoding="utf-8") as f:
            json.dump(data_list, f)

        # break
