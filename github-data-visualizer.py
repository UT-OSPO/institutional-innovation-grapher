import matplotlib.pyplot as plt
import csv
import json
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

    # Optionally, pick the most recent file if there are multiple matches
    matching_files.sort(reverse=True)
    latest_file = matching_files[0]
    file_path = os.path.join(most_recent_path, latest_file)
    df = pd.read_csv(file_path, encoding="latin1")
    print(f"Loaded '{latest_file}' that was exported on '{most_recent_folder}'.")
    return df, most_recent_path

if test:
    outputs_dir = "test/outputs"
else:
    outputs_dir = "outputs"
repo_pattern = "github-repo-list-"
account_pattern = "github-account-list-"
repodata, data_dir = loadmostrecentfile(outputs_dir, repo_pattern)
accountdata, data_dir = loadmostrecentfile(outputs_dir, account_pattern)

# languagedata = []
# licensedata = []
# starcountdata = []
# watchercountdata = []
# forkcountdata = []
# createdatdata = []
# updatedatdata = []

languagedata = repodata["language"]
licensedata = repodata["license"]
starcountdata = repodata["stargazers_count"]
watchercountdata = repodata["watchers_count"]
forkcountdata = repodata["forks_count"]
createdatdata = repodata["created_at"]
updatedatdata = repodata["updated_at"]


# with open(config["githubrepodatacsvpathforvisualization"], "r") as repodatacsv:
#     repodata = csv.reader(repodatacsv)

#     for row in repodata:
#         primarylanguage = row[10]
#         license = row[15]
#         starcount = row[8]
#         watchercount = row[9]
#         forkcount = row[11]
#         datecreated = row[5]
#         dateupdated = row[6]

#         yearssincecreated = ""
#         yearssinceupdated = ""

#         languagedata.append(primarylanguage)
#         licensedata.append(license)
#         starcountdata.append(starcount)
#         watchercountdata.append(watchercount)
#         forkcountdata.append(forkcount)
#         createdatdata.append(datecreated)
#         updatedatdata.append(dateupdated)


# def createpiechart(dataset, otherthreshold, title):

#     datalabels = []
#     datacounts = []

#     dataothercount = 0

#     for datapoint in set(dataset):

#         if dataset.count(datapoint) < otherthreshold:
#             dataothercount += dataset.count(datapoint)

#         else:
#             if datapoint == "":
#                 datalabels.append("None")
#             else:
#                 datalabels.append(datapoint.strip())
#             datacounts.append(dataset.count(datapoint))


#     fig, ax = plt.subplots()

#     ax.set_title = title
#     plt.suptitle(title)
#     notex, notey = .01, .01
#     fig.text(notex, notey,'* values with counts under ' + str(otherthreshold) + ' merged into \'other\' category', transform=fig.transFigure)
#     ax.pie(datacounts, labels=datalabels)

#     plt.show()

def createsavepiechart(dataset, otherthreshold, title, plots_dir, plot_filename, plotFormat="png", show_plot=False):
    # Ensure dataset is a pandas Series
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

    # Ensure plots_dir exists
    os.makedirs(plots_dir, exist_ok=True)
    plot_path = os.path.join(plots_dir, plot_filename)
    plt.savefig(plot_path, format=plotFormat)
    print(f"{plot_filename} has been saved successfully at {plot_path}.\n")
    
    if show_plot:
        plt.show()
    plt.close(fig)

# createsavepiechart(licensedata, 5,"Licenses Assigned to Affiliated GitHub Repositories")
# createsavepiechart(languagedata, 20, "Primary Language Used in Affiliated GitHub Repositories")

plot_filename = f"repo-license-count-{todayDate}.{plotformat}"
createsavepiechart(licensedata, 5,"Licenses Assigned to Affiliated GitHub Repositories", data_dir, plot_filename, plotformat, True)
plot_filename = f"repo-language-count-{todayDate}.{plotformat}"
createsavepiechart(languagedata, 20, "Primary Language Used in Affiliated GitHub Repositories", data_dir, plot_filename, plotformat, True)