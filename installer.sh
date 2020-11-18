#!/bin/bash

#
# Variables
#
version="1.0.1"

echo -e "Hydra installer v$version\n"

user="$(whoami)"
dir_hydra="$(realpath "$(dirname $0)")"
dir_rt="$HOME/rtorrent"
echo "Hydra directory: $dir_hydra"
echo "rtorrent directory: $dir_rt"

#
# Checks
#

check_mediainfo=`which mediainfo`
if [ ! -f $check_mediainfo ] || [ -z "$check_mediainfo" ] ; then
    echo "ERROR: Failed to find mediainfo binary. Aborting"
    exit 1
fi

#
# Setup hydra env
#

echo "Adding hydra and rtorrent directories"
uploadsDirSrc="$dir_rt/hydra-upload"
uploadsDirTmp="$dir_rt/hydra-upload-tmp"
resumeLog="$HOME/resume.log"
standardWatchDir="$HOME/uploads"
rtorrentWatchDir="$dir_rt/hydra-watch"
mkdir -p "$uploadsDirSrc"
mkdir -p "$uploadsDirTmp"
mkdir -p "$standardWatchDir"
mkdir -p "$rtorrentWatchDir"

file_rt_conf="$HOME/.rtorrent.rc"
if [ ! -f $file_rt_conf ]; then
    echo "ERROR: Cannot find rtorrent config file: $file_rt_conf"
    exit 1
fi

# Backup .rtorrent.rc
file_rt_conf_bkp="$file_rt_conf.bak"
if [[ -e $file_rt_conf_bkp ]] ; then
    i=0
    while [[ -e $file_rt_conf_bkp.$i ]] ; do
        let i++
    done
    echo "Backing up .rtorrent.rc to: $file_rt_conf_bkp.$i"
    cp -f $file_rt_conf $file_rt_conf_bkp.$i
fi

# Check if .rtorrent.rc has hydra2 config loaded
if grep -q "### Hydra v2" "$file_rt_conf";
then
echo "WARNING: Config section for Hydra detected in: $file_rt_conf"
else
echo "Adding Hydra config to $file_rt_conf"
cat <<EOF >> $file_rt_conf

### Hydra v2
# Create a watch directory for torrents created by hydra with a custom download dir and label
schedule = watch_nbl-uploader,5,5,"load.start=${rtorrentWatchDir}/*.torrent,d.set_directory=${uploadsDirSrc},d.set_custom1=Hydra-Upload"

# Checks if a torrent's label is Hydra-Download
system.method.insert = hydra_label_check, simple, "equal=d.get_custom1=,cat=Hydra-Download"

# Method that calls the Hydra python script on the base_path of a torrent
# Stick it in a screen daemon because I can't figure out how to fork it into the background from rtorrent
system.method.insert = hydra_upload, simple, "execute.capture=screen,-L,-d,-m,python,${dir_hydra}/nbl-uploader.py,-u,\$d.get_base_path="

# Whenever a download finishes, run hydra_label_check then hydra_upload
# If hydra_label_check fails it will raise an error, preventing hydra_upload from running.
system.method.set_key = event.download.finished, nbl_download_finished, "branch={\$hydra_label_check=,\$hydra_upload=}"
EOF
fi

echo "Setting up screen"
mkdir -p "$HOME/log"
if grep -q "logfile" "$HOME/.screenrc";
then
echo "WARNING: logfile config line detected in: $HOME/.screenrc"
else
echo "Adding logfile config line to: $HOME/.screenrc"
cat <<EOF >> $HOME/.screenrc
logfile "$HOME/log/screen-%p.log"
EOF
fi

cli_script="$HOME/cli_hydra.sh"
echo "Creating Hydra cli wrapper script: $cli_script"
cat <<EOF > "$cli_script"
#!/bin/bash

if [ -z "\$1" ]
  then
    echo -e "Usage: \n"
    echo -e "\t\$0 /full/path/to/release\n"
else

python3 ${dir_hydra}/nbl-uploader.py -u "\$1"

fi
EOF
chmod +x "$cli_script"

#
# hydra config update
#

file_hydra_cfg="${dir_hydra}/config.py"
echo "Setting up Hydra config values for $file_hydra_cfg"
sed -i "s#uploadsDirSrc =.*#uploadsDirSrc = \"$uploadsDirSrc\"#g" $file_hydra_cfg
sed -i "s#uploadsDirTmp =.*#uploadsDirTmp = \"$uploadsDirTmp\"#g" $file_hydra_cfg
sed -i "s#resumeLog = .*#resumeLog = \"$resumeLog\"#g" $file_hydra_cfg
sed -i "s#standardWatchDir = .*#standardWatchDir = \"$standardWatchDir\"#g" $file_hydra_cfg
sed -i "s#rtorrentWatchDir = .*#rtorrentWatchDir = \"$standardWatchTmp\"#g" $file_hydra_cfg

#
# uninstaller
#

uninstall_script="$HOME/uninstall-hydra.sh"
echo "Creating Hydra uninstall script: $uninstall_script"
cat <<EOF > "$uninstall_script"
#!/bin/bash

pip3 uninstall --yes $(paste -sd\  "${dir_hydra}/requirements.txt")

rm -r "$uploadsDirSrc"
rm -r "$uploadsDirTmp"
rm -r "$resumeLog"
rm -r "$standardWatchDir"
rm -r "$rtorrentWatchDir"
rm -r "$dir_rt"

rm "$cli_script"
rm "$uninstall_script"
EOF
chmod +x "$uninstall_script"

#
# hydra python requirements
#

echo "Installing hydra python requirements"
pip3 install --user -r ${dir_hydra}/requirements.txt

#
# reminders
#

echo "REMINDER: You should check $file_hydra_cfg if you want to modify the NBL login or API credentials"
echo "REMINDER: You should check $file_rt_conf and make sure there's no other triggers running that can conflict with hydra"

