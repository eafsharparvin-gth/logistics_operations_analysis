import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent # For GitHub Path


df = pd.read_csv(BASE_DIR/"data"/"raw"/"logistics_shipments_raw.csv") # For GitHub Address
print(df.head())
print(df.shape)
df.info()

print(df.isna().sum()) # missing Values
print(df.duplicated().sum())
print(df.nunique())

# incompatibility check
print(df["Warehouse"].value_counts(dropna=False))
print(df["Carrier"].value_counts(dropna=False))
print(df["Vehicle_Type"].value_counts(dropna=False))

#integer data columns
print(df[["Distance_KM", "Weight_KG", "Shipping_Cost"]].describe())

# detecting nonvalid rows
print(df[df["Distance_KM"] <=0])
print(df[df["Weight_KG"]<=0])
print(df[df["Shipping_Cost"]<=0])

# Outer Data on integer columns
print(df.nlargest(10,"Distance_KM")[
    ["Shipment_ID", "Warehouse", "Destination_City", "Distance_KM"]
      ])
print(df.nlargest(10,"Weight_KG")[
    ["Shipment_ID", "Vehicle_Type", "Weight_KG"]
      ])
print(df.nlargest(10, "Shipping_Cost")[
    ["Shipment_ID","Distance_KM","Weight_KG","Vehicle_Type", "Shipping_Cost"]
      ])