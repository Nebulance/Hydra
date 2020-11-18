# -*- coding: utf-8 -*-

# Website username
username = ""

# Website password
password = ""

# Torrent passkey
passkey = ""

# Website login url
loginUrl = "https://alastor.nebulance.dev/login.php"

# Text to check if user is logged in
loginCheckText = ">%s</a>" % username

# Torrent upload url
uploadUrl = "https://alastor.nebulance.dev/upload.php"

# Message when a torrent already exists
dupeMessage = "The exact same torrent file already exists on the site!"

# Message when a torrent already exists
possibleDupeMessage = "The torrent contained one or more possible dupes."

# Your personal announce URL
announceUrl = "https://alastor.nebulance.dev/%s/announce" % passkey

# Source tag to add into the infohash of the created .torrent
torrentSourceTag = "NBL"

extractRarArchives = True

keepSamples = False

# Set to [] to keep all files except for excludeFileTypes
includeFileTypes = [
	".mkv",
	".mp4",
	".avi",
	".ts",
	".img"
]

# Only really useful if includeFileTypes is empty
excludeFileTypes = [
	".torrent",
	".rar",
	".sub",
	".nfo"
]

# Directory for source torrents
# (set by installer.sh)
uploadsDirSrc = ""

# Temporary directory to link files into before we create the .torrent
# (set by installer.sh)
uploadsDirTmp = ""

# Where to log failed uploads
# (set by installer.sh)
resumeLog = ""

# Directory to store created torrents in
# If you're using rtorrent, use rtorrentWatchDir instead in order to add resume data
# (set by installer.sh)
standardWatchDir = ""

# Directory to save torrents that have had resume data added to them
# (set by installer.sh)
rtorrentWatchDir = ""
