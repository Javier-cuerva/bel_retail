import pandas as pd
import numpy as np
import calendar


def get_data_from_api():

    belstat_url = "https://bestat.statbel.fgov.be/bestat/api/views/426dd076-8098-445e-a3bf-4e9dabce2b51/result/CSV"
    data = pd.read_csv(belstat_url)

    data["Year"] = data.apply(lambda row: int(row["Reference month"][-4:]), axis="columns")
    data["Month Name"] = data.apply(lambda row: row["Reference month"][:-5], axis="columns")
    month_map = pd.DataFrame(
        data={
            "Month Name": list(calendar.month_name)[1:],
            "Month Number": list(range(1, 13))
        }
    )
    data = pd.merge(data, month_map, on="Month Name")
    data["Month"] = data.apply(
        lambda row: np.datetime64("{}-{:02}".format(row["Year"], row["Month Number"])),
        axis="columns"
    )

    return data