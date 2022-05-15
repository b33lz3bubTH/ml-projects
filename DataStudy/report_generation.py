import pandas as pd
import numpy as np

from pandas_profiling import ProfileReport

directory = "./Chinese_Company_dataset"
data_set = "cash_flow.csv"
title = "Cash Flow"

is_minimal = True

dataset = pd.read_csv(f"{directory}/{data_set}")

profile = ProfileReport(dataset,
                        minimal=is_minimal,
                        title=f"{title} Report",
                        correlations={
                        "pearson": {"calculate": True},
                        "spearman": {"calculate": True},
                        "kendall": {"calculate": True},
                        "phi_k": {"calculate": False},
                        })

profile.to_file(f"{directory}/{data_set}_report.html")