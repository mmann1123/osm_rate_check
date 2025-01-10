# %%
import duckdb

# Start a DuckDB session
conn = duckdb.connect()

# Query with S3 access
query = """
select * from  read_parquet('s3://youthmappers-usw2/activity/daily_rollup.parquet') where chapter like '%GWU%';
"""
query = """
INSTALL h3 FROM community;
LOAD h3;
COPY(
  SELECT 
  	h3_cell_to_parent(h3,4) AS h3, 
  	CAST(epoch(date_trunc('month', created_at)) as int) as date,
  	gender,
  	sum(features.new+features.edited) as all_edits 
  FROM read_parquet('s3://youthmappers-usw2/activity/daily_rollup.parquet') 
  GROUP BY 1,2,3
) TO 'edits_by_gender.csv';
"""

query = """
INSTALL h3 FROM community;
LOAD h3;
COPY(
  SELECT 
  	h3_cell_to_parent(h3,4) AS h3, 
  	sum(features.new+features.edited) as all_edits 
  FROM read_parquet('s3://youthmappers-usw2/activity/daily_rollup.parquet') 
  WHERE chapter LIKE '%GWU%'
    AND created_at >= '2024-08-01'
  GROUP BY 1 
) TO 'edits_by_gw.csv';
"""

# edits by week
query = """
INSTALL h3 FROM community;
LOAD h3;
COPY(
  SELECT 
    DATE_TRUNC('week', created_at) AS week_start,
    SUM(features.new + features.edited) AS all_edits
  FROM read_parquet('s3://youthmappers-usw2/activity/daily_rollup.parquet')
  WHERE chapter LIKE '%GWU%'
    AND created_at >= '2024-08-01'
  GROUP BY 1
) TO 'edits_by_gw.csv';
"""
# Execute the query
result = conn.execute(query).fetchall()

# Optionally, display or use the result
print(result)

# Close the connection
conn.close()

# %%
# create a fancy looking plot from edits_by_gw.csv
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns

df = pd.read_csv("edits_by_gw.csv")
df["cumulative_edits"] = df["all_edits"].cumsum()

# ...existing code...
plt.figure(figsize=(10, 6))
plt.plot(
    df["week_start"], df["cumulative_edits"], marker="o", color="orangered", linewidth=2
)
plt.grid(True, which="major", linestyle="--", alpha=0.7)
plt.xlabel("Week Start", fontsize=12)
plt.ylabel("Cumulative Edits", fontsize=12)
plt.title("Cumulative Edits Over Time", fontsize=16, fontweight="bold")
plt.xticks(rotation=45, fontsize=10)
plt.yticks(fontsize=10)
plt.tight_layout()
plt.show()
# ...existing code...

# %%
