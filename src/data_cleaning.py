import pandas as pd
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent # For GitHub Path

df = pd.read_csv(BASE_DIR/"data"/"raw"/"logistics_shipments_raw.csv") # For GitHub Path Address
print(df.shape) # Ok (1500, 12)

# remove duplicates
print(df.duplicated().sum())
df = df.drop_duplicates()
print(df.shape)

# Aligning Text Values : from Inspection ( Warehouse, Carrier, Vehicle_Type)

df["Warehouse"]= df["Warehouse"].str.strip()    # (city ), ( city)
df["Carrier"]= df["Carrier"].str.strip()
df["Vehicle_Type"] = df["Vehicle_Type"].str.strip()

df["Warehouse"]= df["Warehouse"].str.title()    # (City), (city)
df["Carrier"]= df["Carrier"].str.title()
df["Vehicle_Type"] = df["Vehicle_Type"].str.title()

warehouse_mapping = {
    "Qazvin Dc": "Qazvin DC",
    "Tabriz Dc": "Tabriz DC"
}
df["Warehouse"]= df["Warehouse"].replace(warehouse_mapping)
print(df["Warehouse"].value_counts()) # Replacing Control

print(df["Warehouse"].value_counts(dropna=False))   # Check
print(df["Carrier"].value_counts(dropna=False))
print(df["Carrier"].nunique())
print(df["Carrier"].isna().sum())
print(df["Vehicle_Type"].value_counts(dropna=False))

## Missing Values
# Actual_Delivery_Date   35
# Carrier                12
# Weight_KG              11

# Carrier Missing
print(df[df["Carrier"].isna()][
    ["Shipment_ID", "Warehouse", "Destination_City","Carrier", "Vehicle_Type", "Distance_KM"]
      ]) # just for watching related data in mentioned columns.

df["Carrier"] = df["Carrier"].fillna("Unknown") # change Nan to "unknown"
print(df["Carrier"].value_counts(dropna=False)) # check

# Weight_KG Missing
print(df[df["Weight_KG"].isna()][
    ["Shipment_ID", "Warehouse", "Destination_City","Carrier", "Vehicle_Type", "Distance_KM", "Weight_KG"]
      ])
print(df.groupby("Vehicle_Type")["Weight_KG"].median())
vehicle_median = df.groupby("Vehicle_Type")["Weight_KG"].transform("median") # median beside each cell in dataframe

df["Weight_KG"] = df["Weight_KG"].fillna(vehicle_median) # fill NaN with median
print(df["Weight_KG"].isna().sum()) # check to be zero

### Date Validation

# Actual_Delivery_Date Missing

# first making Date formats right
date_columns = [
    "Order_Date",
    "Ship_Date",
    "Planned_Delivery_Date",
    "Actual_Delivery_Date"
]
for col in date_columns:
    df[col]= pd.to_datetime(df[col], errors = "coerce")

print(df[date_columns].dtypes)

# First Step:
invalid_ship_date = df["Ship_Date"] < df["Order_Date"]
#print(invalid_ship_date)
print("Invalid Ship Dates:", invalid_ship_date.sum())
print(
    df[invalid_ship_date][
        ["Shipment_ID", "Order_Date", "Ship_Date"]
    ]
)
# decision : Flag the error not to delete or change it.
df["Date_Error"] = False
df.loc[invalid_ship_date, "Date_Error"] = True
print(df["Date_Error"].value_counts()) # Check Point

# Second Step
invalid_planned_date = (
    df["Planned_Delivery_Date"] < df["Ship_Date"]
)
print("Invalid Planned Delivery Dates:", invalid_planned_date.sum())

# Related Columns
print(df[invalid_planned_date][["Shipment_ID", "Ship_Date", "Planned_Delivery_Date"]])

# If we had nonvalid items; then we make "True" for them either. (add to flag)
df.loc[invalid_planned_date, "Date_Error"] = True
print(df["Date_Error"].value_counts()) # Check Point

# Third Step
invalid_actual_date = (df["Actual_Delivery_Date"] < df["Ship_Date"])
print("Invalid Actual Delivery Dates:", invalid_actual_date.sum())
# Related Columns
print(df[invalid_actual_date][["Shipment_ID", "Ship_Date", "Actual_Delivery_Date"]])

# Like 2 previous items; add them to flag
df.loc[invalid_actual_date, "Date_Error"] = True
print(df["Date_Error"].value_counts()) # Check Point

# Point: if at the end of these 3 kind of time errors we had seen : 5+6+5 = 15 !,
# it would mean that in some records we have had more than one of defined errors.

# Brif Report of Date Invalidation:

# Ship before Order                6
# Planned Delivery before Ship     5
# Actual Delivery before Ship      5
# Rows with Date_Error = True      16

## We JUST FLAGGED these 16 records in order to not calculate in KPIs which are related to Date items.

### Reviewing integer issues revealed in data_inspection: ( <= 0 )
# Distance_KM
# Weight_KG
# Shipping_Cost

# Like Dates first make new Flag:

df["Numeric_Error"] = False
# Next step just Defining rule:
invalid_numeric = ((df["Distance_KM"] <= 0) |
                   (df["Weight_KG"] <= 0) |
                   (df["Shipping_Cost"] <=0 )
                   )
# Next
df.loc[invalid_numeric, "Numeric_Error"] = True
print("Invalid Numeric Rows:", invalid_numeric.sum())

# To see the Records themselves:

print(df[invalid_numeric][["Shipment_ID", "Distance_KM", "Weight_KG", "Shipping_Cost"]])



## Outer issues revealed in data inspections

# Distance_KM = 4200
# light Truck + Weight_KG = 42000
# Light_Truck + Weight_KG = 55000

# Defining Business Rule
print(df.groupby("Vehicle_Type")["Weight_KG"].agg(["min", "median", "max"]))
# Define:
vehicle_capacity = {"Van": 1000, "Pickup": 1500, "Light Truck": 5000, "Heavy Truck": 16000}
# For each row take accepted capacity from dict.
df["Vehicle_Capacity_KG"] = df["Vehicle_Type"].map(vehicle_capacity)
# Capacity violation rule
over_capacity = (df["Weight_KG"] > df["Vehicle_Capacity_KG"])
print("Over Capacity Rows:", over_capacity.sum())

print(df[over_capacity][["Shipment_ID", "Vehicle_Type", "Weight_KG", "Vehicle_Capacity_KG"]])

# make flag

df["Capacity_Error"] = False
df.loc[over_capacity, "Capacity_Error"] = True
print(df["Capacity_Error"].value_counts())


## Reviewing Distance_Km = 4200 in Outer issues
# like Vehicle KG we can not determine specific KM to various destinations so we should analyse KM on itself.
qazvin_route = df[
    (df["Warehouse"] == "Qazvin DC") &
    (df["Destination_City"] == "Qazvin")
]

print(qazvin_route["Distance_KM"].describe())

# make flag
distance_outlier = (
(df["Warehouse"] == "Qazvin DC") &
(df["Destination_City"] == "Qazvin") &
(df["Distance_KM"] == 4200)
)
df["Distance_Outlier"] = False
df.loc[distance_outlier, "Distance_Outlier"] = True

print(df["Distance_Outlier"].value_counts())

# Reviewing Flags:
# Date_Error       --> indicates records with invalid chronological relationships between dates.
# Numeric_Error    --> indicates records with invalid numeric values such as zero or negative values.
# Capacity_Error   --> indicates shipments where the weight exceeds the defined vehicle capacity.
# Distance_Outlier --> indicates shipments with a suspicious or unrealistic distance compared with the same route.

## Assignment NUMERIC flags
# distance
invalid_distance = df["Distance_KM"] <= 0
df.loc[invalid_distance,"Distance_KM"] = pd.NA # Do Not want to impress whole record due to other KPIs , just extraxt selected items.
print("Missing Distance:", df["Distance_KM"].isna().sum())

# Weight_KG
invalid_weight = df["Weight_KG"] <=0
df.loc[invalid_weight, "Weight_KG"] = pd.NA
print("Missing Weight:", df["Weight_KG"].isna().sum())
# after 11 missing values related to Vehicle_Type, that we filled them up with median truck weight. now it is left : 2

# Shipping_Cost
invalid_cost = df["Shipping_Cost"] <=0
df.loc[invalid_cost, "Shipping_Cost"] = pd.NA
print("Missing Shipping Cost:", df["Shipping_Cost"].isna().sum())

# in this 3 Numeric errors we just bring up the missing datas and change them to NA without manipulate th hole record
# in order to not affect other related KPIs.

# Overall Data Quality Flag : If each record contains at least one of four Flags
df["Data_Quality_Issue"] = (
    df["Date_Error"] |
    df["Numeric_Error"] |
    df["Capacity_Error"] |
    df["Distance_Outlier"]
)
print(df["Data_Quality_Issue"].value_counts())

# Date_Error        16  # 16 rows have at least one of Date Errors
# Numeric_Error     6   # 6 rows have one of Numeric values missing ( 0 or Negative )
# Capacity_Error    4   # 4 rows have extera weight over their defined capacity
# Distance_Outlier  1   # 1 row have suspicious distance traveled
print(
    df[
        [
            "Date_Error",
            "Numeric_Error",
            "Capacity_Error",
            "Distance_Outlier",
            "Data_Quality_Issue"
        ]
    ].sum()
)


### Delivery_Status
# For Each Shipment we have one of these situations:

# On Time                  Delivered On Time
# Late                     Delivered Late
# Missing Delivery Record  Actual Date Not Recorded
# Invalid Date             Record Dates have Logical Issues ( 16 records )

df["Delivery_Status"] = "Unknown"

# First Rule: Each record that contains Date issue, is changed to ( Invalid Date ) Status.
df.loc[
    df["Date_Error"] == True,
    "Delivery_Status"
] = "Invalid Date"

# Second Rule: Records which have no Date_Error, and have Empty Actual_Delivery_Date:
missing_delivery = (
(df["Date_Error"] == False ) &
(df["Actual_Delivery_Date"].isna())
)
df.loc[
    missing_delivery,
    "Delivery_Status"
] = "Missing Delivery Record"

print(df["Delivery_Status"].value_counts())

# Now two kind of Situations remains: On Time & Late for the rest of records.

on_time = (
(df["Delivery_Status"] == "Unknown") &
(df["Actual_Delivery_Date"] <= df["Planned_Delivery_Date"])
)
# Then we set (On Time) for these records:
df.loc[
    on_time,
    "Delivery_Status"
] = "On Time"

# Now the rest of the records with Unknown status must be in (Late) status:

df.loc[
    df["Delivery_Status"] == "Unknown",
    "Delivery_Status"
] = "Late"

# At the end:
print(df["Delivery_Status"].value_counts())

## Final Validation

# Final Control : to realized that Cleaning has been done correctly.

# 1: DataFrame Dimensions AND Missing Value Controls:
print("Final Shape:", df.shape)

print("\nFinal Missing Values:")
print(df.isna().sum())

## Exact match with our handling missing

# Actual Delivery --> 35 : Unknown Actual delivery date, Has been changed to Missing Delivery Record
# Distance        --> 02 : Nonvalid distances, Has been changed to Missing
# Weight          --> 02 : Missing
# Shipping Cost   --> 02 : Missing
# Initial Errors  --> Carrier , Weight_KG : Handled previously

# Final Shape: ( 1470, 19 )
# 7 New Column has been added included Flags:
# Date_Error, Numeric_Error, Capacity_Error, Distance_Outlier, Vehicle_Capacity_KG, Data_Quality_Issue, Delivery_Status


### Final Check ###

print("Final Duplicates:", df.duplicated().sum())

print("\nFinal Quality Flags:")
print(
    df[
        [
            "Date_Error",
            "Numeric_Error",
            "Capacity_Error",
            "Distance_Outlier",
            "Data_Quality_Issue"
        ]
    ].sum()
)

df.to_csv(BASE_DIR/"data"/"processed"/"logistic_shipments_clean.csv", index=False) # For GitHub Path Address

# Review Project Pipeline:
# Raw Data -> Inspection -> Cleaning -> Validation ( Through Cleaning ) -> Processed Data

### Validation Included:

## 1) Date Validation: 3 rules reviewed
# Ship_Date < Order_Date              -> Nonvalid
# Planned_Delivery_Date < Ship_Date   -> Nonvalid
# Actual_Delivery_Date  < Ship_Date   -> Nonvalid

# ---> 16 Date_Error

## 2) Numeric Validation: 3 related rules reviewed
# Distance_KM <= 0
# Weight_KG <= 0
# Shipping_Cost <= 0

# ---> 6 Record Revealed

## 3) Vehicle Capacity Validation
# weight_KG > Vehicle_Capacity_KG

# ---> 4 Record Revealed

## 4) Distance/Route Validation
# Have been seen incompatible route ( Qazvin )

# ---> 1 Recorded was taken as Distance_Outlier

### All gathered in : "Data_Quality_Issue" : 27