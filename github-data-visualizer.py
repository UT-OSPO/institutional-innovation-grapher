import json
import matplotlib.pyplot as plt
import os
import pandas as pd
import re
from datetime import datetime

with open(".env") as envfile:
    config = json.loads(envfile.read())

test = config["test"]
todayDate = datetime.now().strftime("%Y-%m-%d") 
plotformat = config["plotformat"]

def loadmostrecentfile(outputs_dir, pattern):
    # regex for YYYY-MM-DD
    date_folder_regex = r"^\d{4}-\d{2}-\d{2}$"
    subfolders = [
        f for f in os.listdir(outputs_dir)
        if os.path.isdir(os.path.join(outputs_dir, f)) and re.match(date_folder_regex, f)
    ]
    if not subfolders:
        print(f"No date-based subfolders found in '{outputs_dir}'.")
        return None, None

    # sort subfolders by date (descending)
    subfolders.sort(key=lambda date: datetime.strptime(date, "%Y-%m-%d"), reverse=True)
    most_recent_folder = subfolders[0]
    most_recent_path = os.path.join(outputs_dir, most_recent_folder)

    # look for the file matching the specified pattern
    files = os.listdir(most_recent_path)
    matching_files = [f for f in files if pattern in f]
    if not matching_files:
        print(f"No file with pattern '{pattern}' found in '{most_recent_path}'.")
        return None, most_recent_path

    if matching_files:
        # Get full file paths
        full_paths = [os.path.join(most_recent_path, f) for f in matching_files]
        # Sort by modification time, newest first
        full_paths.sort(key=os.path.getmtime, reverse=True)
        # Pick the most recently modified file
        latest_file_path = full_paths[0]
        latest_file = os.path.basename(latest_file_path)
        df = pd.read_csv(latest_file_path, encoding="latin1")
        print(f"Loaded '{latest_file}' (most recently modified) from '{most_recent_folder}'.")
        return df, most_recent_path

if test:
    outputs_dir = "test/outputs"
else:
    outputs_dir = "outputs"
repo_pattern = "github-repo-list-"
account_pattern = "github-account-list"
repodata, data_dir = loadmostrecentfile(outputs_dir, repo_pattern)
accountdata, data_dir = loadmostrecentfile(outputs_dir, account_pattern)

languagedata = repodata["language"]
licensedata = repodata["license"]
starcountdata = repodata["stargazers_count"]
watchercountdata = repodata["watchers_count"]
forkcountdata = repodata["forks_count"]
createdatdata = repodata["created_at"]
updatedatdata = repodata["updated_at"]

def createsavepiechart(dataset, otherthreshold, title, plots_dir, plot_filename, plotFormat="png", show_plot=False):
    if not isinstance(dataset, pd.Series):
        dataset = pd.Series(dataset)
    
    counts = dataset.value_counts(dropna=False)
    datalabels = []
    datacounts = []
    dataothercount = 0

    for label, count in counts.items():
        if count < otherthreshold:
            dataothercount += count
        else:
            if pd.isna(label) or label == "":
                datalabels.append("None")
            else:
                datalabels.append(str(label).strip())
            datacounts.append(count)
    if dataothercount > 0:
        datalabels.append("Other")
        datacounts.append(dataothercount)
    
    fig, ax = plt.subplots()
    plt.suptitle(title)
    notex, notey =.01,.01
    fig.text(
        notex, notey, 
        f"* values with counts under {otherthreshold} merged into 'other' category", 
        transform=fig.transFigure
    )
    ax.pie(datacounts, labels=datalabels, autopct='%1.1f%%')
    plt.tight_layout()

    # ensure plots_dir exists
    os.makedirs(plots_dir, exist_ok=True)
    plot_path = os.path.join(plots_dir, plot_filename)
    plt.savefig(plot_path, format=plotFormat)
    print(f"{plot_filename} has been saved successfully at {plot_path}.\n")
    
    if show_plot:
        plt.show()
    plt.close(fig)

plot_filename = f"repo-license-count-{todayDate}.{plotformat}"
createsavepiechart(licensedata, 5,"Licenses Assigned to Affiliated GitHub Repositories", data_dir, plot_filename, plotformat, True)
plot_filename = f"repo-language-count-{todayDate}.{plotformat}"
createsavepiechart(languagedata, 20, "Primary Language Used in Affiliated GitHub Repositories", data_dir, plot_filename, plotformat, True)