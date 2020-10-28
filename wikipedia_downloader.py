#! /usr/bin/python
# -*- coding: utf-8 -*-
#
#  Copyright 2013 Simone F. <groppo8@gmail.com>
#
#  This file is part of wikipedia-tags-in-osm.
#  wikipedia-tags-in-osm is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  wikipedia-tags-in-osm is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU General Public License
#  along with wikipedia-tags-in-osm.  If not, see <http://www.gnu.org/licenses/>.

"""Functions for getting info from Quick Intersection and Wikipedia API:
   - download subcategories and articles names of a category (Quick Intersection)
   - check which articles have/don't have the Coord template (Wikipedia API)
"""


import os
import urllib
import urllib2
import csv
import json
from subprocess import call
import configparser
import time
from wikipedia_coords_downloader import CoordsDownloader


### Manage Quick Intersection data ################################################
def check_catscan_data(app, themesAndCatsNames):
    """Check if we have Wikipedia data from Quick Intersection (subcategories names
       and articles names) of all the categories written in 'config.cfg' file
    """
    print("\n- Check that we have Wikipedia data (from Quick Intersection) of all the categories in `config.cfg`")
    needInfo = {}
    for themeName, categoriesNames in themesAndCatsNames.iteritems():
        for categoryName in categoriesNames:
            categoryCatscanFile = os.path.join(app.CATSCANDIR,
                                               themeName,
                                               "%s.json" % categoryName)
            categoryCatscanFile = categoryCatscanFile.encode("utf-8")
            if not os.path.isfile(categoryCatscanFile):
                if not themeName in needInfo:
                    needInfo[themeName] = []
                needInfo[themeName].append(categoryName)

    #download data of missing categories from Quick Intersection
    for themeName, categoriesNames in needInfo.iteritems():
        for categoryName in categoriesNames:
            result = download_a_new_category(app, themeName, categoryName)
            if not result:
                themesAndCatsNames[themeName].remove(categoryName)
    return themesAndCatsNames


def download_a_new_category(app, themeName, categoryName):
    """Download data (subcategories and articles) of a new category
       from quick_intersection (http://tools.wmflabs.org/catscan2/quick_intersection.php?)
       and save it to: CATSCANDIR/theme name/category name.json
    """
    print("\n- Download the list of sub-categories and articles of a new Wikipedia category.\n  %s" % categoryName.encode("utf-8"))
    #response = raw_input("\n- Scarico dati categoria %s da Quick Intersection?\n[y/N]" % categoryName.encode("utf-8"))
    response = "y"
    if response not in ("y", "Y"):
        return False

    if themeName not in os.listdir(app.CATSCANDIR):
        os.makedirs(os.path.join(app.CATSCANDIR, themeName))

    #Download the JSON file with subcategories and articles of the requested category
    url = "https://tools.wmflabs.org/quick-intersection/index.php?"
    url += "lang=%s" % app.WIKIPEDIALANG
    url += "&project=wikipedia"
    url += "&cats=" + urllib.quote_plus(categoryName.encode("utf-8"))
    url += "&ns=*&depth=-1&max=30000&start=0&format=json&catlist=1&redirects=none&callback="

    print("  url:\n{0}\n  downloading data from Quick Intersection...".format(
        url))
    request = urllib2.Request(url, None, {'User-Agent': app.user_agent})
    data = urllib2.urlopen(request)
    filename = os.path.join(app.CATSCANDIR, themeName, "%s.json" % categoryName)
    csvFile = open(filename, 'w')
    csvFile.write(data.read())
    csvFile.close()
    print("  file:\n%s" % filename)

    #Remember category date
    categoryDate = time.strftime("%b %d, ore %H", time.localtime())
    catsDatesFile = os.path.join("data", "wikipedia", "catscan", "update_dates.cfg")
    configparser = ConfigParser.RawConfigParser()
    configparser.optionxform = str
    configparser.read(catsDatesFile)
    configparser.set("catscan dates", categoryName.encode("utf-8"), categoryDate)
    with open(catsDatesFile, 'wb') as configfile:
        configparser.write(configfile)
    #update category date
    app.categoriesDates[categoryName] = categoryDate
    return True


### Ask to Wikipedia the titles of articles with/without Coord template
def read_old_templates_status(app):
    """Read from old_templates_status.csv which articles have/doesn't have
       the Coord template
    """
    templatesStatus = {}
    fileName = app.TEMPLATESSTATUSFILE
    if os.path.isfile(fileName):
        inFile = open(fileName, "r")
        reader = csv.reader(inFile, delimiter='\t')
        for row in reader:
            title, status = row
            title = title.decode("utf-8")
            templatesStatus[title] = status
        inFile.close()
    print("  Without template:", len([i for i in templatesStatus.values() if i == "False"]))
    return templatesStatus


def update_templates_status(app):
    """Update info from Wikipedia API
    """
    #create strings with fifty titles each
    unknownStatus = []
    for title in sorted(app.titlesInOSM):
        if title not in app.templatesStatus or app.templatesStatus[title] == "False":
            unknownStatus.append(title)
    titlesStrings = []
    for fiftyTitles in [unknownStatus[i:i + 50] for i in range(0, len(unknownStatus), 50)]:
        titlesString = "|".join(fiftyTitles)
        titlesStrings.append(titlesString)
    #download
    print("  Update data with %d requests to Wikipedia:" % len(titlesStrings))
    for i, titlesString in enumerate(titlesStrings):
        continueString = ""
        tlcontinueString = ""
        print("\n  request %d" % i)
        while True:
            wikipediaAnswer = download_templates(app, titlesString, continueString, tlcontinueString)
            if not wikipediaAnswer:
                break
            #parse
            continueString, tlcontinueString = parse_wikipedia_answer(app)
            if (continueString, tlcontinueString) == ("", ""):
                break
            else:
                print("  continue", continueString, tlcontinueString)
    #Save updated templates status to file
    save_updated_templates_status(app)


def download_templates(app, titlesString, continueString, tlcontinueString):
    """Query Wikipedia API for Coord template in articles
    """
    titles = urllib.quote_plus(titlesString.replace("_", " ").encode("utf-8"))
    url = ('http://{0}.wikipedia.org/w/api.php?action=query'
           '&format=json&titles={1}&prop=templates&tltemplates=Template:Coord'
           '&maxlag=5&continue='.format(app.WIKIPEDIALANG, titles))
    if continueString != "":
        url += '%s&tlcontinue=%s' % (urllib.quote_plus(continueString), urllib.quote_plus(tlcontinueString))
    #debugging
    #answer = raw_input("\n  Download 50 titles status from Wikipedia?\n%s\n[y/N]" % url)
    answer = "y"
    request = urllib2.Request(url, None, {'User-Agent': app.user_agent})
    if answer in ("y", "Y"):
        try:
            wikipediaAnswer = urllib2.urlopen(request)
        except:
            print("\n* a problem occurred during downloading:", titlesString, continueString, tlcontinueString)
            return False
        else:
            fileName = os.path.join(app.MISSINGTEMPLATESDIR, "answer.json")
            fileOut = open(fileName, "w")
            fileOut.write(wikipediaAnswer.read())
            fileOut.close()
            return True


def parse_wikipedia_answer(app):
    """Read form Wikipedia the articles with/without Coord
       template
    """
    fileName = os.path.join(app.MISSINGTEMPLATESDIR, "answer.json")
    inFile = open(fileName, "r")
    data = json.load(inFile)
    inFile.close()
    pages = data["query"]["pages"]
    for pageid, pageData in pages.iteritems():
        title = pageData["title"].replace(" ", "_")
        if title in app.templatesStatus and app.templatesStatus[title] == "True":
            continue
        else:
            status = str("templates" in pageData)
            app.templatesStatus[title] = status
        #print("aggiunto ", title.encode("utf-8"), status.encode("utf-8"))
    if "continue" in data:
        return (data["continue"]["continue"], data["continue"]["tlcontinue"])
    else:
        return ("", "")


def save_updated_templates_status(app):
    print("\n- Save file with geo templates' statuses")
    fileName = app.TEMPLATESSTATUSFILE
    oldFileName = os.path.join(app.MISSINGTEMPLATESDIR, "old_%s" % app.TEMPLATESSTATUSFILE.split("/")[-1])
    call("cp '%s' '%s'" % (fileName, oldFileName), shell=True)
    fileOut = open(fileName, "w")
    writer = csv.writer(fileOut, delimiter='\t')
    withTemplate = 0
    for title in sorted(app.templatesStatus.keys()):
        status = app.templatesStatus[title]
        if status == "True":
            withTemplate += 1
        writer.writerow([title.encode("utf-8"), status])
    fileOut.close()
    #Print results
    print("  Tagged articles   : %d" % len(app.templatesStatus))
    print("    with template   : %d" % len([i for i in app.templatesStatus.values() if i == "True"]))
    print("    without template: %d" % len([i for i in app.templatesStatus.values() if i == "False"]))


### Add Wikipedia coordinates to non tagged articles ###################
def add_wikipedia_coordinates(app):
    """Add Wikipedia coordinates to articles

    If Wikipedia knows the position of an article not already tagged
    in OSM, add the attribute wikipediaCoords to the article."""
    coords_file = os.path.join("data",
                               "wikipedia",
                               "wikipedia_{0}_coordinates.csv".format(
                                   app.WIKIPEDIALANG))
    answer_file = os.path.join("data", "wikipedia", "answers", "answer.json")

    coords_downloader = CoordsDownloader(
        app.user_agent,
        coords_file,
        answer_file,
        app.WIKIPEDIALANG,
        app.titlesNotInOSM)

    #coords from Wikipedia = {article title : [lat, lon],...}
    app.titles_coords_from_wikipedia = {}
    for title, (lat, lon) in coords_downloader.titles_coords.iteritems():
        if (lat, lon) != ("", ""):
            app.titles_coords_from_wikipedia[title] = [float(lat), float(lon)]
    app.titlesWithCoordsFromWikipedia = {}
    # create a list of mapapble titles without coordinates, needed by Nuts4Nuts
    app.mappable_titles_without_coords = []

    #add wikipediaCoords attribute to articles
    for theme in app.themes:
        for category in theme.categories:
            category.check_articles_coords_in_wikipedia()
    print("  articles:", len(app.titlesWithCoordsFromWikipedia))

    app.mappable_titles_without_coords = \
        list(set(app.mappable_titles_without_coords))
    with open(os.path.join(
              "data", "nuts4nuts", "articles_to_scan.txt"), "w") as f:
        f.write("\n".join(title.encode('utf-8')
                for title in app.mappable_titles_without_coords))
