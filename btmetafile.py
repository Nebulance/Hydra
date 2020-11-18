# -*- coding: utf-8 -*-

import config
import os
import sys
import bencode3 as bencode
from hashlib import sha1, md5
from pprint import pprint
from time import time
import re
import copy

VERSION = "0.4"

def naturalSort(unsortedList):
    """ Sort the given list in the way that humans expect.
    """
    convert = lambda text: int(text) if text.isdigit() else text
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
    unsortedList.sort( key=alphanum_key )
    return unsortedList

def sortFilesNicely(path):
    if os.path.isfile(path):
        return [path]
    files = []
    if not (os.path.isdir(path)):
        print("Bad directory path %s" % path)
        exit(1)
    dirNames = [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
    if len(dirNames) > 0:
        for dirName in naturalSort(dirNames):
            for file in sortFilesNicely(os.path.join(path, dirName)):
                files.append(file)
    fileNames = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
    if len(fileNames) > 0:
        for file in naturalSort(fileNames):
            files.append(os.path.join(path, file))
    return files

def makeTorrent(filesPath, torrentName="", pieceLength=0, private=False,
    announceUrl="", sourceTag="btmetafile.py %s" % VERSION,
    torrentSavePath="", rtorrentResumeSavePath=""):

    totalFileSize = 0
    pieceHashes = []
    curPiece = b""
    torrent = {}
    torrentFiles = []
    topDir = ""

    # Assume basename for torrentName
    if torrentName == "":
        torrentName = os.path.basename(filesPath)
    if os.path.isdir(filesPath):
        topDir = filesPath
    elif os.path.isfile(filesPath):
        topDir = os.path.dirname(filesPath)

    # Get a list of the files in filesPath
    for file in sortFilesNicely(filesPath):
        torrentFiles.append({
            "fsPath": file,
            "path": os.path.relpath(file, topDir).split("/"),
            "length": os.path.getsize(file),
            "mtime": os.path.getmtime(file)
        })
        totalFileSize += os.path.getsize(file)

    # Fail if there are no files selected
    if not len(torrentFiles) > 0:
        print("No files in path %s" % filesPath)
        exit(1)

    # Determine piece size:
    # pieceLength == 0   -> auto
    # pieceLength < 25   -> 2^pieceLength (emulate mktorrent functionality)
    # Otherwise, make sure pieceSize is a power of 2 between 256KB and 16MB
    KB = 2**10
    MB = 2**20
    GB = 2**30
    if pieceLength == 0:
        if totalFileSize >= 8*GB:      # >= 8GB
            pieceLength = 16*MB        #   16MB pieces
        elif totalFileSize >= 4*GB:    # >= 4GB
            pieceLength = 8*MB         #   8MB pieces
        elif totalFileSize >= 2*GB:    # >= 2GB
            pieceLength = 4*MB         #   4MB pieces
        elif totalFileSize >= 1*GB:    # >= 1GB
            pieceLength = 2*MB         #   2MB pieces
        elif totalFileSize >= 512*MB:  # >= 512MB
            pieceLength = 1*MB         #   1MB pieces
        elif totalFileSize >= 256*MB:  # >= 256MB
            pieceLength = 512*KB       #   512KB pieces
        else:                          # < 256MB
            pieceLength = 256*KB       #   256KB pieces
    elif (pieceLength < 25
    and pieceLength > 17):
        pieceLength = 2**pieceLength
    elif (pieceLength < 256*KB
    or pieceLength > 16*MB
    or not ((pieceLength & (pieceLength - 1)) == 0)): # not a power of 2
        print("Invalid piece size (%d); must be a number between 18 and 24 or a power of 2 between 256KB and 16MB" % pieceSize)
        exit(1)

    # Calculate piece hashes and md5 hashes
    for file in torrentFiles:
        print("Hashing %s" % os.path.relpath(file["fsPath"], topDir))
        md5sum = md5()
        file["pieces"] = 0
        with open(file["fsPath"], "rb") as curFile:
            while True:
                chunk = curFile.read(pieceLength-len(curPiece))
                curPiece += chunk
                md5sum.update(chunk)
                file["pieces"] += 1
                if len(curPiece) != pieceLength:
                    file["md5sum"] = md5sum.hexdigest()
                    print("md5sum: %s" % md5sum.hexdigest())
                    break
                pieceHashes.append(sha1(curPiece).digest())
                curPiece = b""
    if curPiece:
        pieceHashes.append(sha1(curPiece).digest())

    # Construct the metadata contained in the torrent
    torrent["announce"] = announceUrl
    torrent["created by"] = "btmetafile.py %s" % VERSION
    torrent["creation date"] = int(time())
    torrent["info"] = {}
    torrent["info"]["piece length"] = pieceLength
    torrent["info"]["pieces"] = b"".join(pieceHashes)
    torrent["info"]["name"] = torrentName
    torrent["info"]["source"] = sourceTag
    if private:
        torrent["info"]["private"] = 1
    if os.path.isdir(filesPath):
        torrent["info"]["files"] = []
        for file in torrentFiles:
            torrent["info"]["files"].append({
                'length': file["length"],
                'path': file["path"],
                'md5sum': file["md5sum"]
            })
    elif os.path.isfile(filesPath):
        torrent["info"]["length"] = totalFileSize
        for file in torrentFiles:
            torrent["info"]["md5sum"] = file["md5sum"]

    # Create the .torrent
    if len(torrentSavePath) == 0:
        torrentSavePath = os.path.join(os.getcwd(), "%s.torrent" % torrentName)
    elif os.path.isdir(torrentSavePath):
        torrentSavePath = os.path.join(torrentSavePath, "%s.torrent" % torrentName)
    with open(torrentSavePath, "wb") as metaFile:
        metaFile.write(bencode.bencode(torrent))

    # Create a separate .resume.torrent if rtorrentResumePath is set
    if len(rtorrentResumeSavePath) > 0:
        if os.path.isdir(rtorrentResumeSavePath):
            rtorrentResumeSavePath = os.path.join(rtorrentResumeSavePath, "%s.resume.torrent" % torrentName)
        resumeTorrent = copy.deepcopy(torrent)
        resumeTorrent["libtorrent_resume"] = {}
        resumeTorrent["libtorrent_resume"]["bitfield"] = len(pieceHashes)
        resumeTorrent["libtorrent_resume"]["files"] = []
        for file in torrentFiles:
            resumeTorrent["libtorrent_resume"]["files"].append({
                "completed": file["pieces"],
                "mtime": int(file["mtime"]),
                "priority": 1
            })
        resumeTorrent["libtorrent_resume"]["uncertain_pieces.timestamp"] = int(time())
        resumeTorrent["rtorrent"] = {}
        resumeTorrent["rtorrent"]["chunks_done"] = len(pieceHashes)
        resumeTorrent["rtorrent"]["chunks_wanted"] = 0
        resumeTorrent["rtorrent"]["complete"] = 1
        resumeTorrent["rtorrent"]["directory"] = topDir
        resumeTorrent["rtorrent"]["hashing"] = 0
        resumeTorrent["rtorrent"]["state"] = 1
        resumeTorrent["rtorrent"]["state_changed"] = int(time())
        resumeTorrent["rtorrent"]["state_counter"] = 1
        resumeTorrent["rtorrent"]["timestamp.finished"] = int(time())
        resumeTorrent["rtorrent"]["timestamp.started"] = int(time())
        with open(rtorrentResumeSavePath, "wb") as metaFile:
            metaFile.write(bencode.bencode(resumeTorrent))

    return bencode.bencode(torrent)


if __name__ == "__main__":
    t = makeTorrent(sys.argv[1], private=True,
        announceUrl=config.announceUrl,
        sourceTag=config.torrentSourceTag)
    decoded = bencode.bdecode(t)
    decoded["info"]["pieces"] = "PIECES"
    pprint(decoded)
    exit(0)
