# Description
WIP

SpotifySubscriber feed tool. Allows you to subscribe to Spotify playlists, and creates a subscription feed playlist. Whenever any of the subscribed playlists changes, the new songs are added to the subscription feed.

The program can be either run from source using Python, or independently using a set of Windows executables (no additional installations required). See the sections below for instructions.

# Instructions
## <a name="windows_executables"></a> Using the Windows executables
TODO: provide instructions with images.

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
Where USERNAME should be replaced with your own Spotify username. This will open your browser and prompt you to login to the Spotify access terminal. You will then be redirected to a page that cannot be reached (http://localhost/code=?). **You must copy this URL into the terminal from which you executed the script!**
After entering the URL in the terminal, it should print a message about the subscription feed it has created.

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

# Roadmap
There are many improvements that need to be made:
- The Windows executables need clear instructions with images for less technical users, and should be tested on different devices.
- A GUI is necessary, because using three python scripts / executables is cumbersome.
- Instead of having to schedule the update task manually, the code should register this task itself.
- Before adding new songs to the subscription feed, they should be compared to the feed history such that a song will never appear in the subscription feed twice. Currently, update_feed only filters duplicate tracks within the same update.
- Extending on the above, the feed could also filter songs that are already in any of the user's playlists or song library.