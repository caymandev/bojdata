#!/usr/bin/env python3
"""
Simple example: Fetch BOJ data for a specific time period
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bojdata
import pandas as pd
from datetime import datetime


# Example 1: Fetch last 5 years of monetary base data
print("Example 1: Fetch specific time period")
print("-" * 40)

df = bojdata.read_boj(
    series="BS01'MABJMTA",
    start_date="2020-01-01",
    end_date="2024-12-31"
)

print(f"✓ Fetched {len(df)} months of data")
print(f"✓ Period: {df.index[0].strftime('%Y-%m')} to {df.index[-1].strftime('%Y-%m')}")
print(f"✓ Latest value: ¥{df.iloc[0, 0]:,.0f} million")

# Save to CSV
df.to_csv("monetary_base_2020_2024.csv")
print("✓ Saved to: monetary_base_2020_2024.csv")


# Example 2: Fetch year-to-date data
print("\n\nExample 2: Fetch year-to-date data")
print("-" * 40)

current_year = datetime.now().year
ytd_df = bojdata.read_boj(
    series="BS01'MABJMTA",
    start_date=f"{current_year}-01-01",
    end_date=datetime.now().strftime("%Y-%m-%d")
)

print(f"✓ Fetched {len(ytd_df)} months of {current_year} data")
print("\nMonthly values:")
for date, value in ytd_df.iterrows():
    print(f"  {date.strftime('%Y-%m')}: ¥{value.iloc[0]:,.0f} million")


# Example 3: Fetch and analyze recent trends
print("\n\nExample 3: Analyze recent trends")
print("-" * 40)

# Get last 12 months
recent_df = bojdata.read_boj(
    series="BS01'MABJMTA",
    start_date="2024-01-01",
    end_date="2024-12-31"
)

# Calculate statistics
mean_2024 = recent_df.mean().iloc[0]
std_2024 = recent_df.std().iloc[0]
growth_2024 = ((recent_df.iloc[0, 0] - recent_df.iloc[-1, 0]) / recent_df.iloc[-1, 0]) * 100

print(f"2024 Statistics:")
print(f"  Average: ¥{mean_2024:,.0f} million")
print(f"  Std Dev: ¥{std_2024:,.0f} million")
print(f"  Year growth: {growth_2024:.2f}%")

# Calculate month-over-month changes
recent_df['MoM_Change_%'] = recent_df.pct_change() * 100
print("\nMonth-over-month changes:")
for date, row in recent_df.iterrows():
    if pd.notna(row['MoM_Change_%']):
        print(f"  {date.strftime('%Y-%m')}: {row['MoM_Change_%']:.2f}%")


print("\n✅ All examples completed successfully!")
print("\nThe bojdata package makes it easy to:")
print("  • Fetch BOJ data for any time period")
print("  • Work with standard pandas DataFrames")
print("  • Export to any format (CSV, Excel, etc.)")
print("  • Integrate with your analysis workflow")