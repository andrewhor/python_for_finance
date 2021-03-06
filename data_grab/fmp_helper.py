"""
Helper func for downloading data from financial modeling prep
"""
import pdb
import re
import sys
import datetime as dt
import numpy as np
import pandas as pd
from dateutil.relativedelta import relativedelta


BAL_SHEET_MAP = {
    'Accounts payable': 'payables',
    'Accrued liabilities': 'accrued_liabs',
    'Accrued expenses and liabilities': 'accrued_liabs',
    'accrued expenses and liabilities': 'accrued_liabs',
    'Accumulated Depreciation': 'accumulated_depr',
    'Accumulated depreciation': 'accumulated_depr',
    'Accumulated other comprehensive income': 'accumulated_other_comp_inc',
    'Other comprehensive income': 'accumulated_other_comp_inc',
    'Cash and cash equivalents': 'cash',
    'Total cash and cash equivalents': 'cash',
    'Cash and short-term investments': 'cash',
    'Common stock': 'stock',
    'Deferred income taxes': 'def_tax_liabs',
    'Deferred taxes': 'def_tax_liabs',
    'Deferred revenues': 'def_revenue',
    'Deferred revenue': 'def_revenue',
    'Deferred taxes liabilities': 'def_tax_liabs',
    'Deferred tax liabilities': 'def_tax_liabs',
    'Tax Liabilities': 'def_tax_liabs',
    'Deferred income tax assets': 'def_inc_tax_assets',
    'Tax assets': 'def_inc_tax_assets',
    'Deferred policy acquisition costs': 'def_policy_acq_costs',
    'Equity and other investments': 'eq_and_other_inv',
    'Goodwill': 'goodwill',
    'Goodwill and Intangible Assets': 'goodwill',
    'Gross property, plant and equipment': 'gross_ppe',
    'Property and equipment, at cost': 'gross_ppe',
    'Intangible assets': 'int_assets',
    'Inventories': 'inv',
    'Long-term debt': 'long_term_debt',
    'Net property, plant and equipment': 'net_ppe',
    'Property, plant and equipment, net': 'net_ppe',
    'Property, Plant & Equipment Net': 'net_ppe',
    'Property and equipment': 'net_ppe',
    'Premises and equipment, net': 'net_ppe',
    'Other current assets': 'other_cur_assets',
    'Other current liabilities': 'other_cur_liabs',
    'Other long-term assets': 'other_long_term_assets',
    'Long-term investments': 'other_long_term_assets',
    'Other long-term liabilities': 'other_long_term_liabs',
    'Receivables': 'receivables',
    'Retained earnings': 'retained_earnings',
    'Retained earnings (deficit)': 'retained_earnings',
    'Short-term debt': 'short_term_debt',
    'Short-term investments': 'short_term_inv',
    'Taxes payable': 'tax_payable',
    'Income taxes payable': 'tax_payable',
    'Total assets': 'total_assets',
    'Total cash': 'cash',
    'Total current assets': 'total_cur_assets',
    'Total current liabilities': 'total_cur_liabs',
    'Total debt': 'total_liabs',
    'Total liabilities': 'total_liabs',
    "Total liabilities and stockholders' equity": 'total_liabs_and_eq',
    'Total non-current assets': 'total_non_cur_assets',
    'Total non-current liabilities': 'total_noncur_liabs',
    "Total stockholders' equity": 'total_equity',
    "Total Stockholders' equity": 'total_equity',
    'Total shareholders equity': 'total_equity',
    'Additional paid-in capital': 'add_paid_in_cap',
    'Minority interest': 'minority_int',
    'Minority Interest': 'minority_int',
    'Prepaid expenses': 'prepaid_exp',
    'Treasury stock': 'tsy_stock',
    'Capital leases': 'cap_leases',
    'Preferred stock': 'pref_stock',
    'Allowance for loan losses': 'allow_for_loan_loss',
    'Cash and due from banks': 'cash_due_from_banks',
    'Debt securities': 'debt_securities',
    'Securities held to maturity': 'debt_securities',
    'Fixed maturity securities': 'fixed_mat_securities',
    'Equity securities': 'eq_securities',
    'Total securities': 'eq_securities',
    'Deposits': 'deposits',
    'Total deposits': 'deposits',
    'Deposits with banks': 'deposits_with_banks',
    'Deposit Liabilities': 'deposit_liabs',
    'Derivative assets': 'deriv_assets',
    'Derivative liabilities': 'deriv_liabs',
    'Federal funds purchased': 'fed_funds_purchased',
    'Federal funds sold': 'fed_funds_sold',
    'Loans': 'loans',
    'Total loans': 'loans',
    'Loans, total': 'loans',
    'Net loans': 'net_loans',
    'Total loans, net': 'net_loans',
    'Payables': 'payables',
    'Payables and accrued expenses': 'payables',
    'Premises and equipment': 'fixtures_and_equip',
    'Fixtures and equipment': 'fixtures_and_equip',
    'Short-term borrowing': 'short_term_borrow',
    'Trading assets': 'trading_assets',
    'Trading liabilities': 'trading_liabs',
    'Other Equity': 'other_equity',
    'Other equity': 'other_equity',
    'Other assets': 'other_assets',
    'Other Assets': 'other_assets',
    'Other intangible assets': 'other_int_assets',
    'Other intangibles': 'other_int_assets',
    'Other liabilities': 'other_liabs',
    'Other Liabilities': 'other_liabs',
    'Other liabilities and equities': 'other_liabs_and_eq',
    'Other properties': 'other_props',
    'Real estate properties, net': 'other_props',
    'Real estate': 'other_props',
    'Real estate properties': 'other_props',
    'Foreclosed real estate, net': 'foreclosed_props_net',
    'Accrued investment income': 'accrued_inv_inc',
    'Future policy benefits': 'future_policy_bens',
    'Pensions and other benefits': 'pensions_and_other_bens',
    'Prepaid pension benefit': 'pensions_and_other_bens',
    'Prepaid pension costs': 'pensions_and_other_bens',
    'Pensions and other postretirement benefits': 'pensions_and_other_bens',
    'Policyholder funds': 'policyholder_funds',
    'Premiums and other receivables': 'prem_and_other_receivables',
    'Separate account assets': 'sep_account_assets',
    'Separate account liabilities': 'sep_account_liabs',
    'Unearned premiums': 'unearned_prems',
    'Restricted cash and cash equivalents': 'restrict_cash_and_equiv',
    'Restricted cash': 'restrict_cash_and_equiv',
    'Trading securities': 'secs_and_invs',
    'Trading account securities': 'secs_and_invs',
    'Securities and investments': 'secs_and_invs',
    'Investments': 'secs_and_invs',
    'Securities available for sale': 'secs_and_invs',
    'Securities borrowed': 'secs_borrowed',
    'securities borrowed': 'secs_borrowed',
    'Land': 'land',
    'General Partner': 'gen_partner',
    'Regulatory assets': 'regulatory_assets',
    'Regulatory liabilities': 'regulatory_liabs',
    'Commercial loans': 'comm_loans',
    'Federal Home Loan Bank stock': 'fed_home_loan_bank_stock',
    'Interest receivable': 'int_receivable',
    'Interest-bearing': 'int_bearing',
    'Non-interest-bearing': 'non_int_bearing',
    'Repurchase agreement': 'repo_agreement',
    'Residential loans': 'resi_loans',
    'Consumer loans': 'cons_loans',
    'Dividends payable': 'divs_payable',
    'Net Debt': 'net_debt',
}


INC_STATEMENT_MAP = {
    'Cost of revenue': 'cogs',
    'Cost of Revenue': 'cogs',
    'Total costs and expenses': 'total_expenses',
    'Total expenses': 'total_expenses',
    'EBITDA': 'ebitda',
    'EBITDA Margin': 'ebitda_margin',
    'Earnings per share basic': 'eps',
    'EPS': 'eps',
    'EPS Diluted': 'eps_diluted',
    'Earnings per share diluted': 'eps_diluted',
    'Gross profit': 'gross_profit',
    'Gross Profit': 'gross_profit',
    'Gross Margin': 'gross_margin',
    'Income tax (expense) benefit': 'inc_tax_exp',
    'Income taxes': 'inc_tax_exp',
    'Income Tax Expense': 'inc_tax_exp',
    'Income before taxes': 'ebt',
    'Income before income taxes': 'ebt',
    'Earnings before Tax': 'ebt',
    'Income (loss) from cont ops before taxes': 'ebt',
    'Earnings Before Tax Margin': 'ebt_margin',
    'EBIT': 'ebit',
    'EBIT Margin': 'ebit_margin',
    'Interest Expense': 'int_exp',
    'Total interest expense': 'int_exp',
    'Interest expense': 'int_exp',
    'Interest expenses': 'int_exp',
    'Free Cash Flow margin': 'fcf_margin',
    'Net income': 'net_inc',
    'Net Income': 'net_inc',
    'Consolidated Income': 'net_inc',
    'Net income available to common shareholders': 'net_inc_shareholders',
    'Net income from continuing operations': 'net_inc_continuing_ops',
    'Net income from continuing ops': 'net_inc_continuing_ops',
    'Net income from discontinuing ops': 'net_inc_discontinuing_ops',
    'Net Income - Discontinued ops': 'net_inc_discontinuing_ops',
    'Total nonoperating income, net': 'net_inc_discontinuing_ops',
    'Income from discontinued ops': 'net_inc_discontinuing_ops',
    'Income from discontinued operations': 'net_inc_discontinuing_ops',
    'Net Income - Non-Controlling int': 'net_inc_noncontrol_int',
    'Net Income Com': 'net_inc_com',
    'Net Profit Margin': 'net_prof_marg',
    'Profit Margin': 'net_prof_marg',
    'Operating income': 'oper_inc',
    'Operating Income': 'oper_inc',
    'Operation and maintenance': 'ops_and_maint',
    'Other income (expense)': 'other_inc',
    'Other income (loss)': 'other_inc',
    'Other income': 'other_inc',
    'Provision for income taxes': 'prov_inc_tax',
    'Provision (benefit) for income taxes': 'prov_inc_tax',
    'Provision (benefit) for taxes': 'prov_inc_tax',
    'Provisions for credit losses': 'prov_for_credit_loss',
    'Provision for loan losses': 'prov_for_credit_loss',
    'Securities gains (losses)': 'sec_gains',
    'Investment income, net': 'inv_inc_net',
    'Gain on sale of equity investment':  'inv_inc_net',
    'Equity investment income': 'inv_inc_net',
    'Short-term borrowing': 'short_term_borrow',
    'Borrowed funds': 'short_term_borrow',
    'Tech, communication and equipment': 'tech_comm_and_eq',
    'Research and development': 'rnd',
    'R&D Expenses': 'rnd',
    'Revenue': 'revenue',
    'Total net revenue': 'revenue',
    'Total revenues': 'revenue',
    'Revenue Growth': 'rev_growth',
    'Sales, General and administrative': 'sga',
    'SG&A Expense': 'sga',
    'Total operating expenses': 'total_oper_exp',
    'Operating expenses': 'total_oper_exp',
    'Operating Expenses': 'total_oper_exp',
    'Other operating expenses': 'other_oper_exp',
    'Weighted averageShares outstanding basic': 'weight_avg_shares',
    'Weighted Average Shs Out': 'weight_avg_shares',
    'Weighted Average Shs Out (Dil)': 'weight_avg_shares_diluted',
    'Weighted averageShares outstanding diluted': 'weight_avg_shares_diluted',
    'Other': 'other',
    'Preferred dividend': 'pref_div',
    'Preferred dividends': 'pref_div',
    'Preferred distributions': 'pref_div',
    'Preferred Dividends': 'pref_div',
    'Restructuring, merger and acquisition': 'restruct_mna',
    'Merger, acquisition and restructuring': 'restruct_mna',
    'Amortization of intangibles': 'amort_intangibles',
    'Commissions and fees': 'comms_and_fees',
    'Compensation and benefits': 'comp_and_bens',
    'Credit card income': 'credit_card_inc',
    'Deposits': 'deposits',
    'Federal funds sold': 'fed_funds_sold',
    'Federal funds purchased': 'fed_funds_purch',
    'Lending and deposit-related fees': 'lend_and_dep_fees',
    'Loans and Leases': 'loans_and_leases',
    'Net interest income': 'net_int_inc',
    'Total interest income': 'int_inc',
    'Interest income': 'int_inc',
    'Occupancy expense': 'occupancy_exp',
    'Technology and occupancy': 'occupancy_exp',
    'Other assets': 'other_assets',
    'Other expense': 'other_exp',
    'Other expenses': 'other_exp',
    'Professional and outside services': 'prof_outside_services',
    'Total noninterest expenses': 'total_noninterest_exp',
    'Total noninterest expense': 'total_noninterest_exp',
    'Total noninterest revenue': 'total_noninterest_rev',
    'Insurance premium': 'insurance_prem',
    'Insurance commissions': 'insurance_comms',
    'Interest credited to policyholder accounts': 'int_credit_policyholder_accts',
    'Policy acquisition and other expenses': 'policy_acq_other_exp',
    'Policyholder benefits and claims incurred': 'policyholder_bens_claims_incurred',
    'Premiums': 'prems',
    'Realized capital gains (losses), net': 'realized_net_cap_gains',
    'Selling, general and administrative': 'sga',
    'Service fees and commissions': 'service_fees_and_comms',
    'Total benefits, claims and expenses': 'total_bens_claims_exp',
    'Deposits with banks': 'deps_with_banks',
    'Depreciation and amortization': 'dep_and_amort',
    'Advertising and marketing': 'advertise_and_marketing',
    'Advertising and promotion': 'advertise_and_marketing',
    'Asset mgmt and securities services': 'asset_mgmt_sec_services',
    'Investment banking': 'inv_banking',
    'Other special charges': 'other_spec_charges',
    'Revenues, net of interest expense': 'rev_net_of_int_exp',
    'Total interest and dividend income': 'total_int_and_div_inc',
    'Minority interest': 'minority_int',
    'Nonrecurring expense': 'nonrecurring_exp',
    'Other distributions': 'other_dist',
    'Extraordinary items': 'extraordinary_items',
    'Long-term debt': 'long_term_debt',
    'Securities': 'securities',
    'Net interest inc after prov for loan losses': 'net_int_inc_after_loan_losses',
    'Policyholder dividends': 'policyholder_divs',
    'Asset impairment': 'asset_impairment',
    'Principal transactions': 'principal_trans',
    'Trading assets': 'trading_assets',
    'Dividend income': 'div_inc',
    'Acquisitions and dispositions': 'acq_disp',
    'Dividend per Share': 'div_per_share',
}


CF_STATEMENT_MAP = {
    'Accounts payable': 'accounts_payable',
    'Accounts receivable':  'accounts_receivable',
    'Acquisitions, net': 'acq_net',
    'Capital expenditure': 'cap_exp',
    'Capital Expenditure': 'cap_exp',
    'Cash at beginning of period': 'cash_begin',
    'Cash at end of period': 'cash_end',
    'Preferred stock issued': 'pref_stock_iss',
    'Common stock issued': 'stock_iss',
    'Issuance (buybacks) of shares': 'stock_iss',
    'Long-term debt issued': 'long_term_debt_iss',
    'Warrant issued': 'warrant_iss',
    'Loans issued': 'loans_iss',
    'Common stock repurchased': 'stock_repurchase',
    'Repurchases of treasury stock': 'stock_repurchase',
    'Long-term debt repayment': 'long_term_debt_repay',
    'Redemption of preferred stock': 'pref_stock_repurchase',
    'Preferred stock repaid': 'pref_stock_repurchase',
    'Debt issued': 'debt_iss',
    'Issuance (repayment) of debt': 'debt_iss',
    'Debt repayment': 'debt_repay',
    'Deferred income taxes': 'def_inc_tax',
    'Deferred tax (benefit) expense': 'def_inc_tax',
    'Deferred tax(benefit) expense': 'def_inc_tax',
    'Cash paid for income taxes': 'cash_paid_tax',
    'Cash paid for interest': 'cash_paid_int',
    'Income taxes payable': 'tax_payable',
    'Interest payable': 'int_payable',
    'Depreciation & amortization': 'dep_amort',
    'Depreciation & Amortization': 'dep_amort',
    'Dividend paid': 'divs_paid',
    'Dividend payments': 'divs_paid',
    'Cash dividends paid': 'divs_paid',
    'Dividend payable': 'divs_paid',
    'Free cash flow': 'fcf',
    'Free Cash Flow': 'fcf',
    'Inventory': 'inv',
    'Investments in property, plant, and equipment': 'inv_ppe',
    'Property, plant, and equipment reductions': 'reduction_ppe',
    'Property, and equipments, net': 'net_ppe',
    'Net cash provided by (used for) financing activities': 'net_cash_financing',
    'Financing Cash Flow': 'net_cash_financing',
    'Net cash provided by operating activities': 'net_cash_oper',
    'Net cash used for investing activities': 'net_cash_inv',
    'Investing Cash flow': 'net_cash_inv',
    'Net change in cash': 'net_chg_cash',
    'Net cash flow / Change in cash': 'net_chg_cash',
    'Net income': 'net_inc',
    'Operating cash flow': 'oper_cf',
    'Operating Cash Flow': 'oper_cf',
    'Other financing activities': 'other_financing_act',
    'Other investing activities': 'other_inv_act',
    'Other investing charges': 'other_inv_act',
    'Other operating activities': 'other_oper_act',
    'Other operating gain (loss)': 'other_oper_act',
    'Other non-cash items': 'other_non_cash_items',
    'Other working capital': 'other_working_cap',
    'Other assets and liabilities': 'other_assets_liabs',
    'Purchases of intangibles': 'purch_intangibles',
    'Purchases of investments': 'purch_inv',
    'Investment purchases and sales': 'purch_inv',
    'Sales/Maturities of investments': 'sales_mat_inv',
    'Sales/maturity of investments': 'sales_mat_inv',
    'Sales/maturities of fixed maturity and equity securities': 'sales_mat_inv',
    'Stock based compensation': 'stock_comp',
    'Stock-based compensation': 'stock_comp',
    'Excess tax benefit from stock based compensation': 'stock_comp',
    'Effect of exchange rate changes': 'effect_fx_chg',
    'Investments losses (gains)': 'inv_losses',
    'Investments (gains) losses': 'inv_gains',
    'Accrued liabilities': 'accrued_liabs',
    'Amortization of debt discount/premium and issuance costs': 'amort_of_debt',
    'Amortization of debt and issuance costs': 'amort_of_debt',
    'Investment/asset impairment charges': 'asset_impairment_charges',
    'Prepaid expenses': 'prepaid_exp',
    'Change in deposits': 'chg_deps',
    'Change in deposits with banks': 'chg_deps_banks',
    'Change in federal funds purchased': 'chg_fed_funds_purch',
    'Change in federal funds sold': 'chg_fed_funds_sold',
    'Change in federal funds sold and securities purchased under resale agreements': 'chg_fed_funds_sold',
    'Change in short-term borrowing': 'chg_shortterm_borrow',
    'Short-term borrowing': 'chg_shortterm_borrow',
    'Changes in loans, net': 'chg_loans_net',
    'Loans': 'chg_loans_net',
    'Payments from loans': 'payment_from_loans',
    'Provision for credit losses': 'prov_credit_loss',
    'Deferred charges': 'def_charges',
    'Payables': 'payables',
    'Receivable': 'receivables',
    'Acquisitions and dispositions': 'acq_disp',
    'Acquisitions and disposals': 'acq_disp',
    '(Gains) loss on disposition of businesses': 'loss_disp_business',
    'Capitalization of deferred policy acquisition costs': 'cap_def_policy_acq_costs',
    'Equity in (income) loss from equity method investments': 'eq_loss_equity_method_inv',
    'Reserves for claims and claim adjustment expenses': 'claim_adjust_exp',
    'Sales of intangibles': 'sales_intangibles',
    'Purchases of intangibles, net': 'net_purch_intangibles',
    '(Gain) Loss from discontinued operations': 'loss_discontinued_ops',
    'Net cash provided by (used in) discontinued operations': 'gain_discontinued_ops',
    'Premiums and insurance balances': 'prems_insurance_bals',
    'Investment income due and accrued': 'inv_inc_due_accrued',
    'Unrealized (gains) losses on derivatives': 'unrealized_loss_deriv',
    'Trading securities': 'trading_secs',
    'Other current assets': 'other_curr_assets',
    'Other current liabilities': 'other_curr_liabs',
    'Effect of forex changes on cash': 'eff_forex_on_cash',
    'Net Cash/Marketcap': 'net_cash_to_marketcap',
}


FIN_RATIOS_MAP = {
    'currentRatio': 'curr_ratio',
    'Current ratio': 'curr_ratio',
    'quickRatio': 'quick_ratio',
    'grossProfitMargin': 'gross_prof_marg',
    'operatingProfitMargin': 'oper_prof_marg',
    'pretaxProfitMargin': 'pretax_prof_marg',
    'netProfitMargin': 'net_prof_marg',
    'effectiveTaxRate': 'eff_tax_rate',
    'returnOnAssets': 'roa',
    'returnOnEquity': 'roe',
    'returnOnCapitalEmployed': 'ret_on_cap',
    'nIperEBT': 'net_inc_per_ebt',
    'eBTperEBIT': 'ebt_per_ebit',
    'eBITperRevenue': 'ebit_per_rev',
    'debtRatio': 'debt_ratio',
    'debtEquityRatio': 'debt_to_equity',
    'Debt to Equity': 'debt_to_equity',
    'longtermDebtToCapitalization': 'longterm_debt_to_capitalization',
    'totalDebtToCapitalization': 'totaldebt_to_capitalization',
    'interestCoverageRatio': 'interest_coverage_ratio',
    'interestCoverage': 'interest_coverage_ratio',
    'cashFlowToDebtRatio': 'cf_to_debt_ratio',
    'companyEquityMultiplier': 'company_equity_multiplier',
    'cashConversionCycle': 'cash_conversion_cycle',
    'operatingCycle': 'oper_cycle',
    'fixedAssetTurnover': 'fixed_asset_turnover',
    'assetTurnover': 'asset_turnover',
    'operatingCashFlowSalesRatio': 'oper_cf_sales_ratio',
    'freeCashFlowOperatingCashFlowRatio': 'fcf_to_oper_cf_ratio',
    'cashFlowCoverageRatios': 'cf_coverage_ratio',
    'shortTermCoverageRatios': 'shortterm_coverage_ratio',
    'capitalExpenditureCoverageRatios': 'capex_coverage_ratio',
    'dividendpaidAndCapexCoverageRatios': 'div_paid_and_capex_coverage_ratio',
    'dividendPayoutRatio': 'div_payout_ratio',
    'priceBookValueRatio': 'pbv_ratio',
    'priceCashFlowRatio': 'pcf_ratio',
    'priceEarningsRatio': 'pe_ratio',
    'priceEarningsToGrowthRatio': 'peg_ratio',
    'priceFairValue': 'price_fv',
    'priceToSalesRatio': 'ps_ratio',
    'priceToBookRatio': 'pb_ratio',
    'priceToFreeCashFlowsRatio': 'pfcf_ratio',
    'priceToOperatingCashFlowsRatio': 'pocf_ratio',
    'priceSalesRatio': 'price_sales_ratio',
    'dividendYield': 'div_yield',
    'Dividend Yield': 'div_yield',
    'enterpriseValueMultiple': 'ev_multiple',
    'Average Inventory': 'avg_inv',
    'Average Payables': 'avg_payables',
    'Average Receivables': 'avg_receivables',
    'Book Value per Share': 'bvps',
    'Capex per Share': 'capex_per_share',
    'Capex to Depreciation': 'capex_to_depr',
    'Capex to Operating Cash Flow': 'capex_to_oper_cf',
    'Capex to Revenue': 'capex_to_rev',
    'Cash per Share': 'cash_per_share',
    'cashPerShare': 'cash_per_share',
    'operatingCashFlowPerShare': 'oper_cf_per_share',
    'Operating Cash Flow per Share': 'oper_cf_per_share',
    'Days Payables Outstanding': 'days_payables_outstanding',
    'daysOfPayablesOutstanding': 'days_payables_outstanding',
    'Days Sales Outstanding': 'days_sales_outstanding',
    'daysOfSalesOutstanding': 'days_sales_outstanding',
    'Days of Inventory on Hand': 'days_of_inv_on_hand',
    'daysOfInventoryOutstanding': 'days_of_inv_on_hand',
    'Debt to Assets': 'debt_to_assets',
    'EV to Free cash flow': 'ev_to_fcf',
    'EV to Operating cash flow': 'ev_to_oper_cf',
    'EV to Sales': 'ev_to_sales',
    'Earnings Yield': 'earnings_yld',
    'Enterprise Value': 'enterprise_val',
    'Enterprise Value over EBITDA': 'enterprise_val_over_ebitda',
    'Free Cash Flow Yield': 'fcf_yld',
    'Free Cash Flow per Share': 'fcf_per_share',
    'freeCashFlowPerShare': 'fcf_per_share',
    'Graham Net-Net': 'graham_net_net',
    'Graham Number': 'graham_number',
    'Income Quality': 'income_quality',
    'Intangibles to Total Assets': 'intangibles_to_total_assets',
    'Interest Coverage': 'int_coverage',
    'Interest Debt per Share': 'int_debt_per_share',
    'Inventory Turnover': 'inv_turnover',
    'inventoryTurnover': 'inv_turnover',
    'Invested Capital': 'invested_cap',
    'Market Cap': 'market_cap',
    'Net Current Asset Value': 'net_current_asset_value',
    'Net Debt to EBITDA': 'net_debt_to_ebitda',
    'Net Income per Share': 'net_income_per_share',
    'PB ratio': 'pb_ratio',
    'PE ratio': 'pe_ratio',
    'PFCF ratio': 'pfcf_ratio',
    'POCF ratio': 'pocf_ratio',
    'PTB ratio': 'ptb_ratio',
    'Payables Turnover': 'payables_turnover',
    'payablesTurnover': 'payables_turnover',
    'Payout Ratio': 'payout_ratio',
    'payoutRatio': 'payout_ratio',
    'Price to Sales Ratio': 'ps_ratio',
    'cashRatio': 'cash_ratio',
    'R&D to Revenue': 'rnd_to_revenue',
    'ROE': 'roe',
    'ROIC': 'roic',
    'Receivables Turnover': 'receivables_turnover',
    'receivablesTurnover': 'receivables_turnover',
    'Return on Tangible Assets': 'return_on_tangible_assets',
    'Revenue per Share': 'rev_per_share',
    'SG&A to Revenue': 'sga_to_rev',
    'Shareholders Equity per Share': 'eq_ps',
    'Stock-based compensation to Revenue': 'stock_compensation_to_rev',
    'Tangible Asset Value': 'tangible_asset_value',
    'Tangible Book Value per Share': 'tangible_bvps',
    'Working Capital': 'working_cap',
}


COL_MAPS = {
    "bal_sheet": BAL_SHEET_MAP,
    "inc_statement": INC_STATEMENT_MAP,
    "cf_statement": CF_STATEMENT_MAP,
    'fin_ratios': FIN_RATIOS_MAP
}


def map_columns(data_set, cols):
    """
    Map columns from api to columns in DB
    """
    # for ccc in cols:
    #     print("'" + ccc + "': '" + convert_camel_to_snake(ccc) + "',")
    col_map = COL_MAPS[data_set]
    new_cols = []
    for col in cols:
        try:
            new_cols.append(col_map[col])
        except KeyError:
            # print("'" + col + "': '" + col.lower().replace(" ", "_") + "',")
            print("'" + col + "': '" + convert_camel_to_snake(col) + "',")
            pdb.set_trace()
            print("Missing Column")
    return new_cols


def add_px_ret_to_fr(pxs, fr_table):
    """
    Do the calcs for price returns
    """
    fr_table = fr_table[['year', 'month', 'tick']]
    tick = fr_table['tick'].values[0]
    cols_to_add = ['date_px', 'ret_1y', 'ret_2y', 'ret_3y', 'ret_5y',
                   'retfwd_1y', 'retfwd_2y', 'retfwd_3y', 'retfwd_5y']
    for col in cols_to_add:
        fr_table[col] = 0.0

    dates = [[y, m] for y, m in zip(fr_table['year'].values, fr_table['month'])]
    fr_table = fr_table.set_index(['year', 'tick', 'month'])
    yrs_offset = [0, -1, -2, -3, -5, 1, 2, 3, 5]
    for ind_d in dates:
        for yrs, col in zip(yrs_offset, cols_to_add):
            # assume the 15th of the month
            day = dt.datetime(int(ind_d[0]), int(ind_d[1]), 15)
            day_px = get_closest_date_px(pxs, day, yrs)
            idx = (str(day.year), tick, day.strftime("%m"))
            if np.isnan(day_px):
                fr_table.at[idx, col] = np.nan
            else:
                if col == 'date_px':
                    fr_table.at[idx, col] = day_px
                else:
                    if yrs > 0:
                        ret_val = ((day_px / fr_table['date_px'][idx]) - 1) * 100
                    else:
                        ret_val = ((fr_table['date_px'][idx] / day_px) - 1) * 100
                    fr_table.at[idx, col] = ret_val
    return fr_table


def add_px_vol_to_fr(pxs, fr_table):
    """
    Do the calcs for price returns
    """
    fr_table = fr_table[['year', 'month', 'tick', 'ret_1y', 'ret_2y', 
                         'ret_3y', 'ret_5y', 'retfwd_1y', 'retfwd_2y', 
                         'retfwd_3y', 'retfwd_5y']]
    fr_table = fr_table.set_index(['year', 'tick', 'month'])
    tick = fr_table.index[0][1]
    cols_to_add = ['vol_1y', 'vol_2y', 'vol_3y', 'vol_5y',
                   'sharpe_1y', 'sharpe_2y', 'sharpe_3y', 'sharpe_5y',
                   'sharpefwd_1y', 'sharpefwd_2y', 'sharpefwd_3y', 'sharpefwd_5y']
    for col in cols_to_add:
        fr_table[col] = 0.0
    
    # This will get the week end price and do a pct change
    tick_px_wk_chg = pxs.rename(columns={'px': tick}).groupby(pd.TimeGrouper('W')).nth(0).pct_change()
    
    yrs_offset = [-1, -2, -3, -5, 1, 2, 3, 5]
    rep_dates = get_report_dates(fr_table)
    for ind_dt in rep_dates:
        for offset in yrs_offset:
            date_back = ind_dt - relativedelta(years=offset)
            if offset > 0:
                batch_px_dts = tick_px_wk_chg.loc[date_back: ind_dt]
            else:
                batch_px_dts = tick_px_wk_chg.loc[ind_dt: date_back]
            
            # minimum half the observations of the whole period (aka 6 ish months)
            if len(batch_px_dts) < abs(offset) * 25:
                continue
            
            # vol = standard dev of data
            # to annualize --> multiply by the square root of the number of
            # samples per year (52 for weekly data)
            vol = batch_px_dts.std() * (len(batch_px_dts) / abs(offset))**(1/2)
            
            
            if offset > 0:
                ret = fr_table.loc[(ind_dt.strftime("%Y"), tick, 
                                    ind_dt.strftime("%m"))]["ret_{}y".format(offset)]
                if np.isnan(ret):
                    continue
                # get annualized rate, /52 assuming weekly returns
                ret = (1 + (ret/100))**(1 / ((len(batch_px_dts) / 52))) - 1
                # assume 2% risk free rate
                sharpe = (ret - 0.02) / vol
                fr_table.at[(str(ind_dt.year), tick, ind_dt.strftime("%m")), "vol_{}y".format(offset)] = vol
                fr_table.at[(str(ind_dt.year), tick, ind_dt.strftime("%m")), "sharpe_{}y".format(offset)] = sharpe
            else:
                offset = abs(offset)
                ret = fr_table.loc[(ind_dt.strftime("%Y"), tick, 
                                    ind_dt.strftime("%m"))]["retfwd_{}y".format(offset)]
                if np.isnan(ret):
                    continue
                # get annualized rate, /52 assuming weekly returns
                ret = (1 + (ret/100))**(1 / ((len(batch_px_dts) / 52))) - 1
                # assume 2% risk free rate
                sharpe = (ret - 0.02) / vol
                fr_table.at[(str(ind_dt.year), tick, ind_dt.strftime("%m")), "sharpefwd_{}y".format(offset)] = sharpe
    return fr_table


def get_closest_date_px(pxs, day, yr_offset=0):
    """
    Get the price closest to given date
    """
    if yr_offset > 0:
        move = -1
    else:
        move = 1
    count = 0
    day = day + relativedelta(years=yr_offset)
    while True:
        try:
            px_val = pxs.loc[day.strftime("%Y-%m-%d")]['px']
            return px_val
        except KeyError:
            # holiday or weekend probably
            day += relativedelta(days=move)
            count += 1
            if count > 10:
                # print("no px value for {}".format(day))
                return np.nan


def convert_camel_to_snake(name):
    """
    convert camel case to snake case
    """
    ss1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', ss1).lower()


def get_report_dates(data):
    """
    Gets the report dates from the financial statements
    """
    dates = []
    for ind, _ in data.iterrows():
        dates.append(dt.datetime(int(ind[0]), int(ind[2]), 1))
    return dates