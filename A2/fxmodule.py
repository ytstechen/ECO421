#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import csv
import curvemodule610 as cm
from datetime import date


# In[2]:


class FXClass:
    def __init__(self, csv_df):
        self.symbol= []
        self.spotfx= {}
        self.curve = {}
        self.csv_df=csv_df
        i=0
        for s in self.csv_df['Currency']:
            self.symbol.append(s)
            self.spotfx[s] = self.csv_df['Spot FX'][i]
            self.curve[s] = self.csv_df['Curve'][i]
            i += 1
        
        self.base_curr=self.spotfx['From / To']
        
    def spot_fx(self, from_curr, to_curr):
        if from_curr in self.spotfx and to_curr in self.spotfx:
            fx_rate = float(self.spotfx[from_curr]) / float(self.spotfx[to_curr])
        else:
            print(f"FXClass missing currency: {from_curr} or {to_curr}")
            fx_rate = 400
            
        return fx_rate
    
    def spot_fx_scen(self, from_curr, to_curr, scen_df, k):
        if from_curr in self.spotfx and to_curr in self.spotfx:
     
            fxRF_fm=from_curr + ".XS"
            fxRF_to=to_curr + ".XS"

            if fxRF_fm in scen_df.columns:
                spot_from = float(scen_df[fxRF_fm][k])             
            else:
                if from_curr == self.base_curr:
                    spot_from=1
                else:
                    print(f"FXClass error: base currency={self.base_curr} not equal from currency: {from_curr}")
                    return 400

            if fxRF_to in scen_df.columns:
                spot_to=float(scen_df[fxRF_to][k]) 
            else:
                if to_curr == self.base_curr:
                    spot_to=1
                else:
                    print(f"FXClass error: base currency={self.base_curr} not equal to to_curr: {to_curr}")
                    return 400

            fx_rate = spot_from / spot_to        
        else:
            print(f"FXClass missing currency: {from_curr} or {to_curr}")
            fx_rate = 400        

        return fx_rate
        
        
    def fwd_fx_IRP(self, tsim, from_curr, to_curr, xls):
        fx_rate = 400
        fm_curve=self.curve[from_curr]
        to_curve=self.curve[to_curr]
        
        fm_curve_df=pd.read_excel(xls, sheet_name=fm_curve)
        to_curve_df=pd.read_excel(xls, sheet_name=to_curve)
        
        cur_from = cm.CurveClass(fm_curve_df)
        cur_to = cm.CurveClass(to_curve_df)

        fx_rate = self.spot_fx(from_curr, to_curr)
        fwd_fx = fx_rate * cur_from.discount_factor(tsim) / cur_to.discount_factor(tsim)
        return fwd_fx
        
    


# In[ ]:




