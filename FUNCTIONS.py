
import requests
import ZHOR_Modules.nicePrints as np
import ZHOR_Modules.listUtils as lu
import threading
import os
import jsbeautifier
import cssbeautifier
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


from urllib.parse import urlparse

LOCK = threading.Lock()

DOWNLOAD_FOLDER = "TO-BE-SET"
COOKIE_DICT = None
THREADS_JOINED = False

PROGRAM_VERSION = "3.0"
def BANNER():
    
    print("\n")
    print("  ██████╗      █████╗     ███████╗")
    print(" ██╔════╝     ██╔══██╗    ██╔════╝")
    print(" ██║  ███╗    ███████║    █████╗")
    print(" ██║   ██║    ██╔══██║    ██╔══╝  ")
    print(" ╚██████╔╝    ██║  ██║    ██║     ")
    print("  ╚═════╝     ╚═╝  ╚═╝    ╚═╝     ","\tVersion:",PROGRAM_VERSION)
    print("\n Grab All (the) Files")
    
    
    print("\n\n\n")

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


def sanitizeName(resourcePath: str):
    outputName = resourcePath.split('/')[-1]

    outputName = outputName.split('?')[0]   #fix per url del tipo www.abc.com/image.jpg?id=123

    #altri fix qui
    # ...


    return outputName

# scarica tutti i file presenti dalla lista di link in input
def downloadFiles(filesList: list):

    #print("COOKIE",COOKIE_DICT)

    for item in filesList:
        name = sanitizeName(item)

        LOCK.acquire()
        np.infoPrint("Downloading " + str(item))
        LOCK.release()

        
        try:

            r = requests.get(str(item),verify=False,cookies=COOKIE_DICT)

            try:
                open(DOWNLOAD_FOLDER + "/" + name,'wb').write(r.content)
            except Exception as E:
                LOCK.acquire()
                np.errorPrint("Couldn't save " + str(item))
                if(np.DEBUG):
                    print(E)
                LOCK.release()
                
        except Exception as E:
            LOCK.acquire()
            np.errorPrint("Couldn't download " + str(item))
            if(np.DEBUG):
                print(E)
            LOCK.release()


        

# scarica tutti i file presenti dalla lista di link in input (MULTI THREAD)
def downloadFiles_mt(filesList: list,threadCount: int):
    global THREADS_JOINED
    THREADS_JOINED = False

    sublists = lu.splitList(filesList,threadCount)

    threadList = []
    for i in range(0,threadCount):
        argument = sublists[i]
        t = threading.Thread(target=downloadFiles,args=(sublists[i],))
        threadList.append(t)

    for thread in threadList:
        thread.start()

    #aspetta che i thread abbiano finito
    LOCK.acquire()
    np.debugPrint('Waiting for threads to finish ...')
    LOCK.release()

    for thread in threadList:
        thread.join()

    THREADS_JOINED = True
    


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

def filterListBySubstring(fileList: list, substring: str):
    
    np.debugPrint("Filtering by substring")
    temp = []
    for item in fileList:
        if substring in item:
            temp.append(item)

    return temp

    


#rimuove tutti i duplicati
def removeDuplicates(inputList: list):
    temp = list(dict.fromkeys(inputList))
    return temp

# ============================================================================================ UNMINIFY

def unminifyFiles():    
    downloadedFiles = os.listdir(DOWNLOAD_FOLDER)

    jsFiles = []
    cssFiles = []
    #controlla se effettivamente ci sono file js e css
    for item in downloadedFiles:
        if (".js" in item[-3:]):
            jsFiles.append(item)

        if (".css" in item[-4:]):
            cssFiles.append(item)

    if(len(jsFiles) is 0):
        print("No Javascript files were fonud.")
    else:
        unminifyJSFiles(jsFiles)

    
    if(len(cssFiles) is 0):
        print("No CSS files were found.")
    else:
        unminifyCSSFiles(cssFiles)

    

def unminifyJSFiles(inputFiles: list):
    
    print("Unminifying Javascript files")

    for item in inputFiles:
            print("Unminifying",item,"...",end='')

            try:
                res = jsbeautifier.beautify_file(DOWNLOAD_FOLDER + "/" + item)
                
                outputPath = DOWNLOAD_FOLDER + "/" +  item + "_UNMINIFIED.js"
                np.debugPrint(outputPath)
                with open(outputPath,'w') as f:
                    f.write(res)

                print("Done.")

            except Exception as E:
                print("")
                np.errorPrint("Couldn't unminify the file {}. Use the debug mode for more information".format(item))
                if(np.DEBUG):
                    print(E)



def unminifyCSSFiles(inputFiles: list):
    
    print("Unminifying CSS files")

    for item in inputFiles:
            print("Unminifying",item,"...",end='')

            try:

                res = cssbeautifier.beautify_file(DOWNLOAD_FOLDER + "/" + item)
                
                outputPath = DOWNLOAD_FOLDER + "/" +  item + "_UNMINIFIED.css"
                np.debugPrint(outputPath)
                with open(outputPath,'w') as f:
                    f.write(res)

                print("Done.")

            except Exception as E:
                print("")
                np.errorPrint("Couldn't unminify the file {}. Use the debug mode for more information".format(item))
                if(np.DEBUG):
                    print(E)