"""
Script to perform equity research and analysis as described in
Equity Valuation for Analysts and Investors by James Kelleher
"""
import sys
import pdb
import warnings
import datetime as dt
import numpy as np
import pandas as pd
import quandl
quandl.ApiConfig.api_key = 'J4d6zKiPjebay-zW7T8X'

sys.path.append("/home/ec2-user/environment/python_for_finance/")
from res_utils import get_ticker_info, removeEmptyCols, setup_comp_cols, \
                      getNextYear, OLS_COLS, match_px, getNextQuarter, \
                      get_beta, setup_pdv_cols
from dx.frame import get_year_deltas

# NOTES:
# simulate api call --> http://financials.morningstar.com/ajax/exportKR2CSV.html?t=BA

IDX = ['year', 'tick', 'month']
DEBUG = True
warnings.filterwarnings("ignore")


def peer_derived_value(data, period, hist_px):
    """
    Get the value of the stock as compared to its peers
    """
    # get group values first
    group_vals = {}
    years_fwd = 2
    vals = ['ps_ratio', 'pe_avg_hist', 'pb_ratio', 'pfcf_ratio']
    ticks = list(data.keys())

    # get group market cap
    group_mkt_cap = 0
    for key, data_df in data.items():
        per = tuple([period[0], key, data[key][0]['ols'].index.values[0][2]])
        try:
            group_mkt_cap += (data_df[0]['fr']['market_cap'])
        except:
            # May not have reported yet for this year, if this also fails,
            # raise exception as may have bigger problem
            pdb.set_trace()
            per = tuple([str(int(period[0])-1), key, data[key][0].index.values[0][2]])
            group_mkt_cap += data_df[0]['shares'][per] * float(hist_px[key].dropna().values[-1])
            per = tuple([period[0], key, data[key][0].index.values[0][2]])

        # Need to project out vals
        pdb.set_trace()
        for ind_val in vals:
            xvals = data[key][0][ind_val].dropna().reset_index()[['date', 'month']]
            slope, yint = ols_calc(xvals, data[key][0][ind_val].dropna())
            for fwd in range(1, years_fwd+1):
                start = dt.datetime(int(xvals.values[0][0]), int(xvals.values[0][1]), 1).date()
                per = tuple([str(int(period[0])+fwd), val[0].index.values[0][1], val[0].index.values[0][2]+"E"])
                new_x = get_year_deltas([start, dt.datetime(int(per[0]), int(per[2][:-1]), 1).date()])[-1]
                data[key][0].at[per, ind_val] = (yint + new_x * slope)

    for ind_val in vals:
        group_vals[ind_val] = 0
        group_vals[ind_val + "_w_avg"] = 0
        group_vals[ind_val + "_fwd"] = 0
        group_vals[ind_val + "_fwd_w_avg"] = 0
        for tick in ticks:
            per = tuple([period[0], tick, data[tick][0].index.values[0][2]])
            fwd = tuple([str(int(period[0])+years_fwd), tick, data[tick][0].index.values[0][2]+"E"])

            # 5yr avgs, simple and weighted
            try:
                group_vals[ind_val] += data[tick][0][ind_val].rolling(center=False, window=5).mean()[per] / len(ticks)
                group_vals[ind_val + "_w_avg"] += data[tick][0][ind_val].rolling(center=False, window=5).mean()[per] * ((data[tick][0]['shares'][per] * float(hist_px[tick].values[-1])) / group_mkt_cap)
            except:
                # May not have reported yet for this year, if this also fails, raise exception as may have bigger problem
                per = tuple([str(int(period[0])-1), tick, data[tick][0].index.values[0][2]])
                group_vals[ind_val] += data[tick][0][ind_val].rolling(center=False, window=5).mean()[per] / len(ticks)
                group_vals[ind_val + "_w_avg"] += data[tick][0][ind_val].rolling(center=False, window=5).mean()[per] * ((data[tick][0]['shares'][per] * float(hist_px[tick].values[-1])) / group_mkt_cap)

            # 5yr avgs, simpel and weighted
            group_vals[ind_val + "_fwd"] += data[tick][0][ind_val].rolling(center=False, window=years_fwd).mean()[fwd] / len(ticks)
            group_vals[ind_val + "_fwd_w_avg"] += data[tick][0][ind_val].rolling(center=False, window=years_fwd).mean()[fwd] * ((data[tick][0]['shares'][per] * float(hist_px[tick].values[-1])) / group_mkt_cap)
        if DEBUG:
            print("{} 5Y simple avg: {}".format(ind_val, '%.3f' % group_vals[ind_val]))
            print("{} 5Y weighted avg: {}".format(ind_val, '%.3f' % group_vals[ind_val + "_w_avg"]))
            print("{} 2Y fwd avg: {}".format(ind_val, '%.3f' % group_vals[ind_val + "_fwd"]))
            print("{} 2Y fwd weighted avg: {}".format(ind_val, '%.3f' % group_vals[ind_val + "_fwd_w_avg"]))

    comp_df = pd.DataFrame()
    for key, val in data.items():
        per = tuple([period[0], key, data[key][0].index.values[0][2]])
        for ratio in vals:
            if comp_df.empty:
                comp_df = pd.DataFrame(columns=setup_pdv_cols())
            row = [key, ratio]
            try:
                row.append(val[0][ratio].rolling(center=False, window=5).mean()[per])
            except:
                # May not have reported yet for this year, if this also fails, raise exception as may have bigger problem
                per = tuple([str(int(period[0])-1), key, data[key][0].index.values[0][2]])
                row.append(val[0][ratio].rolling(center=False, window=5).mean()[per])
            row.append(row[-1] / group_vals[ratio + "_w_avg"])
            # end of fwd estimate year
            fwd = tuple([str(int(period[0]) + years_fwd), key, data[key][0].index.values[0][2] + "E"])
            row.append(val[0][ratio].rolling(center=False, window=years_fwd).mean()[fwd])
            row.append(row[-1] / group_vals[ratio + "_fwd_w_avg"])
            row.append(row[3] / row[5])
            row.append(float(hist_px[key].dropna().values[-1]) * row[-1])
            data[key][1].append(tuple(["pdv_" + ratio, per[1], str(int(per[0]) + years_fwd), '%.3f' % row[-1]]))
            comp_df.loc[len(comp_df)] = row
    return data, comp_df.set_index(['ticker', 'cat'])


def comparison_anal(data, period):
    """
    doing comparison analysis on security
    """
    comp_df = pd.DataFrame()
    years_back = 5
    years_fwd = 2
    cols = ['net_inc', 'revenue', 'gross_prof_marg', 'pretax_prof_marg',
            'net_prof_marg', 'pe_avg_hist']
    cagr = ['net_inc', 'revenue']
    for tick, dfs in data.items():
        indices = [d for d in list(dfs[0]['ols'].index.values)
                   if int(d[0]) > int(period[0]) - years_back
                   and int(d[0]) <= int(period[0]) + years_fwd]
        ind_df = dfs[0]['ols'].ix[indices]
        if comp_df.empty:
            comp_df = pd.DataFrame(columns=setup_comp_cols(indices))
        for cat in cols:
            if cat in cagr:
                # cagr = compound annual growth rate
                avg = (ind_df[cat][years_back-1] / ind_df[cat][0])**(1/5) - 1
                row = [tick, cat] + list(ind_df[cat].values)
                row.insert(2 + years_back, avg)
                comp_df.loc[len(comp_df)] = row

                # standard avg of growth rate
                avg = ind_df[cat].pct_change()[1:years_back].mean()
                row = [tick, cat + "_g"] + list(ind_df[cat].pct_change().values)
                row.insert(2 + years_back, avg)
                comp_df.loc[len(comp_df)] = row
            else:
                # standard avg
                avg = ind_df[cat][:years_back].mean()
                row = [tick, cat] + list(ind_df[cat].values)
                row.insert(2+years_back, avg)
                comp_df.loc[len(comp_df)] = row
    if DEBUG:
        print(comp_df.set_index(['ticker', 'cat']))
    return comp_df.set_index(['ticker', 'cat'])


def price_perf_anal(period, mkt, ind, hist_px):
    """
    Compare performance of stocks to their indices
    """
    px_df = pd.DataFrame()
    mkt_px = hist_px.loc[mkt]
    ind_px = hist_px.loc[ind]
    for ind_t in list(set(hist_px.index.get_level_values(0).unique()) - set([mkt, ind])):
        t_px = hist_px.loc[ind_t]
        potential_yrs = list(set([ind_dt.year for ind_dt in list(t_px.index)
                                  if ind_dt.year > int(period[0])]))
        for yrs in [int(period[0])] + potential_yrs:
            t_df = pd.DataFrame([ind_t], columns=['tick'])
            t_df['year'] = yrs
            year_px = (t_px[(t_px.index >= dt.datetime(yrs, 1, 1))
                            & (t_px.index <= dt.datetime(yrs, 12, 31))])
            t_df['cur_px'] = year_px.values[-1][0]
            t_df['y_px'] = year_px.values[0][0]
            t_df['ytd_chg'] = (t_df['cur_px'] / t_df['y_px']) - 1
            t_df['ytd_high'] = max(year_px.values)
            t_df['ytd_low'] = min(year_px.values)
            year_mkt_px = (mkt_px[(mkt_px.index >= dt.datetime(yrs, 1, 1))
                                  & (mkt_px.index <= dt.datetime(yrs, 12, 31))])
            year_ind_px = (ind_px[(ind_px.index >= dt.datetime(yrs, 1, 1))
                                  & (ind_px.index <= dt.datetime(yrs, 12, 31))])
            t_df['mkt_ytd_chg'] = (year_mkt_px.values[-1][0]
                                   / year_mkt_px.values[0][0] - 1)
            t_df['mkt_rel_perf'] = t_df['ytd_chg'] - t_df['mkt_ytd_chg']
            t_df['ind_ytd_chg'] = (year_ind_px.values[-1][0]
                                   / year_ind_px.values[0][0] - 1)
            t_df['ind_rel_perf'] = t_df['ytd_chg'] - t_df['ind_ytd_chg']
            px_df = px_df.append(t_df)
    return px_df.set_index(['tick', 'year'])


def discount_fcf(data, period, ests):
    """
    Calculate the value of the security based on
    discounted free cash flow models
    """
    # should be pulled off debt issued by company, hard coded for now
    cost_debt = 0.07
    # rate on 10yr tsy
    r_free = 0.028
    # generally accepted market risk premium above risk free rate
    market_risk_prem = 0.05

    # Take the periods beta, calc'd in res_utils
    beta = data['ols'].loc[period]['beta']
    # CAPM
    cost_equity = r_free + beta * market_risk_prem

    mv_eq = data['fr']['market_cap'][period]
    # mv_debt = HARD TO GET
    bv_debt = (data['bs']['short_term_debt'][period]
               + data['bs']['long_term_debt'][period])
    total_capital = bv_debt + mv_eq
    eq_v_cap = mv_eq / total_capital
    debt_v_cap = bv_debt / total_capital
    # average of the periods we have
    tax_rate = data['fr']['eff_tax_rate'].mean()
    wacc = ((cost_equity * eq_v_cap) + (cost_debt * debt_v_cap)
            * (1 - tax_rate / 100))
    print("WACC: " + str(wacc))

    # TODO: ENTER analysts projected EPS growth here
    eps_g_proj = 0.12
    # average of calc'd growth and analyst projection
    data['ols']['proj_calc_g'] = (data['fr']['const_growth_rate'] + eps_g_proj) / 2
    # avg of constant growth calc
    data['ols']['1st_5yr_lt_g'] = data['fr']['const_growth_rate'].mean()
    # slightly lower than 1st growth calc, usually 2 to 4%
    data['ols']['2nd_5yr_lt_g'] = data['ols']['1st_5yr_lt_g'] - 0.02
    # long term terminal growth rate
    # typically some average of gdp and the industry standard
    term_growth = 0.05

    # 2 Stage DFCF
    years_to_terminal = 2
    fcf_pershare = (data['cf']['fcf_min_twc'][period]
                    / data['is']['weight_avg_shares'][period])
    indices = [d for d in list(data['ols'].index.values)
               if int(d[0]) > int(period[0]) and int(d[0]) <= int(period[0]) + years_to_terminal]
    # fcf geometric growth
    fcfs = [fcf_pershare * (1 + data['ols']['1st_5yr_lt_g'][period])
            ** (int(x[0]) - int(period[0])) for x in indices]
    disc_fcfs = [fcfs[x] / (1 + cost_equity) **
                 (int(indices[x][0]) - int(period[0])) for x in range(0, len(indices))]
    sum_of_disc_cf = sum(disc_fcfs)
    term_val = ((data['ols']['fcf_min_twc'][indices[-1]]
                 / data['is']['weight_avg_shares'][period]) / (cost_equity - term_growth))
    final_val = term_val + sum_of_disc_cf
    ests.append(("2stage", indices[-1][1], indices[-1][0],
                 '%.3f' % (final_val)))
    if DEBUG:
        print("2 Stage Val Est {} {}: {}".format(indices[-1][1],
                                                 indices[-1][0], '%.3f'%(final_val)))

    # 3 Stage DFCF
    years_phase1 = 1
    years_phase2 = 1
    # 1st growth phase
    fcf_pershare = (data['ols']['fcf_min_twc'][period]
                    / data['is']['weight_avg_shares'][period])
    indices = [d for d in list(data['ols'].index.values) if int(d[0]) > int(period[0])
               and int(d[0]) <= int(period[0]) + years_phase1]
    fcfs = [fcf_pershare * (1 + data['ols']['1st_5yr_lt_g'][period])
            ** (int(x[0]) - int(period[0])) for x in indices]
    disc_fcfs_1 = [fcfs[x] / (1 + cost_equity) **
                   (int(indices[x][0]) - int(period[0])) for x in range(0, len(indices))]
    # second growth phase
    # need to make sure hav the right indices after first growth period is over
    indices = [d for d in list(data['ols'].index.values)
               if int(d[0]) > int(period[0]) + years_phase1
               and int(d[0]) <= int(period[0]) + years_phase1 + years_phase2]
    fcfs = [fcf_pershare * (1 + data['ols']['2nd_5yr_lt_g'][period])
            ** (int(x[0]) - int(period[0])) for x in indices]
    disc_fcfs_2 = [fcfs[x] / (1 + cost_equity) **
                   (int(indices[x][0]) - int(period[0])) for x in range(0, len(indices))]
    sum_of_disc_cf = sum(disc_fcfs_1) + sum(disc_fcfs_2)
    term_val = ((data['ols']['fcf_min_twc'][indices[-1]]
                 / data['is']['weight_avg_shares'][period]) / (cost_equity - term_growth))
    final_val = term_val + sum_of_disc_cf
    ests.append(("3stage", indices[-1][1], indices[-1][0],
                 '%.3f' % (final_val)))
    if DEBUG:
        print("3 Stage Val Est {} {}: {}".format(indices[-1][1],
                                                 indices[-1][0], '%.3f'%(final_val)))

    # Component DFCF
    years_to_terminal = 2
    # use the OLS growth calcs for FCFs instead of growth forecasts
    fcfs = (data['ols']['fcf_min_twc'] / data['ols']['weight_avg_shares'])
    indices = [d for d in list(data['ols'].index.values) if int(d[0]) > int(period[0])
               and int(d[0]) <= int(period[0]) + years_to_terminal]
    disc_fcfs = [fcfs[indices[x]] / (1 + cost_equity) **
                 (int(indices[x][0]) - int(period[0])) for x in range(0, len(indices))]
    sum_of_disc_cf = sum(disc_fcfs)
    term_val = (data['ols']['fcf_min_twc'][indices[-1]]
                / data['is']['weight_avg_shares'][period]) / (cost_equity - term_growth)
    final_val = term_val + sum_of_disc_cf
    ests.append(("Component Anal", indices[-1][1], indices[-1][0],
                 '%.3f' % (final_val)))
    if DEBUG:
        print("Component Val {} {}: {}".format(indices[-1][1],
                                               indices[-1][0], '%.3f'%(final_val)))
    return data, ests


def historical_ratios(data, period, hist_px):
    """
    Calculate historical ratios for valuation
    """
    ests = []
    next_per = tuple(getNextYear(period))
    pers_2 = tuple(getNextYear(next_per))

    # fill current price with latest measurement
    curr_px = hist_px.loc[period[1]].iloc[-1]['px']

    # PE Ratios
    data['ols']['eps'] = data['ols']['net_inc'] / data['ols']['weight_avg_shares']
    data['ols']['pe_low_hist'] = data['ols']['lo_52wk'] / data['ols']['eps']
    data['ols']['pe_low_hist'] = data['ols']['hi_52wk'] / data['ols']['eps']
    data['ols']['pe_avg_hist'] = data['ols']['avg_52wk'] / data['ols']['eps']
    data['ols']['pe_curr_hist'] = curr_px / data['ols']['eps']
    data['ols']['pe_fwd'] = ((data['ols']['date_px'] * data['is']['weight_avg_shares'])
                             / data['is']['net_inc'].shift(1))
    data['ols']['pe_5yr_avg_hist'] = data['ols']['pe_avg_hist'].rolling(center=False, window=5).mean()

    for per in [next_per, pers_2]:
        final_val = '%.3f' % (data['ols']['pe_5yr_avg_hist'][period]
                              * (data['ols']['eps'][per]))
        ests.append(("PE", per[1], per[0], final_val))
        if DEBUG:
            print("Hist avg PE: {}  Fwd EPS: {}  DV Est {} {}: {}"
                  "".format('%.3f' % (data['ols']['pe_5yr_avg_hist'][period]),
                            '%.3f' % (data['ols']['eps'][per]), per[1], per[0], final_val))

    # P/S
    # Sales per share
    data['ols']['sps'] = data['ols']['revenue'] / data['ols']['weight_avg_shares']
    data['ols']['ps_avg_hist'] = data['ols']['avg_52wk'] / data['ols']['sps']
    data['ols']['ps_curr_hist'] = curr_px / data['ols']['sps']
    data['ols']['ps_fwd'] = ((data['ols']['date_px'] * data['is']['weight_avg_shares'])
                             / data['is']['revenue'].shift(1))
    data['ols']['ps_5yr_avg_hist'] = data['ols']['ps_avg_hist'].rolling(center=False, window=5).mean()

    for per in [next_per, pers_2]:
        final_val = '%.3f' % (data['ols']['ps_5yr_avg_hist'][period]
                              * (data['ols']['sps'][per]))
        ests.append(("PS", per[1], per[0], final_val))
        if DEBUG:
            print("Hist avg PS: {}  Fwd Rev/share: {}  DV Est {} {}: {}"
                  "".format('%.3f' % (data['ols']['ps_5yr_avg_hist'][period]),
                            '%.3f' % (data['ols']['sps'][per]), per[1], per[0], final_val))

    # P/B
    data['ols']['bvps'] = data['ols']['total_equity'] / data['ols']['weight_avg_shares']
    data['ols']['pb_avg_hist'] = data['ols']['avg_52wk'] / data['ols']['bvps']
    data['ols']['pb_curr_hist'] = curr_px / data['ols']['bvps']
    data['ols']['pb_fwd'] = ((data['ols']['date_px'] * data['is']['weight_avg_shares'])
                             / data['bs']['total_equity'].shift(1))
    data['ols']['pb_5yr_avg_hist'] = data['ols']['pb_avg_hist'].rolling(center=False, window=5).mean()

    for per in [next_per, pers_2]:
        final_val = '%.3f' % (data['ols']['pb_5yr_avg_hist'][period]
                              * (data['ols']['bvps'][per]))
        ests.append(("PS", per[1], per[0], final_val))
        if DEBUG:
            print("Hist avg PB: {}  Fwd BVPS: {}  DV Est {} {}: {}"
                  "".format('%.3f' % (data['ols']['pb_5yr_avg_hist'][period]),
                            '%.3f' % (data['ols']['bvps'][per]), per[1], per[0], final_val))

    # P/CF
    # cash flow per share
    data['ols']['cfps'] = data['ols']['oper_cf'] / data['ols']['weight_avg_shares']
    data['ols']['pcf_avg_hist'] = data['ols']['avg_52wk'] / data['ols']['cfps']
    data['ols']['pcf_curr_hist'] = curr_px / data['ols']['cfps']
    data['ols']['pcf_fwd'] = ((data['ols']['date_px'] * data['is']['weight_avg_shares'])
                              / data['cf']['oper_cf'].shift(1))
    data['ols']['pcf_5yr_avg_hist'] = data['ols']['pcf_avg_hist'].rolling(center=False, window=5).mean()

    for per in [next_per, pers_2]:
        final_val = '%.3f' % (data['ols']['pcf_5yr_avg_hist'][period]
                              * (data['ols']['cfps'][per]))
        ests.append(("PCF", per[1], per[0], final_val))
        if DEBUG:
            print("Hist avg PCF: {}  Fwd CF/share: {}  DV Est {} {}: {}"
                  "".format('%.3f' % (data['ols']['pcf_5yr_avg_hist'][period]),
                            '%.3f' % (data['ols']['cfps'][per]), per[1], per[0], final_val))

    # P/FCF
    # free cash flow per share
    data['ols']['fcfps'] = data['ols']['fcf'] / data['ols']['weight_avg_shares']
    data['ols']['pfcf_avg_hist'] = data['ols']['avg_52wk'] / data['ols']['fcfps']
    data['ols']['pfcf_curr_hist'] = curr_px / data['ols']['fcfps']
    data['ols']['pfcf_fwd'] = ((data['ols']['date_px'] * data['is']['weight_avg_shares'])
                               / data['cf']['fcf'].shift(1))
    data['ols']['pfcf_5yr_avg_hist'] = data['ols']['pfcf_avg_hist'].rolling(center=False, window=5).mean()

    for per in [next_per, pers_2]:
        final_val = '%.3f' % (data['ols']['pfcf_5yr_avg_hist'][period]
                              * (data['ols']['fcfps'][per]))
        ests.append(("PFCF", per[1], per[0], final_val))
        if DEBUG:
            print("Hist avg PFCF: {}  Fwd FCF/share: {}  DV Est {} {}: {}"
                  "".format('%.3f' % (data['ols']['pfcf_5yr_avg_hist'][period]),
                            '%.3f' % (data['ols']['fcfps'][per]), per[1], per[0], final_val))

    # Relative P/E
    # NEED THE EARNIGNS OF THE SNP500
    # data['PE_rel'] = (52WeekAvg * shares) / data['PE_of_SnP']
    # data['PE_rel_curr'] = (cur_px * shares) / data['PE_of_SnP']
    # data['PE_rel_fwd'] = (cur_px * shares) / data['PE_of_SnP'].shift(1)
    # data['PE_rel_5yr_avg'] = PE_rel.rolling(center=False, window=5).mean()
    # for p in [next_per, pers_2]:
        # print("Hist avg PS: {}  Fwd Rev/share: {}  DV Est {} {}: {}"
                # "".format(data['PE_rel__5yr_avg'][period],
        #     data['PE_of_SnP'][p] / data['shares'][period], period[1], period[0]
        #     data['PE_rel__5yr_avg'][period] * data['revenue'][p] / data['shares'][period]))

    # PEG
    # data['PEGY'] = data['PE_avg_hist']
                    #  / ((data['netIncome'].pct_change() + data['divYield']) * 100)
    # data['PEGY_5yr_avg'] = PEGY.rolling(center=False, window=5).mean()
    return data, ests


def ratios_and_valuation(data):
    """
    Add some necessary columns
    """

    # Balance Sheet Columns
    data['bs']['div_per_share'] = (data['cf']['divs_paid']
                                   / data['is']['weight_avg_shares'])

    # Income Statement columns
    # Net Operatin Profit after tax
    data['is']['nopat'] = (data['is']['oper_inc']
                           * (1 - data['fr']['eff_tax_rate']))
    data['is']['rtc'] = data['is']['nopat'] / data['bs']['total_assets']

    # Financial Ratios
    data['fr']['trade_work_cap'] = (data['bs']['receivables']
                                    + data['bs']['inv']
                                    - data['bs']['accounts_payable'])
    data['fr']['ebitda_margin'] = data['is']['ebitda'] / data['is']['revenue']
    data['fr']['ret_earn_ratio'] = (1 - data['fr']['div_payout_ratio'])
    data['fr']['const_growth_rate'] = (data['fr']['roe']
                                       * data['fr']['ret_earn_ratio'])
    data['fr']['oper_lev'] = (data['is']['oper_inc'].pct_change()
                              / data['is']['revenue'].pct_change())
    data['fr']['roe_dupont'] = ((data['is']['net_inc'] / data['is']['revenue'])
                                * (data['is']['revenue'] / data['bs']['total_assets'])
                                * (data['bs']['total_assets'] / data['bs']['total_equity']))

    # Cash Flow Statement Columns
    data['cf']['equity_turnover'] = (data['is']['revenue']
                                     / data['bs']['total_equity'])
    data['cf']['cash_conv_cycle'] = (data['fr']['days_of_inv_on_hand']
                                     + data['fr']['days_sales_outstanding']
                                     - data['fr']['days_payables_outstanding'])
    data['cf']['fcf_min_wc'] = data['cf']['fcf'] - data['cf']['chg_working_cap']
    data['cf']['fcf_min_twc'] = (data['cf']['fcf']
                                 - data['fr']['trade_work_cap'].diff())
    return data


def model_est_ols(years, data, avg_cols=None, use_last=None):
    """
    Create a model based on ordinary least squares regression
    """
    hist = pd.DataFrame()
    data_ols = pd.DataFrame()
    # some cleanup
    for sheet in ['is', 'bs', 'cf', 'fr']:
        data[sheet] = data[sheet].reset_index()[data[sheet].reset_index().year
                                                != 'TTM'].set_index(IDX)

    # next qurater est is equal to revenue * average est margin
    # over the last year
    for _ in range(years):
        if hist.empty:
            n_idx = list(data['is'].iloc[-1].name)
        else:
            n_idx = list(hist.iloc[-1].name)
        n_idx = getNextYear(n_idx)
        n_hist_dict = {k: v for k, v in zip(IDX, n_idx)}

        #########
        # Use OLS to get projected values
        #########
        for cat in OLS_COLS:
            # for columns that are all 0 for a particular security
            skip = False
            # Need this for columns that are too eradic for OLS
            if avg_cols and cat in avg_cols:
                n_hist_dict[cat] = data[cat].mean()
                continue
            # Need this for columns where we just use most recent value
            if use_last and cat in use_last:
                n_hist_dict[cat] = data[cat].values[-1]
                continue
            for sheet in ['is', 'bs', 'cf', 'fr']:
                try:
                    val = data[sheet][cat].dropna()
                    data_ols[cat] = data[sheet][cat]
                    x_val = val.reset_index()[['year', 'month']]
                    break
                except KeyError:
                    if sheet == 'fr':
                        n_hist_dict[cat] = 0
                        data_ols[cat] = 0
                        skip = True
                    else:
                        continue
            # column is 0 for this security
            if skip:
                continue
            slope, yint = ols_calc(x_val, val)
            start = dt.datetime(int(x_val.values[0][0]),
                                int(x_val.values[0][1]), 1).date()
            new_x = get_year_deltas([start, dt.datetime(int(n_idx[0]),
                                                        int(n_idx[2][:-1]),
                                                        1).date()])[-1]
            # Need this to convert terminology for quarterly, also need to divide by four
            n_hist_dict[cat] = (yint + new_x * slope)

        n_hist_dict['ebt'] = (n_hist_dict['oper_inc']
                              + n_hist_dict['net_int_inc'])
        # assume average tax rate over last 5 years
        n_hist_dict['taxes'] = (data['fr']['eff_tax_rate'].mean()
                                * n_hist_dict['ebt'])
        n_hist_dict['net_inc'] = n_hist_dict['ebt'] - n_hist_dict['taxes']
        n_hist_dict['eps'] = (n_hist_dict['net_inc']
                              / n_hist_dict['weight_avg_shares'])
        t_df = pd.DataFrame(n_hist_dict, index=[0]).set_index(IDX)
        hist = hist.append(t_df)
    hist = pd.concat([data_ols, hist])
    hist['net_inc'] = pd.concat([data['is']['net_inc'],
                                 hist['net_inc'].dropna()])
    return hist


def model_est(cum, margin):
    """
    Model based on quarterly estimats
    """
    # some cleanup
    margin = margin.reset_index()[margin.reset_index().date != 'TTM'].set_index(IDX)
    cum = cum.reset_index()[cum.reset_index().month != ''].set_index(IDX)

    # next qurater est is equal to revenue * average est margin over the last year
    for _ in range(4):
        n_idx = list(cum.iloc[-1].name)
        n_idx = getNextQuarter(n_idx)
        n_data = n_idx + list(margin[-5:-1].mean())
        t_df = pd.DataFrame(dict((key, value) for (key, value) in zip(IDX+list(margin.columns), n_data)), columns=IDX+list(margin.columns), index=[0]).set_index(IDX)
        margin = margin.append(t_df)

        n_cum_dict = {k: v for k, v in zip(IDX, n_idx)}
        n_cum_dict['revenue'] = cum[-5:-1]['revenue'].mean()

        #########
        # Use mean of previous few years to get there
        #########
        for col in ['cogs', 'rd', 'sga', 'grossProfit', 'mna', 'otherExp']:
            n_cum_dict[col] = margin.loc[tuple(n_idx)][col] * n_cum_dict['revenue']
        n_cum_dict['operatingCost'] = n_cum_dict['rd'] + n_cum_dict['sga'] + n_cum_dict['mna'] + n_cum_dict['otherExp']
        n_cum_dict['EBIT'] = n_cum_dict['revenue'] - n_cum_dict['operatingCost'] - n_cum_dict['cogs']   # operating income
        # Need to update these when we do balance sheet
        total_debt = cum.iloc[-1]['totalLiab']
        cash_and_inv = cum.iloc[-1]['totalCash']
        # 0.6 = about corp rate , 0.02 = about yield on cash, 0.25 = 1/4 of the year
        n_cum_dict['intExp'] = total_debt * 0.25 * 0.7 - cash_and_inv * 0.25 * 0.02
        # just assume average of last year, gonna be very specific company to company
        n_cum_dict['otherInc'] = cum[-5:-1]['otherInc'].mean()
        n_cum_dict['EBT'] = n_cum_dict['EBIT'] - n_cum_dict['intExp'] + n_cum_dict['otherInc']
        # average tax rate of the last year
        n_cum_dict['taxes'] = (cum[-5:-1]['taxes'] / cum[-5:-1]['EBT']).mean() * n_cum_dict['EBT']
        n_cum_dict['netIncome'] = n_cum_dict['EBT'] - n_cum_dict['taxes']

        # Assume change over the last year continues for next quarter - may need to adjust this per company
        n_cum_dict['shares'] = ((((cum.iloc[-1]['shares'] / cum.iloc[-5]['shares']) - 1) / 4) + 1) * cum.iloc[-1]['shares']
        n_cum_dict['sharesBasic'] = ((((cum.iloc[-1]['sharesBasic'] / cum.iloc[-5]['sharesBasic']) - 1) / 4) + 1) * cum.iloc[-1]['sharesBasic']

        n_cum_dict['EPS'] = n_cum_dict['netIncome'] / n_cum_dict['shares']
        n_cum_dict['EPSBasic'] = n_cum_dict['netIncome'] / n_cum_dict['sharesBasic']

        # Assume cash and liabilities are static
        n_cum_dict['totalLiab'] = total_debt
        n_cum_dict['totalCash'] = cash_and_inv

        t_df = pd.DataFrame(n_cum_dict, index=[0]).set_index(IDX)
        cum = cum.append(t_df)

    # clean up df
    cum = cum.fillna(0)
    empty_cols = [c for c in list(cum.columns) if all(v == 0 for v in cum[c])]
    cum = cum[list(set(cum.columns) - set(empty_cols))]
    return cum


def margin_df(marg_df):
    """
    calculates margin for these columns
    """
    data = marg_df.apply(lambda x: x / x['revenue'], axis=1)
    # tax rate presented as percentage of pre tax income
    data['taxes'] = marg_df['prov_inc_tax'] / marg_df['ebt']
    return data


def ols_calc(xvals, yvals):
    """
    ordinary least squares calculation
    """
    xvals = [dt.datetime(int(x[0]), int(float(str(x[1]).replace("E", ""))),
                         1).date() for x in xvals.values]
    xvals = get_year_deltas(xvals)
    a_mat = np.vstack([xvals, np.ones(len(xvals))]).T
    slope, yint = np.linalg.lstsq(a_mat, yvals.values)[0]
    return (slope, yint)


def get_price_data(ticks, comps, method='db'):
    """
    Grab data from API, File, or DB
    """
    pxs = pd.DataFrame()
    # Cant find an API I can trust for EOD stock data
    for ind_t in ticks + comps:
        if method == 'api':
            pass
            # start = dt.date(2000, 1, 1).strftime("%Y-%m-%d")
            # end = dt.datetime.today().date().strftime("%Y-%m-%d")
            # url = "https://www.quandl.com/api/v1/datasets/WIKI/{0}.csv?column=4&sort_order=asc&trim_start={1}&trim_end={2}".format(ind_t, start, end)
        elif method == 'file':
            qrd = pd.read_csv("/home/ubuntu/workspace/python_for_finance/research/data_grab/{}.csv".format(ind_t))
            qrd = qrd.rename(columns={'close': ind_t}).set_index(['date'])
            if pxs.empty:
                pxs = qrd
            else:
                pxs = pd.merge(pxs, qrd, how='left',
                               left_index=True, right_index=True)
        else:
            pxs = get_ticker_info(ticks + comps, 'eod_px', ['tick', 'date'])
            break
    return pxs


def analyze_ests(data, period, hist_px, years_fwd=2):
    val_models = ['Hist Comps', 'DFCF', 'PDV']
    val_weights = {
        'Hist Comps': 0.35,
        'DFCF': 0.5,
        'PDV': 0.15
    }
    for k, v in data.items():
        per = tuple([period[0], k, v[0].index.values[0][2]])
        print("Tick: {}   Date: {} {}".format(k, per[0], per[2]))
        print("Current Price: {}".format(hist_px[k].dropna().values[-1]))
        try:
            v[0]['beta'][per]
        except:
            # Company may havent reported yet in current year
            per = tuple([str(int(period[0])-1), k, v[0].index.values[0][2]])

        for y in range(1, years_fwd+1):
            year = str(int(per[0])+y)
            year_est = {}
            for mod in val_models:
                mod_est = []
                for val in valuations[mod]:
                    try:
                        e = [float(est[3]) for est in v[1] if est[0] == val and
                             est[1] == k and est[2] == year][0]
                    except:
                        # Might not have this model for this year
                        continue
                    mod_est.append(e)
                    print("Model: {}  tick: {}  year: {}  EST: {}".format(val, k, year, e))
                if len(mod_est) == 0:
                    continue
                year_est[mod] = sum(mod_est)/len(mod_est)
                print("Models AVG: {}  tick: {}  year: {}  EST: {}".format(mod, k, year, '%.4f' % year_est[mod]))
                prem_disc = (year_est[mod] / float(hist_px[k].dropna().values[-1])) - 1
                # Divide by beta
                risk_adj = ((year_est[mod] / float(hist_px[k].dropna().values[-1])) - 1) / v[0]['beta'][per]
                print("Prem/Disc to Current PX: {}  Risk Adj Prem/Disc: {}".format('%.4f' % prem_disc, '%.4f' % risk_adj))
            # Assume 50% for DFCF, 35% for Hist comparables, 15% for peer derived
            year_avg_est = 0
            if len(list(year_est.keys())) < 3:
                # dont have values for all models
                continue
            for key, estimate in year_est.items():
                year_avg_est += estimate * val_weights[key]
            print("Current Price: {}".format(hist_px[k].dropna().values[-1]))
            print("Weighted AVG Estimate   tick: {}  year: {}  EST: {}".format(k, year, '%.4f'%year_avg_est))
            prem_disc = (year_avg_est
                         / float(hist_px[k].dropna().values[-1])) - 1
            # Divide by beta
            risk_adj = ((year_avg_est / float(hist_px[k].dropna().values[-1])) - 1) / v[0]['beta'][per]
            print("Prem/Disc to Current PX: {}  Risk Adj Prem/Disc: {}".format('%.4f'%prem_disc, '%.4f'%risk_adj))


def valuation_model(ticks, mode='db'):
    """
    Main method for valuation model
    """
    full_data = {}

    ind = 'XLK'
    mkt = 'SPY'
    other = [mkt, ind]
    # Get Historical Price data
    hist_px = get_price_data(ticks, other, mode)

    for ind_t in ticks:
        data = {}
        data['is'] = get_ticker_info([ind_t], 'inc_statement',
                                     ['year', 'month', 'tick'])
        data['bs'] = get_ticker_info([ind_t], 'bal_sheet',
                                     ['year', 'month', 'tick'])
        data['cf'] = get_ticker_info([ind_t], 'cf_statement',
                                     ['year', 'month', 'tick'])
        data['fr'] = get_ticker_info([ind_t], 'fin_ratios',
                                     ['year', 'month', 'tick'])
        # join on whatever data you need
        data['is']['gross_profit'] = data['is']['revenue'] - data['is']['cogs']

        data = removeEmptyCols(data)
        # This is only if we have quarterly data
        # data_cum = dataCumColumns(data)
        # data_chg = period_chg(data)
        # data_margin = margin_df(data['is'])[['gross_profit', 'cogs', 'rnd',
        #                                      'sga', 'restruct_mna',
        #                                      'prov_inc_tax', 'other_oper_exp']]

        # Add some columns and adjustemnts and calculate ratios for Use later
        data = ratios_and_valuation(data)

        # project out data based on historicals using OLS regression
        data['ols'] = model_est_ols(10, data)

        # get price info
        data = match_px(data, hist_px, ind_t)
        data = get_beta(data, hist_px, ind_t, other[0], other[1])

        period = [i for i in data['is'].index.values if "E" not in i[2]][-1]
        # Get Historical Ratios for valuation
        hist_rats, ests = historical_ratios(data, period, hist_px)
        # Discounted Free Cash Flow Valuation
        dfcf, ests = discount_fcf(hist_rats, period, ests)
        full_data[ind_t] = [dfcf, ests]

    # calculate performance metrics based on price
    px_df = price_perf_anal(period, mkt, ind, hist_px)
    for ind, px_tick in px_df.iterrows():
        print("{} for year: {}  Return: {}  Rel Mkt Ret: {},  Rel Bmk Ret: {}"
              "".format(ind[0], ind[1], '%.3f' % px_tick['ytd_chg'],
                        '%.3f' % px_tick['mkt_rel_perf'], '%.3f' % px_tick['ind_rel_perf']))

    # Comaprisons
    comp_anal = comparison_anal(full_data, period)
    print(comp_anal)

    # Peer Derived Value
    full_data, pdv = peer_derived_value(full_data, period, hist_px)
    print(pdv)

    # Analysis of all valuations
    pdb.set_trace()
    analyze_ests(full_data, period, hist_px)


if __name__ == '__main__':
    # income_state_model(['MSFT'], 'api')
    # valuation_model(['MSFT'])
    # valuation_model(['MSFT', 'AAPL', 'CSCO', 'INTC', 'ORCL'])
    valuation_model(['MSFT', 'INTC'])
    