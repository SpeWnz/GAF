from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By

import json
import os
import sys
import argparse
import requests
import time
import ZHOR_Modules.nicePrints as np
import ZHOR_Modules.listUtils as lu
import ZHOR_Modules.progressBar as pb
import ZHOR_Modules.osUtils as OU
import ZHOR_Modules.fileManager as fm
import ZHOR_Modules.argparseUtils as apu
import ZHOR_Modules.cookiesUtils as cookiesUtils

import FUNCTIONS
# =========================================================================================================================================================
# VARIABILI GLOBALI E FUNZIONI



totalFilesList = [] #serve per il log


# =========================================================================================================================================================
# ROBA ARGPARSE

parser = argparse.ArgumentParser(description='Grab All the Files (GAF) v' + FUNCTIONS.PROGRAM_VERSION)
REQUIRED_ARGUMENTS = parser.add_argument_group("Necessary arguments")
OPTIONAL_ARGUMENTS = parser.add_argument_group("Optional arguments")


# === Argomenti necessari ===
REQUIRED_ARGUMENTS.add_argument('-u', metavar='\"URL\"', type=str, required=True, help='Page Url')


# === Argomenti opzionali ===
OPTIONAL_ARGUMENTS.add_argument('-e', metavar='\"EXTENTION\"',type=str, help='Extention/s to look for, without the dot, separated by a comma. Example: "jpg,png". If one or more extentions are specified, the json file will be ignored')
OPTIONAL_ARGUMENTS.add_argument('-f',metavar='\"TEXT FILTER\"',type=str, help='Looks for files and resources with a specific substring')
OPTIONAL_ARGUMENTS.add_argument('-l',metavar='\"FILE LIST\"',type=str, help='Makes a txt list containing all found files')
OPTIONAL_ARGUMENTS.add_argument('-t',metavar='\"THREADS\"',type=int, help='Threads count. Use this to download multiple files at once')
OPTIONAL_ARGUMENTS.add_argument('-c',metavar='\"COOKIE STRING\"',type=str, help='Cookie String. Take this from document.cookie (browser console) or from other programs, such as BurpSuite')
OPTIONAL_ARGUMENTS.add_argument('--any', action='store_true', help='Find any extention (ignores json file and -e option)')
OPTIONAL_ARGUMENTS.add_argument('--dl', action='store_true', help='Download the files')
OPTIONAL_ARGUMENTS.add_argument('--sort', action='store_true', help='Sort files by alfabetical order')
OPTIONAL_ARGUMENTS.add_argument('--unmin', action='store_true', help='Unminify files (js and css)')
OPTIONAL_ARGUMENTS.add_argument('--debug', action='store_true', help='Debug mode')
#OPTIONAL_ARGUMENTS.add_argument('--qualcosAltro', action='store_true', help='Descrizione del secondo flag opzionale')


args = parser.parse_args()

# =========================================================================================================================================================
# MAIN 

OU.clear()
FUNCTIONS.BANNER()

JSON_CONFIG_FILE = 'defaultConfig.json'
URL = args.u
ext = args.e

#substring filter
substring = None
if ("-f" in sys.argv):
    substring = args.f




DL = False

MAKE_LOG = False
LOG_PATH = None
ANY_EXTENTION = False
SORT = False
UNMINIFY = False
COOKIES = False

np.DEBUG = args.debug
if(np.DEBUG):
    np.debugPrint("INPUT:")
    print(" URL",URL,"\n ext",ext,"\n substring",substring,"\n DL",DL)

# verifica se --DL viene specificato
if("--dl" in sys.argv):
    DL = True

# verifica se --sort viene specificato
if ("--sort" in sys.argv):
    SORT = True


# verifica se -e sta insieme ad --any
if(apu.checkMutExArgs(sys.argv,['-e','--any'])):
    exit()
    

#verifica se -c viene specificato
if (args.c is not None):
    FUNCTIONS.COOKIE_DICT = cookiesUtils.cookieStringToDict(args.c)
    COOKIES = True

# verifica se unmin e dl stanno insieme (se viene specificato unmin, dl DEVE essere presente)
if ("--unmin" in sys.argv):
    if (apu.checkMutIncArgs(sys.argv,['--unmin','--dl'],'Mutually inclusive arguments. Can\'t use --unmin without downloading the files: ')):
        exit()
    else:
        UNMINIFY = True



# verifica se -e viene specificato
if (("-e" not in sys.argv) and ("--any" not in sys.argv)):
    np.infoPrint("No extensions were specified. Proceeding with the default ones in " + JSON_CONFIG_FILE)

# verifica se --any viene specificato
if ("--any" in sys.argv):
    ANY_EXTENTION = True



# verifica se -l viene specificato
if ("-l" in sys.argv):
    LOG_PATH = args.l
    MAKE_LOG = True
    np.debugPrint("Log file: " + LOG_PATH)

# ========================= JSON DATA LOADING ============================================

#leggi il file di configurazione json e imposta le varie cose
configData = json.load(open(JSON_CONFIG_FILE,'r',encoding='utf-8'))
_Options = Options()
_Options.headless = not np.DEBUG
_Options.binary_location = configData['firefoxPath']                                            # firefox path (https://stackoverflow.com/questions/65318382/expected-browser-binary-location-but-unable-to-find-binary-in-default-location)
np.infoPrint("Starting webdriver ... ")
browser = webdriver.Firefox(options=_Options,executable_path=configData['webdriverPath'])       # webdriver path

if(ext is None):
    targetExtensions = configData['extensions'].split(',')                                      # estensioni da cercare
else:
    targetExtensions = ext.split(',') 

np.infoPrint("Navigating to the Url ... ")
browser.get(URL)

if (COOKIES):
    np.infoPrint("Setting cookies and re-navigating to the page ...")
    seleniumCookies = cookiesUtils.cookieStringToSelenium(args.c,URL)
    for c in seleniumCookies:
        browser.add_cookie(c)
    
    browser.get(URL)

np.infoPrint("Gathering tags ... ")
targetTags = []
for tag in configData['targetTags'].split(','):
    #targetTags += browser.find_elements_by_tag_name(tag)
    targetTags += browser.find_elements(By.TAG_NAME,tag)


# ========================================================================================

# ottieni tutti href non filtrati
hrefList = []
for item in targetTags:
    
    try:
        href = item.get_attribute('href')
        if href is not None:
            hrefList.append(href)

    except Exception as E:
        np.errorPrint("Couldn't get information from the tag " + str(item))
        if(np.DEBUG):
            print(E)

# ottieni tutti gli src non filtrati
for item in targetTags:
    
    try:
        src = item.get_attribute('src')
        if src is not None:
            hrefList.append(src)

    except Exception as E:
        np.errorPrint("Couldn't get information from the tag " + str(item))
        if(np.DEBUG):
            print(E)


np.infoPrint("Done. Filtering by extensions... \n\n\n")


# rimuovi eventuali duplicati
np.debugPrint("Removing duplicates ...")
hrefList = FUNCTIONS.removeDuplicates(hrefList)

if SORT:
    np.debugPrint("Sorting list ...")
    hrefList = sorted(hrefList)


if(ANY_EXTENTION):    
    totalFilesList = hrefList
    np.infoPrint("The following files were found: ")
    lu.fancyPrint(totalFilesList)
else:
    
    # ottieni gli href filtrati (per ogni estensione) se necessario
    for extension in targetExtensions:

        filteredList = FUNCTIONS.filterListByExtention_v2(hrefList,extension)

        totalFilesList += filteredList

        if(len(filteredList) == 0):
            np.infoPrint("No .{} files were found".format(extension))
        else:
            np.infoPrint("The following .{} were found: ".format(extension))
            lu.fancyPrint(filteredList)
            print("\n")


#filtra per substring se necessario
if substring is not None:
    totalFilesList = FUNCTIONS.filterListBySubstring(totalFilesList,substring)
    np.infoPrint("The following files were found, containing the specified text")
    lu.fancyPrint(totalFilesList)


np.debugPrint("Webdriver job is done, closing ...")
browser.quit()


# scarica i file se necessario
if(DL is True):

    print("\n\n\n")
    np.infoPrint("Downloading the files... \n\n")

    FUNCTIONS.setDLFolder(URL)

    if("-t" in sys.argv):
        FUNCTIONS.downloadFiles_mt(totalFilesList,int(args.t))


        while(FUNCTIONS.THREADS_JOINED is False):
            time.sleep(1)

    else:
        FUNCTIONS.downloadFiles(totalFilesList)

if (UNMINIFY):
    print("\n\n")
    np.infoPrint("Unminifying files...")
    FUNCTIONS.unminifyFiles()

# scrivi log dei file scaricati se necessario
if(MAKE_LOG):
    np.debugPrint("Writing log ... ")
    fm.listToFile(totalFilesList,LOG_PATH)
    np.debugPrint("Done.")
