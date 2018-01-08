import sys, pdb

import numpy as np
# import pandas as pd
import datetime as dt

def derivative(f, x, h):
    return (f(x+h) - f(x-h)) / (2.0*h)  # might want to return a small non-zero if ==0


def newton_raphson(func, guess, rng=0.00001):
    try:
        lastX = guess
        nextX = lastX + 10* rng  # "different than lastX so loop starts OK
        while (abs(lastX - nextX) > rng):  # this is how you terminate the loop - note use of abs()
            newY = func(nextX)                     # just for debug... see what happens
            # print("f(", nextX, ") = ", newY)     # print out progress... again just debug
            lastX = nextX
            nextX = lastX - newY / derivative(func, lastX, rng)  # update estimate using N-R
        return nextX
    except Exception as e:
        pdb.set_trace()
        print()


def createCashFlows(start_dt, freq, mat_dt, cpn, par, par_cf=True):
    ''' Creats a list of tuple pairs where each pair is the date and amount of a cash flow
    Parameters
    ==========
    start_dt : date
        start_date of the calculation, usually today
    freq : float
        payment frequency
    mat_dt : date
        date of maturity of the bond
    cpn : float
        coupon rate, will be converted to dollar amount later
    par : float
        par amount of the bond at expiration
    
    Return
    ======
    cfs : list of tuples
        date, amount tuple pairs for each cash flow
    '''
    tenor = (mat_dt - start_dt).days / 365.25 # assumes 365.25 days in a year
    num_cfs = (1 / freq) * tenor
    days_from_issue = [int((365 * freq)*(i+1)) for i in range(round(num_cfs))]
    dates = [start_dt + dt.timedelta(i) for i in days_from_issue]
    cfs = [(dates[i], cpn * par * freq) for i in range(len(dates))]
    if par_cf:
        cfs.append((mat_dt, par))
    return cfs