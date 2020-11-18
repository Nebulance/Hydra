# -*- coding: utf-8 -*-

__VERSION__ = "3.0.0"

import argparse
import re
import os
import errno
import subprocess
from pprint import pprint
import rarfile
import urllib
import bencode3 as bencode
import requests
from bs4 import BeautifulSoup

# Local imports
import config
import btmetafile
import releaseregex


def mkdir(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

# NBL Update resume.log for failed uploads
def logResume(reason, path):
    with open(config.resumeLog, "a") as text_file:
        print("log" + reason + " " + path)
        text_file.write("{0} {1}\n".format(path, reason))

def extractRarArchives(path):
    destFolder = path
    if os.path.isfile(path) and os.path.splitext(path)[1] == ".rar":
        print("archive needs to be unrared")
        destFolder = os.path.join(os.path.dirname(path), os.path.splitext(path)[0])
        with rarfile.RarFile(path) as rf:
            rarFiles = rf.namelist()
            for outFile in rarFiles:
                if isWantedFile(outFile):
                    rf.extract(outFile, destFolder)
    elif os.path.isdir(path):
        for root, dirNames, fileNames in os.walk(path):
            for originalFile in sorted(fileNames):
                # Special case for .part###.rar files
                # TODO: Add propper handling for extension with .part[].rar
                if os.path.splitext(originalFile)[1] == ".rar" and \
                   os.path.splitext(os.path.splitext(originalFile)[0])[1] == ".part001":
                    print("RAR PART detected: " + originalFile)
                    with rarfile.RarFile(os.path.join(root, originalFile)) as rf:
                        rarFiles = rf.namelist()
                        for outFile in rarFiles:
                            print("RAR FILE: " + outFile)
                            if isWantedFile(outFile):
                                rf.extract(outFile, destFolder)
                    # Breake after part0001.rar
                    break
                elif os.path.splitext(originalFile)[1] == ".rar":
                    pprint(originalFile)
                    with rarfile.RarFile(os.path.join(root, originalFile)) as rf:
                        rarFiles = rf.namelist()
                        for outFile in rarFiles:
                            print("RAR FILE: " + outFile)
                            if isWantedFile(outFile):
                                rf.extract(outFile, destFolder)
    # Return original file handle if fail or no rar archives
    return destFolder

def isWantedFile(file):
    #print("??? FILE: "+file)
    wanted = True
    if not config.keepSamples and \
       re.search(r"((^|\/)[^a-z0-9]?sample(\/|\-)|(^|[^a-z0-9])sample\.[a-z0-9]+$)",
                     file, re.IGNORECASE):
        print("sample")
        wanted = False
    if len(config.includeFileTypes) > 0 and \
       os.path.splitext(file)[1] not in config.includeFileTypes:
        wanted = False
    if len(config.excludeFileTypes) > 0 and \
       os.path.splitext(file)[1] in config.excludeFileTypes:
        wanted = False
    return wanted

def getMediainfo(path):
    try:
        # Change dir to source file for media info to run without disclosing the path
        cwd = os.getcwd()
        file_dir = os.path.dirname(path)
        file_basename = os.path.basename(path)
        os.chdir(file_dir)
        if os.name == "nt":
            mediainfo = subprocess.Popen([r"mediainfo", file_basename], shell=True, stdout=subprocess.PIPE).communicate()[0]
        else:
            mediainfo = subprocess.Popen([r"mediainfo", file_basename], stdout=subprocess.PIPE).communicate()[0]
        os.chdir(cwd)
    except OSError:
        sys.stderr.write("Error: Media Info not installed, "
                         "refer to http://mediainfo.sourceforge.net/en for installation")
        exit(1)
    return mediainfo.decode('utf-8')

def detectCategory(releaseName):
    if releaseregex.isStandardEpisode(releaseName) or releaseregex.isDailyEpisode(releaseName):
        return 1
    elif releaseregex.isSeasonPack(releaseName):
        return 3
    else:
        raise Exception("Couldn't detect upload type for {!r}".format(releaseName))
    return release

def websiteLogin():
    session = requests.Session()
    loginResponse = session.post(config.loginUrl,
                                 data={"username": config.username,
                                       "password": config.password})
    if config.loginCheckText in loginResponse.text:
        print("Login successful!")
        match = re.search(r"authkey=([0-9a-z]+)", loginResponse.text)
        session.cookies["authkey"] = match.group(1)
        return session
    else:
        print("Login failed!")

def uploadTorrent(session, torrentPath, release, originalMediaFiles):
    torrentFilename = os.path.basename(torrentPath)

    formPostFiles = {
        "file_input": (torrentFilename, open(torrentPath, "rb"), 'application/x-bittorrent'),
    }

    # Hardcoded values were copied from Firefox inspector
    formPostValues = {
        "submit"         : "true",
        "auth"           : session.cookies["authkey"],
        "MAX_FILE_SIZE"  : 1048576,
        "category"       : detectCategory(release["title"]),
        "title"          : "",
        "tvmazeid"       : "",
        "genre_tags"     : "---",
        "tags"           : "",
        "image"          : "",  # Banner
        "media"          : release["mediainfo"],
        "mediaclean"     : f"[mediainfo]{release['mediainfo']}[/mediainfo]",
        "fontfont"       : -1,
        "fontsize"       : -1,
        "desc"           : release["mediainfo"],
    }
    print('First request:')
    pprint({**formPostValues, **{"media": "[hidden]", "mediaclean": "[hidden]", "desc": "[hidden]"}})
    r = session.post(config.uploadUrl, files=formPostFiles, data=formPostValues)
    # with open('1.html', 'w') as f:
    #     f.write(r.text)

    msg = parseMessage(r.text)
    if msg:
        print('UPLOAD FORM MESSAGE:', msg)
        if config.dupeMessage in msg:
            print("DUPE DETECTED")
        elif config.possibleDupeMessage in msg:
            possibleDupes = parsePossibleDupes(r.text)
            print(f'REPORTED DUPES: {possibleDupes} FILES: {originalMediaFiles}')
            print("IGNORING DUPES")
            formPostValues["ignoredupes"] = 1
            formPostValues["tempfileid"] = parseTempfileid(r.text)
            formPostValues["tempfilename"] = parseTempfilename(r.text)
            pprint({**formPostValues, **{"media": "[hidden]", "mediaclean": "[hidden]", "desc": "[hidden]"}})
            r = session.post(config.uploadUrl, files=formPostFiles, data=formPostValues)
            # with open('2.html', 'w') as f:
            #     f.write(r.text)

    downloadLink = parseDownloadLink(r.text)
    if downloadLink:
        print("NBL UPLOAD SUCCEEDED")
        print(f"TITLE: {parseTitle(r.text)}")
        print(f"TORRENT PAGE: {r.url}")
        print(f"TORRENT FILE: {downloadLink}")
    else:
        print("NBL UPLOAD FAILED")
        logResume("FAIL", torrentPath)
        with open('error.html', 'w') as f:
            f.write(r.text)
        print('See error.html.')

def parseMessage(html):
    elem = BeautifulSoup(html, 'html.parser').find(id='messagebar')
    if elem:
        return elem.string or ""

def parsePossibleDupes(html):
    elem = BeautifulSoup(html, 'html.parser').find(id='upload_table')
    if elem:
        regex = re.compile(r'(\d+)\s+possible\s+dupes?', re.IGNORECASE)
        for string in elem.strings:
            match = regex.search(string)
            if match:
                return int(match.group(1))
    return 0

def parseTempfileid(html):
    elem = BeautifulSoup(html, 'html.parser').find("input", {"name": "tempfileid"})
    if elem:
        return elem.get("value", "")
    return ""

def parseTempfilename(html):
    elem = BeautifulSoup(html, 'html.parser').find("input", {"name": "tempfilename"})
    if elem:
        return elem.get("value", "")
    return ""

def parseTitle(html):
    elem = BeautifulSoup(html, 'html.parser').find('div', id="content")
    if elem:
        return "".join(list(elem.strings)[0:5]).strip()
    return ""

def parseDownloadLink(html):
    elem = BeautifulSoup(html, 'html.parser').find('a', {'title': 'Download'})
    if elem:
        path = elem.get('href')
        if path:
            url = urllib.parse.urlparse(config.uploadUrl)
            return f'{url.scheme}://{url.netloc}/{path}'
    else:
        return ""

if __name__ == "__main__":
    release = {}

    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--resume", action="store_true", help="Resume failed uploads")
    parser.add_argument("-u", "--upload", action="store_true", help="Upload the torrent to NBL")
    parser.add_argument("-f", "--force", action="store_true", help="Overwrite file collisions instead of failing")
    parser.add_argument("path", help="Path to the file or folder containing files to be uploaded")
    args = parser.parse_args()

    # If we're uploading to NBL (-u tag)
    if args.resume:
        print("+++ RESUME " + config.resumeLog)
        exit(1)

    # First, handle rar archives
    if config.extractRarArchives:
        print("+++ RAR: "+ args.path)
        workingPath = extractRarArchives(args.path)
    else:
        print("+++ PATH: "+ args.path)
        workingPath = args.path

    # Detect which files we want to upload
    originalMediaFiles = []
    if os.path.isfile(workingPath) and isWantedFile(workingPath):
        release["title"] = os.path.splitext(os.path.basename(workingPath))[0]
        originalMediaFiles.append(os.path.abspath(workingPath))
    # if workingPath is a file but not a media file
    elif os.path.isfile(workingPath):
        print("File handle provided is not a media file! (%s)" % workingPath)
        exit(1)
    elif os.path.isdir(workingPath):
        release["title"] = os.path.basename(os.path.normpath(workingPath))
        #print("DIR releaseName: %s" % releaseName)
        for root, dirNames, fileNames in os.walk(workingPath):
            for fileName in fileNames:
                originalFile = os.path.join(root, fileName)
                if isWantedFile(originalFile):
                    print("+++ FILE: "+originalFile)
                    originalMediaFiles.append(os.path.abspath(originalFile))
    # if args.path is neither a file or folder
    else:
        print("invalid path: %s" % workingPath)
        exit(1)

    # Link media files into config.uploadsDirTmp, set buildTmpPath
    buildTmpPath = ""
    # Mediafiles to upload
    originalMediaFiles = sorted(originalMediaFiles)
    if len(originalMediaFiles) == 0:
        print("ERROR: No media files detected!")
        exit(1)
    elif len(originalMediaFiles) == 1:
        print("+++ MODE: Single file")
        # If we have a single file in a movie dir, keep the dir
        # We want to keep movie folders because scene tends to fuck their filenames up
        if os.path.isdir(workingPath): # Special case when this is a tvSeries episode but the exclude list will return a single
            print("--- AUTO: Single file in directory")
            destDir = os.path.basename(os.path.normpath(workingPath))
            buildTmpPath = os.path.join(config.uploadsDirTmp, destDir)
            # Make dest directory for NBL and build the destFilename as well
            mkdir(buildTmpPath)
            destFile = os.path.join(buildTmpPath, os.path.basename(originalMediaFiles[0]))
            # Check if destFile exists (and if not make link)
            if os.path.isfile(destFile):
                os.remove(destFile)
            os.symlink(originalMediaFiles[0], destFile)
            # Single file does not require directory to be included
            buildTmpPath = destFile
            # Seed source file check (because we do not include Directory name in single file releases)
            srcFile = os.path.join(config.uploadsDirSrc, os.path.basename(originalMediaFiles[0]))
            if not os.path.isfile(srcFile):
                #print("!!! Symlink fix" + destFile + " # " + srcFile)
                os.symlink(destFile, srcFile)
        else:
            print("--- AUTO: Single file only")
            buildTmpPath = os.path.join(config.uploadsDirTmp, os.path.basename(originalMediaFiles[0]))
            if os.path.isfile(buildTmpPath):
                # NOTE: If DirTmp is not different from DirSrc it will delete the original release
                os.remove(buildTmpPath)
            os.symlink(originalMediaFiles[0], buildTmpPath)
    else:
        print("+++ MODE: Directory")
        buildTmpPath = os.path.join(config.uploadsDirTmp, release["title"])
        mkdir(buildTmpPath)
        #print("!!! SDIR: "+buildTmpPath)
        for originalMediaFile in originalMediaFiles:
            newMediaFile = os.path.join(buildTmpPath, os.path.basename(originalMediaFile))
            if os.path.isfile(newMediaFile):
                # FIX: Bug with os.link/remove correct file!
                os.remove(newMediaFile)
            os.link(originalMediaFile, os.path.join(buildTmpPath, os.path.basename(originalMediaFile)))

    print("+++ NBL buildTmpPath:" + buildTmpPath)

    # Create the .torrent
    torrent = btmetafile.makeTorrent(buildTmpPath,
        private = True,
        announceUrl = config.announceUrl,
        sourceTag = config.torrentSourceTag,
        torrentSavePath = config.standardWatchDir,
        rtorrentResumeSavePath = config.rtorrentWatchDir)
    torrentFile = "%s.torrent" % os.path.basename(buildTmpPath)
    torrentPath = os.path.join(config.standardWatchDir, torrentFile)
    print("+++ NBL torrentPath: " + torrentPath)
    dtorrent = bencode.bdecode(torrent)
    dtorrent["info"]["pieces"] = "[hidden]"
    pprint(dtorrent)

    # Get mediainfo
    release["mediainfo"] = getMediainfo(originalMediaFiles[0])

    # If we're uploading to NBL (-u tag)
    if args.upload:
        print("+++ UPLOAD")

        # Login to the website
        session = websiteLogin()
        if session:
            uploadTorrent(session, torrentPath, release, originalMediaFiles)
        else:
            print("NBL LOGIN FAILED!")
            logResume("POST", torrentPath)
            exit(1)

    exit(0)
