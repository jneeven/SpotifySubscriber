# Description
SpotifySubscriber feed tool. Allows you to subscribe to Spotify playlists, and creates a subscription feed playlist. Whenever any of the subscribed playlists changes, the new songs are added to the subscription feed.

The program can be either run from source using Python, or independently using a set of Windows executables (no additional installations required). See the sections below for instructions.

# Instructions
## Running from source
To run the source code yourself, you first need to [register a new app in Spotify](https://developer.spotify.com/dashboard/applications).

After doing this, create a file called `client_data.json` in the src folder with the following structure:
```JSON
{
    "client_secret": "YOUR_CLIENT_SECRET",
    "client_id": "YOUR_CLIENT_ID"
}
```

To create a subscription feed, run the following command:
```bash
python src/init.py USERNAME
```
Where USERNAME should be replaced with your own Spotify username

### Subscribing to and unsubscribing from playlists
After creating a subscription feed, you can subscribe to a playlist with the following command:
```bash
python src/subscribe.py "PART_OF_PLAYLIST_NAME"
```
Where `PART_OF_PLAYLIST_NAME` is the (part) of the playlist name you want to subscribe to. Note: you can only subscribe to playlist that you actually follow on Spotify. For example: 
```bash
python src/subscribe.py "release"
``` 
will subscribe to all followed playlists with 'release' in their name, for example the Release Radar.


To unsubscribe from a playlist, simply run the same command with the `--unsubscribe` option:
```bash
python src/subscribe.py --unsubscribe "PART_OF_PLAYLIST_NAME"
```

### Updating the feed
To update the subscription feed (i.e. check for new tracks in your subscribed playlists), simply run the following command:
```bash
python src/update.py
```

Since you don't want to have to do this manually every time, I suggest creating a task for it in the Task Scheduler (Windows) or creating a crontab scheduled task for it (Linux). For more information about scheduling the updater as a Windows task, see [Using the Windows executables](#windows_executables).

## <a name="windows_executables"></a> Using the Windows executables

