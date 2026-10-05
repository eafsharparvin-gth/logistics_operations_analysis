import pandas as pd

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent



df = pd.read_csv(BASE_DIR / "data" / "processed" / "logistic_shipments_clean.csv")

print(df.shape)
print(df.head())

print(df.dtypes)
# As its clear columns format specially ( Order_Date, Ship_Date, Planned_Delivery_Date, Actual_Delivery_Date ) reverting
# to the previous state ( STR )

date_columns = [
    "Order_Date",
    "Ship_Date",
    "Planned_Delivery_Date",
    "Actual_Delivery_Date"
]

for col in date_columns:
    df[col] = pd.to_datetime(df[col])


### KPIs ###

# 1) Delivery Performance           -> On-Time Rate, Late Rate, Average Delivery Time, Average Delay

# 2) Carrier Performance            -> Comparing Transportation companies in terms of Delay, Time, Cost

# 3) Warehouse Performance          -> Distributions Center Performance

# 4) Transportation Cost            -> Total Cost, Average Cost Per Shipment, Cost/KM, Cost/KG

# 5) Route Analysis                 -> Busy, Expensive and Delayed Routs

# 6) Vehicle Utilization / Capacity -> Vehicle Type, Weight Carried, Capacity Issue

# 7) Monthly Trend                  -> Posting Volume Monthly Trend, Delay, Cost

# 8) Data Quality KPIs              -> Data Quality Problem Rates


# Delivery Performances KPIs :
# 1)
delivery_counts = df["Delivery_Status"].value_counts()
print(delivery_counts)
on_time_count = delivery_counts["On Time"]
print(on_time_count)
valid_delivered_shipments = delivery_counts["On Time"] + delivery_counts["Late"]
on_time_delivery_rate = on_time_count/valid_delivered_shipments *100
print(on_time_delivery_rate)
# 2)
late_delivery_rate = delivery_counts["Late"]/valid_delivered_shipments *100
print(late_delivery_rate)

# 3) Average Delivery Time
# Actual_Delivery_Date Features : 1) Not Empty 2) Date_Error == False

# making temporary DataFrame ( Not new Column )

valid_delivery_time = df[
    (df["Actual_Delivery_Date"].notna()) &
    (df["Date_Error"] == False)
]
print(valid_delivery_time.shape)

## Delivery Time = Actual Delivery Date - Ship Date

# Keep going on temporary DataFrame:
valid_delivery_time["Delivery_Time"] = (
    valid_delivery_time["Actual_Delivery_Date"] - valid_delivery_time["Ship_Date"]
)

print(valid_delivery_time["Delivery_Time"].head())

# Making Days counts to Numbers:
valid_delivery_time["Delivery_Time_Days"] = valid_delivery_time["Delivery_Time"].dt.days
print(valid_delivery_time["Delivery_Time_Days"].head())

average_delivery_time = valid_delivery_time["Delivery_Time_Days"].mean()
print(average_delivery_time)

# 4) Average Delay

# Delay = Actual_Delivery_Date - Planned_Delivery_Date
# Not involve ON TIME Deliveries.
late_shipments = df[df["Delivery_Status"] == "Late"]
print(late_shipments.shape)

late_shipments["Delay"] = (late_shipments["Actual_Delivery_Date"] - late_shipments["Planned_Delivery_Date"])
print(late_shipments["Delay"].head())

# Making days count to number for calculating
late_shipments["Delay_Days"] = late_shipments["Delay"].dt.days
print(late_shipments["Delay_Days"].head())

average_delay_days = late_shipments["Delay_Days"].mean()
print(average_delay_days)

# 5) Maximum Delay
max_delay_days = late_shipments["Delay_Days"].max()
print(max_delay_days)

max_delay_index = late_shipments["Delay_Days"].idxmax() #  *** for just one worst delay shipment
print(max_delay_index)

#max_delay_shipment = late_shipments.loc[max_delay_index] # The Whole Record
#print(max_delay_shipment)

max_delay_shipment = late_shipments.loc[
    max_delay_index,
    [
        "Shipment_ID",
        "Warehouse",
        "Destination_City",
        "Carrier",
        "Vehicle_Type",
        "Planned_Delivery_Date",
        "Actual_Delivery_Date",
        "Delay_Days"
    ]
]

print(max_delay_shipment)

# *** if we have more than just one worst delay shipment

max_delay_shipments = late_shipments[late_shipments["Delay_Days"] == max_delay_days]
print(max_delay_shipments.shape)

#       Carrier Performance KPIs :
# Temporary DataFrame in order to Extract Unknown Carriers
carrier_data = df[
    df["Carrier"] != "Unknown"
]
print(carrier_data.shape)

# First knowing each carrier transportation count
carrier_shipment_count = carrier_data.groupby("Carrier")["Shipment_ID"].count()
print(carrier_shipment_count)

# 1) Each Carrier On Time Rate

# Eliminating  "Missing Delivery Records" & " Invalid Date" from Calculations
valid_carrier_deliveries = carrier_data[
    carrier_data["Delivery_Status"].isin(["On Time", "Late"])
]
print(valid_carrier_deliveries.shape)

# Knowing for Each Carrier how many Shipments are ON Time
carrier_on_time_counts = (
    valid_carrier_deliveries[
        valid_carrier_deliveries["Delivery_Status"] == "On Time"
    ]
    .groupby("Carrier")["Shipment_ID"].count()
)

print(carrier_on_time_counts)

carrier_valid_counts = (valid_carrier_deliveries.groupby("Carrier")["Shipment_ID"].count())
print(carrier_valid_counts)

carrier_on_time_rate = (carrier_on_time_counts/carrier_valid_counts * 100)
print(carrier_on_time_rate)

# 2) Each Carrier Late Rate

# Knowing for Each Carrier how many Shipments are Late
carrier_late_counts = (
    valid_carrier_deliveries[
        valid_carrier_deliveries["Delivery_Status"] == "Late"
    ]
    .groupby("Carrier")["Shipment_ID"].count()
)
print(carrier_late_counts)

carrier_late_rate = carrier_late_counts / carrier_valid_counts * 100
print(carrier_late_rate)

# 3) Average Delay By Carrier

carrier_average_delay = (
    late_shipments[
        late_shipments["Carrier"] != "Unknown"
    ]
    .groupby("Carrier")["Delay_Days"].mean()
)

print(carrier_average_delay)

# 4) Average Shipping Cost by Carrier

# Using "Carrier_data" in order to Not Calculating Unknown Items.

carrier_average_cost = (carrier_data.groupby("Carrier")["Shipping_Cost"].mean())
print(carrier_average_cost)
# It's not useful itself, Distances for example may be involved. Cost per KM can be useful in decision make.
# And they will be calculated in Transportation KPIs.


### Warehouse Performance
# there is no Unknown Warehouse so No need to primary filter

# 1) Each Warehouse Contains which Shipments

warehouse_shipment_counts = (
    df.groupby("Warehouse")["Shipment_ID"].count()
)

print(warehouse_shipment_counts)

# 2) On-Time Rate by Warehouse

valid_warehouse_deliveries = df[
    df["Delivery_Status"].isin(["On Time", "Late"])
]
# There is no other category in warehouse field for example "Unknown" like Carrier validation Categories.
print(valid_warehouse_deliveries.shape)

# Deduction form
warehouse_on_time_counts = (
    valid_warehouse_deliveries[
        valid_warehouse_deliveries["Delivery_Status"] == "On Time"
    ]
    .groupby("Warehouse")["Shipment_ID"].count()
)
print(warehouse_on_time_counts)

# Denominator of the fraction
warehouse_valid_counts = (
    valid_warehouse_deliveries
    .groupby("Warehouse")["Shipment_ID"]
    .count()
)
print(warehouse_valid_counts)

warehouse_on_time_rate = (warehouse_on_time_counts/ warehouse_valid_counts * 100)
print(warehouse_on_time_rate)

# 3) Late Rate by Warehouse

warehouse_late_counts = (
    valid_warehouse_deliveries[
        valid_warehouse_deliveries["Delivery_Status"] == "Late"
    ]
    .groupby("Warehouse")["Shipment_ID"].count()
)

print(warehouse_late_counts)

warehouse_late_rate= (warehouse_late_counts/ warehouse_valid_counts * 100)
print(warehouse_late_rate)

# 4) Average Delay By Warehouse

warehouse_average_delay = late_shipments.groupby("Warehouse")["Delay_Days"].mean()
print(warehouse_average_delay)

# 5) Average Shipping Cost By Warehouse

warehouse_average_shipping_cost = df.groupby("Warehouse")["Shipping_Cost"].mean()
# There is no need to build "valid" shipping cost; ".mean()" ignores NaN parameters By Default.
print(warehouse_average_shipping_cost)

# Although Tabriz DC has the most warehouse average shipping cost, But there are some ather different parameters that
# Might be effective such az Distance. We will Check these out on Transportation Routs KPIs.


###  Transportation Cost KPIs

# 1) Total Shipping Cost

# NO NEED to filter NaNs, Sum like Mean ignores them in case of existence.
# Previously we have Converted Invalid (TWO) Items to NaN.

total_shipment_cost = df["Shipping_Cost"].sum()
print(total_shipment_cost)

# 2) Average Shipping Cost
average_shipping_cost = df["Shipping_Cost"].mean()
print(average_shipping_cost)

# 3) Cost Per KM

# Conditions: Avoid these 2 kind of data : 1- NaN 2- Distance Outlier = False
valid_cost_per_km = df[
    (df["Shipping_Cost"].notna()) &
    (df["Distance_KM"].notna()) &
    (df["Distance_Outlier"] == False)
]

print(valid_cost_per_km.shape)

# Cost per KM = Shipping Cost / Distance KM

# Point : Because of various distances and specially each shipment unic ( expensive or cheap ) cost;
# Average of Cost/KM each shipment : Not clear out put, - Total Distance / Total Cost is much more Reliable

cost_per_km = (
    valid_cost_per_km["Shipping_Cost"].sum() /
    valid_cost_per_km["Distance_KM"].sum()
)

print(cost_per_km)

# Cost Per KG

# Like Cost Per KM : Total Shipment Cost / Total Weight

# Conditions For Filtering:
valid_cost_per_kg = df[
    (df["Shipping_Cost"].notna()) &
    (df["Weight_KG"].notna()) &
    (df["Capacity_Error"] == False)
]
print(valid_cost_per_kg.shape)

cost_per_kg = (
    valid_cost_per_kg["Shipping_Cost"].sum() /
    valid_cost_per_kg["Weight_KG"].sum()
)
print(cost_per_kg)

### Route Analysis KPIs
# Getting Out from General KPIs & Looking after Routs; to reveal which one is busier and more Costly and etc

# ROUTE = Warehouse + Destination City

# --> Back from PivotChart due to: Create Route column for Excel PivotTables
df["Route"] = df["Warehouse"] + " ---> " + df["Destination_City"]

# Shipment Count by Route
# To see each Route contains how many shipments

#route_shipment_counts = df.groupby(["Warehouse", "Destination_City"])
route_shipment_counts = (df.groupby(["Warehouse", "Destination_City"])["Shipment_ID"].count())
print(route_shipment_counts)

# 1) Which is The most frequented Route?

busiest_route_count = route_shipment_counts.max()
busiest_route = route_shipment_counts.idxmax()
print(busiest_route_count)
print(busiest_route)

# 2) Shipping Cost By Route

# 2-1) Total Shipping Cost By Route
route_total_cost = df.groupby(["Warehouse", "Destination_City"])["Shipping_Cost"].sum()
print(route_total_cost)

highest_route_cost = route_total_cost.max()
highest_route_cost_index= route_total_cost.idxmax()
print(highest_route_cost)
print(highest_route_cost_index)

# 2-2) Average Shipping Cost By Route

route_average_cost = df.groupby(["Warehouse", "Destination_City"])["Shipping_Cost"].mean()
print(route_average_cost)

highest_route_average_cost = route_average_cost.max()
highest_route_average_cost_index = route_average_cost.idxmax()
print(highest_route_average_cost)
print(highest_route_average_cost_index)

# Point : The difference what we earned in 2-1 and 2-2 is obvious.

# 3) Delivery Performance by Route
# we need shipments with just "On Time' & "Late" status :

valid_route_deliveries = df[
    df["Delivery_Status"].isin(["On Time", "Late"])
]
print(valid_route_deliveries)

route_late_count = (
    valid_route_deliveries[
        valid_route_deliveries["Delivery_Status"] == "Late"
    ]
    .groupby(["Warehouse", "Destination_City"])["Shipment_ID"]
    .count()
) # # Deduction form

print(route_late_count)

route_valid_counts = (
    valid_route_deliveries
    .groupby(["Warehouse", "Destination_City"])["Shipment_ID"]
    .count()
) # Denominator of a fraction

print(route_valid_counts)

route_late_rate = (route_late_count/route_valid_counts *100)

print(route_late_rate)

# point: In some routes mey just be 2 shipment, being one of them late; make the related route_late_rate worth.
# So due to transparent this percent we will make a condition of min shipment for every route in order to participate in formula.

eligible_routes = route_valid_counts[
    route_valid_counts >= 20
]
print(eligible_routes)

eligible_route_late_rate = route_late_rate.loc[eligible_routes.index]
print(eligible_route_late_rate)

highest_route_late_rate = eligible_route_late_rate.max()
highest_route_late_rate_index = eligible_route_late_rate.idxmax()
print(highest_route_late_rate)
print(highest_route_late_rate_index)

#
route_average_delay = (
    late_shipments
    .groupby(["Warehouse", "Destination_City"])["Delay_Days"]
    .mean()
)
print(route_average_delay)

highest_route_average_delay = route_average_delay.max()
highest_route_average_delay_index = route_average_delay.idxmax()
print(highest_route_average_delay)
print(highest_route_average_delay_index)

qazvin_mashhad_late_count = route_late_count.loc[
    ("Qazvin DC", "Mashhad")
]
# We have already built "route_late_count"
print(qazvin_mashhad_late_count)

# Report:
# Highest average delay: Qazvin DC --> Mashhad
#         Average delay: 1.83 days
#         Late Shipments: 6


## Vehicle Performance Utilization KPIs

# 1) Each vehicle type contains how many shipments?
vehicle_shipment_counts = df.groupby("Vehicle_Type")["Shipment_ID"].count()
print(vehicle_shipment_counts)

# 2) Average Weight by Vehicle Type
average_vehicle_type_weight = df.groupby("Vehicle_Type")["Weight_KG"].mean()
print(average_vehicle_type_weight)
# mean() also deny calculating NaN items, So there is no need to make a previous filter.

# Point: Average weight of vehicle_type is not enough to take into account the usage capacity of vehicle:
# carrying 8000 KG with 16000 KG capacity ---> 50% of Usage
# carrying  500 KG with 1000  KG capacity ---> 80% of Usage
# So Next KPI:

# 3) Average Capacity Utilization %

# 3-1) First Extract Shipments have Usable weight and haven't Capacity_Errors: So make Temporary DataFrame:

valid_vehicle_utilization = df[
    (df["Weight_KG"].notna()) &
    (df["Capacity_Error"] == False)
]
print(valid_vehicle_utilization.shape)

# We came back here from Dashboard section in order to add column with valid capacity and weight to df.
# Related items to : (False "Capacity_Error") & (Nan "Weight_KG") are considered as NaN, So that Excel ignores them in calculating formulas.
df.loc[
    (df["Weight_KG"].notna()) &
    (df["Capacity_Error"] == False),
    "Capacity_Utilization_Pct"
] = (
    df["Weight_KG"] /
    df["Vehicle_Capacity_KG"] * 100
)

# Again we came back from Dashboard ( Pivot Vehicle : Average capacity Error ) to:
# Convert Capacity_Error boolean values to 0/1 for calculating error rate in Excel pivot tables.
df["Capacity_Error_Flag"] = df["Capacity_Error"].astype(int)

# Come Back here from Dashboard: Convert Data_Quality_Issue boolean values to 0/1
# For Calculating Data Quality Issue Rate in Excel PivotTable
df["Data_Quality_Issue_Flag"] = df["Data_Quality_Issue"].astype(int)  # ( False -> 0 , True -> 1 )

# Getting back here from Dashboard Calculation: Create Delivery Time in days for Excel PivotTables
df.loc[
    (df["Actual_Delivery_Date"].notna()) &
    (df["Date_Error"] == False),
    "Delivery_Time_Days"
] = (
    df["Actual_Delivery_Date"] - df ["Ship_Date"]
).dt.days


# Next step: Making capacity usage percent:

valid_vehicle_utilization["Capacity_Utilization_Pct"] = (
    valid_vehicle_utilization["Weight_KG"] /
    valid_vehicle_utilization["Vehicle_Capacity_KG"] * 100
)
print(valid_vehicle_utilization)

# Review check
print(df.shape)
print(valid_vehicle_utilization.shape) # 6 Rows declines because of ( "Weight_KG" = NaN, "Capacity_Error+ = True )

# Now: Calculating each Vehicle used how much from its capacity percentage by average.

average_vehicle_utilization = (
    valid_vehicle_utilization
    .groupby("Vehicle_Type")["Capacity_Utilization_Pct"]
    .mean()
)
print(average_vehicle_utilization)

# 4) Next step: Capacity Errors

# how many Vehicle Type have capacity issue:

capacity_error_shipments = df[df["Capacity_Error"] == True]
print(capacity_error_shipments.shape)

# Now discover these 4  errors are related to which Vehicle_Type :

capacity_error_by_vehicle = (
    capacity_error_shipments
    .groupby("Vehicle_Type")["Shipment_ID"]
    .count()
) # Deduction Form
print(capacity_error_by_vehicle)

# 5) Capacity Error Rate

capacity_error_rate = (
    capacity_error_by_vehicle / vehicle_shipment_counts * 100
)
# vehicle_shipment_counts : Calculated Previously; considered as Denominator of fraction

print(capacity_error_rate)

# Point: WE KNOW As there are no capacity_error for other type of vehicles except "Light_Truck" their value shown as ; NaN
# So we are going to clear and clean that:

capacity_error_rate = capacity_error_rate.fillna(0)
print(capacity_error_rate)

# 6) Delivery Performance By Vehicle Type

# comparing: Utilization & Late Rate

# For begin: First we need to input valid "Delivery_Status" into calculation
valid_vehicle_deliveries = df[
    df["Delivery_Status"].isin(["On Time", "Late"])
]

print(valid_vehicle_deliveries.shape)

# Next Step: On-Time Count by Vehicle Type
vehicle_on_time_counts = (
    valid_vehicle_deliveries[
        valid_vehicle_deliveries["Delivery_Status"] == "On Time"
    ]
    .groupby("Vehicle_Type")["Shipment_ID"]
    .count()
)
# Deduction form
print(vehicle_on_time_counts)

# Then: For calculating On-Time Rate by Vehicle Type; we need Denominator ( All "On Time" & "Late" Delivery Statuses ) :

vehicle_valid_counts = (
    valid_vehicle_deliveries
        .groupby("Vehicle_Type")["Shipment_ID"]
        .count()

)
print(vehicle_valid_counts)

# Finally: On-Time Rate by Vehicle Type

vehicle_on_time_rate = (vehicle_on_time_counts / vehicle_valid_counts * 100)
print(vehicle_on_time_rate)

# Vehicle Late Rate :
vehicle_Late_rate = 100 -vehicle_on_time_rate
print(vehicle_Late_rate)

# 7) Average Delay by Vehicle Type

# We have already : "late_shipments" and "Delay_Days" column

vehicle_average_delay = (
    late_shipments
    .groupby("Vehicle_Type")["Delay_Days"]
    .mean()
)

# late_shipments -> just having delay shipments
# groupby("Vehicle_Type) -> Vehicle Type Separation
# Delay_days -> Delay Severity
print(vehicle_average_delay)

## Monthly Trend KPIs

# Related column: Ship_Date ( logistic )

# First Monthly Trend:
# Point : "Ship_Date" has already been changed to ' datetime ' format

df["Shipment_Month"] = df["Ship_Date"].dt.to_period("M")
print(df["Shipment_Month"].head())
print(df.head())

# 1) Monthly Shipment Volume : How many Shipments has been sent from warehouses per month?
# And having already "Shipment_month" made:

monthly_shipment_counts = df.groupby("Shipment_Month")["Shipment_ID"].count()
print(monthly_shipment_counts)

# To showing month's names in report:

#df["Shipment_Month_Name"] = df["Ship_Date"].dt.month_name()
#monthly_name_shipment_count = df.groupby("Shipment_Month_Name")["Shipment_ID"].count()
#print(monthly_name_shipment_count)

# We will use month's names in Excell report, here we will keep them deactivated.

# 2) Month On-Time Rate

valid_monthly_deliveries = df[
    df["Delivery_Status"].isin(["On Time", "Late"])
]
print(valid_monthly_deliveries.shape)

monthly_on_time_counts = (
    valid_monthly_deliveries[
        valid_monthly_deliveries["Delivery_Status"] == "On Time"
    ]
    .groupby("Shipment_Month")["Shipment_ID"]
    .count()
) # Deduction form
print(monthly_on_time_counts)

monthly_valid_counts = (
    valid_monthly_deliveries
    .groupby("Shipment_Month")["Shipment_ID"]
    .count()
) # Denominator of a fraction

print(monthly_valid_counts)

monthly_on_time_rate = monthly_on_time_counts / monthly_valid_counts * 100
print(monthly_on_time_rate)

# 3) Monthly Late Time Rate:

monthly_late_time_rate = 100 - monthly_on_time_rate
print(monthly_late_time_rate)

# 4) Monthly Average Delay

# In each month  that shipments had delay, How many days that was on average

monthly_late_shipments = df[
    df["Delivery_Status"] == "Late"
]
print(monthly_late_shipments.shape)

monthly_late_shipments["Delay_Days"] = (
    monthly_late_shipments["Actual_Delivery_Date"] -
    monthly_late_shipments["Planned_Delivery_Date"]
).dt.days

# Conversion difference of date to numbers directly.

monthly_average_delay = (
    monthly_late_shipments
    .groupby("Shipment_Month")["Delay_Days"]
    .mean()
)

print(monthly_average_delay)

# 5) Monthly Shipping Cost

# 5-1) Total Shipping Cost by Month

monthly_total_shipping_cost = (
    df
    .groupby("Shipment_Month")["Shipping_Cost"]
    .sum()
)
print(monthly_total_shipping_cost)

# Because of various numbers of shipments of each month, Can not be told just from total cost on and itself that X month was most expensive.
# So The Next Rational Step:

# 5-2) Average Shipping Cost Per Shipment By Month
monthly_average_shipping_cost = (
    df
    .groupby("Shipment_Month")["Shipping_Cost"]
    .mean()
)
print(monthly_average_shipping_cost)

# Point: we just have converted missing data into NaN values previously, So in .sum() or .mean() It Ignores the NaN Values.

# 6) DATA QUALITY KPIs

# 6-1) Total Data Quality Issue
total_data_quality_isues = df["Data_Quality_Issue"].sum()
print(total_data_quality_isues)

# "Data_Quality_Issue" is a boolean column which counts ( True = 1, False = 0 ), On Counts.

data_quality_issue_rate = total_data_quality_isues / len(df) * 100
print(data_quality_issue_rate)

# Next Step: what was the 27 problems:

# We had 4 main Flags:
# Data_Error
# Numeric_Error
# Capacity_Error
# Distance_Outlier

# We put them all in one place:
data_quality_flag_counts = df[
    ["Date_Error", "Numeric_Error", "Capacity_Error", "Distance_Outlier"]
].sum()
print(data_quality_flag_counts)
# Sum is : 27

# Next Step:
data_quality_flag_rates = data_quality_flag_counts / len(df) * 100
print(data_quality_flag_rates)

# 6-2) Data Quality Issue Rate by Month
# In every month what percent of shipments had at least one issue problem

monthly_data_quality_issue_counts = (
    df.groupby("Shipment_Month")["Data_Quality_Issue"]
    .sum()
)
print(monthly_data_quality_issue_counts)
# Sum is : 27

monthly_data_quality_issue_rate = monthly_data_quality_issue_counts / monthly_shipment_counts * 100
print(monthly_data_quality_issue_rate)

data_quality_issue_count = df["Data_Quality_Issue"].sum()
print(data_quality_issue_count)
# Point: .sum() ok due to sum of True Booleans not .count()

## Output Presentation

# First step building Summary Table for main KPIs
# Total Shipments - On-Time Delivery Rate - Late Delivery Rate - Average Delivery Time - Average Delay - Total Shipping Cost -
# Average Shipping Cost - Cost per KM - Cost per KG - Data Quality Issue Rate

# For beginning we make a DataFrame for these KPIs

# 1) Over All KPI Summery

overall_kpi_summary = pd.DataFrame({
    "KPI": [
        "Total_Shipments",
        "On-Time Delivery Rate",
        "Late Delivery Rate",
        "Average Delivery Time",
        "Average Delay",
        "Total Shipping Cost",
        "average Shipping Cost Per Shipment",
        "Cost per KM",
        "Cost per KG",
        "Data Quality Issue Rate",
        "Max Delay Days",
        "Data Quality Issue Count"
    ],
    "Value": [
        len(df),
        on_time_delivery_rate,
        late_delivery_rate,
        average_delivery_time,
        average_delay_days,
        total_shipment_cost,
        average_shipping_cost,
        cost_per_km,
        cost_per_kg,
        data_quality_issue_rate,
        max_delay_days,
        data_quality_issue_count
    ]
})
print(overall_kpi_summary)

# 2) Summary Table : Carrier Performance Summery

# Difference Between this Table and Previous one: in previous we had only 2 general column no other items,
# But in this table we are going to compare different Carriers so we are going to have more than One Columns.

carrier_summary = pd.DataFrame({
    "Shipment_Count": carrier_shipment_count,
})

# Adding: Carrier On-Time Rate
carrier_summary["Carrier On-Time Rate (%)"] = carrier_on_time_rate

# Next Column: Carrier Late Rate
carrier_summary["Carrier Late Rate (%)"] = carrier_late_rate

# Show All Columns On DataFrame
pd.set_option("display.max_columns", None)
pd.set_option("display.width", None)
print(carrier_summary)

# Next Column: Average Delay Days

carrier_summary["Carrier Average Delay (Days)"] = carrier_average_delay

# Next Column (No: 5 ) Carrier Average Shipping Cost
carrier_summary["Carrier Average Shipping Cost"] = carrier_average_cost

carrier_summary.index.name = "Carrier" # For Naming column in Excel output.
print(carrier_summary)

# 3) Summary Table: Warehouse Summary

# ) Shipment Count
warehouse_summary = pd.DataFrame({
    "Warehouse_Shipment_Count": warehouse_shipment_counts
})

# ) Warehouse On-Time Rate (%)
warehouse_summary["Warehouse On-Time Rate (%)"]= warehouse_on_time_rate

# ) Warehouse Late Rate (%)
warehouse_summary["Warehouse Late Rate (%)"] =  warehouse_late_rate

# ) Warehouse Average Delay (Days)
warehouse_summary["Warehouse Average Delay (Days)"] = warehouse_average_delay

# ) Warehouse Average Shipping Cost
warehouse_summary["Warehouse Average Shipping Cost"] = warehouse_average_shipping_cost

warehouse_summary.index.name = "Warehouse" # For column naming in Excel output.
print(warehouse_summary)

## 4) Summary Table: Vehicle Summary

# )
vehicle_summary = pd.DataFrame({
    "Vehicle Shipment Count": vehicle_shipment_counts
})

# ) Average Capacity Utilization
vehicle_summary["Vehicle Average Capacity Utilization (%)"] = average_vehicle_utilization

# ) Capacity Error Rate (%)
vehicle_summary["Capacity Error Rate (%)"] = capacity_error_rate
#print(vehicle_summary)
# We have already Converted NaN Items in Capacity_error_rate into " 0 " . There is No need to Change it here.

# ) Vehicle On-Time Rate (%)
vehicle_summary["Vehicle On-Time Rate (%)"] = vehicle_on_time_rate

# ) Vehicle Late Rate (%)
vehicle_summary["Vehicle Late Rate (%)"] = vehicle_Late_rate

# ) Vehicle Average Delay (%)
vehicle_summary["Vehicle Average Delay (Days)"] = vehicle_average_delay

vehicle_summary.index.name = "Vehicle Type"
print(vehicle_summary)

## 5) Summary Table : Route Summary

# ) Route Shipment Count
route_summary = pd.DataFrame({
    "Route Shipment Count": route_shipment_counts
})

# ) Route Total Shipping Cost
route_summary["Route Total Shipping Cost"] = route_total_cost

# ) Route Average Shipping Cost
route_summary["Route Average Shipping Cost"] = route_average_cost

# ) Route On-Time Rate (%)
route_on_time_rate = 100 - eligible_route_late_rate

route_summary["Route On-Time Rate (%)"] = route_on_time_rate

# Route Late Rate (%)
route_summary["Route Late Rate (%)"] = eligible_route_late_rate

route_summary.index.names = ["Warehouse", "Destination City"] # we have 2 index to name them in Excel output
print(route_summary)

# We have Multi index DataFrame in this Summary Table, In Excel Export we decide whether these 2 columns be shown in one or remain separated.

## 6) Summary Table : Monthly Summary

monthly_summary = pd.DataFrame({
    "Monthly Shipment Count" : monthly_shipment_counts
})

monthly_summary["Monthly On-Time Rate (%)"] = monthly_on_time_rate

monthly_summary["Monthly Late Rate (%)"]= monthly_late_time_rate

monthly_summary["Monthly Average Delay (Days)"] = monthly_average_delay

monthly_summary["Monthly Total Shipping Cost"] = monthly_total_shipping_cost

monthly_summary["Monthly Average Shipping Cost"] = monthly_average_shipping_cost

monthly_summary["Monthly Data Quality Issue Count"] = monthly_data_quality_issue_counts

monthly_summary["Monthly Data Quality Issue Rate (%)"] = monthly_data_quality_issue_rate

monthly_summary.index.name = "Shipment Month" # First Column Name ( index ) in Excel Output
print(monthly_summary)

## 7) Data Quality Summary

# Structure is similar to Overall KPI Somehow ,Each record would be related to its own Flag.
# And we have already made both Series before: 1) data_quality_flag_counts 2)data_quality_flag_rates

data_quality_summary = pd.DataFrame({
    "Flag Count": data_quality_flag_counts
})

data_quality_summary["Flag Rate (%)"] =data_quality_flag_rates

data_quality_summary.index.name = "Data Quality Flag" # Index is the name of Flags
print(data_quality_summary)

## Output Preparation is completed with 7 Tables :
# Overall -> Carrier -> Warehouse -> Vehicle -> Route -> Monthly -> Data Quality


### Excel Output:

excel_report_path = (BASE_DIR / "output" / "logistics_operations_report.xlsx")

with pd.ExcelWriter(excel_report_path) as writer:
    overall_kpi_summary.to_excel(
        writer,
        sheet_name= "Overall KPI",
        index=False
    )

    carrier_summary.to_excel(writer, sheet_name = "Carrier Performance", index = True)
    warehouse_summary.to_excel(writer, sheet_name = "Warehouse Performance", index = True)
    vehicle_summary.to_excel(writer, sheet_name = "Vehicle Performance", index = True)
    route_summary.to_excel(writer, sheet_name = "Route Performance", index = True)
    monthly_summary.to_excel(writer, sheet_name = "Monthly Performance", index = True)
    data_quality_summary.to_excel(writer, sheet_name = "Data Quality", index = True)

    df.loc[df["Delivery_Status"] == "Late", "Delay_Days"] = (df["Actual_Delivery_Date"] - df["Planned_Delivery_Date"]
                                                                ).dt.days

    df.to_excel(
        writer,
        sheet_name = "Processed Data",
        index = False
    )
# 20th column : "Shipment Month" is added in df platform for our Data Table.


# Managing DataFrame on Excel files due to add Sheets to the file.
# First sheet name is "Overall KPI"
# in carrier summary we need indexes ( transportation names ) so we set it TRUE.


## Pivot Tables / Dashboard   includes:

# 1) Monthly Performance 2) Carrier Performance 3) Warehouse Performance 4) Vehicle Performance 5) Route Performance
# 6) Monthly Performance 7) Data Quality 8) Processed Data 9) Pivot Monthly

# Making Delay_Days on df so we can make a pivot of that
# Business Logic: Just put Delivery Status == "Late" on new column in df others should be NaN
# df.loc[df["Delivery_Status"] == "Late", "Delivery_Days"] = (df["Actual_Delivery_Date"] - df["Planned_Delivery_Date"]
#                                                             ).dt.days
# we transfered it to line 930 in order to be made in excel out put



