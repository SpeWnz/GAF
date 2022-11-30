from selenium import webdriver
from selenium.webdriver.firefox.options import Options

import json
import os
import sys
import argparse
import requests
import ZHOR_Modules.nicePrints as np
import ZHOR_Modules.listUtils as lu
import ZHOR_Modules.progressBar as pb
import ZHOR_Modules.osUtils as OU
import ZHOR_Modules.fileManager as fm

import FUNCTIONS
# =========================================================================================================================================================
# VARIABILI GLOBALI E FUNZIONI

_Options = Options()
_Options.headless = not np.DEBUG

totalFilesList = [] #serve per il log


# =========================================================================================================================================================
# ROBA ARGPARSE

parser = argparse.ArgumentParser(description='Grab All the Files (GAF) v1')
REQUIRED_ARGUMENTS = parser.add_argument_group("Argomenti necessari")
OPTIONAL_ARGUMENTS = parser.add_argument_group("Argomenti opzionali")


# === Argomenti necessari ===
REQUIRED_ARGUMENTS.add_argument('-u', metavar='\"URL\"', type=str, required=True, help='Url della pagina')


# === Argomenti opzionali ===
OPTIONAL_ARGUMENTS.add_argument('-e', metavar='\"ESTENSIONE\"',type=str, help='Estensione/i dei file da cercare (senza il punto). ES: "pdf", oppure "pdf,jpg,txt". Specificare una o più estensioni comporta ignorare il file di configurazione')
OPTIONAL_ARGUMENTS.add_argument('-f',metavar='\"TEXT FILTER\"',type=str, help='Filtro testo. Cerca solo i file contenenti una certa sottostringa.')
OPTIONAL_ARGUMENTS.add_argument('-l',metavar='\"FILE LIST\"',type=str, help='Produce una lista contenente tutti i file trovati. ES: -l "files.txt"')
OPTIONAL_ARGUMENTS.add_argument('-t',metavar='\"THREADS\"',type=int, help='Threads per scaricare in parallelo i file')
OPTIONAL_ARGUMENTS.add_argument('-c',metavar='\"COOKIE STRING\"',type=str, help='Cookie String (presa da burp) (WIP)')
OPTIONAL_ARGUMENTS.add_argument('--any', action='store_true', help='Trova qualsiasi estensione (ignora l\'opzione -e)')
OPTIONAL_ARGUMENTS.add_argument('--dl', action='store_true', help='Scarica i file trovati')
OPTIONAL_ARGUMENTS.add_argument('--unminify', action='store_true', help='Unminify dei file (js e css) (WIP)')
OPTIONAL_ARGUMENTS.add_argument('--debug', action='store_true', help='Modalità debug')
#OPTIONAL_ARGUMENTS.add_argument('--qualcosAltro', action='store_true', help='Descrizione del secondo flag opzionale')


args = parser.parse_args()

# =========================================================================================================================================================
# MAIN 

OU.clear()

JSON_CONFIG_FILE = 'defaultConfig.json'
URL = args.u
ext = args.e
substring = args.f
DL = False

MAKE_LOG = False
LOG_PATH = None
ANY_EXTENTION = False

np.DEBUG = args.debug
if(np.DEBUG):
    np.debugPrint("INPUT:")
    print(" URL",URL,"\n ext",ext,"\n substring",substring,"\n DL",DL)

# verifica se --DL viene specificato
if("--dl" in sys.argv):
    DL = True

# verifica se -e sta insieme ad --any
if ("-e" in sys.argv and "--any" in sys.argv):
    np.errorPrint("Sono stati specificati due campi mutualmente esclusivi: -e & --any")
    exit()


# verifica se -e viene specificato
if ("-e" not in sys.argv):
    np.infoPrint("Non è stato specificato un set di estensioni. Procedo con le estensioni specificate nel file " + JSON_CONFIG_FILE)

# verifica se -l viene specificato
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

np.infoPrint("Avvio webdriver ... ")
browser = webdriver.Firefox(options=_Options,executable_path=configData['webdriverPath'])       #webdriver path

if(ext is None):
    targetExtensions = configData['extensions'].split(',')                                      #estensioni da cercare
else:
    targetExtensions = ext.split(',') 

np.infoPrint("Navigo sull'url ... ")
browser.get(URL)

np.infoPrint("Ottengo tags ... ")
targetTags = []
for tag in configData['targetTags'].split(','):
    targetTags += browser.find_elements_by_tag_name(tag)


# ========================================================================================

# ottieni tutti href non filtrati
hrefList = []
for item in targetTags:
    href = item.get_attribute('href')
    if href is not None:
        hrefList.append(href)

# ottieni tutti gli src non filtrati
for item in targetTags:
    src = item.get_attribute('src')
    if src is not None:
        hrefList.append(src)


np.infoPrint("Fatto. Filtro le tag in base alle estensioni specificate. \n\n\n")



if(ANY_EXTENTION):
    totalFilesList = FUNCTIONS.removeDuplicates(hrefList)
    np.infoPrint("Sono presenti i seguenti file: ")
    lu.fancyPrint(totalFilesList)
else:

    # ottieni gli href filtrati (per ogni estensione) se necessario
    for extension in targetExtensions:

        filteredList = FUNCTIONS.removeDuplicates(FUNCTIONS.filterListByExtention_v2(hrefList,extension))

        totalFilesList += filteredList

        if(len(filteredList) == 0):
            np.infoPrint("Non sono presenti file {}.".format(extension))
        else:
            np.infoPrint("Sono presenti i seguenti file {}: ".format(extension))
            lu.fancyPrint(filteredList)
            print("\n")

        
# scarica i file se necessario
if(DL is True):

    print("\n\n\n")
    np.infoPrint("Procedo con il download dei file trovati. \n\n")

    FUNCTIONS.setDLFolder(URL)

    if("-t" in sys.argv):
        FUNCTIONS.downloadFiles_mt(totalFilesList,int(args.t))
    else:
        FUNCTIONS.downloadFiles(totalFilesList)


# scrivi log se necessario
if(MAKE_LOG):
    np.debugPrint("Scrivo log ... ")
    fm.listToFile(totalFilesList,LOG_PATH)
    np.debugPrint("Log scritto")