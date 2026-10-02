import pandas as pd

# Load the original dataset
original_df = pd.read_csv("dataset.csv")

# Create a copy
df = original_df.copy()

# Categories to convert
dark_categories = [
    "Urgency",
    "Scarcity",
    "Social Proof",
    "Misdirection",
    "Sneaking",
    "Obstruction",
    "Forced Action"
]

# Convert Pattern Category
df["Pattern Category"] = df["Pattern Category"].replace(
    dark_categories,
    "Dark Pattern"
)

# Update labels
df["label"] = df["Pattern Category"].apply(
    lambda x: 0 if x == "Not Dark Pattern" else 1
)

# Save as a NEW file
df.to_csv("dark_patterns_binary.csv", index=False)

print("Original dataset shape:", original_df.shape)
print("New dataset shape:", df.shape)

print("\nCategory Counts:")
print(df["Pattern Category"].value_counts())

print("\nLabel Counts:")
print(df["label"].value_counts())