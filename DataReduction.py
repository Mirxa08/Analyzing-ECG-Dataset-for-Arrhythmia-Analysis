import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt

# Load ECG data from the CSV file
filename = 'JS00101'
data = pd.read_csv('CSV/' + filename + '.csv')

# Extract ECG signal data (excluding the 'time' column)
X = data.iloc[:, 1:].values

# Store original column names for labeling
original_column_names = data.columns[1:]

# Apply PCA
n_components = 6
pca = PCA(n_components=n_components)  # Reduce to specified number of principal components
X_pca = pca.fit_transform(X)

# Get the indices of the principal components with the highest variance
component_indices = np.argsort(pca.explained_variance_ratio_)[::-1][:n_components]

# Get the principal axes in feature space
principal_axes = pca.components_

# Keep track of selected leads
selected_leads = set()

# Create a new DataFrame with the principal components and time
df_pca = pd.DataFrame({'time': data['time']})
for i, idx in enumerate(component_indices):
    # Find the original attribute name corresponding to the principal component
    original_attr_index = np.argmax(np.abs(principal_axes[idx]))
    original_attr_name = original_column_names[original_attr_index]

    # Check if the lead is already selected
    while original_attr_name in selected_leads:
        # If lead is repeated, choose the next best one
        principal_axes[idx, original_attr_index] = 0  # Exclude this lead from consideration
        original_attr_index = np.argmax(np.abs(principal_axes[idx]))
        original_attr_name = original_column_names[original_attr_index]

    # Add the selected lead to the set
    selected_leads.add(original_attr_name)

    df_pca[f'{original_attr_name}'] = X_pca[:, idx]

# Save the DataFrame to a new CSV file
output_file_name = 'Reduced/' + filename + '_reduced.csv'
df_pca.to_csv(output_file_name, index=False)

# Plot the principal components against time
plt.figure(figsize=(12, 6))
for col in df_pca.columns[1:]:
    plt.plot(df_pca['time'], df_pca[col], label=col)
plt.xlabel('Time')
plt.ylabel('Amplitude')
plt.title('ECG Signals Projected onto the First Four Principal Components')
plt.legend()
plt.show()