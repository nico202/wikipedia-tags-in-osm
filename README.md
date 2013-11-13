Wikipedia tags in OSM
---------------------
This program creates simple web pages with lists of Wikipedia articles, showing which ones are still to be tagged in OpenStreetMap (OSM).<br>
Its aim is to show the progress of Wikipedia articles tagging in OSM, in a specific country, regarding a selected list of *mappable* categories.

##Features:
* Download and parse OSM and Wikipedia data to show the tagging **progress** of selected Wikipedia categories, in the configured country
* Informations reagarding articles and their corresponding objects in OSM are provided through **links** to: [WIWOSM](https://wiki.openstreetmap.org/wiki/WIWOSM) map, OSM web pages, JOSM remote control and [Overpass Turbo](http://overpass-turbo.eu/). OSM objects belonging to the same category can be loaded on a map (downloaded, saved as image, etc...), through another Overpass Turbo link.
* Tools that help to **add tags**:
    * each category has a link to add-tags [service](http://wiki.openstreetmap.org/wiki/JOSM/Plugins/RemoteControl/Add-tags) (from Kolossos), where category name and country bounding box parameters are already filled in
    * a JOSM remote link lets the user zoom to the position of a non tagged article, if Wikipedia knows its position
* **Non-mappable** categories and articles can be added to a blacklist, so that they are not visible in web pages by default (e.g. "Paintings in X Museum").
* a warning icon marks articles **without template** (Coord).

Updated webpages for Italy can be found [here](http://geodati.fmach.it/gfoss_geodata/osm/wtosm/index.html) (thanks to [fmach.it](http://fmach.it) for hosting).

##Development
Author: Simone F. <groppo8@gmail.com>, [OSM Wiki](http://wiki.openstreetmap.org/wiki/User:Groppo/)
Contributors: Luca Delucchi, Cristian Consonni
Code: Python, GPLv3

###Credits and attributions
Services linked from the pages: [WIWOSM](http://wiki.openstreetmap.org/wiki/WIWOSM) (master, Kolossos), [add-tags](http://wiki.openstreetmap.org/wiki/JOSM/Plugins/RemoteControl/Add-tags) (Kolossos), [OverpassTurbo](http://overpass-turbo.eu/) (tyr.asd)

Services used by the program: [CatScan](http://toolserver.org/%7Edaniel/WikiSense/CategoryIntersect.php) (Duesentrieb), MediaWiki [API](https://www.mediawiki.org/wiki/API:Main_page), [Wikipedia coordinates](https://toolserver.org/~kolossos/wp-world/pg-dumps/wp-world), [Nuts4Nuts](http://nuts4nutsrecon.spaziodati.eu/), [quick_intersection](http://tools.wmflabs.org/catscan2/quick_intersection.php) (Magnus Manske)

* themes icons are from [Maki](https://github.com/mapbox/maki), License BSD
* regions icons are from [araldicacivica.it](http://www.araldicacivica.it), License [CC BY-NC-ND 3.0](http://creativecommons.org/licenses/by-nc-nd/3.0/it/)
* nodes, ways, relations and Overpass Turbo icons are from the [OSM Wiki](http://wiki.openstreetmap.org/)

##Overview
Starting from a list of Wikipedia categories, written by the user in the 'config' file, the script:

0. downloads/updates the OSM data (PBF) of a country (from GEOFABRIK)
1. downloads Wikipedia data regarding the selected categories (from catscan), specifically: subcategories names and articles titles
2. parses the OSM file, filtering the [tags](http://wiki.openstreetmap.org/wiki/Wikipedia) accepted by [WIWOSM](https://wiki.openstreetmap.org/wiki/WIWOSM) project
3. creates webpages to show which articles are already tagged and which ones are not, providing links to inspect how the objects have been mapped.

##Requirements
* python-lxml
* osmupdate
* osmconvert
* osmfilter
* wget
* zgrep, cut (if using --show_link_to_wikipedia_coordinates)
* python-requests (if using --infer_coordinates_from_wikipedia)

[osmconvert/update/filter](http://wiki.openstreetmap.org/wiki/Osmconvert) tools (from Marqqs) can be downloaded and installed with:

        sudo wget http://m.m.i24.cc/osmconvert32 -O /usr/bin/osmconvert
        sudo wget http://m.m.i24.cc/osmupdate32 -O /usr/bin/osmupdate
        sudo wget http://m.m.i24.cc/osmfilter32 -O /usr/bin/osmfilter
        sudo chmod +x /usr/bin/osmconvert /usr/bin/osmupdate /usr/bin/osmfilter
    
On 64 bit system install 'ia32-libs' package to execute the previous 32 bit programs.

##Usage

###Fill the config file
Write in './config' file:

* 'osmdir', the directory where you want to download national OSM data
* 'osmbbox', the bbox of the country (it will be used by WIWOSM add-tags tool)
* 'preferred language', Wikipedia lang, for example: 'it'
* 'country', the country name as used in GEOFABRIK repository, for example: 'italy'
* (optional) add a Wikipedia category to the project, by adding its name to an existing theme, or to a new one, in 'themes' section. The script will then download its data (subcategories and articles names) from Wikipedia. To refresh a category, just delete its file in '.data/wikipedia/catscan/theme'.

###Run the script
0. (Optional) Print categories in the project:

        launch_script.py --print_categories_list

1. Download OpenStreetMap data of the country:

        launch_script.py --download_osm
next time, just update the previously downloaded OSM data to the last minute (through osmupdate):

        launch_script.py --update_osm

2. Read Wikipedia data (categories -> subcategories -> articles), search tagged articles in the OSM file and create updated webpages:

        launch_script.py --create_webpages

####Other options
* (Optional) Point 3 + mark on the webpages the articles without Coord template on Wikipedia:

         launch_script.py --show_missing_templates  --create_webpages
        
* (Optional) Point 3 + show JOSM link for zooming to the position of a non already tagged article, known by Wikipedia:

         launch_script.py --show_link_to_wikipedia_coordinates  --create_webpages
       
* (Optional) Point 3 + show JOSM link for zooming to the position of a non already tagged article, whose coordinates have been infered with [Nuts4Nuts](https://github.com/SpazioDati/Nuts4Nuts)(see below for more info)

         launch_script.py --infer_coordinates_from_wikipedia  --create_webpages

##Notes
###Non mappable categories or articles
Add the names of *non mappable* categories or articles (for example "Paintings in the X Museum") to the file './data/wikipedia/non_mappable'. The script will set them as invisible in webpages.

If you need to add many names to 'non_mappable' file, set the option 'clickable_cells = true' in config file and create webpages again.<br>Now, by clicking on tables cells, a string of names will be automatically created on top of the page, ready to be copied and pasted to './data/wikipedia/non_mappable' file.

###Infer coordinates with Nuts4Nuts
The first time the script is run with the option -n it infers the coordinates of Wikipedia articles without a geographic position. The coordinates are saved to the file 'data/nuts4nuts/nuts4nuts_LANG_coords.txt'. Since this can take a long time it is better to create the file on its own, by running 'python nuts4nuts_infer.py'. This script can be interrupted to scan more articles a little at a time.

###Workarounds
####Tagged articles not detected by the script
If the the script does not correctly detect a tag in the OSM file, add the article name and OSM objects ids to './data/workaround/tagged.csv' (and fix the parser ;-)

####False positive errors
If the the script flag as error a tag which is considered correct (strange tags), add the tag to the file './data/workaround/false_positive.csv' and the tag will not be flagged as error again.

##Debugging
For debugging purpose, categories trees can be print to text files, by setting 'print categories to text files = true' option in the config file.