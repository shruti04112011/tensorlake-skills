import pandas as pd
import matplotlib.pyplot as plt

# Load data
df = pd.read_csv("data.csv")

print("Dataset:\n", df)

# Total revenue
total_revenue = df["Amount"].sum()
print("\nTotal Revenue:", total_revenue)

# Revenue by category
category_sales = df.groupby("Category")["Amount"].sum()
print("\nSales by Category:\n", category_sales)

# Top products
top_products = df.groupby("Product")["Amount"].sum().sort_values(ascending=False)
print("\nTop Products:\n", top_products)

# Plot category sales
category_sales.plot(kind='bar')
plt.title("Sales by Category")
plt.xlabel("Category")
plt.ylabel("Revenue")
plt.show()