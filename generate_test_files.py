"""
Generates sample CSV and Excel files for drag-and-drop file upload testing.
"""

import os
import pandas as pd
from datetime import date, timedelta

today = date.today()

sample_rows = [
    {
        "Batch ID": "IMPORT-001",
        "Machine ID": "M01",
        "Fabric Type": "Cotton",
        "Operator": "John Doe",
        "Shift": "Morning",
        "Total Production Quantity": 1500,
        "Production Speed": 850,
        "Waste Quantity": 52.5,
        "Machine Age": 8.5,
        "Last Maintenance Date": (today - timedelta(days=18)).strftime("%Y-%m-%d"),
        "Humidity": 56.0,
        "Temperature": 24.5
    },
    {
        "Batch ID": "IMPORT-002-HIGHPROD-LOWPCT",
        "Machine ID": "M08",
        "Fabric Type": "Denim",
        "Operator": "David Kim",
        "Shift": "Morning",
        "Total Production Quantity": 5000,
        "Production Speed": 780,
        "Waste Quantity": 100.0,  # 2.0% -> NORMAL
        "Machine Age": 1.5,
        "Last Maintenance Date": (today - timedelta(days=10)).strftime("%Y-%m-%d"),
        "Humidity": 58.0,
        "Temperature": 25.0
    },
    {
        "Batch ID": "IMPORT-003-LOWPROD-HIGHPCT",
        "Machine ID": "M02",
        "Fabric Type": "Silk",
        "Operator": "Priya Sharma",
        "Shift": "Night",
        "Total Production Quantity": 100,
        "Production Speed": 660,
        "Waste Quantity": 30.0,  # 30.0% -> HIGH RISK
        "Machine Age": 6.2,
        "Last Maintenance Date": (today - timedelta(days=88)).strftime("%Y-%m-%d"),
        "Humidity": 38.0,
        "Temperature": 29.0
    },
    {
        "Batch ID": "IMPORT-004-MISSING-HUMIDITY",
        "Machine ID": "M04",
        "Fabric Type": "Polyester",
        "Operator": "Carlos Rossi",
        "Shift": "Afternoon",
        "Total Production Quantity": 1800,
        "Production Speed": 920,
        "Waste Quantity": 54.0,  # 3.0%
        "Machine Age": 3.5,
        "Last Maintenance Date": (today - timedelta(days=20)).strftime("%Y-%m-%d"),
        "Humidity": None,  # Missing!
        "Temperature": 26.0
    },
    {
        "Batch ID": "IMPORT-005-OVERDUE-MAINT",
        "Machine ID": "M05",
        "Fabric Type": "Wool",
        "Operator": "Elena Rostova",
        "Shift": "Night",
        "Total Production Quantity": 900,
        "Production Speed": 710,
        "Waste Quantity": 85.0,  # 9.44%
        "Machine Age": 4.1,
        "Last Maintenance Date": (today - timedelta(days=92)).strftime("%Y-%m-%d"),
        "Humidity": 52.0,
        "Temperature": 27.0
    },
    {
        "Batch ID": "IMPORT-006-ZERO-PROD",
        "Machine ID": "M06",
        "Fabric Type": "Cotton",
        "Operator": "John Doe",
        "Shift": "Morning",
        "Total Production Quantity": 0,  # Zero production invalid guard
        "Production Speed": 0,
        "Waste Quantity": 10.0,
        "Machine Age": 2.8,
        "Last Maintenance Date": (today - timedelta(days=15)).strftime("%Y-%m-%d"),
        "Humidity": 55.0,
        "Temperature": 25.0
    }
]

df = pd.DataFrame(sample_rows)
csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_test_batches.csv")
xlsx_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_test_batches.xlsx")

df.to_csv(csv_path, index=False)
df.to_excel(xlsx_path, index=False)
print(f"Generated {csv_path} and {xlsx_path}")
