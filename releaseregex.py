# -*- coding: utf-8 -*-

import re

# https://regex101.com/r/gp1qWA/18
# standardEpisodeRegex = r"^(.*?)[ .]((S(eason[ .]?)?(\d{1,4}))?[ .]?(E(pisode[ .]?)?(\d{1,4})[ab]?([-–—]?(E?(pisode[ .]?)?(\d{1,4})[ab]?))*))[ .](.+?)(-([^.]+?))?(\.(mkv|mp4|avi|ts|iso))?(\.torrent)?$"
standardEpisodeRegex = r"[ \.]?(?:(?:S\d{2,})?(?:E\d{2,})+[a-z]?|\d+x\d+)[ \.]?"
standardEpisodeList = [
    "Kings.of.Atlantis.S01E07.The.Hunter.and.the.Hunted.1080p.RED.WEBRip.AAC5.1.VP9-BTW",
    "Girls.S06E09.1080p.WEBRip.x264-MOROSE",
    "Pig.Goat.Banana.Cricket.S02E04.HDTV.x264-W4F",
    "The.Pioneer.Woman.S16E01.All.in.One.720p.FOOD.WEBRip.AAC2.0.x264-AJP69",
    "The.Price.Is.Right.S45E140.WEB.x264-MTV",
    "Inside.S01E04.Inside.Strangeways.720p.HDTV.x264-QPEL.mkv.torrent",
    "Hur.Gor.Djur.S01E03.SWEDiSH.720p.HDTV.x264-CCCAM",
    "Better.Call.Saul.S03E02.720p.NF.WEBRip.DD5.1.x264-ViSUM",
    "GWs.Mord.S01E01.SWEDiSH.720p.HDTV.x264-CCCAM",
    "Long.Island.Medium.S07E09.Panic.Attack.HDTV.x264-NY2.-",
    "Masterchef.UK.S13E16.720p.HDTV.X264-DEADPOOL",
    "Masterchef.UK.S13E16.HDTV.X264-DEADPOOL",
    "Robot.Wars.2016.S02E06.720p.iP.WEBRip.AAC2.0.H.264-RTN.mkv",
    "Time After Time S01E01E02 1080p HDTV x264-DIMENSION",
    "Teen.Titans.Go.S04E07b.BBRAE.Part.2.720p.WEB-DL.AAC2.0.H.264-YFN",
    "WWE.Monday.Night.War.E17.The.Kliq.WEB.H264-RELiANCE",
    "Charlie Brooker's Screenwipe 1x01",
    "1x03 - Our Friends in the Norse" ]

# https://regex101.com/r/zRBZjT/17
dailyEpisodeRegex = r"^(.*?)[ .]((20[01][0-9]|19[5-9][0-9])[ .-](\d{2})[ .-](\d{2}))[ .](.+?)(-([^.]+?))?(\.(mkv|mp4|avi|ts|iso))?(\.torrent)?$"
dailyEpisodeList = [
    "VICE.News.Tonight.2017.04.18.1080p.HBO.WEB-DL.AAC2.0.H.264-monkee",
    "Stephen.Colbert.2017.03.20.1080i.HDTV.DD5.1.MPEG2-CTL",
    "TMZ.on.TV.2017.04.17.WEB.x264-MTV",
    "The.Jump.(2016).2017.04.27.720p.HDTV.x264-NTb",
    "The.Late.Show.with.Stephen.Colbert.2017.04.27.LL.Cool.J.720p.CBS.WEBRip.AAC2.0.x264-RTN",
    "Stephen.Colbert.2017.04.27.LL.Cool.J.720p.HDTV.x264-CROOKS" ]

# https://regex101.com/r/jq2QNr/10
#seasonPackRegex = r"^(.*?)[ .](S(eason[ .]?)?(\d{1,4}))[ .](?!E(pisode[ .]?)?(\d{1,4})[ab]?([-–—]?(E?(pisode[ .]?)?(\d{1,4})[ab]?))*[ .])(.+?)(-([^.]+?))?(\.torrent)?$"
seasonPackRegex = r"[ \.](?:S\d{2,}|Season[ \.]\d+)[ \.]?(?!E\d{2,}|Episode[ \.]\d+)"
seasonPackList = [
    "Turkey.with.Simon.Reeve.S01.720p.iP.WEBRip.AAC2.0.H.264-RTN",
    "Bill Nye Saves the World S01 1080p Netflix WEBRip DD5.1 x264-TrollHD",
    "Dimension.404.S01.720p.WEB-DL.DD5.1.H.264-Coo7",
    "Who.Do.You.Think.You.Are.US.S09.1080p.WEBRip.AAC2.0.x264-BTW",
    "Mad.Jack.the.Pirate.S01.SD.DVDRip.AAC2.0.x264-NG",
    "Sun.Records.S01.1080p.WEBRip.AAC2.0.x264-BTN",
    "Outsiders.2016.S02.720p.HDTV.x264-Scene",
    "Versailles.2015.S02.1080p.BluRay.x264-SH0W"
    "Charlie Brooker's Screenwipe - Season 1" ]

def isStandardEpisode(releaseName):
    return bool(re.search(standardEpisodeRegex, releaseName, re.IGNORECASE))

def isDailyEpisode(releaseName):
    return bool(re.search(dailyEpisodeRegex, releaseName, re.IGNORECASE))

def isSeasonPack(releaseName):
    return bool(re.search(seasonPackRegex, releaseName, re.IGNORECASE))

def testRegex(regex, testList, wantMatch=True):
    success = 0
    fail = 0
    for testStr in testList:
        if re.search(regex, testStr):
            if wantMatch:
                success += 1
            else:
                fail += 1
                print("Incorrect match found on: %s" % testStr, re.IGNORECASE)
        else:
            if wantMatch:
                fail += 1
                print("Match not found on: %s" % testStr, re.IGNORECASE)
            else:
                success += 1
    print("%d success, %d fail" % (success, fail))
    return fail == 0

if __name__ == "__main__":
    import argparse
    from pprint import pprint

    print("Testing standard episode regex:")
    testRegex(standardEpisodeRegex, standardEpisodeList)
    testRegex(standardEpisodeRegex, dailyEpisodeList, False)
    testRegex(standardEpisodeRegex, seasonPackList, False)
    print("Testing daily episode regex:")
    testRegex(dailyEpisodeRegex, standardEpisodeList, False)
    testRegex(dailyEpisodeRegex, dailyEpisodeList)
    testRegex(dailyEpisodeRegex, seasonPackList, False)
    print("Testing season pack regex:")
    testRegex(seasonPackRegex, standardEpisodeList, False)
    testRegex(seasonPackRegex, dailyEpisodeList, False)
    testRegex(seasonPackRegex, seasonPackList)
