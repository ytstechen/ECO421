#!/usr/bin/env python
# coding: utf-8

# In[1]:


import numpy as np
import pandas as pd
from datetime import date
import math
import corefunctions as co
import bondmodule630 as im


# # ALM modules

# In[2]:



def pv_bond_yield(y_yield:float, tsim, cf:dict, frq:str, dcb:str ):
    value = 0
    for t in cf:
        if  t >= tsim:
            disc = co.core_discount_factor(y_yield, tsim, t,  frq, dcb)
            if disc > 0:
                value = value + cf[t] * disc
            else:
                print(f"disc={disc} <=0,exit")
                return 'nan'
    return value


# In[3]:


#calc 1st order derivative of fixed rate bond
def d_fixed_bond_value_wrt_yield(y_yield, tsim, cf:dict, frq:str, dcb:str):
    TF=-1
    disc=-1
    df = 0
    for t in cf:
        if t >= tsim:
            TF = co.time_factor_DCB(tsim, t, dcb)
            disc = co.core_discount_factor(y_yield, tsim, t,  frq, dcb)
            if TF >= 0 and disc > 0:
                if frq.lower() == "smp":
                    df = df - cf[t]*TF*disc**2
                elif frq.lower() == "cont":
                    df = df - cf[t]*TF*disc
                else: #discrete compounding case'
                    m = co.year_frq(frq)
                    if m != 0:
                        df = df - cf[t] * TF * disc / (1 + y_yield / m)
                    else:
                        print(f"m={m} is zero, exit")
                        return 'nan'
            else:
                print(f"TF ={TF} is <=0, exit")
                return "nan"
#             print(f"df = {df}, t={t}, cf={cf[t]}")
    return df


# In[4]:


#cale bond yield using newton method, y0=0.05 is initial yield 
def bond_yield(mktV:float,  y0:float,  tsim, cf:dict, frq:str, dcb:str):
    e = 1e-7
    y1=0
    f1= 1 + e
    i = 0
    while f1 > e and i < 100:
        f0 = pv_bond_yield(y0, tsim, cf, frq, dcb) - mktV
        dfy = d_fixed_bond_value_wrt_yield(y0, tsim, cf, frq, dcb)
        if dfy != 0:
            y1 = y0 - f0 / dfy
        else:
            print(f"dfy={dfy} is zero, exit")
            return 'nan'
        f1 = pv_bond_yield(y1, tsim, cf, frq, dcb) - mktV
        y0 = y1
        i+=1
    
    if f1 > e and i >= 100:
        print(f"Iteration i={i} exit max=100, Newton method doesn't converge, exit")
        return -1
    
    return y1
    


# In[5]:


def modified_duration_fixed_bond_given_yield(y, tsim, cf, frq, dcb):
    v = pv_bond_yield(y, tsim, cf, frq, dcb)
    if v > 0:
        dur = - d_fixed_bond_value_wrt_yield(y, tsim, cf, frq, dcb) / v
    else:
        print(f"bond value v={v} is <=0, exit")
        return "nan"
    
    return dur


# In[6]:


def modified_duration_fixed_bond(tsim, bond_obj):
    #generate cashflow
    bond_obj.state_procedure()
    
    v = co.core_pv_bond_cf(tsim, bond_obj.cash_flow, bond_obj.curve_obj)
    frq = bond_obj.curve_obj.frq
    dcb = bond_obj.curve_obj.dcb
    root = bond_yield(v, 0.05, tsim, bond_obj.cash_flow, frq, dcb)
    dur = modified_duration_fixed_bond_given_yield(root, tsim, bond_obj.cash_flow, frq, dcb)
    return dur


# In[7]:


def modified_duration_floating_bond(tsim, bond_obj):
    #generate cashflow
    bond_obj.state_procedure()
    #value bond
    v0 = co.core_pv_bond_cf(tsim, bond_obj.cash_flow, bond_obj.curve_obj)
    if v0 == 0.0:
        return 0.0
    
    frq = bond_obj.curve_obj.frq
    dcb = bond_obj.curve_obj.dcb
    #floating bond duration = pure floating bond duration: dur_f + Fixed Rate Bond duration with coupon rate = spread
    #duration of pure floating bond:
    i=0
    for t_next in sorted(bond_obj.cash_flow):
        if t_next >= tsim:
            break
    else: #tsim is after boond maturity date
        return 0
    #claim: key is next coupon date after tsim    
    dur_f = co.time_factor_DCB(tsim, t_next, dcb)
    
    #duration of fixed bond
    #create a fix rate bond with coupon rate = spread
    modf = 0.0
    v = 0.0
    if bond_obj.spread > 0.0:
        bond_obj.type = 'fixed rate bond'
        #coupon rate is formate: "x% frq dcb"
        bond_obj.coupon_rate = str(bond_obj.spread) + ' ' + frq + ' ' + dcb
        bond_obj.state_procedure()
        v = co.core_pv_bond_cf(tsim, bond_obj.interest_cf, bond_obj.curve_obj)
        root = bond_yield(v, 0.05, tsim, bond_obj.interest_cf, frq, dcb)
        modf = modified_duration_fixed_bond_given_yield(root, tsim, bond_obj.interest_cf, frq, dcb)
    
    w1 = (v0 - v) / v0 #claim pure floating bond value: v1=v0-v
    w2 = v / v0
    dur = dur_f * w1 + modf * w2
    return dur


# In[8]:


def modified_duration(tsim, bond_obj, kth_scen_dict:dict):
    #apply kth scenario #only when scen is not empty
    if kth_scen_dict != {}: 
        for key in bond_obj.curve_obj.RF_list:
            if key in kth_scen_dict:
                term = bond_obj.curve_obj.Term_fm_RF[key]
                j=0
                while bond_obj.curve_obj.term[j] != term:
                    j +=1
                else: #corresponding to j travers all curve term list but can't find a match 
#                     print(f"term = {term} missing from curve.term list, please check, exit.")
#                     return 'nan'
                    bond_obj.curve_obj.rate[j] =  kth_scen_dict[key]

    if bond_obj.type.lower() == "fixed rate bond":
        dur = modified_duration_fixed_bond(tsim, bond_obj)
    elif bond_obj.type.lower() == "floating rate note":
        dur = modified_duration_floating_bond(tsim, bond_obj)
    else:
        print( f"Error: in modifiedDuration: bond type={bond_obj.type.lower()} which does not exist. exit")
        return nan
    return dur


# In[ ]:




