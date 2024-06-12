import os
import csv
import pandas as pd
import requests
import json
from dotenv import dotenv_values
from datetime import datetime


config = dotenv_values(".env")

institutionname = "ut-austin"
outputcsvpath = "outputs/simple-github-account-url-list-" + datetime.now().strftime("%Y-%m-%d") + "-" + institutionname + ".csv"
outputcsvcolumns = ["html_url", "name", "company", "email", "bio","public_repos", "followers", "created_at", "updated_at", "predicted general UT Austin connection/role", "additional predicted info", "query"]
pagelimit = 2
resultsperpage = 50
minimumfollowers = 1
minimumrepos = 1


usercharacteristicstoprocess = ['login','id','avatar_url','url','html_url','name','company','blog','location','email','bio','public_repos','public_gists','followers','following','created_at','updated_at','organizations_url','type']
querylist = []
querylist.append("ut+austin+followers:>=" + str(minimumfollowers) + "+repos:>=" + str(minimumrepos))
# querylist.append("university+of+texas+at+austin+followers:>=" + str(minimumfollowers) + "+repos:>=" + str(minimumrepos))
# querylist.append("location:%22university+of+texas+at+austin%22&followers:>=" + str(minimumfollowers) + "&repos:>=" + str(minimumrepos))
# querylist.append("location:\"ut+austin\"&followers:>=" + str(minimumfollowers) + "&repos:>=" + str(minimumrepos))
# querylist.append("location%3AAustin+followers%3A%3E%3D40+repos%3A%3E%3D1&type=Users&ref=advsearch&l=&l=&s=followers&o=desc")



overlappingusersacrossqueries = []
uniquerusersfound = []
apiendpoint = "users"


try:
    os.mkdir("inputs")
except:
    print("inputs directory already exists")
try:
    os.mkdir("outputs")
except:
    print("outputs directory already exists")

#ADD ROLES FOR UT BOOTCAMP STUDENT, PHD STUDENT, ALUMNI, TURING SCHOLAR, ORGANIZATION (AS OPPOSED TO INDIVIDUAL),
#FINAL ROLES: current student, current doctoral student,
def predictrole(parseddesc, fulldesc):
    prediction = ""
    additionalinfo = ""
    descriptions = [fulldesc.lower(), parseddesc.lower()]

    for desc in descriptions:

        if "prof" in desc or "faculty" in desc:
            prediction = "Faculty"

        if "post" in desc and "doc" in desc:
            prediction = "Postdoc"

        if "student" in desc or "freshman" in desc or "sophmore" in desc or "junior" in desc or "senior" in desc or "major" in desc or "research assistant" in desc or "candidate" in desc or "studying" in desc:
            prediction = "Student"

            if "freshman" in desc or "sophmore" in desc or "junior" in desc or "senior" in desc or "undergrad" in desc:
                additionalinfo = "Undergraduate student"

            if "graduate student" in desc or " grad student" in desc or "masters" in desc:
                additionalinfo = "Graduate student"

            if "doctoral student" in desc or "phd student" in desc or "candidate" in desc or "ph.d. student" in desc:
                additionalinfo = "Doctoral student"

        if "alumn" in desc or "graduate of" in desc or "previously" in desc or "'2" in desc or "'1" in desc or "'0" in desc or "completed" in desc:
            prediction = "Alum"


    predictionlist = [prediction,additionalinfo]

    print("returning the following predictionlist: " + str(predictionlist))
    return predictionlist


csvoutputrows = []
csvrowdictionarylist = []

githubaccountschecked = 0

for query in querylist:

    try:
        queryurl = "https://api.github.com/search/"+ apiendpoint +"?q="+ query +"&per_page=" + str(resultsperpage)

        print(queryurl)
        data = requests.get(queryurl, headers={"X-GitHub-Api-Version": "2022-11-28", "Authorization": "Bearer " + config['githubtoken'], "Accept": "application/vnd.github+json" })

        response = json.loads(data.content)
        try:
            responselinkheaders = data.headers["Link"]
            pageinfo = responselinkheaders.split(",")

            nexturl = pageinfo[0].replace("<","").split(">; ")[0].strip()
            lasturl = pageinfo[1].replace("<","").split(">; ")[0].strip()
            lastpagenum = lasturl.split("=")[-1]

            print("total count for query '"+query+"' = " + str(response['total_count']))
            print("next page = " + nexturl)
            print("lastpage = " + lasturl)
            print()
        except:
            print("less than one page of results returned")

        pagecount = 0

        while pagecount < pagelimit:

            try:
                pagecount += 1

                queryurl = "https://api.github.com/search/"+ apiendpoint +"?q="+ query +"&per_page=" + str(resultsperpage) + "&page=" + str(pagecount)

                print("queryurl = " + queryurl)

                data = requests.get(queryurl, headers={"X-GitHub-Api-Version": "2022-11-28", "Authorization": "Bearer " + config['githubtoken'], "Accept": "application/vnd.github+json" })

                response = json.loads(data.content)


                # FOR USER IN LIST OF RETRIEVED USERS
                for u in response['items']:

                    githubaccountschecked += 1


                    print("\nchecking github account... #" + str(githubaccountschecked))

                    utaffiliated = False

                    if 'location%3AAustin+' in queryurl:

                        for k, v in u.items():
                            if k == "url":
                                accountdetailsurl = v
                                accountdetailsdata = requests.get(accountdetailsurl, headers={"X-GitHub-Api-Version": "2022-11-28", "Authorization": "Bearer " + config['githubtoken']})
                                accountdetailsdatalist = accountdetailsdata.content.decode("latin-1")
                                accountdetailsdatalist = json.loads(accountdetailsdatalist)

                                for k2, v2 in accountdetailsdatalist.items():
                                    try:
                                        if k2 == "email":
                                            print("   email: " + str(v2))
                                            if "utexas.edu" in v2:
                                                utaffiliated = True

                                        if k2 == "company":
                                            print("   company: " + str(v2))
                                            if "ut austin" in v2.lower() or "university of texas at austin" in v2.lower() or "UT" in v2:
                                                utaffiliated = True

                                    except Exception as e:
                                        pass



                    if utaffiliated or 'location%3AAustin+' not in queryurl:

                        useralreadyfound = False

                        csvrow = []
                        csvrowdictionary = {}
                        orgaccount = False
                        for k, v in u.items():
                            if k in usercharacteristicstoprocess or "*" in usercharacteristicstoprocess:
                                # print(k + ":  " + str(v))

                                if k == "login":
                                    if v not in uniquerusersfound:
                                        uniquerusersfound.append(v)
                                    else:
                                        overlappingusersacrossqueries.append(v)
                                        useralreadyfound = True


                                if k == "type":
                                    if v.lower() == "organization":
                                        orgaccount = True


                                if k == "url":
                                    accountdetailsurl = v
                                    accountdetailsdata = requests.get(accountdetailsurl, headers={"X-GitHub-Api-Version": "2022-11-28", "Authorization": "Bearer " + config['githubtoken']})
                                    accountdetailsdatalist = accountdetailsdata.content.decode("latin-1")
                                    accountdetailsdatalist = json.loads(accountdetailsdatalist)

                                    for k2, v2 in accountdetailsdatalist.items():
                                        if k2 in outputcsvcolumns:
                                            try:
                                                if k2 == "name":
                                                    v2 = v2.title().replace("\n","")
                                                    csvrowdictionary[k2] = v2

                                                elif k2 == "created_at" or k2 == "updated_at":
                                                    v2 = v2.split("T")[0].replace("\n","")
                                                    csvrowdictionary[k2] = v2

                                                elif k2 == "company":
                                                    v2 = v2.replace("@","").replace("\n","")
                                                    csvrowdictionary[k2] = v2

                                                elif k2 == "email":
                                                    if v2 is None or "@" not in str(v2):
                                                        emailaddress = ""
                                                    else:
                                                        emailaddress = str(v2).replace("\n","")
                                                    csvrowdictionary[k2] = emailaddress



                                                elif k2 == "bio":
                                                    utaustinrole = ""
                                                    if " at university of" in v2.lower():
                                                        utaustinrole = v2.lower().split(" at university of")[0]
                                                    elif " at the university of" in v2.lower():
                                                        utaustinrole = v2.lower().split(" at the university of")[0]
                                                    elif " at ut" in v2.lower():
                                                        utaustinrole = v2.lower().split(" at ut")[0]
                                                    elif "@" in v2.lower():
                                                        utaustinrole = v2.lower().split("@")[0].strip()
                                                    elif ", the university of" in v2.lower():
                                                        utaustinrole = v2.lower().split(", the university of")[0]
                                                    elif "- university of" in v2.lower():
                                                        utaustinrole = v2.lower().split("- university of")[0]
                                                    else:
                                                        pass

                                                    utaustinrole.replace("i am a ","")

                                                    csvrowdictionary["bio"] = v2

                                                    if orgaccount:
                                                        csvrow.extend(["organization",""])
                                                        csvrowdictionary["predicted general UT Austin connection/role"] = "organization"
                                                        csvrowdictionary["additional predicted info"] = ""

                                                    else:
                                                        csvrowdictionary["predicted general UT Austin connection/role"] = predictrole(utaustinrole, v2.lower())[0]
                                                        csvrowdictionary["additional predicted info"] = predictrole(utaustinrole, v2.lower())[1]
                                                        csvrow.extend(predictrole(utaustinrole, v2.lower()))

                                                else:
                                                    csvrowdictionary[k2] = v2

                                            except Exception as e:
                                                print(str(e))
                                                csvrowdictionary[k2] = ""

                                        if k in usercharacteristicstoprocess or "*" in usercharacteristicstoprocess:
                                            print("   " + k2 + ": " + str(v2))

                                    print()

                        if not useralreadyfound:
                            csvrowdictionary['query'] = query
                            csvrowdictionarylist.append(csvrowdictionary)

                        print("\n\n\n")

            except Exception as e:
                print("ERROR: " + str(e))

    except Exception as e:
        print("ERROR: " + str(e))

finalfinalcsvrows = []
for obj in csvrowdictionarylist:
    newrow = []
    for columnname in outputcsvcolumns:
        matchfound = False
        for k,v in obj.items():
            if k == columnname:
                matchfound = True
                if str(v) == "None" or v == None:
                    newrow.append("")
                else:
                    newrow.append(v)
        if not matchfound:
            newrow.append("")
    finalfinalcsvrows.append(newrow)


print("preparing to generate " + outputcsvpath)
print("estimated valid rows to create in CSV: " + str(len(csvoutputrows)))

with open(outputcsvpath,"w", newline="") as opencsv:

    csvwriter = csv.writer(opencsv)

    csvwriter.writerow(outputcsvcolumns)

    for csvrow in finalfinalcsvrows:
        try:
            csvwriter.writerow(csvrow)
            print("written to CSV successfully: " + str(csvrow))

        except Exception as e:
            print("ERROR: " + str(e))




print("\n\nNumber of overlapping users across queries: " + str(len(overlappingusersacrossqueries)))
