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
#  along with Nome-Programma.  If not, see <http://www.gnu.org/licenses/>.

"""Functions for getting info from CatScan and Wikipedia API:
   - download subcategories and articles names of a category (CatScan)
   - check which articles have/don't have the Coord template (Wikipedia API)
"""


import os
import urllib
import urllib2
import csv
import json
from subprocess import call


### Manage catscan data ################################################
def check_catscan_data(app, themesAndCatsNames):
    """Check if we have Wikipedia data from catscan (subcategories names
       and articles names) of all the categories written in 'config' file
    """
    print "\n- Controlla la presenza dei dati Wikipedia (catscan) di tutte le categorie nel file 'config'"
    needInfo = {}
    for themeName, categoriesNames in themesAndCatsNames.iteritems():
        for categoryName in categoriesNames:
            categoryCatscanFile = os.path.join(app.CATSCANDIR, themeName, "%s.csv" % categoryName)
            categoryCatscanFile = categoryCatscanFile.encode("utf-8")
            if not os.path.isfile(categoryCatscanFile):
                if not themeName in needInfo:
                    needInfo[themeName] = []
                needInfo[themeName].append(categoryName)
    #download catscan data of missing categories
    for themeName, categoriesNames in needInfo.iteritems():
        for categoryName in categoriesNames:
            result = download_a_new_category(themeName, categoryName)
            if not result:
                themesAndCatsNames[themeName].remove(categoryName)
    return themesAndCatsNames

def download_a_new_category(app, themeName, categoryName):
    """Download data (subcategories and articles) of a new category
       from catscan (http://toolserver.org/%7Edaniel/WikiSense/CategoryIntersect.php)
       and save it to: CATSCANDIR/theme name/category name.csv
    """
    print "\n- Scarico (da catscan) la lista di sottocategorie ed articoli di una nuova categoria Wikipedia"
    response = raw_input("\n- Scarico dati categoria %s da catscan?\n[y|n]" % categoryName.encode("utf-8"))
    if response != "y":
        return False
    print "\ndownloading category info from catscan..."

    if themeName not in os.listdir(app.CATSCANDIR):
        os.makedirs(os.path.join(app.CATSCANDIR, themeName))

    #Download the CSV file with subcategories and articles of the requested category
    url = "http://toolserver.org/~daniel/WikiSense/CategoryIntersect.php?"
    url += "wikilang=%s" % app.WIKIPEDIALANG
    url += "&wikifam=.wikipedia.org"
    url += "&basecat=" + urllib.quote_plus(categoryName.encode("utf-8"))
    url += "&basedeep=8&templates=&mode=al&format=csv"

    print "url:"
    print url

    data = urllib2.urlopen(url)
    filename = os.path.join(app.CATSCANDIR, themeName, "%s.csv" % categoryName)
    csvFile = open(filename,'w')
    csvFile.write(data.read())
    csvFile.close()
    print "Dati Wikipedia sulla nuova categoria salvati in:\n%s" % filename

    #Remember category date
    configparser = ConfigParser.RawConfigParser()
    configparser.optionxform=str
    configparser.read("config")
    categoryDate = time.strftime("%b %d, ore %H", time.localtime())
    configparser.set("catscan dates", categoryName.encode("utf-8"), categoryDate)
    configparser.write(open("config", "w"))
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
        inFile  = open(fileName, "r")
        reader = csv.reader(inFile, delimiter='\t')
        for row in reader:
            title, status = row
            title = title.decode("utf-8")
            templatesStatus[title] = status
        inFile.close()
    print "  Senza template:",  len([i for i in templatesStatus.values() if i == "False"])
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
    for fiftyTitles in [unknownStatus[i:i+50] for i in range(0, len(unknownStatus), 50)]:
        titlesString = "|".join(fiftyTitles)
        titlesStrings.append(titlesString)
    #download
    print "  Update data with %d requests to Wikipedia:" % len(titlesStrings)
    for i, titlesString in enumerate(titlesStrings):
        continueString = ""
        tlcontinueString = ""
        print "\n  request %d" % i
        while True:
            wikipediaAnswer = download_templates(app, titlesString, continueString, tlcontinueString)
            if not wikipediaAnswer:
                break
            #parse
            continueString, tlcontinueString = parse_wikipedia_answer(app)
            if (continueString, tlcontinueString) == ("", ""):
                break
            else:
                print "  continue", continueString, tlcontinueString
    #Save updated templates status to file
    save_updated_templates_status(app)


def download_templates(app, titlesString, continueString, tlcontinueString):
    """Query Wikipedia API for Coord template in articles
    """
    titles = urllib.quote_plus(titlesString.replace("_", " ").encode("utf-8"))
    url = 'http://it.wikipedia.org/w/api.php?action=query'
    url += '&format=json'
    url += '&titles=%s' % titles
    url += '&prop=templates'
    url += '&tltemplates=Template:Coord'
    url += '&continue='
    if continueString != "":
        url += '%s&tlcontinue=%s' % (urllib.quote_plus(continueString), urllib.quote_plus(tlcontinueString))
    #debugging
    #answer = raw_input("\n  Download 50 titles status from Wikipedia?\n%s\n[y/N]" % url)
    answer = "y"
    if answer in ("y", "Y"):
        try:
            wikipediaAnswer = urllib2.urlopen(url)
        except:
            print "\n* a problem occurred during downloading:", titlesString, continueString, tlcontinueString
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
        #print "aggiunto ", title.encode("utf-8"), status.encode("utf-8")
    if "continue" in data:
        return (data["continue"]["continue"], data["continue"]["tlcontinue"])
    else:
        return ("", "")


def save_updated_templates_status(app):
    print "\n- Salvataggio del file con lo status dei template"
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
    print "  Articoli taggati: %d" % len(app.templatesStatus)
    print "    con template  : %d" % len([i for i in app.templatesStatus.values() if i == "True"])
    print "    senza template: %d" % len([i for i in app.templatesStatus.values() if i == "False"])


### Add Wikipedia coordinates to non tagged articles ###################
def add_wikipedia_coordinates(app):
    #If Wikipedia knows the position of an article not already tagged
    #in OSM add the attribute wikipediaCoords to the article
    coordsFile = os.path.join(os.path.join("data", "wikipedia", "wikipedia_%s_coordinates.csv" % app.WIKIPEDIALANG))
    if not os.path.isfile(coordsFile):
        #download the file with Wikipedia coordinates if missing
        download_and_filter_wikipedia_coordinates(app)
    app.titlesCoords = {}
    #read coords
    inFile = open(coordsFile, "r")
    reader = csv.reader(inFile, delimiter = '\t')
    for row in reader:
        title, lat, lon = row
        app.titlesCoords[title.replace(" ", "_").decode("utf-8")] = [float(lat), float(lon)]
    inFile.close()
    app.titlesInProjectWithCoords = []
    #add wikipediaCoords attribute to articles
    for theme in app.themes:
        for category in theme.categories:
            category.check_articles_coords_in_wikipedia()
    app.titlesInProjectWithCoords = list(set(app.titlesInProjectWithCoords))
    print "  articoli:", len(app.titlesInProjectWithCoords)

def download_and_filter_wikipedia_coordinates(app):
    """Download and filter file with Wikipedia coordinates, provided by
       user Kolossos
    """
    #download
    url = "http://toolserver.org/~kolossos/wp-world/pg-dumps/wp-world/new_C.gz"
    print "\n* Il file con le coordinate Wikipedia non è presente e sarà scaricato."
    print "  File provided by user Kolossos:", url
    inFile = os.path.join("data", "wikipedia", "new_C.gz")
    #call('wget -c "%s" -O %s' % (url, inFile), shell=True)
    coordsFile = os.path.join("data", "wikipedia", "wikipedia_%s_coordinates.csv" % app.WIKIPEDIALANG)
    #filter coordinates of articles in WIKIPEDIALANG
    print "  filtra coordinate in %s ..." % app.WIKIPEDIALANG
    call('zgrep ^%s "%s" | cut -f2,3,4 > %s' % (app.WIKIPEDIALANG, inFile, coordsFile), shell=True)
    print "  rimuovi il file non più necessario: %s" % inFile
    call('rm "%s"' % inFile, shell=True)
