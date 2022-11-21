#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import math
import scipy

import datetime
from datetime import date

import corefunctions as co

import fxmodule as fx
from fxmodule import FXClass

import curvemodule610 as cm
from curvemodule610 import CurveClass

# import varmodule
# from varmodule import var_ir_var_maps


# In[3]:


class FXFwdClass:
    def __init__(self, fxfwd_file, xls_file):
        self.sheet_df=pd.read_excel(xls_file, sheet_name=fxfwd_file)
        self.attr_dict={}
        self.contract_size=1
        self.position_unit = 1 #portfolio pos units
        self.maturity_date=[]
        self.session_date=[]
        self.spot_fx=0.0
        self.value=0.0
        self.d_disc_curve=[]
        self.d_cash_flow={}
        self.f_cash_flow={}
        self.var_maps = {}
        
        self.load_fxfwd(self.sheet_df)
        
        #the following lines must placed after load_eq_fwd
        self.d_discount_curve_df=pd.read_excel(xls_file, sheet_name=self.d_disc_curve)
        self.dcurve_obj=CurveClass(self.d_discount_curve_df)
        self.f_discount_curve_df=pd.read_excel(xls_file, sheet_name=self.f_disc_curve)
        self.fcurve_obj=CurveClass(self.f_discount_curve_df)        
        
        fx_df=pd.read_excel(xls_file, sheet_name="SpotFXFile")
        self.fx_obj=FXClass(fx_df)
        fm_curr=self.underlying
        to_curr=self.currency
        self.spot_fx = self.fx_obj.spot_fx(fm_curr, to_curr)
        
        self.session_t=self.dcurve_obj.datum
        self.maturity_t = self.session_t +  datetime.timedelta(days=self.effective_date)
        self.maturity_t = self.maturity_t + datetime.timedelta(days=self.life_term)

        self.state_procedure()
        
    def state_procedure(self):
        
        #load cash flows 
        #there are 2 cash flows 
        self.d_cash_flow[self.maturity_t] = -self.strike_price * self.contract_size * self.position_unit
        self.f_cash_flow[self.maturity_t] = self.spot_fx * self.contract_size * self.position_unit
                

        
    def load_fxfwd(self, sheet_df):
            
        i=0
        for a in sheet_df['FX Forward']:
            self.attr_dict[a]=sheet_df['Attribute'][i]
            i+=1        
        self.name=self.attr_dict['Name']
        self.position_unit=self.attr_dict['POS Units']
        self.contract_size=int(self.attr_dict['Contract Size'])
        self.type=self.attr_dict['Type']
        self.effective_date=int(self.attr_dict['Effective Date'])
        self.currency=self.attr_dict['Currency']
        self.life_term=int(self.attr_dict['Life Term'])
        self.d_disc_curve=self.attr_dict['Discount Curve']
        self.f_disc_curve=self.attr_dict['Foreign Discount Curve']
        self.underlying=self.attr_dict['Underlying (Foreign Currency)']
        self.strike_price=float(self.attr_dict['Strike Price'])
        
        
        
    def theo_value(self):
        d_disc=self.dcurve_obj.discount_factor(self.maturity_t)
        f_disc=self.fcurve_obj.discount_factor(self.maturity_t)

        #Find Value
        forwardValue = self.spot_fx * f_disc - self.strike_price * d_disc
        self.value = forwardValue * self.contract_size * self.position_unit

        return self.value

  
    def theo_value_scen(self, dt, scen_df, k):
        tsim = self.session_t + datetime.timedelta(days=dt)
        self.dcurve_obj.datum = self.fcurve_obj.datum =tsim
        
        i=0
#         print(len(self.dcurve_obj.rate))
        for RF in scen_df.columns:
            if RF in self.dcurve_obj.RF_list:
#                 print(f"i={i}, RF={RF}, rate={scen_df[RF][k]}")
                self.dcurve_obj.rate[i] = float(scen_df[RF][k])
                i+=1

        i=0
#         print(len(self.dcurve_obj.rate))
        for RF in scen_df.columns:
            if RF in self.fcurve_obj.RF_list:
#                 print(f"i={i}, RF={RF}, rate={scen_df[RF][k]}")
                self.fcurve_obj.rate[i] = float(scen_df[RF][k])
                i+=1        
        
        d_disc = self.dcurve_obj.discount_factor(self.maturity_t)
        f_disc = self.fcurve_obj.discount_factor(self.maturity_t)

        fm_curr=self.underlying
        to_curr=self.currency    
        print(f"in fx fwd class: fm_curr={fm_curr}, to_curr={to_curr}")
        value = self.fx_obj.spot_fx_scen(fm_curr, to_curr, scen_df, k) * f_disc - self.strike_price * d_disc
        
        return value * self.contract_size * self.position_unit

    # A3 Q1
    # Since price_vol and vcv_df is not usable in here, delete these input variables
    def var_map_calculation(self): 
        
        # define df discount factor the same as in theo value
        f_disc=self.fcurve_obj.discount_factor(self.maturity_t)
        
        # FX VaR map = df discount factor * spot fx
        fwd_var_maps = self.spot_fx * f_disc
            
        self.var_maps = fwd_var_maps
        
        return self.var_maps 


# In[ ]:





# In[ ]:




