# Institutional Innovation Grapher
This repository contains scripts for collecting and analyzing data about open source activity associated with a university or institution.

## Tools
The vision for this repository is to build out a set of Python scripts that can effectively be utilized by open source program offices to gain a better understanding of their specific institution. See details below about specific tools.

### github-activity-metrics-tool
This script is designed to gather data about GitHub accounts which mention the specified institution in the "bio" statement associated with the account and save that information in a CSV (simple-github-account-url-list-[year]-[month]-[day]-[institutionname].csv). In addition to gathering summary information about each account, it has been developed with a specific focus on gathering data about the open source activity of university research communities and uses the provided "bio" information associated with each account to make a prediction about type of affiliation with the defined university. The script is also able to gather information about the individual GitHub repositories under each account and saves information about those repositories to a separate CSV file (simple-github-repo-url-list-[year]-[month]-[day]-[institutionname].csv).


## Contact
For any questions about this repository, please contact the UT Austin Open Source Program Office at ospo@utlists.utexas.edu.
