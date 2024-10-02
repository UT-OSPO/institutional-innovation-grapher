import matplotlib.pyplot as plt
import csv
import json




with open(".env") as envfile:
    config = json.loads(envfile.read())


languagedata = []
licensedata = []
starcountdata = []
watchercountdata = []
forkcountdata = []
createdatdata = []
updatedatdata = []


with open(config["githubrepodatacsvpathforvisualization"], "r") as repodatacsv:
    repodata = csv.reader(repodatacsv)

    for row in repodata:
        primarylanguage = row[10]
        license = row[15]
        starcount = row[8]
        watchercount = row[9]
        forkcount = row[11]
        datecreated = row[5]
        dateupdated = row[6]

        yearssincecreated = ""
        yearssinceupdated = ""

        languagedata.append(primarylanguage)
        licensedata.append(license)
        starcountdata.append(starcount)
        watchercountdata.append(watchercount)
        forkcountdata.append(forkcount)
        createdatdata.append(datecreated)
        updatedatdata.append(dateupdated)


def createpiechart(dataset, otherthreshold, title):

    datalabels = []
    datacounts = []

    dataothercount = 0

    for datapoint in set(dataset):

        if dataset.count(datapoint) < otherthreshold:
            dataothercount += dataset.count(datapoint)

        else:
            if datapoint == "":
                datalabels.append("None")
            else:
                datalabels.append(datapoint.strip())
            datacounts.append(dataset.count(datapoint))


    fig, ax = plt.subplots()

    ax.set_title = title
    plt.suptitle(title)
    notex, notey = .01, .01
    fig.text(notex, notey,'* values with counts under ' + str(otherthreshold) + ' merged into \'other\' category', transform=fig.transFigure)
    ax.pie(datacounts, labels=datalabels)

    plt.show()

createpiechart(licensedata, 5,"Licenses Assigned to Affiliated GitHub Repositories")
createpiechart(languagedata, 20, "Primary Language Used in Affiliated GitHub Repositories")
