#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import math
import scipy
import corefunctions as co
import datetime
from datetime import date

import curvemodule610 as cm
from curvemodule610 import CurveClass

# import varmodule
# from varmodule import var_ir_var_maps


# In[2]:


class BondClass:
    
    def __init__(self, bond_id, bondmkt, xls):
        self.bond_id = bond_id        
        self.sheet_df = pd.read_excel(xls, sheet_name=bondmkt)
        self.position_unit = 1
        self.ir_var_maps = {}
        self.var_maps = {}
        self.value = 0.0
        
        err = self.load_bond(self.sheet_df)
        if err == 'nan':
            print('Error: loading bond_sheet error!!! exit')
            return 'nan'

        curve_df = pd.read_excel(xls, sheet_name=self.discount_curve)
        self.curve_obj = CurveClass(curve_df)

        self.session_t = self.curve_obj.datum
        self.previous_coupon_date = self.session_t
        self.maturity_t = self.session_t + datetime.timedelta(days=self.life_term)
        if self.issue_date == '1900/01/01' or self.issue_date == 'none':
            self.issue_t = self.session_t
        else:
            self.issue_t = date.fromisoformat(self.issue_date)
        self.interest_cf = {}
        self.cash_flow = {}
        
    def load_bond(self, sheet_df):
        id_dict = {}
        bond_attr = {}
        i = 0
        for b in sheet_df['ISSUE_ID']:
            id_dict[str(b)] = i
            i+=1          
        # need to check if id_dict fail to find key bond_id
        row = id_dict[self.bond_id]
        if row == 'nan':
            print(f"bond_id={self.bond_id} doesn't exist! check input!")
            return 'nan'
            
        for e in sheet_df.columns:
            bond_attr[e] = sheet_df[e][row]   
                
#         for b in str(sheet_df['ISSUE_ID']): 
#             if b != self.bond_id:
#                 row += 1
#             else:
#                 for e in sheet_df.columns:
#                     bond_attr[e] = sheet_df[e][row]
                    
        self.name = bond_attr['ISSUER-CP_NM']
        self.type = bond_attr['TYPE']
        self.credit_rateing = bond_attr['BLR_RATING']
        self.recovery_rate = bond_attr['RECOVERY_RATING']
        self.currency = bond_attr['CURR_DESC']
        self.notional = int(bond_attr['FACILITY'])
        if self.bond_id != str(bond_attr['ISSUE_ID']):
            print(f"Err: in load_bond: self.bond_id={self.bond_id} not equal to {bond_attr['ISSUE_ID']}, exit!")
            return 'nan'
        
        self.issue_date = bond_attr.get('Issue Date', '1900/01/01')
        self.country = bond_attr['COUNTRY_DESC']
        self.organization_id = bond_attr['ORG_ID']
        self.life_term = int(bond_attr['LIFE_TO_M'])
        self.coupon_rate = bond_attr['COUPON_RATE']
        self.coupon_term = bond_attr['COUPON_TERM']
        self.discount_curve = bond_attr['DISCOUNT_CV']
        
        y = bond_attr['SPREAD']
        if pd.isna(y):
            self.spread = 0.0
        else:
            self.spread = float(y)
        
        x = bond_attr['LAST_RESET_RATE']
        if self.type == 'Floating Rate Note' and pd.isna(x):
            self.last_reset_rate=0.01 # default to 1%
        else:  
            self.last_reset_rate = float(x)
        
        return 0
        
  

    def coupon_date_gen(self):  # assume backward generation from maturity date
#         print("----------------------------coupon_date_gen--------------------------------------")
        date_t = self.maturity_t
        m = 0
#         print(self.maturity_t, self.coupon_term)
#         print(self.coupon_term.split())
        m = int(co.find_nth_word(1, self.coupon_term) )
#         print(m)
        term = co.find_nth_word(2, self.coupon_term)
#         print(f"in coupon date gen: term = {term} ")
        while date_t >= self.issue_t:
            self.interest_cf[date_t] = 0.0
            self.cash_flow[date_t] = 0.0
            date_t = co.add_terms(date_t, -m, term)
#             print(f"in coupon date gen: date_t = {date_t} ")
            
        self.previous_coupon_date = date_t

    
    
    def cf_generation(self):
#         print("----------------------------cf_generation--------------------------------------")
        first_coupon=True
#         print(self.coupon_rate)

        frq = self.curve_obj.frq 
        dcb = self.curve_obj.dcb         
        for t in sorted(self.interest_cf):  # note: self.interest_cf keys are in desending order, reorder!
            if first_coupon == True:
#                 print(f"in cf_gen: self.previous_coupon_date={self.previous_coupon_date}, t={t} {t.year}")if self.type.lower() == 'floating rate note':
                if self.type.lower() == 'floating rate note':
                    ini_r = self.last_reset_rate
                elif self.type.lower() == 'fixed rate bond':
                    cr = co.find_nth_word(1, self.coupon_rate)
                    ini_r = float(cr)                     
                else: 
                    print(f"error: in cf_generation, bond type {self.type.lower()} is incorrect!")
                    return 400
                
                disc = co.core_discount_factor(ini_r, self.previous_coupon_date, t, frq, dcb)
#                 TF = co.time_factor_DCB(self.previous_coupon_date, t, dcb)
                first_coupon = False
            else:
#                 print(f"in cf_gen: t_1={t_1}, t={t}")
                if self.type.lower() == 'floating rate note':
                    frq = self.curve_obj.frq
                    dcb = self.curve_obj.dcb
                    fwd_r = self.curve_obj.fwd_rate(t_1 , t) + self.spread
                    disc = co.core_discount_factor(fwd_r, t_1 , t, frq, dcb)
#                     TF = co.time_factor_DCB(t_1, t, dcb)
                elif self.type.lower() == 'fixed rate bond':
                    cr = co.find_nth_word(1, self.coupon_rate)
                    c_rate = float(cr)   
                    disc = co.core_discount_factor(c_rate, t_1 , t, frq, dcb)
#                     TF = co.time_factor_DCB(t_1, t, dcb)
                else: 
                    print("error: in cf_generation, bond type is incorrect!")
                    return 400
            
            if disc == 'nan':
                print(f'disc is not defined: {disc}, exit! ')
                break
                
            self.interest_cf[t] = self.position_unit * (1 / disc - 1) * self.notional
            self.cash_flow[t] = self.interest_cf[t]      
            t_1 = t
            
        if t != self.maturity_t: 
            print(f"in cf_ gen, claim: t = {t} == maturity date = {self.maturity_t} false")
            return 400
        
        self.cash_flow[t] = self.interest_cf[self.maturity_t] + self.notional * self.position_unit
        
  
    def state_procedure(self):
        self.coupon_date_gen()
        self.cf_generation()        
        
    def theo_value(self):
        self.state_procedure()
        self.payment_procedure()
        value = 0.0
        for t in sorted(self.cash_flow):
            if t >= self.session_t:
#             print("-------------------------------theo_value-----------------------------------")
#             print(f"in theo_value: self.interest_cf[t] at {t} = {self.interest_cf[t]}")
                value += self.cash_flow[t] * self.curve_obj.discount_factor(t)
        self.value = value 
        
        return self.value
    
    def theo_value_scen(self, dt, scen_df, k):
        tsim = self.session_t + datetime.timedelta(days=dt)
#         update_scenario(self.curve_obj, scen_df, k)
#         self.state_procedure(dt, scen_df, k)
#         self.payment_procedure(dt, scen_df, k)
        self.state_procedure()
        self.payment_procedure()
        value = 0.0
        for t in sorted(self.cash_flow):
            if t >= tsim:
#             print("-------------------------------theo_value-----------------------------------")
#             print(f"in theo_value: self.interest_cf[t] at {t} = {self.interest_cf[t]}")
                value += self.cash_flow[t] * self.curve_obj.fwd_discount(tsim, t)
        self.value = value 
        
        return self.value
    

    def payment_procedure(self):
        pass

    
    def amort_cf_gen(self):
        pass
    
    def amort_cf_generation(self):
        pass
        
    def var_map_calculation(self, price_vol, vcv_df):
        self.state_procedure() #update self.cash_flow 
        
        #no need to scale by pos unit as cf has been scaled
#         ir_maps = var_ir_var_maps(self.cash_flow, price_vol, self.curve_obj, vcv_df) 
#         print(f"debug in BondClass: ir_maps={ir_maps}")
#         self.var_maps.update(ir_maps)

        return self.var_maps 


# In[ ]:




