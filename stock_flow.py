## Stock and Flow functions

#Import packages
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
#from plotnine import *
import os

# Helper Functions

## Function to get age distribution of initial stock
def vintage0(v,input_file):
    age_dist = pd.read_excel(input_file,sheet_name = (v+"_vintage")).fillna(0)
    return age_dist

# Function to read in total sales from input file
def get_sales(v_types, input_file):
    all_sales = {}
    for v in v_types:
        sales = pd.read_excel(input_file,sheet_name = (v+"_sales")).fillna(0)
        sales = sales.set_index("year")
        all_sales[v] = sales
    return all_sales
    
#Function to read in survival profiles
def get_survival(v,input_file):
    survival = pd.read_excel(input_file,sheet_name = (v+"_survival")).fillna(0)
    survival = survival.set_index("Age")
    return survival

#Function to read in stock profile
def get_stock(input_file):
    tot_stock = pd.read_excel(input_file, sheet_name = "stock_profile").fillna(0)
    tot_stock = tot_stock.set_index("year")
    return tot_stock
 
#Function to read in sales percentages
def get_sales_pct(v, input_file):
    sales_pct = pd.read_excel(input_file, sheet_name = (v+"_sales_pct")).fillna(0)
    sales_pct = sales_pct.set_index("year")
    return sales_pct

#Function to define sales percentages assuming ZEVs reach 100% by a given year (target_year), and a fraction of
# zero-emission vehicles that are electric (frac_elec). This assumes all other zero-emission vehicles are hydrogen
def create_sales_pct(v, input_file, target_year, frac_elec, base_year, end_year, sales_mode):
    if sales_mode == "linear":
        sales_base = pd.read_excel(input_file, sheet_name = v+"_sales_pct").fillna(0).set_index("year")
        sales_pct = pd.DataFrame(index = np.arange(base_year, end_year+1), columns = sales_base.columns)
        sales_pct.loc[base_year,:] = sales_base.loc[base_year,:]
        #target_year sales %
        sales_pct.loc[target_year:end_year, :] = 0
        sales_pct.loc[target_year:end_year,"Electricity"] = 100*frac_elec
        sales_pct.loc[target_year:end_year,"Hydrogen"] = 100*(1-frac_elec)
        sales_pct = sales_pct.astype(float).interpolate()
    else:
        sales_base = pd.read_excel(input_file, sheet_name = v+"_sales_pct").fillna(0).set_index("year")
        sales_pct = pd.DataFrame(index = np.arange(base_year, end_year+1), columns = sales_base.columns)
        sales_pct.loc[base_year:(target_year-1),:] = sales_base.loc[base_year:(target_year-1),:]
        sales_pct.loc[target_year:end_year, :] = 0
        sales_pct.loc[target_year:end_year,"Electricity"] = 100*frac_elec
        sales_pct.loc[target_year:end_year,"Hydrogen"] = 100*(1-frac_elec)
        sales_pct = sales_pct.fillna(0)
    
    
    return sales_pct

# Function to read in retirement profile
def get_ret_prof(input_file, retirement_profile):
    if len(retirement_profile) > 0:
        ret_prof = pd.DataFrame(index = retirement_profile.keys(), columns = ["ret_age","ret_year","pct_replaced","phase_in"])
        for i in ret_prof.index:
            ret_prof.loc[i] = [retirement_profile[i]["ret_age"],retirement_profile[i]["ret_year"], 100, retirement_profile[i]["phase_in"]]
    else:
        ret_prof = pd.read_excel(input_file, sheet_name = ("retirement_schedule"))
        ret_prof = ret_prof.set_index("veh_type")
    return ret_prof

# Function to read in retirement rules -- which types are being forced to retire
def ret_rules(input_file):
    ret_rules = pd.read_excel(input_file, sheet_name = ("retirement_rules"))
    remove = pd.Series(ret_rules["remove"])
    replace = pd.Series(ret_rules["replace"])
    ret = {"remove":remove, "replace":replace}
    return ret

#Function to calculate early retirements
# def get_early_ret(y, v, model, ret_prof, to_remove, end_year): 
#     ban_year = ret_prof.loc[v,"ret_year"]
#     ban_age = ret_prof.loc[v,"ret_age"]
#     phase_in = ret_prof.loc[v, "phase_in"]
#     if y >= ban_year:
#         for f in to_remove:
#             max_age = model.loc[(model.year == y) & (model.veh_type == v) & (model.fuel_type == f),"age"].max()
#             # Remove all vehicles >= the retirement age
#             for age in range(ban_age,max_age):
#                 model.loc[(model.year == y) & 
#                           (model.veh_type == v) & 
#                           (model.fuel_type == f) & 
#                           (model.age == age),"early_ret"] = model.loc[(model.year == y) & 
#                           (model.veh_type == v) & 
#                           (model.fuel_type == f) & 
#                           (model.age == age),"stock"] - model.loc[(model.year == y) & 
#                           (model.veh_type == v) & 
#                           (model.fuel_type == f) & 
#                           (model.age == age),"retirements"]
                
#     elif y in range(ban_year - phase_in, ban_year):
#         #phase in removal of vehicles that will eventually be banned
#         for f in to_remove:
#             max_age = model.loc[(model.year == y) & (model.veh_type == v) & (model.fuel_type == f),"age"].max()
#             for age in range(ban_age - phase_in, max_age):
#                 model.loc[(model.year == y) & 
#                           (model.veh_type == v) & 
#                           (model.fuel_type == f) & 
#                           (model.age == age),"early_ret"] = (model.loc[(model.year == y) & 
#                           (model.veh_type == v) & 
#                           (model.fuel_type == f) & 
#                           (model.age == age),"stock"] - model.loc[(model.year == y) & 
#                           (model.veh_type == v) & 
#                           (model.fuel_type == f) & 
#                           (model.age == age),"retirements"])/((ban_year - y+1)*1)
                
#     ## EXTRA RETIREMENTS IN 2045 ASSUMING THE SAME PHASE-IN PERIOD -- This function could be reorganized
#     ban_year = end_year-1 # Note the -1 here is because we want zero ICE vehicles by the start of 2045 to have zero emissions in 2045.
#     ban_age = 0
#     if y == ban_year:
#         for f in to_remove:
#             max_age = model.loc[(model.year == y) & (model.veh_type == v) & (model.fuel_type == f),"age"].max()
#             # Remove all vehicles >= the retirement age
#             for age in range(ban_age,max_age):
#                 model.loc[(model.year == y) & 
#                           (model.veh_type == v) & 
#                           (model.fuel_type == f) & 
#                           (model.age == age),"early_ret"] = model.loc[(model.year == y) & 
#                           (model.veh_type == v) & 
#                           (model.fuel_type == f) & 
#                           (model.age == age),"stock"] - model.loc[(model.year == y) & 
#                           (model.veh_type == v) & 
#                           (model.fuel_type == f) & 
#                           (model.age == age),"retirements"]
                
#     elif y in range(ban_year - phase_in, ban_year):
#         #phase in removal of vehicles that will eventually be banned
#         for f in to_remove:
#             max_age = model.loc[(model.year == y) & (model.veh_type == v) & (model.fuel_type == f),"age"].max()
#             for age in range(ban_age - phase_in, max_age):
#                 model.loc[(model.year == y) & 
#                           (model.veh_type == v) & 
#                           (model.fuel_type == f) & 
#                           (model.age == age),"early_ret"] = (model.loc[(model.year == y) & 
#                           (model.veh_type == v) & 
#                           (model.fuel_type == f) & 
#                           (model.age == age),"stock"] - model.loc[(model.year == y) & 
#                           (model.veh_type == v) & 
#                           (model.fuel_type == f) & 
#                           (model.age == age),"retirements"])/((ban_year - y+1)*1)

def get_early_ret(y, v, model, ret_prof, to_remove, end_year): 
    ban_year = ret_prof.loc[v,"ret_year"]
    ban_age = ret_prof.loc[v,"ret_age"]
    phase_in = ret_prof.loc[v, "phase_in"]
    if y >= ban_year:
        for f in to_remove:
            max_age = model.loc[(model.year == y) & (model.veh_type == v) & (model.fuel_type == f),"age"].max()
            # Remove all vehicles >= the retirement age
            for age in range(ban_age,max_age):
                model.loc[(model.year == y) & 
                          (model.veh_type == v) & 
                          (model.fuel_type == f) & 
                          (model.age == age),"early_ret"] = model.loc[(model.year == y) & 
                          (model.veh_type == v) & 
                          (model.fuel_type == f) & 
                          (model.age == age),"stock"] - model.loc[(model.year == y) & 
                          (model.veh_type == v) & 
                          (model.fuel_type == f) & 
                          (model.age == age),"retirements"]
                
    elif y in range(ban_year - phase_in, ban_year):
        #phase in removal of vehicles that will eventually be banned
        for f in to_remove:
            max_age = model.loc[(model.year == y) & (model.veh_type == v) & (model.fuel_type == f),"age"].max()
            for age in range(ban_age - phase_in, max_age):
                model.loc[(model.year == y) & 
                          (model.veh_type == v) & 
                          (model.fuel_type == f) & 
                          (model.age == age),"early_ret"] = (model.loc[(model.year == y) & 
                          (model.veh_type == v) & 
                          (model.fuel_type == f) & 
                          (model.age == age),"stock"] - model.loc[(model.year == y) & 
                          (model.veh_type == v) & 
                          (model.fuel_type == f) & 
                          (model.age == age),"retirements"])/((ban_year - y+1)*1)
                
    ## EXTRA RETIREMENTS IN 2045 ASSUMING THE SAME PHASE-IN PERIOD -- This function could be reorganized
    ban_year = end_year-1 # Note the -1 here is because we want zero ICE vehicles by the start of 2045 to have zero emissions in 2045.
    ban_age = 0
    if y == ban_year:
        for f in to_remove:
            max_age = model.loc[(model.year == y) & (model.veh_type == v) & (model.fuel_type == f),"age"].max()
            # Remove all vehicles >= the retirement age
            for age in range(ban_age,max_age):
                model.loc[(model.year == y) & 
                          (model.veh_type == v) & 
                          (model.fuel_type == f) & 
                          (model.age == age),"early_ret"] = model.loc[(model.year == y) & 
                          (model.veh_type == v) & 
                          (model.fuel_type == f) & 
                          (model.age == age),"stock"] - model.loc[(model.year == y) & 
                          (model.veh_type == v) & 
                          (model.fuel_type == f) & 
                          (model.age == age),"retirements"]
                
    elif y in range(ban_year - phase_in, ban_year):
        #phase in removal of vehicles that will eventually be banned
        for f in to_remove:
            max_age = model.loc[(model.year == y) & (model.veh_type == v) & (model.fuel_type == f),"age"].max()
            for age in range(ban_age - phase_in, max_age):
                model.loc[(model.year == y) & 
                          (model.veh_type == v) & 
                          (model.fuel_type == f) & 
                          (model.age == age),"early_ret"] = (model.loc[(model.year == y) & 
                          (model.veh_type == v) & 
                          (model.fuel_type == f) & 
                          (model.age == age),"stock"] - model.loc[(model.year == y) & 
                          (model.veh_type == v) & 
                          (model.fuel_type == f) & 
                          (model.age == age),"retirements"])/((ban_year - y+1)*1)
  
        
   
#Function to read in fuel economy
def get_fuel_econ(model, input_file, veh_types, fuel_types):
    fuel_econ = pd.read_excel(input_file, sheet_name = "fuel_eff").astype({'Model Year':float, 'veh_class':str, 'Fuel':str, 'fuel_economy':float})
    print(fuel_econ.dtypes)
    model["model_year"] = model.year - model.age
    #model["fuel_eff"] = -1
    
    fuel_econ2 = {}
    for i, row in fuel_econ.iterrows():
        fuel_econ2[(row["Model Year"], row["veh_class"], row["Fuel"])] = row["fuel_economy"]

    model["fuel_eff"] = -1
    model.loc[model.stock > 0,"fuel_eff"] = model.loc[model.stock >0].apply(lambda row: fuel_econ2[(row["model_year"], row["veh_type"], row["fuel_type"])], axis = 1)
           

#Function to read in fuel economy
def get_fuel_econ(model, input_file, veh_types, fuel_types):
    fuel_econ = pd.read_excel(input_file, sheet_name = "fuel_eff").astype({'Model Year':float, 'veh_class':str, 'Fuel':str, 'fuel_economy':float})
    print(fuel_econ.dtypes)
    model["model_year"] = model.year - model.age
    #model["fuel_eff"] = -1
    
    fuel_econ2 = {}
    for i, row in fuel_econ.iterrows():
        fuel_econ2[(row["Model Year"], row["veh_class"], row["Fuel"])] = row["fuel_economy"]

    model["fuel_eff"] = -1
    model.loc[model.stock > 0,"fuel_eff"] = model.loc[model.stock >0].apply(lambda row: fuel_econ2[(row["model_year"], row["veh_type"], row["fuel_type"])], axis = 1)


#Function to calculate vmt
def get_vmt(model, input_file, veh_types, vmt_mode):
    new_vmt = pd.read_excel(input_file, sheet_name = "new_vmt")
    new_vmt = new_vmt.set_index("veh_type")
    vmt_deg = pd.read_excel(input_file, sheet_name = "vmt_deg")
    vmt_deg = vmt_deg.set_index("age")
    model["vmt"] = 0
    
    for v in veh_types:
            for age in range(0,model.loc[model.veh_type == v,"age"].max()):
                # print(model.loc[(model.veh_type == v) & 
                #           (model.age == age), "vmt"])
                # print(new_vmt.loc[v,"vmt"])
                # print(model.loc[(model.veh_type == v) & (model.age == age), "stock"])
                model.loc[(model.veh_type == v) & 
                          (model.age == age), "vmt"] = new_vmt.loc[v,"vmt"]*vmt_deg.loc[age, v]*model.loc[(model.veh_type == v) & (model.age == age), "stock"]/100
                          

    if vmt_mode == "prof":
        print(input_file)
        vmt_prof = pd.read_excel(input_file, sheet_name = "vmt_prof")
        vmt_prof = vmt_prof.set_index("year")
        for y in model.year.unique():
            for v in veh_types:
                #scale vmt to match desired total
                tot_vmt = model.loc[(model.year == y) & (model.veh_type == v),"vmt"].sum()
                model.loc[(model.year == y) & (model.veh_type == v),"vmt"] *= vmt_prof.loc[y,v]/tot_vmt
        
#Function to calculate CO2
def get_co2(model, veh_types, fuel_types):
    model["co2"] = 0
    model.loc[model.fuel_type == "Gasoline", "co2"] = model.loc[model.fuel_type == "Gasoline", "fuel_consumption"]*9.48328/1000
    model.loc[model.fuel_type == "Diesel", "co2"] = model.loc[model.fuel_type == "Diesel", "fuel_consumption"]*11.1945/1000
    model.loc[model.fuel_type == "Natural Gas", "co2"] = model.loc[model.fuel_type == "Natural Gas", "fuel_consumption"]*8.651661/1000
    model.loc[model.fuel_type == "Hybrid", "co2"] = model.loc[model.fuel_type == "Hybrid", "fuel_consumption"]*9.48328/1000 #Currently assuming all hybrids are gasoline and fuel consumption is just gasoline, not electric. 
    
    
#Function to calculate average vehicle lifetime from survival profile
def get_lifetime(v, input_file):
    surv_prof = get_survival(v, input_file)
    above_50 = surv_prof[surv_prof["%"] > 50].index.max()
    below_50 = surv_prof[surv_prof["%"] <= 50].index.min()
    median_age = -1*(50+above_50*surv_prof.loc[above_50,"%"]-surv_prof.loc[below_50,"%"]*below_50)/(-1*surv_prof.loc[above_50,"%"]+surv_prof.loc[below_50,"%"])
    
    return median_age
 
#Function to calculate vehicle-years remaining of vehicles that are retired early
def get_veh_years_remaining(model,input_file):
    veh_types = model.veh_type.unique()
    model["veh_years_removed"] = 0
    for v in veh_types:
        lifetime = get_lifetime(v, input_file)
        model.loc[model.veh_type == v,"veh_years_removed"] = model.loc[model.veh_type == v, "early_ret"] * (lifetime - model.loc[model.veh_type == v,"age"])
    model.loc[model.veh_years_removed < 0,"veh_years_removed"] = 0

 
#Function to calculate cumulative CO2
def get_cum_co2(model):
    years = np.arange(model.year.min(), model.year.max()+1)
    cum_co2 = pd.DataFrame(columns = ["cum_co2"], index = years)
    for y in years:
        cum_co2.loc[y,"cum_co2"] = model.loc[model.year <= y,"co2"].sum()
        
    return cum_co2

#Function to calculate the cumulative vehicle years remaining of early retired vehicles
def get_cum_veh_years_removed(model):
    years = np.arange(model.year.min().astype(int), model.year.max().astype(int)+1)
    cum_veh_years_removed = pd.DataFrame(columns = ["cum_veh_years_removed"], index = years)
    for y in years:
        cum_veh_years_removed.loc[y,"cum_veh_years_removed"] = model.loc[model.year <= y,"veh_years_removed"].sum()
        
    return cum_veh_years_removed


#Function to make some basic plots of a scenario - NOTE: As is, this only works for scenarios with early retirements.
def plot_scenario_results(model, input_file):
    display(ggplot(model, aes(x = "year", 
                   y = "stock", fill = "fuel_type"))+ geom_bar(position = "stack", stat = "identity"))
    display(ggplot(model, aes(x = "year", 
                   y = "sales", fill = "fuel_type"))+ geom_bar(position = "stack", stat = "identity"))
    display(ggplot(model, aes(x = "year", 
                   y = "early_ret", fill = "fuel_type"))+ geom_bar(position = "stack", stat = "identity"))
    display(ggplot(model, aes(x = "year", 
                   y = "co2", fill = "fuel_type"))+ geom_bar(position = "stack", stat = "identity"))
    
    
    cum_co2 = get_cum_co2(model)
    if "veh_years_removed" in model.columns:
        pass 
    else:
        get_veh_years_remaining(model, input_file)
    cum_veh_years_removed = get_cum_veh_years_removed(model)
    
    f, ax= plt.subplots(1,3, figsize = (20,10))
    ax = ax.flatten()
    ax[0].plot(cum_veh_years_removed.index,cum_veh_years_removed.cum_veh_years_removed)
    ax[0].set_title("Cumulative Vehicle Years Removed")
    
    ax[1].plot(cum_co2.index,cum_co2.cum_co2)
    ax[1].set_title("Cumulative CO2 Emissions")
    
    ax[2].plot(cum_co2.cum_co2,cum_veh_years_removed.cum_veh_years_removed)
    ax[2].set_title("Cumulative Vehicle Years Removed vs. Cumulative CO2 Emissions")
    
#Function to make some basic plots of the baseline scenario (no early retirements).
def plot_baseline_results(model):
    display(ggplot(model, aes(x = "year", 
                   y = "stock", fill = "fuel_type"))+ geom_bar(position = "stack", stat = "identity"))
    display(ggplot(model, aes(x = "year", 
                   y = "sales", fill = "fuel_type"))+ geom_bar(position = "stack", stat = "identity"))
    display(ggplot(model, aes(x = "year", 
                   y = "retirements", fill = "fuel_type"))+ geom_bar(position = "stack", stat = "identity"))
    display(ggplot(model, aes(x = "year", 
                   y = "co2", fill = "fuel_type"))+ geom_bar(position = "stack", stat = "identity"))
    
    
    cum_co2 = get_cum_co2(model)
    
    f, ax= plt.subplots(1,1, figsize = (20,10))

    ax.plot(cum_co2.index,cum_co2.cum_co2)
    ax.set_title("Cumulative CO2 Emissions")

    
def extract_stock_profile(model, veh_types):
    years = model.year.unique()
    tot_stock = pd.DataFrame(index = years, columns = veh_types)
    for v in veh_types:
        for y in years:
            tot_stock.loc[y,v] = model.loc[(model.year == y) & (model.veh_type == v),"stock"].sum()
    return tot_stock


def extract_vmt_profile(model, veh_types):
    years = model.year.unique()
    tot_vmt = pd.DataFrame(index = years, columns = veh_types)
    for v in veh_types:
        for y in years:
            tot_vmt.loc[y,v] = model.loc[(model.year == y) & (model.veh_type == v),"vmt"].sum()
    return tot_vmt

def retire_old_cars(model, n_cars, curr_year, veh_type, fuel_types):
    to_retire = n_cars
    new_rets = 0
    age = model.loc[(model.year == curr_year) & 
                (model.fuel_type.isin(fuel_types)) &
               (model.veh_type == veh_type),"age"].max()
    while to_retire > new_rets:
        for f in fuel_types:
            if to_retire > new_rets:
                # print(f, curr_year, age)
                st = model.loc[(model.year == curr_year) & 
                        (model.fuel_type == f) &
                       (model.veh_type == veh_type) & 
                               (model.age == age),"stock"].item()
                r = model.loc[(model.year == curr_year) & 
                        (model.fuel_type == f) &
                       (model.veh_type == veh_type) & 
                               (model.age == age),"retirements"].item()
                e_r = model.loc[(model.year == curr_year) & 
                        (model.fuel_type == f) &
                       (model.veh_type == veh_type) & 
                               (model.age == age),"early_ret"].item()
                if (new_rets + st - r - e_r) <= to_retire:
                    model.loc[(model.year == curr_year) & 
                        (model.fuel_type == f) &
                       (model.veh_type == veh_type) & 
                               (model.age == age),"early_ret"] += st - r - e_r

                    new_rets += st - r - e_r
                    # if st - r - e_r:
                    #     print(f"if retiring {st - r - e_r} {age} old {veh_type} {f} vehicles in {curr_year}")
                else:
                    model.loc[(model.year == curr_year) & 
                        (model.fuel_type == f) &
                       (model.veh_type == veh_type) & 
                               (model.age == age),"early_ret"] += to_retire - new_rets
                    # if to_retire - new_rets:
                        # print(f"else retiring {to_retire - new_rets} {age} old {veh_type} {f} vehicles in {curr_year}")
                    new_rets += (to_retire - new_rets)
                    
        age = age - 1
        if age <0:
            break
    return new_rets

def get_expected_stock(model, ret_prof, v , y, to_remove, survival):
    ban_year = ret_prof.loc[v,"ret_year"]
    ban_age = ret_prof.loc[v,"ret_age"]
    phase_in = ret_prof.loc[v, "phase_in"]
    expected_stock = 0
    max_age = model.age.max()#model.loc[(model.year == y) & 
                #(model.fuel_type.isin(to_remove)) &
               #(model.veh_type == v),"age"].max()
    for age in np.arange(max((ban_age - phase_in+1),0), (max_age-phase_in+1)):
        expected_stock += (model.loc[(model.year == y) & 
                (model.fuel_type.isin(to_remove)) &
               (model.veh_type == v) & 
                (model.age == age),"stock"]).sum() * survival.loc[(age + phase_in-1), "%"] / survival.loc[age,"%"]
    return expected_stock

def retire_leftover_cars(model, y, v, fuel_types, ret_age):
    r_tot = 0
    for f in fuel_types:        
        r = model.loc[(model.year == y) & 
                  (model.veh_type == v) & 
                  (model.fuel_type == f) & 
                  (model.age >= ret_age),"stock"] - model.loc[(model.year == y) & 
                  (model.veh_type == v) & 
                  (model.fuel_type == f) & 
                  (model.age >= ret_age),"retirements"] - model.loc[(model.year == y) & 
                  (model.veh_type == v) & 
                  (model.fuel_type == f) & 
                  (model.age >= ret_age),"early_ret"]
        model.loc[(model.year == y) & 
                  (model.veh_type == v) & 
                  (model.fuel_type == f) & 
                  (model.age >= ret_age),"early_ret"] += r
        r_tot+=r.sum()
    return r_tot



####### STOCK AND FLOW MODELS ########
def stock_and_flow_baseline(start_year, end_year, veh_types, fuel_types, input_file, vmt_mode):
    #begin at base year
    year = start_year
    #initialize model
    model = pd.DataFrame(columns = ["age","stock","retirements","sales","veh_type","fuel_type","year"]).astype({'age': int, 'stock': float, 'retirements': float, 'sales': float, 'veh_type': str, 'fuel_type': str, 'year': float})
    #load sales data
    all_sales = get_sales(veh_types, input_file)  
    
    
    for y in range(start_year,end_year+1):
        for v in veh_types:
            #load initial vintage and survival profiles
            vintage = vintage0(v, input_file)
            survival = get_survival(v, input_file)
            
            for f in fuel_types:
                #print(y, v, f)
                #Stock and flow for year 0:
                if y == start_year:
                    temp = vintage[["Age",f]].copy()
                    temp.columns = ["age","stock"]
                    temp["retirements"] = 0
                    print(y)
                    print("stock t:",temp.stock.sum())
                    
                else:
                    temp = model.loc[(model.veh_type == v) & (model.fuel_type == f) & (model.year == y-1),["age","stock","sales","retirements"]].copy()
                    temp["age"] = temp["age"]+1
                    temp.loc[temp["age"]==max(temp["age"]),:] = 0
                    print(y)
                    print("stock t-1:", temp.stock.sum())
                    print("retirements t-1:", temp.retirements.sum())
                    print("sales t-1:",temp.sales.sum())
                    temp["stock"] = temp.stock - temp.retirements + temp.sales
                    print("stock t:", temp.stock.sum())
                    
                    
                temp["sales"] = 0
                temp.loc[temp.age==0,"sales"] = all_sales[v].loc[y,f]
                
                for age in range(1, temp.age.max()):
                    temp.loc[temp["age"]==age,"retirements"] = temp.loc[temp["age"]==age, "stock"]*(survival.loc[age, "%"] - survival.loc[age+1, "%"])/survival.loc[age, "%"]
                temp.loc[temp["age"]==temp.age.max(),"retirements"] = temp.loc[temp["age"]==temp.age.max(),"stock"]
                temp["veh_type"] = v
                temp["fuel_type"] = f
                temp["year"] = y
                
                model = model.append(temp)
                
    get_fuel_econ(model, input_file, veh_types, fuel_types)
    get_vmt(model, input_file, veh_types, vmt_mode)
    model["fuel_consumption"] = model["vmt"]/model["fuel_eff"]
    get_co2(model, veh_types, fuel_types)
                
    return model
   
    
def stock_and_flow(start_year, end_year, veh_types, fuel_types, input_file, stock_prof, vmt_mode):
    #begin at base year
    year = start_year
    #initialize model
    model = pd.DataFrame(columns = ["age","stock","retirements","sales","veh_type","fuel_type","year"]).astype({'age': int, 'stock': float, 'retirements': float, 'sales': float, 'veh_type': str, 'fuel_type': str, 'year': float})
    #load sales data
    all_sales = get_sales(veh_types, input_file) 
    stock_profile = get_stock(input_file)
       
    for y in range(start_year,end_year+1):
        for v in veh_types:
            #load initial vintage and survival profiles
            vintage = vintage0(v, input_file)
            tot_stock = vintage[fuel_types].sum().sum()
            survival = get_survival(v, input_file)
            # print(vintage)
            for f in fuel_types:
                print(y, v, f)
                #Stock and flow for year 0:
                if y == start_year:
                    temp = vintage[["Age",f]].copy()
                    temp.columns = ["age","stock"]
                    # print(stock_profile.loc[y,v], tot_stock, stock_profile.loc[y,v]/tot_stock)
                    temp["stock"] = temp["stock"]*stock_profile.loc[y,v]/tot_stock
                    temp["retirements"] = 0
                    for age in range(1, temp.age.max()):
                        temp.loc[temp["age"]==age,"retirements"] = temp.loc[temp["age"]==age, "stock"]*(survival.loc[age, "%"] - survival.loc[age+1, "%"])/survival.loc[age, "%"]
                    temp["sales"] = 0
                    #sales are desired stock in next year(scaled by fuel ratio) - current stock + retirements
                    f_ratio = vintage[f].sum()/tot_stock
                    temp.loc[temp.age==0,"sales"] = stock_profile.loc[y+1,v]*f_ratio - temp.stock.sum() + temp.retirements.sum()
                    
                    
                else:
                    temp = model.loc[(model.veh_type == v) & (model.fuel_type == f) & (model.year == y-1),["age","stock","sales","retirements"]].copy()
                    temp["age"] = temp["age"]+1
                    temp.loc[temp["age"]==max(temp["age"]),:] = 0
                    f_ratio = temp.stock.sum()/model.loc[(model.veh_type == v) & (model.year == y-1),"stock"].sum().item()
                    temp.stock = temp.stock - temp.retirements+temp.sales                   
                    for age in range(1, temp.age.max()):
                        temp.loc[temp["age"]==age,"retirements"] = temp.loc[temp["age"]==age, "stock"]*(survival.loc[age, "%"] - survival.loc[age+1, "%"])/survival.loc[age, "%"]
                    temp.loc[temp["age"]==temp.age.max(),"retirements"] = temp.loc[temp["age"]==temp.age.max(),"stock"]
                    temp["sales"] = 0
                    temp.loc[temp.age==0, "sales"] = stock_profile.loc[y+1, v]*f_ratio - temp.stock.sum()+temp.retirements.sum()
                    
                
                temp["veh_type"] = v
                temp["fuel_type"] = f
                temp["year"] = y
                
                model = model.append(temp)
                
    # get_fuel_econ(model, input_file, veh_types, fuel_types)
    # get_vmt(model, input_file, veh_types, vmt_mode)
    # model["fuel_consumption"] = model["vmt"]/model["fuel_eff"]
    # get_co2(model, veh_types, fuel_types)
    
    return model
 
    
def stock_and_flow_sales(start_year, end_year, veh_types, fuel_types, input_file, stock_prof, vmt_mode):
    #begin at base year
    year = start_year
    #initialize model
    model = pd.DataFrame(columns = ["age","stock","retirements","sales","veh_type","fuel_type","year"]).astype({'age': int, 'stock': float, 'retirements': float, 'sales': float, 'veh_type': str, 'fuel_type': str, 'year': float})
    all_sales = get_sales(veh_types, input_file) 
    stock_profile = get_stock(input_file)
       
    for y in range(start_year,end_year+1):
        for v in veh_types:
            #load initial vintage and survival profiles
            vintage = vintage0(v, input_file)
            tot_stock = vintage[fuel_types].sum().sum()
            survival = get_survival(v, input_file)
            sales_pct = get_sales_pct(v,input_file)
            #print(vintage)
            for f in fuel_types:
                print(y, v, f)
                #Stock and flow for year 0:
                if y == start_year:
                    temp = vintage[["Age",f]].copy()
                    temp.columns = ["age","stock"]
                    #print(stock_profile.loc[y,v], tot_stock, stock_profile.loc[y,v]/tot_stock)
                    temp["stock"] = temp["stock"]*stock_profile.loc[y,v]/tot_stock
                    temp["retirements"] = 0
                    for age in range(1, temp.age.max()):
                        temp.loc[temp["age"]==age,"retirements"] = temp.loc[temp["age"]==age, "stock"]*(survival.loc[age, "%"] - survival.loc[age+1, "%"])/survival.loc[age, "%"]
                    temp["sales"] = 0
                    #sales are desired stock in next year(scaled by fuel ratio) - current stock + retirements
                    f_ratio = vintage[f].sum()/tot_stock
                    # temp.loc[temp.age==0,"sales"] = stock_profile.loc[y+1,v]*f_ratio - temp.stock.sum() + temp.retirements.sum()
                    
                    
                else:
                    temp = model.loc[(model.veh_type == v) & (model.fuel_type == f) & (model.year == y-1),["age","stock","sales","retirements"]].copy()
                    temp["age"] = temp["age"]+1
                    temp.loc[temp["age"]==max(temp["age"]),:] = 0
                    f_ratio = temp.stock.sum()/model.loc[(model.veh_type == v) & (model.year == y-1),"stock"].sum()
                    temp.stock = temp.stock - temp.retirements+temp.sales                   
                    for age in range(1, temp.age.max()):
                        temp.loc[temp["age"]==age,"retirements"] = temp.loc[temp["age"]==age, "stock"]*(survival.loc[age, "%"] - survival.loc[age+1, "%"])/survival.loc[age, "%"]
                    temp.loc[temp["age"]==temp.age.max(),"retirements"] = temp.loc[temp["age"]==temp.age.max(),"stock"]
                    temp["sales"] = 0
                    # temp.loc[temp.age==0, "sales"] = stock_profile.loc[y+1, v]*f_ratio - temp.stock.sum()+temp.retirements.sum()
        
                
                temp["veh_type"] = v
                temp["fuel_type"] = f
                temp["year"] = y
                
                model = model.append(temp)
            #Calculate total sales for vehicle type
            tot_sales = stock_profile.loc[y+1, v] - model.loc[(model.year==y) & (model.veh_type == v),"stock"].sum() + model.loc[(model.year==y) & (model.veh_type == v),"retirements"].sum()
            for f in fuel_types:
                model.loc[(model.year==y) & (model.veh_type == v) & (model.fuel_type == f) & (model.age == 0),"sales"] = tot_sales * sales_pct.loc[y,f]/100
    get_fuel_econ(model, input_file, veh_types, fuel_types)
    get_vmt(model, input_file, veh_types, vmt_mode)
    model["fuel_consumption"] = model["vmt"]/model["fuel_eff"]
    get_co2(model, veh_types, fuel_types)
                
    return model



# def stock_and_flow_sales_ret(start_year, end_year, veh_types, fuel_types, input_file, stock_prof, vmt_mode, target_year = {}, frac_elec = {}, retirement_profile = [], retirement_mode = [], sales_mode = "", replacement_mode = ""):
#     #initialize model
#     model = pd.DataFrame(columns = ["age","stock","retirements","sales","veh_type","fuel_type","year","early_ret"]).astype({'age': int, 'stock': float, 'retirements': float, 'sales': float, 'veh_type': str, 'fuel_type': str, 'year': float, 'early_ret': float})
#     all_sales = get_sales(veh_types, input_file) 
#     stock_profile = get_stock(input_file)
#     ret_profs = []
#     for r in retirement_profile:        
#         ret_profs.append(get_ret_prof(input_file, r))
#     to_remove = ret_rules(input_file)["remove"].unique()
#     to_replace = ret_rules(input_file)["replace"].unique()
    
#     def advance_model(model, v, year, num_years, expected_stock, ret_prof_idx):
#         model = model.copy()
#         tot_retired = 0
        
#         vintage = vintage0(v, input_file)
#         tot_stock = vintage[fuel_types].sum().sum()
#         survival = get_survival(v, input_file)
#         if len(target_year) > 0:
#             sales_pct = create_sales_pct(v,input_file,target_year[v],frac_elec[v],start_year,end_year, sales_mode)
#         else:
#             sales_pct = get_sales_pct(v,input_file)

#         for y in range(year,year+num_years):
#             print(y)
#             #load initial vintage and survival profiles
            

#             for f in fuel_types:
#                 # print(y, v, f)
#                 #Stock and flow for year 0:
#                 if y == start_year:
#                     temp = vintage[["Age",f]].copy()
#                     temp.columns = ["age","stock"]
#                     temp["stock"] = temp["stock"]*stock_profile.loc[y,v]/tot_stock
#                     temp["retirements"] = 0
#                     for age in range(1, temp.age.max()):
#                         temp.loc[temp["age"]==age,"retirements"] = temp.loc[temp["age"]==age, "stock"]*(survival.loc[age, "%"] - survival.loc[age+1, "%"])/survival.loc[age, "%"]
#                     temp["sales"] = 0
#                     temp["early_ret"] = 0

#                 else:
#                     temp = model.loc[(model.veh_type == v) & (model.fuel_type == f) & (model.year == y-1),["age","stock","sales","retirements","early_ret"]].copy()
#                     temp["age"] = temp["age"]+1
#                     temp.loc[temp["age"]==max(temp["age"]),:] = 0
#                     f_ratio = temp.stock.sum()/model.loc[(model.veh_type == v) & (model.year == y-1),"stock"].sum()
#                     temp.stock = temp.stock - temp.retirements - temp.early_ret +temp.sales                   
#                     for age in range(1, temp.age.max()):                           
#                         temp.loc[temp["age"]==age,"retirements"] = temp.loc[temp["age"]==age, "stock"]*(survival.loc[age, "%"] - survival.loc[age+1, "%"])/survival.loc[age, "%"]
#                     temp.loc[temp["age"]==temp.age.max(),"retirements"] = temp.loc[temp["age"]==temp.age.max(),"stock"]

#                     temp["sales"] = 0
#                     temp["early_ret"] = 0


#                 temp["veh_type"] = v
#                 temp["fuel_type"] = f
#                 temp["year"] = y

#                 model = model.append(temp)

#             leftover_vehicles = np.zeros(len(ret_profs))

#             for i, ret_prof in enumerate(ret_profs):
#                 ban_year = ret_prof.loc[v,"ret_year"]
#                 ban_age = ret_prof.loc[v,"ret_age"]
#                 phase_in = ret_prof.loc[v, "phase_in"]  
#                 r = 1.2
#                 if (y >= (ban_year - phase_in) and (y < ban_year)):
#                     already_early_retired = model.loc[(model.year == y) & (model.veh_type == v),"early_ret"].sum()
#                     retiring = 0
#                     if retirement_mode[v][i] == "uniform":
#                         retiring = expected_stock/phase_in - already_early_retired
#                     elif retirement_mode[v][i] == "ramp":
#                         a0 = expected_stock*(1-r)/(1-r**(phase_in))
#                         retiring = a0*(r**(phase_in - ban_year+y)) - already_early_retired
#                     else:
#                         print("Invalid Retirement Mode")
#                     tot_retired += retire_old_cars(model, retiring, y, v,to_remove)
#                 if y >= ban_year:
#                     tot_retired += retire_leftover_cars(model, y, v, to_remove, ban_age)

#                 young_retired = model.loc[(model.year == ban_year-1) & (model.fuel_type.isin(to_remove)) & (model.veh_type == v) & (model.age < ban_age), "early_ret"].sum()
#                 old_remaining = (model.loc[(model.year == ban_year-1) & (model.fuel_type.isin(to_remove)) & (model.veh_type == v) & (model.age >= ban_age), "stock"].sum() -
#                                  model.loc[(model.year == ban_year-1) & (model.fuel_type.isin(to_remove)) & (model.veh_type == v) & (model.age >= ban_age), "early_ret"].sum() -
#                                  model.loc[(model.year == ban_year-1) & (model.fuel_type.isin(to_remove)) & (model.veh_type == v) & (model.age >= ban_age), "retirements"].sum())
#                 if young_retired > 0:
#                     leftover_vehicles[i] = -young_retired
#                 elif old_remaining > 0.5:
#                     leftover_vehicles[i] = old_remaining
#                 elif phase_in > 1:
#                     if retirement_mode[v][i] == "uniform":
#                         leftover_vehicles[i] = (model.loc[(model.year == ban_year-1) & (model.fuel_type.isin(to_remove)) & (model.veh_type == v) & (model.age >= ban_age), "early_ret"].sum() -
#                                                 model.loc[(model.year == ban_year-2) & (model.fuel_type.isin(to_remove)) & (model.veh_type == v) & (model.age >= ban_age), "early_ret"].sum())
#                     if retirement_mode[v][i] == "ramp":
#                         leftover_vehicles[i] = (model.loc[(model.year == ban_year-1) & (model.fuel_type.isin(to_remove)) & (model.veh_type == v) & (model.age >= ban_age), "early_ret"].sum() -
#                                                 r * model.loc[(model.year == ban_year-2) & (model.fuel_type.isin(to_remove)) & (model.veh_type == v) & (model.age >= ban_age), "early_ret"].sum())

#             #Calculate total sales for vehicle type
#             max_age = model.age.max()
#             # tot_sales = (stock_profile.loc[y+1, v] - model.loc[(model.year==y) & (model.veh_type == v),"stock"].sum() + 
#             #              model.loc[(model.year==y) & (model.veh_type == v),"retirements"].sum() +  
#             #              model.loc[(model.year==y) & (model.veh_type == v),"early_ret"].sum())
#             tot_sales = (stock_profile.loc[y+1, v] - model.loc[(model.year==y) & (model.veh_type == v) & (model.age < max_age),"stock"].sum() + 
#                          model.loc[(model.year==y) & (model.veh_type == v) & (model.age < max_age),"retirements"].sum() +  
#                          model.loc[(model.year==y) & (model.veh_type == v) & (model.age < max_age),"early_ret"].sum())
            
#             for f in fuel_types:
#                 #update sales
#                 # print(f"{f}_sales =", tot_sales * sales_pct.loc[y,f]/100)
#                 model.loc[(model.year==y) & (model.veh_type == v) & (model.fuel_type == f) & (model.age == 0),"sales"] = tot_sales * sales_pct.loc[y,f]/100
            
            
            
            
#             if (replacement_mode == "ZEV_only") and (y < ban_year) and (y >= ban_year - phase_in):
#                 y_diff = ban_year - y
#                 tot_sales_all = (stock_profile.loc[y+1, v] - model.loc[(model.year==y) & (model.veh_type == v) & (model.age < max_age),"stock"].sum() + 
#                          model.loc[(model.year==y) & (model.veh_type == v) & (model.age < (ban_age - y_diff)),"retirements"].sum() +  
#                          model.loc[(model.year==y) & (model.veh_type == v) & (model.age < (ban_age - y_diff)),"early_ret"].sum())
                
#                 zev_only_sales = (model.loc[(model.year==y) & (model.veh_type == v) & (model.age >= (ban_age - y_diff)) & (model.age < max_age),"retirements"].sum() +  
#                          model.loc[(model.year==y) & (model.veh_type == v) & (model.age >= (ban_age - y_diff)) & (model.age < max_age),"early_ret"].sum())
                   
#                 for f in fuel_types:
#                 #update sales
#                     model.loc[(model.year==y) & (model.veh_type == v) & (model.fuel_type == f) & (model.age == 0),"sales"] = tot_sales_all * sales_pct.loc[y,f]/100
                

#                 model.loc[(model.year==y) & (model.veh_type == v) & (model.fuel_type == "Electricity") & (model.age == 0),"sales"]+= zev_only_sales*frac_elec[v]
#                 model.loc[(model.year==y) & (model.veh_type == v) & (model.fuel_type == "Hydrogen") & (model.age == 0),"sales"]+= zev_only_sales*(1-frac_elec[v])
                
            
#             if (replacement_mode == "ZEV_only") and (y >= ban_year):
#                 tot_sales_all = (stock_profile.loc[y+1, v] - model.loc[(model.year==y) & (model.veh_type == v) & (model.age < max_age),"stock"].sum() + 
#                          model.loc[(model.year==y) & (model.veh_type == v) & (model.age < ban_age),"retirements"].sum() +  
#                          model.loc[(model.year==y) & (model.veh_type == v) & (model.age < ban_age),"early_ret"].sum())
                
#                 zev_only_sales = (model.loc[(model.year==y) & (model.veh_type == v) & (model.age >= ban_age) & (model.age < max_age),"retirements"].sum() +  
#                          model.loc[(model.year==y) & (model.veh_type == v) & (model.age >= ban_age) & (model.age < max_age),"early_ret"].sum())
#                 #sales_all_types = tot_sales_all - zev_only_sales
#                 # print("retirements: ",model.loc[(model.year==y) & (model.veh_type == v) & (model.age >= ban_age) & (model.age < max_age),"retirements"].sum())
#                 # print("early retirements: ",model.loc[(model.year==y) & (model.veh_type == v) & (model.age >= ban_age) & (model.age < max_age),"early_ret"].sum())
#                 # print(f"{tot_sales_all=}")
#                 # print(f"{zev_only_sales=}")
#                 # #print(f"{sales_all_types=}")


                
#                 for f in fuel_types:
#                 #update sales
#                     model.loc[(model.year==y) & (model.veh_type == v) & (model.fuel_type == f) & (model.age == 0),"sales"] = tot_sales_all * sales_pct.loc[y,f]/100
                

#                 model.loc[(model.year==y) & (model.veh_type == v) & (model.fuel_type == "Electricity") & (model.age == 0),"sales"]+= zev_only_sales*frac_elec[v]
#                 model.loc[(model.year==y) & (model.veh_type == v) & (model.fuel_type == "Hydrogen") & (model.age == 0),"sales"]+= zev_only_sales*(1-frac_elec[v])
                
#             # print(f"total sales in year {y}: {tot_sales}")
#             # print("stock t+1 = ",stock_profile.loc[y+1, v])
#             # print("current stock = ",model.loc[(model.year==y) & (model.veh_type == v),"stock"].sum())
#             # print("retirements = ",model.loc[(model.year==y) & (model.veh_type == v),"retirements"].sum())
#             # print("early retirements = ",model.loc[(model.year==y) & (model.veh_type == v),"early_ret"].sum())
            
        
#         return model, leftover_vehicles[ret_prof_idx]

#     for v in veh_types:
#         #print(v)
#         ret_profs.sort(key = lambda ret_prof: ret_prof.loc[v, "ret_year"])
#         for i in range(len(ret_profs) - 1):
#             ret_prof1 = ret_profs[i]
#             ret_prof2 = ret_profs[i+1]
#             if ret_prof2.loc[v, "ret_year"] - ret_prof2.loc[v, "phase_in"] < ret_prof1.loc[v, "ret_year"]:
#                 raise ValueError("Invalid Retirement Profile. Overlapping phase-in")
            
#         #begin at base year
#         year = start_year
#         while year <= end_year:
#             for i, ret_prof in enumerate(ret_profs):
#                 ban_year = ret_prof.loc[v,"ret_year"]
#                 phase_in = ret_prof.loc[v, "phase_in"]
#                 if phase_in > 0 and year == ban_year - phase_in:
#                     survival = get_survival(v, input_file)
#                     expected_stock = get_expected_stock(model, ret_prof, v,(ban_year - phase_in-1),to_remove, survival)
#                     # tol = 10
#                     # l_bound = expected_stock*0.5
#                     # u_bound = expected_stock*2
#                     # l_bound = 0
#                     # u_bound = model.loc[(model.veh_type == v) & (model.fuel_type.isin(to_remove)) & (model.year == year-1),"stock"].sum()
#                     l_bound = 0
#                     u_bound = expected_stock
#                     _, leftover_vehicles = advance_model(model, v, year, phase_in, u_bound, i)
#                     while leftover_vehicles > 0:
#                         l_bound = u_bound
#                         u_bound *= 1.3
#                         _, leftover_vehicles = advance_model(model, v, year, phase_in, u_bound, i)
#                         print("Searching for bounds")
#                         print(f"{u_bound=}")
#                         print(f"{l_bound=}")
#                         print(f"{leftover_vehicles=}")
                        
#                     while l_bound <= u_bound:
#                         m = (l_bound + u_bound)/2
#                         tol = max(1e-4*m,10)
#                         model_temp, leftover_vehicles = advance_model(model, v, year, phase_in, m, i)
#                         print(f"{u_bound=}")
#                         print(f"{l_bound=}")
#                         print(f"{m=}")
#                         print(f"{leftover_vehicles=}")
#                         if leftover_vehicles > tol:
#                             l_bound = m+1
#                         elif leftover_vehicles < -tol:
#                             u_bound = m-1
#                         else:
#                             model = model_temp
#                             break
#                     year += phase_in
#                     break
#             else:
#                 model, _ = advance_model(model, v, year, 1, 0, 0)
#                 year += 1
    
#     get_fuel_econ(model, input_file, veh_types, fuel_types)
#     get_vmt(model, input_file, veh_types, vmt_mode)
#     model["fuel_consumption"] = model["vmt"]/model["fuel_eff"]
#     get_co2(model, veh_types, fuel_types)

#     return model

def stock_and_flow_sales_ret(start_year, end_year, veh_types, fuel_types, input_file, stock_prof, vmt_mode, target_year = {}, frac_elec = {}, retirement_profile = [], retirement_mode = [], sales_mode = "", replacement_mode = ""):
    #initialize model
    model = pd.DataFrame(columns = ["age","stock","retirements","sales","veh_type","fuel_type","year","early_ret"]).astype({'age': int, 'stock': float, 'retirements': float, 'sales': float, 'veh_type': str, 'fuel_type': str, 'year': float, 'early_ret': float})
    all_sales = get_sales(veh_types, input_file) 
    stock_profile = get_stock(input_file)
    ret_profs = []
    for r in retirement_profile:        
        ret_profs.append(get_ret_prof(input_file, r))
    to_remove = ret_rules(input_file)["remove"].unique()
    to_replace = ret_rules(input_file)["replace"].unique()
    
    def advance_model(model, v, year, num_years, expected_stock, ret_prof_idx):
        model = model.copy()
        tot_retired = 0
        
        vintage = vintage0(v, input_file)
        tot_stock = vintage[fuel_types].sum().sum()
        survival = get_survival(v, input_file)
        if len(target_year) > 0:
            sales_pct = create_sales_pct(v,input_file,target_year[v],frac_elec[v],start_year,end_year, sales_mode)
        else:
            sales_pct = get_sales_pct(v,input_file)

        for y in range(year,year+num_years):
            print(y)
            #load initial vintage and survival profiles
            

            for f in fuel_types:
                # print(y, v, f)
                #Stock and flow for year 0:
                if y == start_year:
                    temp = vintage[["Age",f]].copy()
                    temp.columns = ["age","stock"]
                    temp["stock"] = temp["stock"]*stock_profile.loc[y,v]/tot_stock
                    temp["retirements"] = 0
                    for age in range(1, temp.age.max()):
                        temp.loc[temp["age"]==age,"retirements"] = temp.loc[temp["age"]==age, "stock"]*(survival.loc[age, "%"] - survival.loc[age+1, "%"])/survival.loc[age, "%"]
                    temp["sales"] = 0
                    temp["early_ret"] = 0

                else:
                    temp = model.loc[(model.veh_type == v) & (model.fuel_type == f) & (model.year == y-1),["age","stock","sales","retirements","early_ret"]].copy()
                    temp["age"] = temp["age"]+1
                    temp.loc[temp["age"]==max(temp["age"]),:] = 0
                    f_ratio = temp.stock.sum()/model.loc[(model.veh_type == v) & (model.year == y-1),"stock"].sum()
                    temp.stock = temp.stock - temp.retirements - temp.early_ret +temp.sales                   
                    for age in range(1, temp.age.max()):                           
                        temp.loc[temp["age"]==age,"retirements"] = temp.loc[temp["age"]==age, "stock"]*(survival.loc[age, "%"] - survival.loc[age+1, "%"])/survival.loc[age, "%"]
                    temp.loc[temp["age"]==temp.age.max(),"retirements"] = temp.loc[temp["age"]==temp.age.max(),"stock"]

                    temp["sales"] = 0
                    temp["early_ret"] = 0
                    
                temp.loc[temp["retirements"] < 0, "sales"] -= temp.loc[temp["retirements"] < 0, "retirements"]
                temp.loc[temp["retirements"] < 0, "retirements"] = 0


                temp["veh_type"] = v
                temp["fuel_type"] = f
                temp["year"] = y

                model = model.append(temp)

            leftover_vehicles = np.zeros(len(ret_profs))

            for i, ret_prof in enumerate(ret_profs):
                ban_year = ret_prof.loc[v,"ret_year"]
                ban_age = ret_prof.loc[v,"ret_age"]
                phase_in = ret_prof.loc[v, "phase_in"]  
                r = 1.2
                if (y >= (ban_year - phase_in) and (y < ban_year)):
                    already_early_retired = model.loc[(model.year == y) & (model.veh_type == v),"early_ret"].sum()
                    retiring = 0
                    if retirement_mode[v][i] == "uniform":
                        retiring = expected_stock/phase_in - already_early_retired
                    elif retirement_mode[v][i] == "ramp":
                        a0 = expected_stock*(1-r)/(1-r**(phase_in))
                        retiring = a0*(r**(phase_in - ban_year+y)) - already_early_retired
                    else:
                        print("Invalid Retirement Mode")
                    tot_retired += retire_old_cars(model, retiring, y, v,to_remove)
                if y >= ban_year:
                    tot_retired += retire_leftover_cars(model, y, v, to_remove, ban_age)

                young_retired = model.loc[(model.year == ban_year-1) & (model.fuel_type.isin(to_remove)) & (model.veh_type == v) & (model.age < ban_age), "early_ret"].sum()
                old_remaining = (model.loc[(model.year == ban_year-1) & (model.fuel_type.isin(to_remove)) & (model.veh_type == v) & (model.age >= ban_age), "stock"].sum() -
                                 model.loc[(model.year == ban_year-1) & (model.fuel_type.isin(to_remove)) & (model.veh_type == v) & (model.age >= ban_age), "early_ret"].sum() -
                                 model.loc[(model.year == ban_year-1) & (model.fuel_type.isin(to_remove)) & (model.veh_type == v) & (model.age >= ban_age), "retirements"].sum())
                if young_retired > 0:
                    leftover_vehicles[i] = -young_retired
                elif old_remaining > 0.5:
                    leftover_vehicles[i] = old_remaining
                elif phase_in > 1:
                    if retirement_mode[v][i] == "uniform":
                        leftover_vehicles[i] = (model.loc[(model.year == ban_year-1) & (model.fuel_type.isin(to_remove)) & (model.veh_type == v) & (model.age >= ban_age), "early_ret"].sum() -
                                                model.loc[(model.year == ban_year-2) & (model.fuel_type.isin(to_remove)) & (model.veh_type == v) & (model.age >= ban_age), "early_ret"].sum())
                    if retirement_mode[v][i] == "ramp":
                        leftover_vehicles[i] = (model.loc[(model.year == ban_year-1) & (model.fuel_type.isin(to_remove)) & (model.veh_type == v) & (model.age >= ban_age), "early_ret"].sum() -
                                                r * model.loc[(model.year == ban_year-2) & (model.fuel_type.isin(to_remove)) & (model.veh_type == v) & (model.age >= ban_age), "early_ret"].sum())

            #Calculate total sales for vehicle type
            max_age = model.age.max()
            # tot_sales = (stock_profile.loc[y+1, v] - model.loc[(model.year==y) & (model.veh_type == v),"stock"].sum() + 
            #              model.loc[(model.year==y) & (model.veh_type == v),"retirements"].sum() +  
            #              model.loc[(model.year==y) & (model.veh_type == v),"early_ret"].sum())
            tot_sales = (stock_profile.loc[y+1, v] - model.loc[(model.year==y) & (model.veh_type == v) & (model.age < max_age),"stock"].sum() -
                         model.loc[(model.year==y) & (model.veh_type == v) & (model.age < max_age),"sales"].sum() +  
                         model.loc[(model.year==y) & (model.veh_type == v) & (model.age < max_age),"retirements"].sum() +  
                         model.loc[(model.year==y) & (model.veh_type == v) & (model.age < max_age),"early_ret"].sum())
            
            for f in fuel_types:
                #update sales
                # print(f"{f}_sales =", tot_sales * sales_pct.loc[y,f]/100)
                model.loc[(model.year==y) & (model.veh_type == v) & (model.fuel_type == f) & (model.age == 0),"sales"] = tot_sales * sales_pct.loc[y,f]/100
            
            
            
            
            if (replacement_mode == "ZEV_only") and (y < ban_year) and (y >= ban_year - phase_in):
                y_diff = ban_year - y
                tot_sales_all = (stock_profile.loc[y+1, v] - model.loc[(model.year==y) & (model.veh_type == v) & (model.age < max_age),"stock"].sum() -
                         model.loc[(model.year==y) & (model.veh_type == v) & (model.age < (ban_age - y_diff)),"sales"].sum() +  
                         model.loc[(model.year==y) & (model.veh_type == v) & (model.age < (ban_age - y_diff)),"retirements"].sum() +  
                         model.loc[(model.year==y) & (model.veh_type == v) & (model.age < (ban_age - y_diff)),"early_ret"].sum())
                
                zev_only_sales = (model.loc[(model.year==y) & (model.veh_type == v) & (model.age >= (ban_age - y_diff)) & (model.age < max_age),"retirements"].sum() +  
                         model.loc[(model.year==y) & (model.veh_type == v) & (model.age >= (ban_age - y_diff)) & (model.age < max_age),"early_ret"].sum())
                   
                for f in fuel_types:
                #update sales
                    model.loc[(model.year==y) & (model.veh_type == v) & (model.fuel_type == f) & (model.age == 0),"sales"] = tot_sales_all * sales_pct.loc[y,f]/100
                

                model.loc[(model.year==y) & (model.veh_type == v) & (model.fuel_type == "Electricity") & (model.age == 0),"sales"]+= zev_only_sales*frac_elec[v]
                model.loc[(model.year==y) & (model.veh_type == v) & (model.fuel_type == "Hydrogen") & (model.age == 0),"sales"]+= zev_only_sales*(1-frac_elec[v])
                
            
            if (replacement_mode == "ZEV_only") and (y >= ban_year):
                tot_sales_all = (stock_profile.loc[y+1, v] - model.loc[(model.year==y) & (model.veh_type == v) & (model.age < max_age),"stock"].sum() + 
                         model.loc[(model.year==y) & (model.veh_type == v) & (model.age < ban_age),"retirements"].sum() +  
                         model.loc[(model.year==y) & (model.veh_type == v) & (model.age < ban_age),"early_ret"].sum())
                
                zev_only_sales = (model.loc[(model.year==y) & (model.veh_type == v) & (model.age >= ban_age) & (model.age < max_age),"retirements"].sum() +  
                         model.loc[(model.year==y) & (model.veh_type == v) & (model.age >= ban_age) & (model.age < max_age),"early_ret"].sum())
                #sales_all_types = tot_sales_all - zev_only_sales
                # print("retirements: ",model.loc[(model.year==y) & (model.veh_type == v) & (model.age >= ban_age) & (model.age < max_age),"retirements"].sum())
                # print("early retirements: ",model.loc[(model.year==y) & (model.veh_type == v) & (model.age >= ban_age) & (model.age < max_age),"early_ret"].sum())
                # print(f"{tot_sales_all=}")
                # print(f"{zev_only_sales=}")
                # #print(f"{sales_all_types=}")


                
                for f in fuel_types:
                #update sales
                    model.loc[(model.year==y) & (model.veh_type == v) & (model.fuel_type == f) & (model.age == 0),"sales"] = tot_sales_all * sales_pct.loc[y,f]/100
                

                model.loc[(model.year==y) & (model.veh_type == v) & (model.fuel_type == "Electricity") & (model.age == 0),"sales"]+= zev_only_sales*frac_elec[v]
                model.loc[(model.year==y) & (model.veh_type == v) & (model.fuel_type == "Hydrogen") & (model.age == 0),"sales"]+= zev_only_sales*(1-frac_elec[v])
                
            # print(f"total sales in year {y}: {tot_sales}")
            # print("stock t+1 = ",stock_profile.loc[y+1, v])
            # print("current stock = ",model.loc[(model.year==y) & (model.veh_type == v),"stock"].sum())
            # print("retirements = ",model.loc[(model.year==y) & (model.veh_type == v),"retirements"].sum())
            # print("early retirements = ",model.loc[(model.year==y) & (model.veh_type == v),"early_ret"].sum())
            
        # model.loc[model["retirements"] < 0, "sales"] -= model.loc[model["retirements"] < 0, "retirements"]
        # model.loc[model["retirements"] < 0, "retirements"] = 0
        
            tot_base_rets = model.loc[(model.year==y) & (model.veh_type == v),"retirements"].sum()
            negative_sales = model.loc[(model.year==y) & (model.veh_type == v) & (model.sales < 0),"sales"].sum()
            ret_scale = 1 - negative_sales/tot_base_rets
            model.loc[(model.year==y) & (model.veh_type == v),"retirements"] *= ret_scale
            model.loc[(model.year==y) & (model.veh_type == v) & (model.sales < 0),"sales"] = 0
        
        return model, leftover_vehicles[ret_prof_idx]

    for v in veh_types:
        #print(v)
        ret_profs.sort(key = lambda ret_prof: ret_prof.loc[v, "ret_year"])
        for i in range(len(ret_profs) - 1):
            ret_prof1 = ret_profs[i]
            ret_prof2 = ret_profs[i+1]
            if ret_prof2.loc[v, "ret_year"] - ret_prof2.loc[v, "phase_in"] < ret_prof1.loc[v, "ret_year"]:
                raise ValueError("Invalid Retirement Profile. Overlapping phase-in")
            
        #begin at base year
        year = start_year
        while year <= end_year:
            for i, ret_prof in enumerate(ret_profs):
                ban_year = ret_prof.loc[v,"ret_year"]
                phase_in = ret_prof.loc[v, "phase_in"]
                if phase_in > 0 and year == ban_year - phase_in:
                    survival = get_survival(v, input_file)
                    expected_stock = get_expected_stock(model, ret_prof, v,(ban_year - phase_in-1),to_remove, survival)
                    # tol = 10
                    # l_bound = expected_stock*0.5
                    # u_bound = expected_stock*2
                    # l_bound = 0
                    # u_bound = model.loc[(model.veh_type == v) & (model.fuel_type.isin(to_remove)) & (model.year == year-1),"stock"].sum()
                    l_bound = 0
                    u_bound = expected_stock
                    _, leftover_vehicles = advance_model(model, v, year, phase_in, u_bound, i)
                    while leftover_vehicles > 0:
                        l_bound = u_bound
                        u_bound *= 1.3
                        _, leftover_vehicles = advance_model(model, v, year, phase_in, u_bound, i)
                        print("Searching for bounds")
                        print(f"{u_bound=}")
                        print(f"{l_bound=}")
                        print(f"{leftover_vehicles=}")
                        
                    while l_bound <= u_bound:
                        m = (l_bound + u_bound)/2
                        tol = max(1e-4*m,10)
                        model_temp, leftover_vehicles = advance_model(model, v, year, phase_in, m, i)
                        print(f"{u_bound=}")
                        print(f"{l_bound=}")
                        print(f"{m=}")
                        print(f"{leftover_vehicles=}")
                        if leftover_vehicles > tol:
                            l_bound = m+1
                        elif leftover_vehicles < -tol:
                            u_bound = m-1
                        else:
                            model = model_temp
                            break
                    year += phase_in
                    break
            else:
                model, _ = advance_model(model, v, year, 1, 0, 0)
                year += 1
    
    get_fuel_econ(model, input_file, veh_types, fuel_types)
    get_vmt(model, input_file, veh_types, vmt_mode)
    model["fuel_consumption"] = model["vmt"]/model["fuel_eff"]
    get_co2(model, veh_types, fuel_types)

    return model













    






 