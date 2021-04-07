import os
import requests
import sys
import argparse
import platform
import ZHOR_Modules.fileManager as fm
import ZHOR_Modules.nicePrints as np

TEMP_FILE = "temp.html"
np.DEBUG = True

# salva una risposta html in un file
def __saveHtmlToFile(url: str):
    r = requests.get(url)
    
    f = open(TEMP_FILE,'wb')
    f.write(r.content)
    f.close()

# dato un file html, trova le righe in cui si trova un href ad un file con estensione di interesse
# NOTA: la variabile "extention" rappresenta l'estensione, e deve essere scritta in questo modo:
# ".pdf", ".png", ".zip", ecc...
def __getNeededLines(path: str, extention: str):
    lines = fm.fileToSimpleList(TEMP_FILE)
    neededLines = []
    for item in lines:
        if(extention in item):
            neededLines.append(item)

    return neededLines

# data una lista di righe contenenti 
def __getFileNames_fromNeededLines(neededLines: list,extention: str):
    resourceNames = []
    for item in neededLines:
        f = item.split("\"")
        for string in f:
            if(extention in string):
                resourceNames.append(string)

    return resourceNames

# rimuove il file temp.html
def __removeTempFile():
    if("Windows" in platform.system()):
        os.system("del " + TEMP_FILE)
    else:
        os.system("rm " + TEMP_FILE)


# ottiene la lista dei file presenti sulla pagina web
def getFileNames_fromURL(url: str, extention: str, searchFilter=None):
    __saveHtmlToFile(url)    
    return __getFileNames_fromNeededLines(__getNeededLines(TEMP_FILE,extention),extention)

# dato un url completo con tanto di pagina .html, restituisce tutto l'url tranne il nome della pagina html
# quindi ad esempio:
# http://www.mat.uniroma2.it/~guala/ASDL_2017.htm
# diventa
# http://www.mat.uniroma2.it/~guala/ 
def getBaseLocationURL(url: str):
    parts = url.split("/")

    # crea http://www.sito.com
    result = parts[0] + "/" + parts[1] + "/"

    for i in range(2,len(parts)-1):
        result += parts[i] + "/"

    return result


# scarica tutti i file presenti su un url
def downloadFiles(filesList: list, url: str):
    baseUrl = getBaseLocationURL(url)

    for item in filesList:
        np.debugPrint("Sto scaricando " + str(baseUrl + item))
        r = requests.get(baseUrl + item)
        open(item,'wb').write(r.content)
        


# =========================================================================================================================================================
# ROBA ARGPARSE

parser = argparse.ArgumentParser(description='Get All the Files (GAF) v1')
REQUIRED_ARGUMENTS = parser.add_argument_group("Argomenti necessari")
OPTIONAL_ARGUMENTS = parser.add_argument_group("Argomenti opzionali")


# === Argomenti necessari ===
REQUIRED_ARGUMENTS.add_argument('-u', metavar='\"URL\"', type=str, required=True, help='Url della pagina')
REQUIRED_ARGUMENTS.add_argument('-e', metavar='\"ESTENSIONE\"',type=str, required=True, help='Estensione dei file da cercare')

# === Argomenti opzionali ===
OPTIONAL_ARGUMENTS.add_argument('-f',metavar='\"TEXT FILTER\"',type=str, help='Filtro testo. Cerca solo i file contenenti una certa sottostringa.')
OPTIONAL_ARGUMENTS.add_argument('--noDL', action='store_true', help='Non scarica i file. Stampa solo le informazioni relative.')
#OPTIONAL_ARGUMENTS.add_argument('--qualcosAltro', action='store_true', help='Descrizione del secondo flag opzionale')


args = parser.parse_args()

# =========================================================================================================================================================
# MAIN 
URL = args.u
ext = args.e
substring = args.f
noDL = False

# verifica se --noDL viene specificato
if("--noDL" in sys.argv):
    noDL = True

resourcesList = getFileNames_fromURL(url=URL,extention=ext)

# se ci sono file, mostrali
resourcesCount = len(resourcesList)
if(resourcesCount> 0):
    np.infoPrint("Sulla pagina sono presenti i seguenti file in formato " + ext + ": \n")
    
    for i in range(0,resourcesCount):
        print(i+1, "\t",resourcesList[i])

    print("\n")

else:   
    np.infoPrint("Non ci sono file di questo formato sulla pagina. \n")

if(noDL):
    if(resourcesCount > 0):
        np.infoPrint("I file non verranno scaricati. \n")
else:
    np.infoPrint("Download dei file in corso...")
    downloadFiles(resourcesList,URL)


__removeTempFile()