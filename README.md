# stock_flow_decarb
California Transport Decarbonization Stock and Flow Model

Files included:

`stock_flow.py` contains the main code for the stock and flow model. 

The model simulates one year at a time, beginning at the start_year, and going through the end_year. The model iterates through the years, provided vheicle types, and provided fuel types. Stock(t) is the vehicle stock at the beginning of year t, and sales(t) and retirements(t) are the sales and retirements occuring during year t.

`run_model.ipynb` contains an example of how to run the model for various scenarios.

`AQ_Analysis_and_Plotting` contains the code to run an air quality analysis on the stock and flow scenarios and plot the results.



## Stock and flow model options included in `stock_flow.py`:

### Baseline Stock and Flow:
Sales profile and survival profiles are given, along with the initial stock by age and fuel type. The stock in each year is then calculated according to stock(t+1) = stock(t) + sales(t) - retirements(t). Stock is maintained by vehicle type, fuel type, and age. This function can be used if you don't already have an existing stock profile (i.e. the total number of vehicles of each type (summed accross fuel type and age in each year)). If you do not have a stock profile, this function can be used to determine the stock profile.



### Stock and Flow with Stock Profile Given:
In addition to the inputs to the baseline stock and flow function, this function takes in a stock profile, which is the total number of vehicles in a given category (e.g. T6, passenger vehicles, etc.) in each year. Sales by vehicle type and fuel type are still an input, but are scaled up or down to match the stock profile. It also includes the option to either calculate total VMT based on the age of the vehicles, or to set a total VMT profile (total VMT by vehicle category in each year). If you want to use a preexisting VMT profile, vmt_mode = "prof"


### Stock and Flow Model with Sales Percentages
This model is very similar to the stock and flow model with stock profile. The only difference is that in this version, sales percentages are given rather than sales numbers. If you already have a stock profile, and you don't have total sales numbers, but you do have sales percentages (e.g. breakdown by fuel type), this is probably the model you want to use. It also includes the option to either calculate total VMT based on the age of the vehicles, or to set a total VMT profile (total VMT by vehicle category in each year). If you want to use a preexisting VMT profile, vmt_mode = "prof"


### Stock and flow with sales percentages and early retirement
This model allows you to set sales percentages for each vehicle type, and a schedule for early retirements. A retirement schedule consists of the age at which to retire vehicles in each category, and the year in which the retirements are required. The retirements are phased in to avoid a sudden spike. The phase in period is set in the Inputs file. Currently, the retirements function assumes all ICE vehicles will be retired by the end of the study period, and that the phase-in for the final retirement is the same as for the initial retirement. (E.g. if the phase-in period is 5-years, remaining ICE will start to be retired 5-years before 2045). It also includes the option to either calculate total VMT based on the age of the vehicles, or to set a total VMT profile (total VMT by vehicle category in each year). If you want to use a preexisting VMT profile, vmt_mode = "prof"






## Required Data Inputs
* Stock by age and fuel type ("vintage")
* Annual total sales and sales pct
* Survival profiles for each vehicle type (not by fuel type)
* Total stock profile (optional)
* Total vmt profile (optional)
* Retirement schedule (if scenarios include early retirements)
* Fuel efficiency (in Diesel gallon equivalents) for each model year
* VMT degradatation (as percent of new vehicle VMT)
* List of vehicle types to include
* List of fuel types to include
* Path to input file


A sample input excel file is included.





