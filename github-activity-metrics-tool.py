import os
import csv
import pandas as pd
import requests
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta




# Check to ensure that essential repo directories exist, and create them if they do not
if not os.path.isdir("inputs"):
    os.mkdir("inputs")

if not os.path.isdir("outputs"):
    os.mkdir("outputs")

if not os.path.isdir("logs"):
    os.mkdir("logs")

if not os.path.isdir("outputs/" + datetime.now().strftime("%Y-%m-%d")):
    os.mkdir("outputs/" + datetime.now().strftime("%Y-%m-%d"))



# Open and read config parameters from .env file
with open(".env") as envfile:
    config = json.loads(envfile.read())


# Modify config parameters
simplifiedinstitutionname = config['institutionname'].replace(" ","-").lower().strip()
config['githubaccountdetailscsvpath'] = config['githubaccountdetailscsvpath'].replace('institutionnameplaceholder',simplifiedinstitutionname).replace('dateplaceholder',datetime.now().strftime("%Y-%m-%d")).replace("detaillevelplaceholder",config['detaillevel'])
config['githubrepodetailscsvpath'] = config['githubrepodetailscsvpath'].replace('institutionnameplaceholder',simplifiedinstitutionname).replace('dateplaceholder',datetime.now().strftime("%Y-%m-%d")).replace("lastupdatethresholdplaceholder","last" + str(config['githubrepolastupdatethresholdinmonths']) + "months")




####EXAMPLE QUERY
# querylist.append("firstpartofname+firstpartofname+followers:>=" + str(minimumfollowers) + "+repos:>=" + str(minimumrepos))

# update this list of queries to fit your institution
querylist = []
querylist.append("ut+austin+followers:>=" + str(config['minimumfollowers']) + "+repos:>=" + str(config['minimumrepos']))
querylist.append("university+of+texas+at+austin+followers:>=" + str(config['minimumfollowers']) + "+repos:>=" + str(config['minimumrepos']))
querylist.append("location:%22university+of+texas+at+austin%22&followers:>=" + str(config['minimumfollowers']) + "&repos:>=" + str(config['minimumrepos']))
querylist.append("location:\"ut+austin\"&followers:>=" + str(config['minimumfollowers']) + "&repos:>=" + str(config['minimumrepos']))
querylist.append("location%3AAustin+followers%3A%3E%3D40+repos%3A%3E%3D1&type=Users&ref=advsearch&l=&l=&s=followers&o=desc")
querylist.append("texas+advanced+computing+center+in:bio&type=Users")



githubaccountdetailscsvcolumns = []
# if config['detaillevel'] == "fulldetail":
githubaccountdetailscsvcolumns.append("name")
githubaccountdetailscsvcolumns.append("html_url")
githubaccountdetailscsvcolumns.append("company")
githubaccountdetailscsvcolumns.append("email")
githubaccountdetailscsvcolumns.append("bio")
githubaccountdetailscsvcolumns.append("public_repos")
githubaccountdetailscsvcolumns.append("followers")
githubaccountdetailscsvcolumns.append("created_at")
githubaccountdetailscsvcolumns.append("updated_at")
githubaccountdetailscsvcolumns.append("predicted general " + config['institutionname'] + " connection/role")
githubaccountdetailscsvcolumns.append("additional predicted info")
githubaccountdetailscsvcolumns.append("query")
githubaccountdetailscsvcolumns.append("querydate")



githubrepodetailscsvcolumns = ['name','full_name','html_url','description','fork','created_at','updated_at','size','stargazers_count','watchers_count','language','forks_count','archived','disabled','open_issues_count','license','allow_forking','topics','forks','visibility','open_issues']


uniquerepolist = []


usercharacteristicstoprocess = ['login','id','avatar_url','url','html_url','name','company','blog','location','email','bio','public_repos','public_gists','followers','following','created_at','updated_at','organizations_url','type']

repocharacteristicstoprocess = ['name','full_name','html_url','description','fork','created_at','updated_at','size','stargazers_count','watchers_count','language','forks_count','archived','disabled','open_issues_count','license','allow_forking','visibility','forks','topics','open_issues']



overlappingusersacrossqueries = []
uniquerusersfound = []
apiendpoint = "users"

repolanguagelist = []
repolicenselist = []
repostargazerlist = []
repowatcherlist = []
repoforklist = []

finalgithubaccountdetailscsvrows = []
finalgithubrepodetailscsvrows = []







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

        if "boot" in desc and "camp" in desc:
            prediction = "UT bootcamp student"

        if "turing" in desc and "scholar" in desc:
            prediction = "Student"
            additionalinfo += "Undergraduate student (Turing Scholar)"

    predictionlist = [prediction,additionalinfo]

    print("returning the following predictionlist: " + str(predictionlist))
    return predictionlist


csvoutputrows = []
csvrowdictionarylist = []

githubaccountschecked = 0

for query in querylist:

    try:
        queryurl = "https://api.github.com/search/"+ apiendpoint +"?q="+ query +"&per_page=" + str(config['resultsperpage'])

        print(queryurl)

        data = requests.get(queryurl, headers={"X-GitHub-Api-Version": "2022-11-28", "Authorization": "Bearer " + config['githubtoken'], "Accept": "application/vnd.github+json" })

        response = json.loads(data.content)

        print(response)

        try:
            responselinkheaders = data.headers["Link"]
            pageinfo = responselinkheaders.split(",")

            nexturl = pageinfo[0].replace("<","").split(">; ")[0].strip()
            lasturl = pageinfo[1].replace("<","").split(">; ")[0].strip()
            lastpagenum = lasturl.split("=")[-1]

            print("total count for query '" + query + "' = " + str(response['total_count']))
            print("next page = " + nexturl)
            print("lastpage = " + lasturl)
            print()

        except:
            print("less than one page of results returned")

        pagecount = 0

        while pagecount < config['pagelimit']:

            try:
                pagecount += 1

                queryurl = "https://api.github.com/search/"+ apiendpoint +"?q="+ query +"&per_page=" + str(config['resultsperpage']) + "&page=" + str(pagecount)

                print("queryurl = " + queryurl)

                data = requests.get(queryurl, headers={"X-GitHub-Api-Version": "2022-11-28", "Authorization": "Bearer " + config['githubtoken'], "Accept": "application/vnd.github+json" })

                response = json.loads(data.content)


                # FOR USER IN LIST OF RETRIEVED USERS
                for u in response['items']:

                    githubaccountschecked += 1


                    print("\nchecking github account... #" + str(githubaccountschecked))

                    utaffiliated = False

                    if str('location%3A' + config['institutioncity'] + '+') in queryurl:

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
                                            if config['institutionemaildomain'] in v2:
                                                utaffiliated = True

                                        if k2 == "company":
                                            print("   company: " + str(v2))

                                            for permutation in config['institutionnamepermutations']:
                                                if permutation.lower() in v2.lower():
                                                    utaffiliated = True

                                    except Exception as e:
                                        pass



                    if str('location%3A' + config['institutioncity'] + '+') not in queryurl:

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
                                        if k2 in githubaccountdetailscsvcolumns:
                                            try:
                                                if k2 == "name":
                                                    v2 = v2.title().replace("\n","")
                                                    csvrowdictionary[k2] = v2

                                                elif k2 == "created_at" or k2 == "updated_at":
                                                    v2 = v2.split("T")[0].replace("\n","")
                                                    csvrowdictionary[k2] = v2

                                                elif k2 == "company":
                                                    if config['detaillevel'] == "fulldetail":
                                                        v2 = v2.replace("@","").replace("\n","")
                                                        csvrowdictionary[k2] = v2
                                                    else:
                                                        csvrowdictionary[k2] = ""

                                                elif k2 == "email":
                                                    if v2 is None or "@" not in str(v2):
                                                        emailaddress = ""
                                                    else:
                                                        emailaddress = str(v2).replace("\n","")

                                                    if config['detaillevel'] == "fulldetail":
                                                        csvrowdictionary[k2] = emailaddress

                                                    else:
                                                        csvrowdictionary[k2] = ""


                                                elif k2 == "bio":

                                                    institutionrole = ""
                                                    if " at university of" in v2.lower():
                                                        institutionrole = v2.lower().split(" at university of")[0]
                                                    elif " at the university of" in v2.lower():
                                                        institutionrole = v2.lower().split(" at the university of")[0]
                                                    elif " at ut" in v2.lower():
                                                        institutionrole = v2.lower().split(" at ut")[0]
                                                    elif "@" in v2.lower():
                                                        institutionrole = v2.lower().split("@")[0].strip()
                                                    elif ", the university of" in v2.lower():
                                                        institutionrole = v2.lower().split(", the university of")[0]
                                                    elif "- university of" in v2.lower():
                                                        institutionrole = v2.lower().split("- university of")[0]
                                                    else:
                                                        pass

                                                    institutionrole.replace("i am a ","")

                                                    if config['detaillevel'] == "fulldetail":
                                                        csvrowdictionary["bio"] = v2
                                                    else:
                                                        csvrowdictionary["bio"] = ""

                                                    if orgaccount:
                                                        csvrow.extend(["organization",""])
                                                        csvrowdictionary["predicted general "+ config['institutionname'] +" connection/role"] = "organization"
                                                        csvrowdictionary["additional predicted info"] = ""

                                                    else:
                                                        csvrowdictionary["predicted general "+ config['institutionname'] +" connection/role"] = predictrole(institutionrole, v2.lower())[0]
                                                        csvrowdictionary["additional predicted info"] = predictrole(institutionrole, v2.lower())[1]
                                                        csvrow.extend(predictrole(institutionrole, v2.lower()))

                                                else:
                                                    csvrowdictionary[k2] = v2

                                            except Exception as e:
                                                print(str(e))
                                                csvrowdictionary[k2] = ""

                                        if k in usercharacteristicstoprocess or "*" in usercharacteristicstoprocess:
                                            print("   " + k2 + ": " + str(v2))

                                            if k2 == "repos_url":
                                                try:
                                                    reposqueryurl = v2
                                                    reposdata = requests.get(reposqueryurl, headers={"X-GitHub-Api-Version": "2022-11-28", "Authorization": "Bearer " + config['githubtoken'], "Accept": "application/vnd.github+json" })
                                                    reposdatalist = json.loads(reposdata.content.decode("latin-1"))



                                                    for reponum, repo in enumerate(reposdatalist):
                                                        keycount = 0
                                                        print("       Data for repo #" + str(reponum + 1) + " out of " + str(len(reposdatalist)))
                                                        repocsvrow = []

                                                        processrepo = False


                                                        yearofmostrecentupdate = int(repo['updated_at'].lower().split("t")[0].split("-")[0])
                                                        monthofmostrecentupdate = int(repo['updated_at'].lower().split("t")[0].split("-")[1])
                                                        dayofmostrecentupdate = int(repo['updated_at'].lower().split("t")[0].split("-")[2])

                                                        # Example time: 2021-04-24T15:13:29Z
                                                        datetimeofmostrecentupdate = datetime.strptime(repo['updated_at'], '%Y-%m-%dT%H:%M:%SZ')

                                                        monthssincemostrecentupdate = (float(relativedelta(datetime.now(), datetimeofmostrecentupdate).years)*12) + float(relativedelta(datetime.now(), datetimeofmostrecentupdate).months)
                                                        print("       LAST UPDATE DATE: " + repo['updated_at'])
                                                        print("       REPO LAST UPDATED " + str(monthssincemostrecentupdate) + " MONTHS AGO")

                                                        if monthssincemostrecentupdate < config['githubrepolastupdatethresholdinmonths']:
                                                            processrepo = True


                                                            for k2, v2 in repo.items():

                                                                if k2 in repocharacteristicstoprocess:

                                                                    try:
                                                                        license = ""



                                                                        if repo['html_url'] not in uniquerepolist:
                                                                            keycount += 1

                                                                            print("            " + str(keycount) + "  " +  k2 + ": " + str(v2))

                                                                            if k2 == "language":
                                                                                repolanguagelist.append(str(v2))
                                                                                repocsvrow.append(str(v2))

                                                                            elif k2 == "license":
                                                                                if v2 == "None":
                                                                                    license = "None"
                                                                                    repolicenselist.append("None")
                                                                                    repocsvrow.append("None")
                                                                                else:
                                                                                    repolicenselist.append(v2['name'])
                                                                                    repocsvrow.append(v2['name'])
                                                                                    license = v2['name']

                                                                            elif k2 == "stargazers_count":
                                                                                repostargazerlist.append(v2)
                                                                                repocsvrow.append(v2)

                                                                            elif k2 == "watchers_count":
                                                                                repowatcherlist.append(v2)

                                                                                repocsvrow.append(v2)

                                                                            elif k2 == "forks":
                                                                                repoforklist.append(v2)

                                                                                repocsvrow.append(v2)

                                                                            else:
                                                                                repocsvrow.append(v2)
                                                                    except:
                                                                        pass

                                                            print(str(len(repocsvrow)) + "   " + str(repocsvrow))

                                                            #if licensing information not provided, add default license value of ""
                                                            if len(repocsvrow) < 21:
                                                                repocsvrow.insert(15,license)

                                                            finalgithubrepodetailscsvrows.append(repocsvrow)
                                                        print("\n\n")

                                                except Exception as e:
                                                    print(str(e))

                                    print()

                                # if k == "organizations_url":
                                #     try:
                                #         orgsqueryurl = v
                                #         orgsdata = requests.get(orgsqueryurl, headers={"X-GitHub-Api-Version": "2022-11-28", "Authorization": "Bearer " + config['githubtoken']})
                                #         orgsdatalist = json.loads(orgsdata.content.decode("latin-1"))
                                #         for org in list(orgsdatalist):
                                #             for k2, v2 in org.items():
                                #                 print("      " + k2 + ": " + str(v2))
                                #             print()
                                #
                                #
                                #     except Exception as e:
                                #         print(str(e))

                                # if k == "starred_url":
                                #     starredqueryurl = v
                                #     starreddata = requests.get(starredqueryurl, headers={"X-GitHub-Api-Version": "2022-11-28", "Authorization": "Bearer " + config['githubtoken'], "Accept": "application/vnd.github+json" })
                                #     starreddatalist = json.loads(starreddata.content.decode("latin-1"))
                                #
                                #     for starred in list(starreddatalist):
                                #         for k2, v2 in starred.items():
                                #             print("   " + k2 + ": " + str(v2))
                                #         print()

                                # if k == "followers_url":
                                #     followersqueryurl = v
                                #     followersdata = requests.get(followersqueryurl, headers={"X-GitHub-Api-Version": "2022-11-28", "Authorization": "Bearer " + config['githubtoken'], "Accept": "application/vnd.github+json" })
                                #     followersdatalist = json.loads(followersdata.content.decode("latin-1"))
                                #
                                #     for follower in list(followersdatalist):
                                #         for k2, v2 in follower.items():
                                #             print("   " + k2 + ": " + str(v2))
                                #         print()

                                # if k == "following_url":
                                #     followingqueryurl = v
                                #     followingdata = requests.get(followingqueryurl, headers={"X-GitHub-Api-Version": "2022-11-28", "Authorization": "Bearer " + config['githubtoken'], "Accept": "application/vnd.github+json" })
                                #     followingdatalist = json.loads(followingdata.content.decode("latin-1"))
                                #
                                #     for following in list(followingdatalist):
                                #         for k2, v2 in following.items():
                                #             print("   " + k2 + ": " + str(v2))
                                #         print()

                        if not useralreadyfound:
                            csvrowdictionary['query'] = query
                            csvrowdictionary['querydate'] = datetime.now().strftime("%Y-%m-%d")
                            csvrowdictionarylist.append(csvrowdictionary)

                        print("\n\n\n")

            except Exception as e:
                print("ERROR: " + str(e))

    except Exception as e:
        print("ERROR: " + str(e))



for obj in csvrowdictionarylist:
    newrow = []
    for columnname in githubaccountdetailscsvcolumns:
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
    finalgithubaccountdetailscsvrows.append(newrow)



print("\n\n" + "preparing to generate " + config['githubaccountdetailscsvpath'])
print("estimated valid rows to create in GitHub account details CSV: " + str(len(finalgithubaccountdetailscsvrows)))

with open(config['githubaccountdetailscsvpath'],"w", newline="") as opencsv:

    csvwriter = csv.writer(opencsv)

    csvwriter.writerow(githubaccountdetailscsvcolumns)

    for i, csvrow in enumerate(finalgithubaccountdetailscsvrows):
        try:
            csvwriter.writerow(csvrow)
            if i%10 == 0:
                print("row #" + str(i) + " written successfully")

        except Exception as e:
            print("ERROR: " + str(e))



print("\n\n" + "preparing to generate " + config['githubrepodetailscsvpath'])
print("estimated valid rows to create in GitHub repo details CSV: " + str(len(finalgithubrepodetailscsvrows)))

topstarredrepos = []
topwatchedrepos = []
topforkedrepos = []

with open(config['githubrepodetailscsvpath'],"w", newline="") as opencsv:

    csvwriter = csv.writer(opencsv)

    csvwriter.writerow(githubrepodetailscsvcolumns)

    for i, csvrow in enumerate(finalgithubrepodetailscsvrows):

        try:
            csvwriter.writerow(csvrow)

            stargazercount = csvrow[8]
            watchercount = csvrow[9]
            forkcount = csvrow[11]

            if i%10 == 0:
                print("row #" + str(i) + " written successfully")

        except Exception as e:
            print("ERROR: " + str(e))








print("\n\nNumber of overlapping users across queries: " + str(len(overlappingusersacrossqueries)))



print("\n\n")
print("Programming language statistics:")
languagecountlist = []

for language in set(repolanguagelist):
    languagecountlist.append(repolanguagelist.count(language))

for i in reversed(range(max(languagecountlist) + 1)):
    for language in set(repolanguagelist):
        try:
            if repolanguagelist.count(language) == i and i >= 5:
                print("   " + str(repolanguagelist.count(language)) + (" " * (7-len(str(repolanguagelist.count(language))))) + language)
        except Exception as e:
            pass


print("\n\n")
print("License statistics:")
licensecountlist = []

for license in set(repolicenselist):
    licensecountlist.append(repolicenselist.count(license))

for i in reversed(range(max(licensecountlist) + 1)):
    for license in set(repolicenselist):
        try:
            if repolicenselist.count(license) == i:
                print("   " + str(repolicenselist.count(license)) + (" " * (7-len(str(repolanguagelist.count(language))))) + license)

        except Exception as e:
            print(str(e))
