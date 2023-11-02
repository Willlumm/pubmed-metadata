# ~~~~~~~~~~~~~~~~~~~~~~ extractPubMed.py ~~~~~~~~~~~~~~~~~~~~~
#
# From an XML of PubMed records, creates a CSV containing
# metadata for each record and a CSV containing calculations on
# the time between metadata dates by journal NLM ID and time period
# 
# See "extractPubMed Documentation.txt"
#
# ~~~~~~~~~~~~~~~~~~~~~~~~~ Parameters ~~~~~~~~~~~~~~~~~~~~~~~~

# File path of input XML file or folder containing XML files.
input = "2017-2019 Inputs"

# Type of time period to sort publications by for calculations.
# ("Year"/"Quarter"/"Month")
periodType = "Quarter"

# Only include publications published online between these dates.
# ("YYYY-MM-DD")
minDate = "2017-01-01"
maxDate = "2019-06-30"

# Minimum number of publications per time period per journal to be
# included in dates ouput file.
minCount = 0

# Toggle writing the publications output file. (True/False)
writePubsFile = True

# Toggle writing the dates output file. (True/False)
writeDatesFile = True

import csv
from datetime import date
import xml.etree.ElementTree as et
import numpy as np
import os

# ~~~~~~~~~~~~~~~~~~~~ Reading input file ~~~~~~~~~~~~~~~~~~~~
     
# Get field text as string from publication root element and
# field path. Returns empty string if publication does not
# contain field.
def getField(element, path):
    if element.find(path) is not None:
        field = str(element.find(path).text)
    else:
        field = ""
    return field
    
# Get text from multiple fields as a string from publication root
# element and the path of the fields' parent.
def getFields(element, path):
    return ", ".join([field.text for field in element.find(path)])

# Get date as date object from publication root element and
# date path. Prints error and returns None if date is invalid.
# Returns None if publication does not contain date.
def getDate(element, path):
    dateXML = element.find(path)
    if dateXML is not None:
        try:
            y = int(dateXML[0].text)
            m = int(dateXML[1].text)
            d = int(dateXML[2].text)
            dat = date(y, m, d)
        except ValueError:
            dat = None
            print("Bad Date: " + " ".join([str(y), str(m), str(d)]) + " PMID: " + element.find("MedlineCitation/PMID").text)
    else:
        dat = None  
    return dat

# Read data from publication element and return data as
# dictionary.
def readElement(element):
    return {
        "PMID" : getField(element, "MedlineCitation/PMID"),
        "DOI" : getField(element, "PubmedData/ArticleIdList/*[@IdType='doi']"),
        "Publication Types" : getFields(element, "MedlineCitation/Article/PublicationTypeList"),
        "Journal" : getField(element, "MedlineCitation/Article/Journal/Title"),
        "ISSN" : getField(element, "MedlineCitation/Article/Journal/ISSN"),
        "ISSN-L" : getField(element, "MedlineCitation/MedlineJournalInfo/ISSNLinking"),
        "NLM ID" : getField(element, "MedlineCitation/MedlineJournalInfo/NlmUniqueID"),
        "Date Received" : getDate(element, "PubmedData/History/*[@PubStatus='received']"),
        "Date Revised" : getDate(element, "PubmedData/History/*[@PubStatus='revised']"),
        "Date Accepted" : getDate(element, "PubmedData/History/*[@PubStatus='accepted']"),
        "Date Online" : getDate(element, "MedlineCitation/Article/ArticleDate")
    }
    
# Read XML from path and return data as list of dictionaries.
# Takes a set of PMIDs to ignore to avoid duplicates.
# Parsing is iterative and delayed by one publication to ensure
# all sub-elements have been parsed.
def readXML(path, pmidSet):
    print("Reading XML file " + path)
    context = et.iterparse(path, events=("start",))
    pubs = list()
    prevElement = None
    for event, element in context:
        if element.tag == "PubmedArticle":
            if prevElement:
                pub = readElement(prevElement)
                if pub["PMID"] not in pmidSet:
                    pubs.append(pub)
                    pmidSet.add(pub["PMID"])
                prevElement.clear()
            prevElement = element
    pubs.append(readElement(prevElement))
    return pubs, pmidSet

# Read all XML files in folder from path and return data as
# list of dictionaries. If the path specifies an XML file
# instead of a folder, 
def readFolder(path):
    if path[-4:] == ".xml":
        pubs, pmidset = readXML(path, set())
        return pubs
    pubs = list()
    pmidSet = set()
    for file in os.listdir(path):
        if file[-4:] == ".xml":
            newPubs, newPmidSet = readXML(path + "/" + file, pmidSet)
            pubs.extend(newPubs)
            pmidSet.update(newPmidSet)
    return pubs

# ~~~~~~~~~~~~~~~~~~~~~~~~~ Processing ~~~~~~~~~~~~~~~~~~~~~~~~

# Sort list of publications by NLM ID into dictionary of lists.
def sortPubsByNLM(pubs):
    sortedPubs = dict()
    for pub in pubs:
        nlm = pub["NLM ID"]
        if nlm not in sortedPubs:
            sortedPubs[nlm] = [pub]
        else:
            sortedPubs[nlm].append(pub)
    return sortedPubs
    
# Sort list of publications by type of time period into
# dictionary of lists. Ignores publications outside of the
# specified range.
def sortPubsByPeriod(pubs, periodType):
    sortedPubs = dict()
    for pub in pubs:
        dat = pub["Date Online"]
        if dat is None or dat < date.fromisoformat(minDate) or dat > date.fromisoformat(maxDate):
            continue
        if periodType == "Year":
            period = str(dat.year)
        elif periodType == "Quarter":
            period = str(dat.year) + "Q" + str(int((dat.month-1)/3)+1)
        elif periodType == "Month":
            period = str(dat.year) + "M" + str(dat.month)
        if period not in sortedPubs:
            sortedPubs[period] = [pub]
        else:
            sortedPubs[period].append(pub)
    return sortedPubs

# Get dictionary of intervals in days between each date from
# publication. Returns None if any interval is invalid or if no
# intervals are calculated.
def getIntervals(pub):
    intervals = dict()
    prevDates = dict()
    for dateType, dateValue in pub.items():
        if not (isinstance(dateValue, date) and dateValue):
            continue
        for prevDateType, prevDateValue in prevDates.items():
            intervalType = prevDateType[5:8] + "-" + dateType[5:8]
            intervalDays = (dateValue - prevDateValue).days
            if intervalDays < 1 or intervalDays > 1416:
                return None
            intervals[intervalType] = [intervalDays]
        prevDates[dateType] = dateValue
    if len(intervals) == 0:
        return None
    return intervals

# Get list of interval dictionaries from list of publications.
def getIntervalList(pubs):
    intervalLists = dict()
    for pub in pubs:
        if not getIntervals(pub):
            continue
        for intervalType, intervalDays in getIntervals(pub).items():
            if intervalType not in intervalLists:
                intervalLists[intervalType] = [intervalDays]
            else:
                intervalLists[intervalType].append(intervalDays)
    return intervalLists

# Get list of dictionary of calculations on list of intervals.
def getCalcs(intervalList):
    allCalcs = dict()
    for intervalType, intervalDaysList in intervalList.items():
        calcs = {
            "Count" : len(intervalDaysList),
            "Mean" : np.mean(intervalDaysList),
            "1st Quartile": np.percentile(intervalDaysList, 25),
            "Median" : np.percentile(intervalDaysList, 50),
            "3rd Quartile" : np.percentile(intervalDaysList, 75),
        }
        allCalcs[intervalType] = calcs
    return allCalcs
    
# Count number of publications with each date and return as
# dictionary.
def countDates(pubs):
    counts = {
        "Date Received" : 0,
        "Date Revised" : 0,
        "Date Accepted" : 0,
        "Date Online" : 0,
        "Total" : 0,
        "Total Valid" : 0
    }
    for pub in pubs:
        counts["Total"] += 1
        if not getIntervals(pub):
            continue
        for dateType, dateValue in pub.items():
            if isinstance(dateValue, date):
                counts[dateType] += 1
        counts["Total Valid"] += 1
    return counts

# Get calculation data by NLM ID, time period, and interval as
# four nested dictionaries from list of publications. Ignores
# periods with fewer than the minimum publications with valid
# dates.
# NLM ID : Period : Interval : Calculation
def getData(rawPubs):
    print("Calculating...")
    nlmPubs = sortPubsByNLM(rawPubs)
    data = dict()
    for nlm, pubsA in nlmPubs.items():
        nlmDict = dict()
        periodPubs = sortPubsByPeriod(pubsA, periodType)
        for period, pubsB in periodPubs.items():
            counts = countDates(pubsB)
            if counts["Total Valid"] >= minCount:
                intervals = getIntervalList(pubsB)
                calcs = getCalcs(intervals)
                nlmDict[period] = calcs
                nlmDict[period]["Aggregate"] = counts
        if len(nlmDict) > 0:
            data[nlm] = nlmDict
    return data
    
# ~~~~~~~~~~~~~~~~~~~~ Writing output files ~~~~~~~~~~~~~~~~~~~

# Split list of publications into dictionary of lists by either 
# year, quarter, or month so that no list is longer than
# 750,000 publications.
def splitPubs(pubs):
    maxPubs = len(pubs)
    pubDict = {"All" : pubs}
    periodTypes = ("Year", "Quarter", "Month")
    for periodType in periodTypes:
        maxPubs = 0
        for pubsA in pubDict.values():
            if len(pubsA) > maxPubs:
                maxPubs = len(pubsA)
        if maxPubs < 750000:
            return pubDict
        pubDict = sortPubsByPeriod(pubs, periodType)
    return pubDict

# Write CSV file of publication metadata from list of
# publications.
def writePubsCSV(pubs, name):
    if not writePubsFile:
        return
    for period, sortedPubs in splitPubs(pubs).items():
        filename = name.replace(".xml","") + " " + period + " Publications.csv"
        print("Writing publications file " + filename)
        header = sortedPubs[0].keys()
        with open(filename, "w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=header)
            writer.writeheader()
            for pub in sortedPubs:
                try:
                    writer.writerow(pub)
                except UnicodeEncodeError:
                    print(pub["DOI"] + " failed to write.")

# Write CSV file of publication date calculations.
def writeDatesCSV(data, name):
    if not writeDatesFile:
        return
    filename = input.replace(".xml","") + " Dates.csv"
    print("Writing dates file " + filename)
    header = list()
    rows = list()
    for nlm, periods in data.items():
        for period, intervals in periods.items():
            if intervals["Aggregate"]["Total Valid"] < minCount:
                continue
            row = {"NLM ID" : nlm, "Period" : period}
            for interval, calcs in intervals.items():
                for calc, value in calcs.items():
                    heading = interval + " " + calc
                    row[interval + " " + calc] = value
            if len(row) > len(header):
                header = row.keys()
            rows.append(row)
    with open(filename, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)

# ~~~~~~~~~~~~~~~~~~~~~~~~~ Run script ~~~~~~~~~~~~~~~~~~~~~~~~

pubs = readFolder(input)
writePubsCSV(pubs, input)
data = getData(pubs)
writeDatesCSV(data, input)