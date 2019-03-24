schtasks /create /tn "SpotifySubcriber Feed Updater onstart" /tr %~dp0\update.exe /sc ONSTART
# note: requires administrator permission.