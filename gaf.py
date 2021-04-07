import os
import requests
import sys
import argparse
import platform
import ZHOR_Modules.fileManager as fm
import ZHOR_Modules.nicePrints as np
import ZHOR_Modules.listUtils as lu
import ZHOR_Modules.progressBar as pb
# =========================================================================================================================================================
# VARIABILI GLOBALI E FUNZIONI

TEMP_FILE = "temp.html"
np.DEBUG = False

# salva una risposta html in un file
def __saveHtmlToFile(url: str):
    r = requests.get(url)
    
    f = open(TEMP_FILE,'wb')
    f.write(r.content)
    f.close()

'''
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
'''

# data una lista di righe contenenti la sottostringa che rappresenta l'estensione (ad esempio ".pdf")
# filtra ogni riga in maniera da estrarre il nome del file. Restituisice una lista contenente i nomi dei file
def __getFileNames_fromHrefLines(extention: str, searchFilter=None):
    
    # mi salvo le righe di file in cui c'è l'estensione che mi interessa
    lines = fm.fileToSimpleList(TEMP_FILE)
    neededLines = []
    for item in lines:
        if(extention in item):
            neededLines.append(item)

    
    # da quelle righe di file, mi estraggo il nome contenuto in href="nome.ext"
    resourceNames = []
    for item in neededLines:
        f = item.split("\"")
        for string in f:

            #se voglio anche un filtro per il nome del file da cercare, cerco sia l'estensione che il filtro
            if(searchFilter is not None):
                if(extention in string) and (searchFilter in string):
                    resourceNames.append(string)

            #se non voglio alcun filtro, cerco solo l'estensione
            if(searchFilter is None):
                if(extention in string):
                    resourceNames.append(string)

    return resourceNames

# rimuove il file temp.html
def __removeTempFile():
    if("Windows" in platform.system()):
        os.system("del " + TEMP_FILE)
    else:
        os.system("rm " + TEMP_FILE)


# dato un url e un'estensione (ad es ".pdf") restituisce una lista di tutti i nomi dei file
# con quell'estensione presenti su quella pagina
def getFileNames_fromURL(url: str, extention: str, searchFilter=None):
    __saveHtmlToFile(url)    
    return __getFileNames_fromHrefLines(extention)

# restituisce vero se il nome del file contiene una di quelle flag
# falso altrimenti
def isAbsolute(hrefItem: str):
    absoluteFlags = ["http://","https://","ftp://"]
    for flag in absoluteFlags:
        if flag in hrefItem:
            return True

    return False

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

    progressCounter = 0
    total = len(filesList)

    for item in filesList:
        print(pb.percentageAndProgressBar(progressCounter,total),end='\r')

        if(isAbsolute(item)):
            x = item.split("/")[-1]
            r = requests.get(item)

            np.debugPrint("Sto scaricando " + str(item))
            open(x,'wb').write(r.content)
        else:
            np.debugPrint("Sto scaricando " + str(baseUrl + item))
            r = requests.get(str(baseUrl + item))
            open(item,'wb').write(r.content)

        progressCounter += 1

    #necessario per non sminchiare il terminale quando hai finito di scaricare
    print("\n\n")

        


# =========================================================================================================================================================
# ROBA ARGPARSE

parser = argparse.ArgumentParser(description='Grab All the Files (GAF) v1')
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

# clear screen
if("Windows" in platform.system()):
        os.system("cls")
else:
        os.system("clear")


URL = args.u
ext = args.e
substring = args.f
noDL = False

# verifica se --noDL viene specificato
if("--noDL" in sys.argv):
    noDL = True

resourcesList = getFileNames_fromURL(url=URL,extention=ext)

#lu.fancyPrint(resourcesList)


# se ci sono file, mostrali
resourcesCount = len(resourcesList)
if(resourcesCount > 0):
    np.infoPrint("Sulla pagina sono presenti i seguenti file in formato " + ext + ": \n")
    lu.fancyPrint(resourcesList)
    print("\n")

else:   
    np.infoPrint("Non ci sono file di questo formato sulla pagina. \n")


# se viene specificata la flag --noDL, non fare il download
if(noDL):
    if(resourcesCount > 0):
        np.infoPrint("I file non verranno scaricati. \n")
else:
    np.infoPrint("Download dei file in corso...")
    downloadFiles(resourcesList,URL)


# alla fine rimuovi il file html temporaneo
__removeTempFile()
