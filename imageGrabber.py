import os,argparse,json,ssl,shutil,threading,sys
from collections import defaultdict
import subprocess

try :
    from bs4 import BeautifulSoup
    import urllib.request
    import tqdm
except ImportError:
    subprocess.call(['pip3', 'install', 'tqdm','urllib3'])
    from bs4 import BeautifulSoup
    import urllib.request
    import tqdm

config = {}
imageDir = "Downloads"
actualImages,threads=[],[]
exceptions=defaultdict(list)
header={'User-Agent':"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.134 Safari/537.36"
}



#configuring ssl certificate verification
if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
    getattr(ssl, '_create_unverified_context', None)):
    ssl._create_default_https_context = ssl._create_unverified_context


def get_soup(url,header):
    return BeautifulSoup(urllib.request.urlopen(urllib.request.Request(url,headers=header)),'html.parser')

def parseArg():

    parser = argparse.ArgumentParser()

    threadedParser = parser.add_mutually_exclusive_group(required=False)
    threadedParser.add_argument('--thread', help="enables multithreaded downloads(Default)",dest='threaded', action='store_true')
    threadedParser.add_argument('--no-thread', help="disables multithreaded downloads",dest='threaded', action='store_false')
    threadedParser.set_defaults(threaded=True)

    errorParser = parser.add_mutually_exclusive_group(required=False)
    errorParser.add_argument('--showerrors', help ="delete existing images under query",dest='showErrors', action='store_true')
    errorParser.set_defaults(overWrite=False)


    parser.add_argument("-q","--query",help="images to search",dest="query",type=str,default = '')

    parsed = parser.parse_args()

    config['threaded'] = parsed.threaded
    config['showErrors'] = parsed.showErrors
    config['query'] = parsed.query if parsed.query != '' else input("Enter image query: ")

def handleFS():
    global imageDir,config
    query = config['query']
    if not os.path.exists(imageDir):
        os.mkdir(imageDir)
    imageDir = os.path.join(imageDir,query.split()[0])
    if not os.path.exists(imageDir):
        os.mkdir(imageDir)
    else:
        shutil.rmtree(imageDir,ignore_errors = True)
        print("Cleaning up..")
        os.mkdir(imageDir)

def getImageList():
    global config,actualImages,header
    query = config['query']
    url="https://www.google.co.in/search?q="+query+"&source=lnms&tbm=isch"
    soup = get_soup(url,header)
    for a in soup.find_all("div",{"class":"rg_meta"}):
        link, Type = json.loads(a.text)["ou"],json.loads(a.text)["ity"]
        actualImages.append((link,Type))
    print("Saving images to: .Downloads > "+query.split()[0])
    header = urllib.parse.urlencode(header)
    header = header.encode('ascii')


def handleThreads():
    global config
    if config["threaded"]:
        imagesPerThread = 20
        for i in range (0,5):
            t = threading.Thread(target = getImages,args = (imagesPerThread*i,imagesPerThread*(i+1)-1,i))
            t.start()
            threads.append(t)
    else:
        getImages(0,99)


def getImages(start,stop,num):
    global header,imageDir,config,exceptions
    image_type="image"
    cntr = start
    for i,(img,Type) in enumerate(tqdm.tqdm(actualImages[start:stop],desc ="thread "+str(num+1),leave = True)):
        try:
            req = urllib.request.Request(img,headers = {'User-Agent': header})
            raw_img = urllib.request.urlopen(req).read()
            cntr += 1
            # print (cntr)
            if len(Type)==0:
                f = open(os.path.join(imageDir,image_type+"_"+str(cntr)+".jpg"),'wb')
            else:
                f = open(os.path.join(imageDir,image_type+"_"+str(cntr)+"."+Type),'wb')
                f.write(raw_img)
                f.close()
        except Exception as e:
                exceptions[e].append(img)
    print("\n",flush = True)

def main():
    parseArg()
    handleFS()
    getImageList()
    handleThreads()
    for x in threads:
        x.join()
    print('\x1b[6;30;42m' + 'done gathering!' + '\x1b[0m\n')
    if config['showErrors']:
        print(exceptions)

if __name__ == "__main__":
    main()
