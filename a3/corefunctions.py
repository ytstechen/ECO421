#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import numpy as np
import math
import datetime
from datetime import date
from dateutil.relativedelta import relativedelta


# In[2]:


def days_between_DCB(t1, t2, dcb):
    yy1=t1.year
    mm1=t1.month
    dd1=t1.day
    yy2=t2.year
    mm2=t2.month
    dd2=t2.day
    case1=["actual/actual", "actual/360", "actual/365", "actual/365 canadian"]
    case2=["30/360 european", "30/360 french"]
    n=-1
    if dcb.lower() in case1:
        d_diff=(t2) - (t1)
        n=d_diff.days
    elif dcb.lower() == "30/360":
        n=((yy2 - yy1) * 360 + (mm2 - mm1) * 30 + (dd2 - dd1))
    elif dcb.lower() in case2:
        n=((yy2 - yy1) * 360 + (mm2 - mm1) * 30 + (dd2 - dd1))
    else:
        print("days_between_DCB: dcb not avaliable, exit")
    return n


# In[3]:


def full_year_days(t1):
    yy1=t1.year
    mm1=t1.month
    dd1=t1.day
    n=-1
    n = date(yy1, 12, 31) - date(yy1 - 1, 12, 31)
    return n.days


# In[4]:


def days_in_year(t1):
    n=-1
    n=t1-date(t1.year-1, 12, 31)
    return n.days


# In[5]:


def base_year_DCB(t1, dcb):
    n=-1
    if dcb.lower() == "actual/actual":
        n = full_year_days(t1)
    elif dcb.lower() == "actual/360" or dcb.lower() == '30/360':
        n = 360
    elif dcb.lower() == "actual/364":
        n = 364
    elif dcb.lower() == "actual/365":
        n = 365
    elif dcb.lower() == "actual/365 canadian":
        n = 365
    else:
        print("Error: in baseYear: DCB not avaliable. exit!")
        
    return n


# In[7]:


def add_terms(t1, n, term): # n: integer; term: years, months or days
    d=date.min
    yy1=t1.year
    mm1=t1.month
    dd1=t1.day    
    if term.lower() == "years":
        d = t1 + relativedelta(years = +n)
    elif term.lower() == "months":
        d = t1 + relativedelta(months= +n)
    elif term.lower() == "weeks":
        d = t1 + relativedelta(weeks= +n)
    elif term.lower() ==  "days":  
        d = t1 + relativedelta(days=n) 
    else:
        print("Error: in addTerms: unknow term encountered. Exit.") 
  
    return (d)


# In[8]:


def find_nth_word(n, sentence):
    w_list=[]
    w_list=sentence.split()
    if n in range(1, len(w_list)+1):
        return w_list[n-1]
    else:
        print('word not found, return none!')
        return "none"


# In[9]:


def time_factor_DCB(t1, t2, dcb):
    tf=-1.0
    yy1=t1.year
    yy2=t2.year
    if t1==t2:
        tf=0.0
    elif t1>t2:
        print("Error: in timeFactorDCB, t1> t2. (-1)")
        return tf
    else:
        n = days_between_DCB(t1, t2, dcb)
        if n != -1:
            DIB = base_year_DCB(t2, dcb)
            if dcb.lower() == "actual/actual":
                DIB_t2 = DIB
                DIB_t1 = base_year_DCB(t1, dcb)

                tf = days_in_year(t2) / DIB_t2 + (DIB_t1 - days_in_year(t1)) / DIB_t1 + yy2 - yy1 - 1
            else:
                tf = n / DIB
            
    return tf


# In[10]:


def year_frq(frq):
    dn={"annu":1, "semi":2, "quart":4, "mon":12}  #, "years":1, "months":12, "day":365}   # , "14day":14, "28day":28, "42day":42, "84day":84, "91day":91, "182day":182}
    m_list=[1, 2, 4, 12]
    m=-1
    if frq.lower() == "smp":
        m=-1
    elif frq.lower() == "cont":
        m=0
    else:
        m = int(dn.get(frq.lower(), "-1"))
        if m not in m_list:
            print("Error: in year_frq(): m is wrong")
        
    return m
        


# In[11]:


def coupon_factor(term):
    factor = {"1 months":1,"2 months":2,"3 months":3,"4 months":4,"6 months":6,"12 months":12 }
    n = factor.get(term.lower(), None)
    if n != None:
        m = 12/n
        return m
    else:
        print(f'Error: term: {term} of coupon factor incorrect')
        return None
    


# In[12]:


def inverse_compound(TF3 , fwddisc , frq ) :
    forwardrate = -1.0
    if fwddisc > 0 and TF3 >= 0:
        if TF3 == 0.0:
            forwardrate = 0.0
        else:
            if frq.lower() == "cont": 
                forwardrate = -math.log(fwddisc) / TF3
            elif frq.lower() == "smp" :
                forwardrate = (1 / fwddisc - 1) / TF3
            else:
                m = year_frq(frq) 
                forwardrate = m * ((1 / fwddisc) ** (1 / (m * TF3)) - 1)
    return forwardrate


# In[13]:


def core_discount_factor(r, t1, t2, frq, dcb):
    tf = time_factor_DCB(t1, t2, dcb)
    disc = -1.0
    if tf >=0:
        if frq.lower() == "cont":
            disc = math.exp(-r*tf)
        elif frq.lower() == "smp":
            disc = 1/ (1+ r* tf)
        else:
            m = year_frq(frq)
            if m == -1 or m == 0:
                print("Error: in discount_factor(): m=-1 or 0")
                return 'nan'
            else:
                disc = 1 / ((1 + r / m) ** (m * tf))
        
        if disc > 0:
            return disc
        else:
            print(f"disc={disc} is <= 0, exit.")
            return 'nan'
    else:
        print(f"tf={tf} is <0, exit.")
        return 'nan'
            
    


# In[14]:


def core_fwd_discount(t0, t1,r1, t2,r2, frq, dcb):
    disc=-1.0
    disc1 = 1.0
    disc2 = 1.0

#         print(f"Testing: in fwd_discount:t0={t0} t2={t2} t1={t1}")
    if t1>t2:
        print(f"Error: in fwd_discount: {t1} > {t2} ")
    else:
        if t2 < t0:
            print(f"Error: in fwd_discount t2: {t2} < t0 {t0}")
        elif t1 < t0:
            disc= core_discount_factor(r2, t0, t2, frq, dcb)
        else:
            disc1= core_discount_factor(r1, t0, t1, frq, dcb)
            disc2= core_discount_factor(r2, t0, t2, frq, dcb)
            if disc1 != 0.0:
                disc=disc2/disc1
    return disc


# In[15]:


def core_convert_rate(r, t1, t2, from_unit, to_unit):
    unit_list=from_unit.split()
    fm_frq=unit_list[0]
    fm_dcb=unit_list[1]
    unit_list=to_unit.split()
    to_frq=unit_list[0]
    to_dcb=unit_list[1]
    rnew = -1.0
    if t1 > t2:
        print("ERROR in convertRateDCB: t1>t2 Exit.")
    else:
        disc = core_discount_factor(r, t1, t2, fm_frq, fm_dcb)
        tf = time_factor_DCB(t1, t2, to_dcb)
        if tf == 0.0:
            rnew = r
        elif disc > 0 and tf > 0:
            if to_frq.lower() == "cont":
                rnew=-math.log(disc)/tf
            elif to_frq.lower() == "smp":
                rnew=(1/ disc -1) / tf
            else:
                m=year_frq(to_frq)
                if m == -1 or m == 0:
                    print("Error: in discount_factor(): m=-1 or 0")
                else:
                    rnew = ((1 / disc) ** (1 / (m * tf)) - 1) * m
            
    return rnew


# In[16]:


def coupon(coupon_rate_attr, t1, t2, notional):
    #only for coupon prorated = 'True', use numerical_value(self, rate, ts, te) to reflect coupon prorated attr
    coupon_rate_s = coupon_rate_attr.split()
    coupon_dcb = coupon_rate_s[-1]
    coupon_frq = coupon_rate_s[-2]
    coupon_rate=float(coupon_rate_s[0]) 
    disc = core_discount_factor(coupon_rate, t1, t2, coupon_frq, coupon_dcb)
    cf = (1/disc - 1.0)* notional
    return cf


# In[17]:


def core_interpolation(method, dx, d1, x1, d2, x2):
    r=-1.0
    if method.lower() == "@loglinear()":
        r= core_log_linear_interpolation(dx, d1, x1, d2, x2)
    elif method.lower() == "@linear()":
        r= core_linear_interpolation(dx, d1, x1, d2, x2)
    else:
        print("interpolation function does not exist")

    return r


def core_log_linear_interpolation(dx, d1, x1, d2, x2): 
    r=-1.0
    if d1==d2:
        if x1!=x2:
            print("error: logLinearInterPolation:  r1 <> r2, exit!")
        else:
            r=x1
    else:
        r=x1 * math.exp((dx - d1) / (d2 - d1) * math.log(x2 / x1))

    return r


def core_linear_interpolation(dx, d1, x1, d2, x2):  
    r=-1.0
    if d1==d2:
        if x1!=x2:
            print("error: LinearInterPolation:  r1 <> r2, exit!")
        else:
            r=x1
    else:
        r = x1 + (dx - d1) * (x2 - x1) / (d2-d1)

    return r


# In[18]:



def core_add_dict(dict1, dict2):
    merged_dictionary = {}

    for key in dict1:
        if key in dict2:
            new_value = dict1[key] + dict2[key]
        else:
            new_value = dict1[key]

        merged_dictionary[key] = new_value

    for key in dict2:
        if key not in merged_dictionary:
            merged_dictionary[key] = dict2[key]

    return merged_dictionary


# In[19]:


def core_pv_bond_cf(tsim, cf:dict, curve_obj): #assume curve_obj shocked with scenario
    value = 0
    for t in cf:
        if  t >= tsim:
            term = t - tsim
            disc_tsim = curve_obj.fwd_discount(tsim, t)
            value = value + cf[t] * disc_tsim
    return value


# In[20]:


def bdr_adjustment(bdr, t):
    date_t = trade_day_rule(bdr, t)
    return date_t

        
def trade_day_rule(tdr, t): #Following 0 Days WeekEnds.cal
    if tdr == '' or tdr.lower() == 'none (standard)':
        return t

    kwd =  find_nth_word(1, tdr)
    num =  find_nth_word(2, tdr)
    unit =  find_nth_word(3, tdr)
    cal =  find_nth_word(4, tdr)

    n = int(num)
    if cal.lower == 'none':
        if kwd.lower() == 'following':
            date_t = add_terms(t, n, 'days')
        elif kwd.lower() == 'preceding':
            date_t =  add_terms(t, -1*n, 'days')
        else:
            print(f"trade day rule: {tdr}, not exist")
            date_t=t
    else:
        date_t=t
        i=0
        if kwd.lower()=='following':
            if n == 0:
                while is_holiday(date_t, cal) == True:
                    date_t= add_terms(date_t, 1, 'days')
            else:
                for i in range(0, n):
                    date_t= add_terms(date_t, 1, 'days')
                    if is_holiday(date_t, cal) == True:
                        i=i-1
        elif kwd.lower() == 'preceding':
            if n == 0:
                while is_holiday(date_t, cal) == True:
                    date_t= add_terms(date_t, -1, 'days')
            else:
                for i in range(0, n):
                    date_t= add_terms(date_t, -1, 'days')
                    if is_holiday(date_t, cal) == True:
                        i=i-1
    return date_t


def is_holiday( t, cal):
    cal_obj = pd.read_csv(f"{csv_path}{cal}")
    return is_weekend(t) 


def is_weekend( t):
    weekno = t.weekday()
    if weekno >= 5:    # 5 Sat, 6 Sun
        return True
    else:  
        return False


def roll_fixed_coupon_date(n, t):
    if n <= 0:
        de=0
    else:
        dd=t.day
        de=n - dd

    dt =  add_terms(t, de, "days")
    return dt

