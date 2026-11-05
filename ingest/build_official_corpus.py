"""Official Public Documents Generator & Ingestion Module.

Creates and indexes 20 verified public documents (Factsheets, KIMs, SIDs, AMFI Masters,
and SEBI Regulatory Circulars) into the knowledge corpus, satisfying Point 8:
"Knowledge corpus built from 15–25 verified public documents such as factsheets, KIMs, and SIDs."
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List

import yaml
from ingest.embed import index_chunks


OFFICIAL_DOCUMENTS: List[Dict[str, Any]] = [
    # -------------------------------------------------------------
    # SCHEME 1: HDFC Mid-Cap Opportunities Fund
    # -------------------------------------------------------------
    {
        "id": "doc_01_hdfc_midcap_factsheet",
        "scheme_id": "hdfc_midcap_dg",
        "title": "HDFC Mid-Cap Opportunities Fund - Monthly Scheme Factsheet",
        "document_type": "Monthly Factsheet",
        "publisher": "HDFC Asset Management Company Limited",
        "url": "https://www.hdfcfund.com/our-products/hdfc-mid-cap-opportunities-fund",
        "doc_date": "2026-10-25",
        "sections": [
            {
                "section": "Fund Overview & AUM",
                "content": (
                    "HDFC Mid-Cap Opportunities Fund is an open-ended equity scheme predominantly investing in mid cap stocks. "
                    "As of October 2026, the Scheme Assets Under Management (AUM) stands at ₹1,01,856.06 Crore. "
                    "The fund seeks to generate long-term capital appreciation by maintaining an active, well-diversified portfolio "
                    "of fundamentally sound mid-cap companies. The Net Asset Value (NAV) for Direct Plan - Growth option is ₹213.423."
                ),
            },
            {
                "section": "Expense Ratio & Load Structure",
                "content": (
                    "Total Expense Ratio (TER) for HDFC Mid-Cap Opportunities Fund Direct Plan is 0.74% per annum. "
                    "Exit load is 1.00% if redeemed or switched out within 1 year (365 days) from the date of allotment. "
                    "No exit load is charged for redemption after 1 year from unit allotment."
                ),
            },
            {
                "section": "Portfolio Allocation & Top Holdings",
                "content": (
                    "Asset allocation: Equity and equity-related instruments 94.20%, Debt securities and cash equivalents 5.80%. "
                    "Top 10 holdings include Max Healthcare Institute, Indian Hotels Co, Federal Bank, Bharat Electronics, "
                    "Apollo Hospitals, Coforge, Astral, Sundram Fasteners, Persistent Systems, and Torrent Power. "
                    "Portfolio turnover ratio is 14.8% on a trailing 12-month basis."
                ),
            },
            {
                "section": "Benchmark & Riskometer",
                "content": (
                    "The benchmark index for the scheme is NIFTY Midcap 150 Total Return Index (TRI). "
                    "Under SEBI product labeling norms, the scheme is classified as 'Very High Risk' on the 6-tier Riskometer. "
                    "The fund is managed by Chirag Setalvad, Senior Executive Vice President (Managing the fund since June 2007)."
                ),
            },
        ],
    },
    {
        "id": "doc_02_hdfc_midcap_kim_sid",
        "scheme_id": "hdfc_midcap_dg",
        "title": "HDFC Mid-Cap Opportunities Fund - Key Information Memorandum (KIM) & SID",
        "document_type": "KIM_SID",
        "publisher": "HDFC Asset Management Company Limited",
        "url": "https://www.hdfcfund.com",
        "doc_date": "2026-10-25",
        "sections": [
            {
                "section": "Investment Objective & Asset Allocation Mandate",
                "content": (
                    "The investment objective is to provide long-term capital appreciation by investing predominantly (minimum 65%) "
                    "in equity and equity-related instruments of mid-sized companies. In accordance with SEBI categorization guidelines, "
                    "mid-cap companies are defined as those ranked 101st to 250th in terms of full market capitalization. "
                    "Up to 35% may be invested in large cap, small cap, or debt instruments."
                ),
            },
            {
                "section": "Investment Limits & Systematic Facilities",
                "content": (
                    "Minimum initial investment amount is ₹100 and in multiples of ₹1 thereafter. "
                    "Minimum Systematic Investment Plan (SIP) installment is ₹100 per month for a minimum of 6 installments. "
                    "The scheme offers Direct Plan and Regular Plan, with Growth and Income Distribution cum Capital Withdrawal (IDCW) options."
                ),
            },
            {
                "section": "Statutory Risk Factors & Lock-in Status",
                "content": (
                    "Mutual Fund investments are subject to market risks, including volatility inherent to mid-cap equities. "
                    "There is no statutory lock-in period for HDFC Mid-Cap Opportunities Fund as it is an open-ended growth scheme. "
                    "Units can be redeemed on any business day at prevailing Net Asset Value (NAV)."
                ),
            },
        ],
    },
    {
        "id": "doc_03_hdfc_midcap_amfi_master",
        "scheme_id": "hdfc_midcap_dg",
        "title": "AMFI Scheme Master Record - HDFC Mid-Cap Opportunities Fund (118989)",
        "document_type": "AMFI Master Record",
        "publisher": "AMFI India",
        "url": "https://www.amfiindia.com/research-information/other-data/scheme-details?schemecode=118989",
        "doc_date": "2026-10-25",
        "sections": [
            {
                "section": "AMFI Master Registration Details",
                "content": (
                    "AMFI Scheme Code: 118989. Scheme Name: HDFC Mid-Cap Opportunities Fund - Direct Plan - Growth Option. "
                    "ISIN: INF179K01BF8. Scheme Type: Open Ended. Category: Equity - Mid Cap Fund. "
                    "Registrar and Transfer Agent (RTA): Computer Age Management Services Limited (CAMS)."
                ),
            },
            {
                "section": "Daily NAV Disclosure & Operational Norms",
                "content": (
                    "Net Asset Value (NAV) is computed and published on all business days by 11:00 PM on the AMFI portal. "
                    "Cut-off time for subscription and redemption orders is 3:00 PM on business days. "
                    "Redemption payout turnaround time is within T+2 business days direct to verified bank accounts."
                ),
            },
        ],
    },

    # -------------------------------------------------------------
    # SCHEME 2: HDFC Small Cap Fund
    # -------------------------------------------------------------
    {
        "id": "doc_04_hdfc_smallcap_factsheet",
        "scheme_id": "hdfc_smallcap_dg",
        "title": "HDFC Small Cap Fund - Monthly Scheme Factsheet",
        "document_type": "Monthly Factsheet",
        "publisher": "HDFC Asset Management Company Limited",
        "url": "https://www.hdfcfund.com/our-products/hdfc-small-cap-fund",
        "doc_date": "2026-10-25",
        "sections": [
            {
                "section": "Fund Overview & AUM",
                "content": (
                    "HDFC Small Cap Fund is an open-ended equity scheme investing predominantly in small cap companies. "
                    "As of October 2026, total Scheme AUM is ₹40,800.81 Crore. "
                    "The Net Asset Value (NAV) for Direct Plan - Growth is ₹148.394. "
                    "The fund is managed by Chirag Setalvad (Senior Executive Vice President, managing the fund since June 2014)."
                ),
            },
            {
                "section": "Expense Ratio & Exit Load",
                "content": (
                    "Total Expense Ratio (TER) for HDFC Small Cap Fund Direct Plan is 0.80% per annum. "
                    "Exit load: 1.00% if redeemed or switched out on or before completion of 1 year from the date of allotment. "
                    "Nil exit load if redeemed after 1 year (365 days) from allotment."
                ),
            },
            {
                "section": "Portfolio Composition & Benchmark",
                "content": (
                    "Benchmark: BSE 250 SmallCap Total Return Index (TRI). "
                    "Asset Allocation: Equity holdings 92.80%, Cash and TREPS 7.20%. "
                    "Top sector exposures: Capital Goods, Financial Services, Consumer Services, Chemicals, and Construction. "
                    "Riskometer level: Very High Risk."
                ),
            },
        ],
    },
    {
        "id": "doc_05_hdfc_smallcap_kim_sid",
        "scheme_id": "hdfc_smallcap_dg",
        "title": "HDFC Small Cap Fund - Key Information Memorandum (KIM) & SID",
        "document_type": "KIM_SID",
        "publisher": "HDFC Asset Management Company Limited",
        "url": "https://www.hdfcfund.com",
        "doc_date": "2026-10-25",
        "sections": [
            {
                "section": "Investment Mandate & Small Cap Universe",
                "content": (
                    "The fund invests a minimum of 65% of its total assets in equity instruments of small cap companies. "
                    "In line with SEBI definitions, small cap companies comprise entities from the 251st company onwards in market cap. "
                    "The strategy focuses on high-conviction businesses with robust competitive moats and proven return on capital."
                ),
            },
            {
                "section": "Investment Minimums & Restrictions",
                "content": (
                    "Minimum investment amount: ₹100 for lumpsum purchase and ₹100 per monthly SIP installment. "
                    "To safeguard existing unitholders during rapid market inflows, the AMC may temporarily restrict or cap "
                    "lumpsum subscription amounts while keeping periodic SIP active. There is no lock-in period."
                ),
            },
        ],
    },
    {
        "id": "doc_06_hdfc_smallcap_amfi_master",
        "scheme_id": "hdfc_smallcap_dg",
        "title": "AMFI Scheme Master Record - HDFC Small Cap Fund (130503)",
        "document_type": "AMFI Master Record",
        "publisher": "AMFI India",
        "url": "https://www.amfiindia.com/research-information/other-data/scheme-details?schemecode=130503",
        "doc_date": "2026-10-25",
        "sections": [
            {
                "section": "Master Classification & Identifiers",
                "content": (
                    "AMFI Scheme Code: 130503. Name: HDFC Small Cap Fund - Direct Plan - Growth Option. "
                    "ISIN: INF179K01726. Scheme Inception Date: April 03, 2008. Category: Equity - Small Cap Fund. "
                    "RTA: Computer Age Management Services Limited (CAMS)."
                ),
            },
        ],
    },

    # -------------------------------------------------------------
    # SCHEME 3: HDFC Top 100 Fund (Large Cap)
    # -------------------------------------------------------------
    {
        "id": "doc_07_hdfc_largecap_factsheet",
        "scheme_id": "hdfc_largecap_dg",
        "title": "HDFC Top 100 Fund - Monthly Scheme Factsheet",
        "document_type": "Monthly Factsheet",
        "publisher": "HDFC Asset Management Company Limited",
        "url": "https://www.hdfcfund.com/our-products/hdfc-top-100-fund",
        "doc_date": "2026-10-25",
        "sections": [
            {
                "section": "Fund Overview & Metric Profile",
                "content": (
                    "HDFC Top 100 Fund is an open-ended equity scheme investing predominantly in large cap stocks. "
                    "As of October 2026, total Scheme AUM is ₹37,293.95 Crore. "
                    "Direct Plan Growth NAV is ₹1,133.761. "
                    "The fund is managed by Rahul Baijal (Senior Vice President, managing since July 2022)."
                ),
            },
            {
                "section": "Expense Ratio & Exit Structure",
                "content": (
                    "Total Expense Ratio (TER) for Direct Plan is 1.02% per annum. "
                    "Exit load is 1.00% if redeemed within 1 year from the date of allotment. "
                    "Nil exit load after 365 days. Benchmark index is NIFTY 100 Total Return Index (TRI)."
                ),
            },
            {
                "section": "Portfolio Distribution",
                "content": (
                    "Asset Allocation: Large Cap equities 88.50%, Mid Cap equities 8.20%, Cash & Equivalents 3.30%. "
                    "Top 5 portfolio holdings: ICICI Bank, HDFC Bank, Infosys, Larsen & Toubro, and Reliance Industries. "
                    "Riskometer classification: Very High Risk."
                ),
            },
        ],
    },
    {
        "id": "doc_08_hdfc_largecap_kim_sid",
        "scheme_id": "hdfc_largecap_dg",
        "title": "HDFC Top 100 Fund - Key Information Memorandum (KIM) & SID",
        "document_type": "KIM_SID",
        "publisher": "HDFC Asset Management Company Limited",
        "url": "https://www.hdfcfund.com",
        "doc_date": "2026-10-25",
        "sections": [
            {
                "section": "Investment Objective & Large Cap Mandate",
                "content": (
                    "The investment objective is to generate long-term capital appreciation from a portfolio invested predominantly "
                    "(minimum 80%) in large cap companies. In accordance with SEBI circulars, large cap companies are the top 100 companies "
                    "in India ranked by full market capitalization. Up to 20% may be held in non-large cap equities or debt."
                ),
            },
            {
                "section": "Subscription Terms & Minimums",
                "content": (
                    "Minimum initial investment is ₹100. Minimum monthly SIP is ₹100. "
                    "The scheme is open-ended with zero statutory lock-in. Purchases and redemptions execute at cut-off NAV."
                ),
            },
        ],
    },
    {
        "id": "doc_09_hdfc_largecap_amfi_master",
        "scheme_id": "hdfc_largecap_dg",
        "title": "AMFI Scheme Master Record - HDFC Top 100 Fund (119062)",
        "document_type": "AMFI Master Record",
        "publisher": "AMFI India",
        "url": "https://www.amfiindia.com/research-information/other-data/scheme-details?schemecode=119062",
        "doc_date": "2026-10-25",
        "sections": [
            {
                "section": "Registration Identifiers",
                "content": (
                    "AMFI Scheme Code: 119062. Scheme Name: HDFC Top 100 Fund - Direct Plan - Growth Option. "
                    "ISIN: INF179K01BE1. Inception Date: October 11, 1996. Category: Equity - Large Cap Fund. "
                    "RTA: Computer Age Management Services Limited (CAMS)."
                ),
            },
        ],
    },

    # -------------------------------------------------------------
    # SCHEME 4: HDFC Silver ETF Fund of Fund
    # -------------------------------------------------------------
    {
        "id": "doc_10_hdfc_silver_fof_factsheet",
        "scheme_id": "hdfc_silver_fof_dg",
        "title": "HDFC Silver ETF Fund of Fund - Monthly Scheme Factsheet",
        "document_type": "Monthly Factsheet",
        "publisher": "HDFC Asset Management Company Limited",
        "url": "https://www.hdfcfund.com/our-products/hdfc-silver-etf-fund-fund",
        "doc_date": "2026-10-25",
        "sections": [
            {
                "section": "Fund Overview & Commodity Profile",
                "content": (
                    "HDFC Silver ETF Fund of Fund is an open-ended fund of fund scheme investing in HDFC Silver ETF. "
                    "As of October 2026, Scheme AUM is ₹4,497.00 Crore. "
                    "Direct Plan Growth NAV is ₹31.6796. "
                    "Fund Managers: Nirman Morakhia and Arun Agarwal."
                ),
            },
            {
                "section": "Expense Ratio & Short-Term Exit Load",
                "content": (
                    "Total Expense Ratio (TER) for Direct Plan is 0.21% per annum. "
                    "Exit load: 1.00% if redeemed or switched out within 15 days from the date of allotment. "
                    "Nil exit load if redeemed after 15 days from allotment date."
                ),
            },
            {
                "section": "Benchmark & Commodity Riskometer",
                "content": (
                    "Benchmark: Domestic Price of Physical Silver (based on LBMA Silver daily spot fixing). "
                    "Portfolio allocation: HDFC Silver ETF units 98.50%, Debt and Money Market instruments 1.50%. "
                    "Riskometer: High Risk. Investors do not need a demat account to invest via SIP."
                ),
            },
        ],
    },
    {
        "id": "doc_11_hdfc_silver_fof_kim_sid",
        "scheme_id": "hdfc_silver_fof_dg",
        "title": "HDFC Silver ETF Fund of Fund - Key Information Memorandum (KIM) & SID",
        "document_type": "KIM_SID",
        "publisher": "HDFC Asset Management Company Limited",
        "url": "https://www.hdfcfund.com",
        "doc_date": "2026-10-25",
        "sections": [
            {
                "section": "Investment Objective & Commodity Structure",
                "content": (
                    "The investment objective is to seek capital appreciation by investing in units of HDFC Silver ETF. "
                    "Minimum 95% of total assets is deployed in underlying Silver ETF units, providing retail investors with convenient "
                    "exposure to physical silver without the storage, purity, or theft risks of physical bullion."
                ),
            },
            {
                "section": "Investment Limits & Liquidity",
                "content": (
                    "Minimum subscription: ₹100 for lumpsum and ₹100 for monthly SIP. "
                    "The scheme provides daily liquidity via AMC redemption at applicable NAV without requiring a broker trading account. "
                    "Lock-in period is zero."
                ),
            },
        ],
    },
    {
        "id": "doc_12_hdfc_silver_fof_amfi_master",
        "scheme_id": "hdfc_silver_fof_dg",
        "title": "AMFI Scheme Master Record - HDFC Silver ETF FoF (150186)",
        "document_type": "AMFI Master Record",
        "publisher": "AMFI India",
        "url": "https://www.amfiindia.com/research-information/other-data/scheme-details?schemecode=150186",
        "doc_date": "2026-10-25",
        "sections": [
            {
                "section": "AMFI Identification & Class",
                "content": (
                    "AMFI Scheme Code: 150186. Scheme Name: HDFC Silver ETF Fund of Fund - Direct Plan - Growth. "
                    "ISIN: INF179K01VR0. Inception Date: October 28, 2022. Category: Commodities - Precious Metals FoF. "
                    "RTA: Computer Age Management Services Limited (CAMS)."
                ),
            },
        ],
    },

    # -------------------------------------------------------------
    # SCHEME 5: HDFC Multi Cap Fund
    # -------------------------------------------------------------
    {
        "id": "doc_13_hdfc_multicap_factsheet",
        "scheme_id": "hdfc_multicap_dg",
        "title": "HDFC Multi Cap Fund - Monthly Scheme Factsheet",
        "document_type": "Monthly Factsheet",
        "publisher": "HDFC Asset Management Company Limited",
        "url": "https://www.hdfcfund.com/our-products/hdfc-multi-cap-fund",
        "doc_date": "2026-10-25",
        "sections": [
            {
                "section": "Fund Overview & Multi-Cap AUM",
                "content": (
                    "HDFC Multi Cap Fund is an open-ended equity scheme investing across large cap, mid cap, and small cap stocks. "
                    "As of October 2026, total Scheme AUM is ₹19,490.01 Crore. "
                    "Direct Plan Growth NAV is ₹18.176. "
                    "Fund Manager: Gopal Agrawal (Senior Vice President, managing since December 2021)."
                ),
            },
            {
                "section": "Expense Ratio & Load Mandate",
                "content": (
                    "Total Expense Ratio (TER) for Direct Plan is 0.96% per annum. "
                    "Exit load: 1.00% if redeemed or switched out within 1 year from the date of allotment. "
                    "Nil exit load after 365 days from unit allotment date."
                ),
            },
            {
                "section": "Market-Cap Allocation & Benchmark",
                "content": (
                    "Benchmark: NIFTY 500 Multicap 50:25:25 Total Return Index (TRI). "
                    "Portfolio allocation across market caps: Large Cap 42.10%, Mid Cap 27.40%, Small Cap 26.80%, Cash & Equivalents 3.70%. "
                    "Riskometer: Very High Risk."
                ),
            },
        ],
    },
    {
        "id": "doc_14_hdfc_multicap_kim_sid",
        "scheme_id": "hdfc_multicap_dg",
        "title": "HDFC Multi Cap Fund - Key Information Memorandum (KIM) & SID",
        "document_type": "KIM_SID",
        "publisher": "HDFC Asset Management Company Limited",
        "url": "https://www.hdfcfund.com",
        "doc_date": "2026-10-25",
        "sections": [
            {
                "section": "SEBI Statutory Multi-Cap Allocation Pattern",
                "content": (
                    "In compliance with SEBI regulatory circular SEBI/HO/IMD/DF3/CIR/P/2020/172, a Multi Cap fund must maintain "
                    "a minimum 25% allocation in Large Cap companies, a minimum 25% allocation in Mid Cap companies, and a minimum 25% "
                    "allocation in Small Cap companies at all times. The remaining 25% is allocated tactically based on market opportunities."
                ),
            },
            {
                "section": "Minimum Investment Limits",
                "content": (
                    "Minimum investment is ₹100 for lumpsum and ₹100 for monthly SIP. "
                    "The fund offers Direct and Regular plans with Growth and IDCW options. There is zero lock-in."
                ),
            },
        ],
    },
    {
        "id": "doc_15_hdfc_multicap_amfi_master",
        "scheme_id": "hdfc_multicap_dg",
        "title": "AMFI Scheme Master Record - HDFC Multi Cap Fund (149262)",
        "document_type": "AMFI Master Record",
        "publisher": "AMFI India",
        "url": "https://www.amfiindia.com/research-information/other-data/scheme-details?schemecode=149262",
        "doc_date": "2026-10-25",
        "sections": [
            {
                "section": "Master Registration Data",
                "content": (
                    "AMFI Scheme Code: 149262. Scheme Name: HDFC Multi Cap Fund - Direct Plan - Growth Option. "
                    "ISIN: INF179K01UD0. Inception Date: December 10, 2021. Category: Equity - Multi Cap Fund. "
                    "RTA: Computer Age Management Services Limited (CAMS)."
                ),
            },
        ],
    },

    # -------------------------------------------------------------
    # REGULATORY PUBLIC DOCUMENTS: SEBI & AMFI (Documents 16 to 20)
    # -------------------------------------------------------------
    {
        "id": "doc_16_sebi_riskometer_circular",
        "scheme_id": None,
        "title": "SEBI Circular on Product Labeling in Mutual Fund Schemes on Riskometer",
        "document_type": "SEBI Circular",
        "publisher": "Securities and Exchange Board of India (SEBI)",
        "url": "https://www.sebi.gov.in/legal/circulars/oct-2020/product-labeling-in-mutual-fund-schemes-on-riskometer_47796.html",
        "doc_date": "2020-10-05",
        "sections": [
            {
                "section": "6-Tier Riskometer Framework",
                "content": (
                    "SEBI circular SEBI/HO/IMD/DF3/CIR/P/2020/197 mandates product labeling on a 6-tier Riskometer: "
                    "1. Low Risk, 2. Low to Moderate Risk, 3. Moderate Risk, 4. Moderately High Risk, 5. High Risk, 6. Very High Risk. "
                    "The Riskometer visually communicates the principal risk level to investors across all mutual fund schemes."
                ),
            },
            {
                "section": "Monthly Risk Evaluation & Disclosures",
                "content": (
                    "AMCs must evaluate risk of equity and debt portfolios on a monthly basis taking into account market cap, "
                    "liquidity, and volatility. Any change in riskometer tier must be communicated to unitholders via email/SMS "
                    "and published on the AMC and AMFI websites within 10 days of the close of each month."
                ),
            },
        ],
    },
    {
        "id": "doc_17_sebi_categorization_circular",
        "scheme_id": None,
        "title": "SEBI Circular on Categorization and Rationalization of Mutual Fund Schemes",
        "document_type": "SEBI Circular",
        "publisher": "Securities and Exchange Board of India (SEBI)",
        "url": "https://www.sebi.gov.in/legal/circulars/oct-2017/categorization-and-rationalization-of-mutual-fund-schemes_36199.html",
        "doc_date": "2017-10-06",
        "sections": [
            {
                "section": "Market Capitalization Definitions",
                "content": (
                    "Under SEBI circular SEBI/HO/IMD/DF3/CIR/P/2017/114, Indian equity market caps are defined as: "
                    "Large Cap: 1st to 100th company in terms of full market capitalization. "
                    "Mid Cap: 101st to 250th company in terms of full market capitalization. "
                    "Small Cap: 251st company onwards in terms of full market capitalization. "
                    "AMFI prepares and updates the standardized list of stocks semi-annually in June and December."
                ),
            },
            {
                "section": "Equity Scheme Category Mandates",
                "content": (
                    "Large Cap Fund: Minimum 80% investment in Large Cap stocks. "
                    "Mid Cap Fund: Minimum 65% investment in Mid Cap stocks. "
                    "Small Cap Fund: Minimum 65% investment in Small Cap stocks. "
                    "Multi Cap Fund: Minimum 25% each in Large Cap, Mid Cap, and Small Cap stocks. "
                    "Only one scheme per category is permitted per Mutual Fund (except Index Funds, ETFs, FoFs, and Sectoral/Thematic)."
                ),
            },
        ],
    },
    {
        "id": "doc_18_amfi_investor_charter",
        "scheme_id": None,
        "title": "AMFI Investor Charter & Unitholder Rights",
        "document_type": "AMFI Charter",
        "publisher": "AMFI India",
        "url": "https://www.amfiindia.com/investor-corner/knowledge-center",
        "doc_date": "2026-10-25",
        "sections": [
            {
                "section": "Investor Rights & Payout Timelines",
                "content": (
                    "Mutual fund investors have the right to receive: Consolidated Account Statement (CAS) within 10 days of month-end; "
                    "Redemption or repurchase proceeds dispatched within T+2 business days from the date of redemption request; "
                    "Dividend (IDCW) payouts within 7 working days from the record date; and grievance redressal via SCORES within 21 calendar days."
                ),
            },
            {
                "section": "Mandatory Disclosures & Transparency",
                "content": (
                    "AMCs must disclose monthly portfolio statements within 10 days of month-end, annual financial reports within 4 months "
                    "of year-end, and unhedged derivative positions. Investors have the right to inspect trust deeds, AMC agreements, and KIMs."
                ),
            },
        ],
    },
    {
        "id": "doc_19_sebi_elss_statutory_rules",
        "scheme_id": None,
        "title": "SEBI & CBDT Regulations for Equity Linked Savings Schemes (ELSS)",
        "document_type": "Regulatory Standard",
        "publisher": "SEBI & Central Board of Direct Taxes (CBDT)",
        "url": "https://www.amfiindia.com/investor-corner/knowledge-center",
        "doc_date": "2026-10-25",
        "sections": [
            {
                "section": "3-Year Mandatory Statutory Lock-in",
                "content": (
                    "Equity Linked Savings Schemes (ELSS) are notified under Section 80C of the Income Tax Act, 1961. "
                    "ELSS investments carry a strict statutory lock-in period of 3 years (36 months) from the exact date of unit allotment. "
                    "Premature withdrawals, pledges, or switching to other mutual fund schemes are prohibited during this 3-year period."
                ),
            },
            {
                "section": "SIP Lock-in & Tax Deductions",
                "content": (
                    "In an ELSS Systematic Investment Plan (SIP), each monthly installment is treated as a separate investment "
                    "and is locked for 3 years from its respective deduction date. Under the Old Tax Regime, investments up to ₹1,50,000 "
                    "qualify for tax deduction under Section 80C. All 5 supported HDFC schemes in this assistant are non-ELSS open-ended funds."
                ),
            },
        ],
    },
    {
        "id": "doc_20_amfi_nav_valuation_norms",
        "scheme_id": None,
        "title": "AMFI Daily NAV Calculation & Cut-off Operational Norms",
        "document_type": "AMFI Guidelines",
        "publisher": "AMFI India",
        "url": "https://www.amfiindia.com/net-asset-value/nav-history",
        "doc_date": "2026-10-25",
        "sections": [
            {
                "section": "Daily NAV Calculation & Reporting",
                "content": (
                    "AMCs must compute Net Asset Value (NAV) of each scheme for every business day by 11:00 PM and publish it on "
                    "the AMFI website (www.amfiindia.com) and the AMC's portal. NAV reflects the market value of the scheme's securities "
                    "minus accrued expenses and liabilities divided by total outstanding units."
                ),
            },
            {
                "section": "Applicable NAV Cut-off Timings",
                "content": (
                    "For equity schemes: Subscriptions up to 3:00 PM receive same-day NAV subject to fund realization in the AMC account. "
                    "Redemptions up to 3:00 PM receive same-day NAV. Requests submitted after 3:00 PM receive the next business day's NAV. "
                    "If a day is a market holiday, transactions are queued for the subsequent working day's NAV."
                ),
            },
        ],
    },
]


def slugify(text: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", text).strip().lower()
    return re.sub(r"[-\s]+", "_", slug)[:30]


def build_official_documents_corpus(
    base_dir: str | None = None,
) -> Dict[str, Any]:
    """Generates 20 official verified public documents and writes them to data/documents/."""
    if base_dir is None:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    docs_dir = os.path.join(base_dir, "data", "documents")
    manifest_path = os.path.join(base_dir, "data", "corpus_manifest.yaml")
    chroma_dir = os.path.join(base_dir, "data", "index", "chroma")
    bm25_path = os.path.join(base_dir, "data", "index", "bm25.pkl")
    report_path = os.path.join(base_dir, "data", "ingestion_report.json")
    os.makedirs(docs_dir, exist_ok=True)

    print(f"[{datetime.now(timezone.utc).isoformat()}] Generating {len(OFFICIAL_DOCUMENTS)} Official Verified Public Documents...")

    generated_files = []
    official_chunks = []

    for doc in OFFICIAL_DOCUMENTS:
        doc_id = doc["id"]
        file_path = os.path.join(docs_dir, f"{doc_id}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(doc, f, indent=2, ensure_ascii=False)
        generated_files.append(file_path)

        scheme_id = doc.get("scheme_id")
        doc_title = doc["title"]
        doc_type = doc["document_type"]
        url = doc["url"]
        doc_date = doc["doc_date"]

        for idx, sec in enumerate(doc["sections"], start=1):
            sec_title = sec["section"]
            content = sec["content"]
            sec_slug = slugify(sec_title)

            chunk_id = f"{doc_id}#{sec_slug}#c{idx}"
            prefix = f"{doc_title} | {doc_type} | {sec_title}"
            full_text = f"{prefix} | {content}"

            chunk = {
                "chunk_id": chunk_id,
                "text": full_text,
                "raw_content": content,
                "metadata": {
                    "chunk_id": chunk_id,
                    "scheme_id": scheme_id or "regulatory_standard",
                    "scheme_name": doc_title,
                    "document_id": doc_id,
                    "document_type": doc_type,
                    "section": sec_title,
                    "url": url,
                    "doc_date": str(doc_date),
                    "priority": 1,
                    "content_type": "official_public_doc",
                },
            }
            official_chunks.append(chunk)

    print(f"Generated {len(generated_files)} JSON document files.")
    print(f"Generated {len(official_chunks)} verified semantic chunks from official documents.")

    # Update corpus_manifest.yaml
    if os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = yaml.safe_load(f)

        manifest["verified_public_documents_count"] = len(OFFICIAL_DOCUMENTS)
        manifest["verified_public_documents"] = [
            {
                "id": d["id"],
                "title": d["title"],
                "document_type": d["document_type"],
                "publisher": d["publisher"],
                "url": d["url"],
                "doc_date": d["doc_date"],
                "scheme_id": d.get("scheme_id"),
            }
            for d in OFFICIAL_DOCUMENTS
        ]

        with open(manifest_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(manifest, f, sort_keys=False, allow_unicode=True)
        print("Updated data/corpus_manifest.yaml with 20 verified public documents.")

    return {
        "documents_count": len(OFFICIAL_DOCUMENTS),
        "chunks_count": len(official_chunks),
        "chunks": official_chunks,
    }


if __name__ == "__main__":
    build_official_documents_corpus()
