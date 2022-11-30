from concurrent.futures import thread
import requests
import ZHOR_Modules.nicePrints as np
import ZHOR_Modules.listUtils as lu
import threading
import os
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

from urllib.parse import urlparse

LOCK = threading.Lock()

DOWNLOAD_FOLDER = "TO-BE-SET"

# imposta il nome della dl folder in base all'url
# https://stackoverflow.com/questions/9626535/get-protocol-host-name-from-url
def setDLFolder(urlStr: str):
    global DOWNLOAD_FOLDER

    #parsed_uri = urlparse('http://stackoverflow.com/questions/1234567/blah-blah-blah-blah' )
    parsed_uri = urlparse(urlStr)
    result = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
    np.debugPrint(result)

    DOWNLOAD_FOLDER = result.replace("/","_").replace(".","_").replace(":","_")
    os.system("mkdir " + DOWNLOAD_FOLDER)

# scarica tutti i file presenti dalla lista di link in input
def downloadFiles(filesList: list):
    for item in filesList:
        name = item.split('/')[-1]

        LOCK.acquire()
        np.infoPrint("Download in corso di " + str(item))
        LOCK.release()
        
        r = requests.get(str(item),verify=False)
        open(DOWNLOAD_FOLDER + "/" + name,'wb').write(r.content)

# scarica tutti i file presenti dalla lista di link in input (MULTI THREAD)
def downloadFiles_mt(filesList: list,threadCount: int):

    sublists = lu.splitList(filesList,threadCount)

    threadList = []
    for i in range(0,threadCount):
        argument = sublists[i]
        t = threading.Thread(target=downloadFiles,args=(sublists[i],))
        threadList.append(t)

    for thread in threadList:
        thread.start()
    


# data una lista di file restituisce un'altra lista contenente solo i file che rispettano quel formato
def filterListByExtention(filesList: list, extention: str):
    filteredList = []

    # esempio: .avi = 4 ---> -4
    extStartIndex = len(extention) * -1

    for item in filesList:
        if item[extStartIndex:] in extention:
            filteredList.append(item)

    return filteredList

# v2: valuta solo la presenza di .ABC (dove .ABC è una qualsiasi estensione) nella stringa
# del link 
def filterListByExtention_v2(filesList: list, extension: str):
    filteredList = []


    for item in filesList:
        if '.' + extension in item:
            filteredList.append(item)

    return filteredList

# v3: valuta la presenza di .ABC (dove .ABC è una qualsiasi estensione) nella stringa del 
# link, e successivamente spezza in corrispondenza dell'estensione in maniera da eliminare qualsiasi informazione
# successiva ad esso (probabilmente inutile)
# es: www.sito.it/immagine.png?blablabla ---> www.sito.it/immagine.png
def filterListByExtention_v3(filesList: list, extension: str):
    filteredList = []

    dotExt = '.' + extension

    for item in filesList:
        if '.' + extension in item:
            i = item.split(dotExt)[0] + dotExt
            filteredList.append(i)

    return filteredList


#rimuove tutti i duplicati
def removeDuplicates(inputList: list):
    temp = list(dict.fromkeys(inputList))
    return temp