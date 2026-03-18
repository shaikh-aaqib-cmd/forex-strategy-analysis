# ============================================================
# FOREX STRATEGY ANALYSIS — Step 1: Clean & Enrich Data
# Author: Shaikh Aaqib
# Description: Reads raw backtest CSV, cleans it, adds all
#              calculated columns needed for SQL and Power BI
# ============================================================

import pandas as pd
import os

# ── STEP 1: Load the raw data ────────────────────────────────
# Read the CSV file from the data folder
# encoding='utf-8-sig' handles the special character at the
# start of the file (called BOM) that Excel sometimes adds

df = pd.read_csv(r'C:\Users\aaqib\Documents\forex-project\data\eu_backtest.csv', encoding='utf-8-sig')

print("=== RAW DATA LOADED ===")
print(f"Total rows: {len(df)}")
print(f"Columns: {df.columns.tolist()}")
print("\nFirst 5 rows:")
print(df.head())
print("\nData types:")
print(df.dtypes)


# ── STEP 2: Clean column names ───────────────────────────────
# Remove spaces and special characters from column names
# so SQL and Power BI don't have trouble reading them

df.columns = df.columns.str.strip()           # remove spaces around names
df.columns = df.columns.str.replace('-', '_') # replace dash with underscore
df.columns = df.columns.str.replace('/', '_') # replace slash with underscore

print("\n=== CLEANED COLUMN NAMES ===")
print(df.columns.tolist())
# Now columns are: DATE, DAY, IFVG_ENTRY, IFVG_FORMED, MAX_RR, B_S, W_L


# ── STEP 3: Clean individual columns ─────────────────────────
# Remove any accidental spaces inside values

df['DAY']        = df['DAY'].str.strip()
df['IFVG_ENTRY'] = df['IFVG_ENTRY'].str.strip()
df['IFVG_FORMED']= df['IFVG_FORMED'].str.strip()
df['B_S']        = df['B_S'].str.strip()
df['W_L']        = df['W_L'].str.strip()

# Check for any unexpected values in W/L column
print("\n=== W/L VALUE CHECK ===")
print(df['W_L'].value_counts())
# Should only show: WIN, LOSS, BE


# ── STEP 4: Add MONTH column ─────────────────────────────────
# Your DATE column looks like "06-Jan", "15-Jul" etc.
# We extract the month name from the right side of the date

df['MONTH'] = df['DATE'].str.split('-').str[1]

# Define correct month order for sorting in Power BI
month_order = ['Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan']
df['MONTH_NUM'] = df['MONTH'].map({
    'Jul': 1, 'Aug': 2, 'Sep': 3, 'Oct': 4,
    'Nov': 5, 'Dec': 6, 'Jan': 7
})

print("\n=== MONTH CHECK ===")
print(df['MONTH'].value_counts())


# ── STEP 5: Add TRADE_NO column ──────────────────────────────
# Sequential trade number from 1 to 221
# Useful for the equity curve chart in Power BI

df['TRADE_NO'] = range(1, len(df) + 1)

print("\n=== TRADE NUMBER CHECK ===")
print(f"First trade: {df['TRADE_NO'].iloc[0]}")
print(f"Last trade:  {df['TRADE_NO'].iloc[-1]}")


# ── STEP 6: Add PNL_PCT column ───────────────────────────────
# Risk per trade = 0.25% of account
# Reward (TP) = 5 x 0.25% = 1.25%
# WIN  = +1.25%
# LOSS = -0.25%
# BE   = 0.00% (SL moved to breakeven, came back)

RISK   = 0.25   # percent
REWARD = 1.25   # percent (5 x risk)

df['PNL_PCT'] = df['W_L'].map({
    'WIN' : REWARD,
    'LOSS': -RISK,
    'BE'  : 0.0
})

print("\n=== PNL_PCT CHECK ===")
print(df['PNL_PCT'].value_counts())
# Should show: -0.25, 0.0, 1.25


# ── STEP 7: Add RUNNING_BALANCE column ───────────────────────
# Starting account = $10,000
# Each trade, the balance grows or shrinks by PNL_PCT%
# This is COMPOUND growth — each trade is % of current balance

STARTING_BALANCE = 10000
balance = STARTING_BALANCE
running_balance = []

for pnl in df['PNL_PCT']:
    balance = balance * (1 + pnl / 100)
    running_balance.append(round(balance, 2))

df['RUNNING_BALANCE'] = running_balance

print("\n=== RUNNING BALANCE CHECK ===")
print(f"Start balance : ${STARTING_BALANCE:,.2f}")
print(f"Final balance : ${df['RUNNING_BALANCE'].iloc[-1]:,.2f}")
print(f"Total return  : ${df['RUNNING_BALANCE'].iloc[-1] - STARTING_BALANCE:+,.2f}")


# ── STEP 8: Add CUMULATIVE_RETURN column ─────────────────────
# Percentage growth from starting balance at each trade
# Formula: ((current balance / starting balance) - 1) x 100

df['CUMULATIVE_RETURN_PCT'] = round(
    (df['RUNNING_BALANCE'] / STARTING_BALANCE - 1) * 100, 2
)

print("\n=== CUMULATIVE RETURN CHECK ===")
print(f"Final cumulative return: {df['CUMULATIVE_RETURN_PCT'].iloc[-1]}%")


# ── STEP 9: Add SESSION_MATCH column ─────────────────────────
# TRUE  = entry session is the same as where IFVG was formed
# FALSE = entry session is different from where IFVG was formed
# Example: IFVG formed in LN, entry taken in NY = FALSE (mismatch)

df['SESSION_MATCH'] = df['IFVG_ENTRY'] == df['IFVG_FORMED']

print("\n=== SESSION MATCH CHECK ===")
print(df['SESSION_MATCH'].value_counts())
# True = 145 trades (matched), False = 76 trades (mismatched)


# ── STEP 10: Add WIN_LOSS_NUM column ─────────────────────────
# Numeric version of W/L for calculations in Power BI
# WIN=1, LOSS=0, BE=0 (for win rate calculations)

df['WIN_NUM'] = (df['W_L'] == 'WIN').astype(int)


# ── STEP 11: Final check — see all new columns ───────────────
print("\n=== FINAL ENRICHED DATA ===")
print(f"Total columns: {len(df.columns)}")
print(f"Column names:  {df.columns.tolist()}")
print("\nSample of enriched data (first 5 rows):")
print(df[['TRADE_NO','DATE','DAY','MONTH','W_L',
          'PNL_PCT','RUNNING_BALANCE','CUMULATIVE_RETURN_PCT',
          'SESSION_MATCH']].head())

print("\nSummary statistics:")
print(f"  Total trades      : {len(df)}")
print(f"  Wins              : {len(df[df['W_L']=='WIN'])} ({len(df[df['W_L']=='WIN'])/len(df)*100:.1f}%)")
print(f"  Losses            : {len(df[df['W_L']=='LOSS'])} ({len(df[df['W_L']=='LOSS'])/len(df)*100:.1f}%)")
print(f"  Breakevens        : {len(df[df['W_L']=='BE'])} ({len(df[df['W_L']=='BE'])/len(df)*100:.1f}%)")
print(f"  Starting balance  : ${STARTING_BALANCE:,.2f}")
print(f"  Final balance     : ${df['RUNNING_BALANCE'].iloc[-1]:,.2f}")
print(f"  Total return      : {df['CUMULATIVE_RETURN_PCT'].iloc[-1]}%")


# ── STEP 12: Add TRADE_QUALITY column ────────────────────────
# Tag each trade as BEST or WORST based on day + session

best_sessions = {
    'MON': ['LN', 'POST NY'],
    'TUE': ['PRE LN', 'LN'],
    'WED': ['LN', 'NY'],
    'THU': ['LN', 'PRE NY'],
    'FRI': ['NY', 'POST NY']
}

df['TRADE_QUALITY'] = df.apply(
    lambda row: 'BEST' if row['IFVG_ENTRY'] in best_sessions.get(row['DAY'], []) else 'WORST',
    axis=1
)

print("\n=== TRADE QUALITY CHECK ===")
print(df['TRADE_QUALITY'].value_counts())
# Should show: BEST = 118, WORST = 103


# ── STEP 13: Add RISK and REWARD columns ─────────────────────
# BEST trades → 0.50% risk, 2.50% reward
# WORST trades → 0.25% risk, 1.25% reward (original)

df['RISK_PCT']   = df['TRADE_QUALITY'].map({'BEST': 0.50, 'WORST': 0.25})
df['REWARD_PCT'] = df['TRADE_QUALITY'].map({'BEST': 2.50, 'WORST': 1.25})

print("\n=== RISK/REWARD CHECK ===")
print(df.groupby('TRADE_QUALITY')[['RISK_PCT','REWARD_PCT']].first())


# ── STEP 14: Add OPTIMISED_BALANCE column ────────────────────
# This simulates what happens when you:
# - Only take BEST session trades
# - Risk 0.50% on each trade
# - Skip all WORST session trades entirely

balance = 10000
optimised_balance = []
optimised_return  = []

for _, row in df.iterrows():
    if row['TRADE_QUALITY'] == 'BEST':
        # Only calculate for BEST trades
        if row['W_L'] == 'WIN':
            balance *= (1 + row['REWARD_PCT'] / 100)
        elif row['W_L'] == 'LOSS':
            balance *= (1 - row['RISK_PCT'] / 100)
        # BE = no change to balance
    # WORST trades are skipped — balance stays the same

    optimised_balance.append(round(balance, 2))
    optimised_return.append(round((balance / 10000 - 1) * 100, 2))

df['OPTIMISED_BALANCE']    = optimised_balance
df['OPTIMISED_RETURN_PCT'] = optimised_return

print("\n=== OPTIMISED BALANCE CHECK ===")
print(f"Starting balance    : $10,000.00")
print(f"Final balance       : ${df['OPTIMISED_BALANCE'].iloc[-1]:,.2f}")
print(f"Total return        : {df['OPTIMISED_RETURN_PCT'].iloc[-1]}%")

# Quick check — best trades only
best_only = df[df['TRADE_QUALITY'] == 'BEST']
wins   = len(best_only[best_only['W_L'] == 'WIN'])
losses = len(best_only[best_only['W_L'] == 'LOSS'])
be     = len(best_only[best_only['W_L'] == 'BE'])
print(f"\nBEST trades breakdown:")
print(f"  Total  : {len(best_only)}")
print(f"  Wins   : {wins} ({wins/len(best_only)*100:.1f}%)")
print(f"  Losses : {losses}")
print(f"  BE     : {be}")

# ── STEP 15: Export enriched CSV ─────────────────────────────
# Save the enriched file to the output folder
# This file will be used by SQL and Power BI

output_path = r'C:\Users\aaqib\Documents\forex-project\output\eu_enriched.csv'
df.to_csv(output_path, index=False)

print(f"\n=== FILE SAVED ===")
print(f"Enriched CSV saved to: {output_path}")
print("You are ready for Step 2 — SQL!")