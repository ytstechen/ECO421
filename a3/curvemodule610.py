#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import math
import datetime
from datetime import date
import corefunctions as co


# In[2]:


class CurveClass:

    def __init__(self, st_sheet):  #st_sheet is DataFrame with header
        self.name=st_sheet['Unnamed: 1'][1]
        self.id = st_sheet['Unnamed: 1'][2]
        self.curve_type=st_sheet['Unnamed: 1'][3]
        self.curve_origin= str(st_sheet['Unnamed: 1'][4])
        self.interpolation_type=st_sheet['Unnamed: 3'][1]
        self.term=[]
        self.rate=[]
        self.RF_list=[]
        self.RF_fm_Term={}
        self.Term_fm_RF={}
        self.frq=frq=''
        self.dcb=dcb=''
        self.curve_unit=st_sheet['Unnamed: 3'][2]
        self.datum=date.fromisoformat(self.curve_origin)
        self.load_curve(st_sheet)
    
    def load_curve(self, st_sheet):
        unit=[]
        unit=self.curve_unit.split()
        self.frq = unit[0]
        self.dcb = unit[1]
        max_row=len(st_sheet)
        for row in range(8, max_row):
            self.term.append(int(st_sheet.loc[row][0]))
            self.rate.append(float(st_sheet.loc[row][1]))

        for e in self.term:
            RF = self.name[2:5] + '.Z(T' + str(e) + ')'
            self.RF_list.append(RF)
            self.RF_fm_Term[e]=RF
            self.Term_fm_RF[RF]=e
            
    def get_rate(self, dx):
        imax=len(self.term)  
        if imax<1:
            print(f"error: curve {self.name} is not loaded!")
            return -1
        else:
            d0=self.term[0]
            dend=self.term[imax-1]
            if dx<=d0:
                return self.rate[0]
            if dx>=dend:
                return self.rate[imax-1]
            
            i=0
            while self.term[i] < dx:
                i+=1

                    
            d2=self.term[i]
            x2=self.rate[i]
            d1=self.term[i-1]
            x1=self.rate[i-1]
            r=self.interpolation(dx, d1, x1, d2, x2)
            return r
        
        
    def interpolation(self, dx, d1, x1, d2, x2):
        r=-1.0
        if self.interpolation_type.lower() == "@loglinear()":
            r=self.log_linear_interpolation(dx, d1, x1, d2, x2)
        elif self.interpolation_type.lower() == "@linear()":
            r=self.linear_interpolation(dx, d1, x1, d2, x2)
        else:
            print("interpolation function does not exist")

        return r

    
    def log_linear_interpolation(self, dx, d1, x1, d2, x2): 
        r=-1.0
        if d1==d2:
            if x1!=x2:
                print("error: logLinearInterPolation:  r1 <> r2, exit!")
            else:
                r=x1
        else:
            r=x1 * math.exp((dx - d1) / (d2 - d1) * math.log(x2 / x1))
            
        return r
    
 
    def linear_interpolation(self, dx, d1, x1, d2, x2):  
        r=-1.0
        if d1==d2:
            if x1!=x2:
                print("error: LinearInterPolation:  r1 <> r2, exit!")
            else:
                r=x1
        else:
            r = x1 + (dx - d1) * (x2 - x1) / (d2-d1)
            
        return r
    
    
    def discount_factor(self, t2):
        dn={"annu":1, "semi":2, "quart":4, "mon":12}
        disc = -1.0
        t1 = self.datum
        d_diff=t2-t1
        if (t1) <= (t2):
            term = d_diff.days
            tf = co.time_factor_DCB(t1, t2, self.dcb)
            if tf == -1.0 or term <0:
                print("Error: in discount_factor: tf=-1 or term <0")
            else:
                r = self.get_rate(term)
                if self.frq.lower() == "cont":
                    disc = math.exp(-r*tf)
                elif self.frq.lower() == "smp":
                    disc = 1/ (1+ r* tf)
                else:
                    m = int(dn.get(self.frq.lower(), "-1"))
                    if m == -1 or m == 0:
                        print("Error: in discount_factor(): m=-1 or 0")
                    else:
                        disc = 1 / ((1 + r / m) ** (m * tf))
        else:
            print("Error: in discountFactor: t1>t2 Exit. ")
        return disc
    

    def fwd_discount(self, t1, t2):
        disc=-1.0
        disc1 = 1.0
        disc2 = 1.0
        t0 = self.datum
#         print(f"Testing: in fwd_discount:t0={t0} t2={t2} t1={t1}")
        if t1>t2:
            print(f"Error: in fwd_discount: {t1} > {t2} ")
        else:
            if t2 < t0:
                print(f"Error: in fwd_discount: {t2} < curve origin {t0}")
            elif t1 < t0:
                disc= self.discount_factor(t2)
            else:
                disc1= self.discount_factor(t1)
                disc2= self.discount_factor(t2)
                if disc1 != 0.0:
                    disc=disc2/disc1
        return disc
    
    def fwd_rate(self, t1, t2):
        r2 = -1.0
        if t1 > t2:
            print("fwdRate:  t1  > =  t2  error.")
        else:
            t0=self.datum
            if t1 < t0 and t2 < t0:
                print("fwdRate: both t1, t2 < curve origin.")
            elif t1 < t0 :
                d_num = t2 - t1
                r2=self.spot_rate(d_num.days)
            else:
                TF3 = co.time_factor_DCB(t1, t2, self.dcb)
                fwddisc = self.fwd_discount(t1, t2)
                r2 = co.inverse_compound(TF3, fwddisc, self.frq)
                
        return r2
    
    
         


# In[ ]:


class HistoCurveClass:

    def __init__(self, histo_df):  #histo_df is DataFrame with header
        self.name=histo_df['Unnamed: 1'][1]
        self.id = histo_df['Unnamed: 1'][2]
        self.curve_type=histo_df['Unnamed: 1'][3]
        self.curve_origin= str(histo_df['Unnamed: 1'][4])
        self.interpolation_type=histo_df['Unnamed: 3'][1]
        self.date_t=[]
        self.rate=[]
        self.RF_list=[]
        self.RF_fm_Term={}
        self.date_t_fm_RF={}
        self.frq=frq=''
        self.dcb=dcb=''
        self.curve_unit=histo_df['Unnamed: 3'][2]
        self.datum=date.fromisoformat(self.curve_origin)
        self.load_curve(histo_df)
    
    def load_curve(self, histo_df):
        unit=[]
        unit=self.curve_unit.split()
        self.frq = unit[0]
        self.dcb = unit[1]
        max_row=len(histo_df)
        for row in range(8, max_row):
            self.date_t.append(date.fromisoformat(histo_df.loc[row][0]))
            self.rate.append(float(histo_df.loc[row][1]))

            
    def get_rate(self, dx):
        imax=len(self.date_t)  
        if imax<1:
            print(f"error: curve {self.name} is not loaded!")
            return -1
        else:
            d0=self.date_t[0]
            dend=self.date_t[imax-1]
            if dx<=d0:
                return self.rate[0]
            if dx>=dend:
                return self.rate[imax-1]
            
            i=0
            while self.date_t[i] < dx:
                i+=1

                    
            d2=self.date_t[i]
            x2=self.rate[i]
            d1=self.date_t[i-1]
            x1=self.rate[i-1]
            r=self.interpolation(dx, d1, x1, d2, x2)
            return r
        
        
    def interpolation(self, dx, d1, x1, d2, x2):
        r=-1.0
        if self.interpolation_type.lower() == "@loglinear()":
            r=self.log_linear_interpolation(dx, d1, x1, d2, x2)
        elif self.interpolation_type.lower() == "@linear()":
            r=self.linear_interpolation(dx, d1, x1, d2, x2)
        else:
            print("interpolation function does not exist")

        return r

    
    def log_linear_interpolation(self, dx, d1, x1, d2, x2): 
        r=-1.0
        if d1==d2:
            if x1!=x2:
                print("error: logLinearInterPolation:  r1 <> r2, exit!")
            else:
                r=x1
        else:
            r=x1 * math.exp((dx - d1) / (d2 - d1) * math.log(x2 / x1))
            
        return r
    
 
    def linear_interpolation(self, dx, d1, x1, d2, x2):  
        r=-1.0
        if d1==d2:
            if x1!=x2:
                print("error: LinearInterPolation:  r1 <> r2, exit!")
            else:
                r=x1
        else:
            r = x1 + (dx - d1) * (x2 - x1) / (d2-d1)
            
        return r


# In[ ]:


# under construction: how to load RiskWatch vol 2D surface csv ?
class VolSurface():
    def __init__(self, session_t, csv_path, df_vol):
        self.session_t = session_t
        self.csv_path = csv_path
        self.df_vol = df_vol
        self.load_vol_surface()
        
        
    def load_vol_surface(self):
        vol_attribute_dict = {}
        for abt in self.df_vol.columns:
            vol_attribute_dict[abt.strip()] = self.df_vol[abt][0] 
    
        self.name=vol_attribute_dict['Name']
        self.id = vol_attribute_dict['ID']
        self.curve_type=self.df_vol.columns[0]
        self.curve_origin= str(vol_attribute_dict['Datum'])
        self.interpolation_option_term = vol_attribute_dict['Interpolate Option Term']
        self.interpolation_delta = vol_attribute_dict['Interpolate Delta']
        self.surface = []

