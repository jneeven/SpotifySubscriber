import os
import inspect
import numpy as np
import time
import pickle
import json
import itertools
from datetime import datetime
from tqdm import tqdm

from utils import safe_print
from classes import Track, SubscribedPlaylist, SubscriptionFeed

# Note: have built spotipy from source, because the pip version is outdated.
# To install: `pip install git+https://github.com/plamere/spotipy.git --upgrade`
from spotipy import Spotify
import spotipy.util as sp_util


class SpotifySubscriber:
    """
    Main class. Description necessary.

    Default storage dir: ../storage
    """

    def __init__(
        self,
        user_id: str = None,
        storage_dir: str = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "storage"
        ),
    ):
        self.user_id: str = user_id

        # Playlists are stored by ID in dictionaries for quick lookup
        self.user_playlists: dict = {}
        self.followed_playlists: dict = {}
        self.subscribed_playlists: dict = {}

        # This is the playlist in which all new songs will be pushed
        self.subscription_feed: SubscriptionFeed = None

        loaded = False
        save_path = os.path.join(storage_dir, "storage.p")
        # If a save file exists, load it.
        if os.path.isfile(save_path):
            self._load(save_path)
            loaded = True

        # Since we need the user_id, we cannot continue if it was not specified and we did not obtain it from a save file.
        elif user_id is None:
            raise Exception(
                "No save file found and no user_id specified! Please specify user_id."
            )

        # If there is no save file, there may not be a storage directory either
        elif not os.path.isdir(storage_dir):
            os.mkdir(storage_dir)

        # We deliberately set these after loading, so they may be updated if we move the save file to a different location.
        self.storage_dir = storage_dir
        self._save_path = save_path
        self._cache_path = os.path.join(
            self.storage_dir, ".cache-{}".format(self.user_id)
        )
        self._feed_log_path = os.path.join(self.storage_dir, "feed_log.npy")

        # If no save file exists, load the client secret and ID from file so that we can request a token.
        if not loaded:
            self._load_client_secrets()

        # Refresh token and create spotify object
        self.token = self._get_token(self.user_id)
        self.sp = Spotify(auth=self.token)

        # If not loaded from save file, perform initial setup
        if not loaded:
            if self.user_id != "jneeven":
                self._follow_user("jneeven")

            self.subscription_feed = SubscriptionFeed(self.sp, self.user_id)
            self.refresh_user_playlists()
            self._save()

    # Load a token from the cache or request one from the spotify API. Will open the browser to ask for permission if necessary.
    def _get_token(self, username: str):
        """
        Alternatively, I can set these variables using the command line too:
        export SPOTIPY_CLIENT_ID='your-spotify-client-id'
        export SPOTIPY_CLIENT_SECRET='your-spotify-client-secret'
        export SPOTIPY_REDIRECT_URI='your-app-redirect-url'
        """
        scopes = " ".join(
            [
                "user-read-recently-played",
                "user-library-modify",
                "playlist-read-private",
                "playlist-modify-public",
                "playlist-modify-private",
                "user-library-read",
                "playlist-read-collaborative",
                "user-read-playback-state",
                "user-follow-read",
                "user-top-read",
                "user-read-currently-playing",
                "user-follow-modify",
            ]
        )

        token = sp_util.prompt_for_user_token(
            username,
            scopes,
            client_id=self._client_id,
            client_secret=self._client_secret,
            redirect_uri="http://localhost",
            cache_path=self._cache_path,
        )
        return token

    # Load the client secret and ID from client_data.json
    def _load_client_secrets(self):
        data_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "client_data.json"
        )
        if not os.path.isfile(data_path):
            raise FileNotFoundError("client_data.json does not exist in src folder!")

        with open(data_path, "r") as data_file:
            info = json.load(data_file)

        self._client_id = info["client_id"]
        self._client_secret = info["client_secret"]

    # Save the entire object to a storage file
    def _save(self):
        pickle.dump(self, open(self._save_path, "wb"))

    # Load the storage file and overwrite the current object attributes
    def _load(self, save_path: str):
        load_obj = pickle.load(open(save_path, "rb"))

        # Overwrite own attributes with the ones we just loaded
        for attr, val in load_obj.__dict__.items():
            self.__dict__[attr] = val

    # Obtain the playlists the user owns or follows (both private and public)
    def refresh_user_playlists(self):
        self.user_playlists = {}
        self.followed_playlists = {}

        # Only obtains 50 playlists at a time, is API limit
        playlists_data = self.sp.user_playlists(self.user_id)

        while playlists_data:
            for playlist in playlists_data["items"]:
                # If we own a playlist but it's collaborative, we treat it as a followed one since we might be interested in updates.
                if playlist["owner"]["id"] != self.user_id or playlist["collaborative"]:
                    self.followed_playlists[playlist["id"]] = playlist
                else:
                    self.user_playlists[playlist["id"]] = playlist

            # If there were more playlists than we just received, query the next batch
            if playlists_data["next"]:
                playlists_data = self.sp.next(playlists_data)
            else:
                break

    # Subscribe to multiple playlists based on their ID or patterns in their names.
    def subscribe_to_playlists(self, playlist_ids: list = [], contains: list = []):
        new_subscriptions = False

        for playlist_id in playlist_ids:
            if playlist_id not in self.followed_playlists.keys():
                raise Exception(
                    "Cannot subscribe to playlist with id {}. Either the user owns it or does not follow it.".format(
                        playlist_id
                    )
                )

            if playlist_id not in self.subscribed_playlists.keys():
                playlist = self.followed_playlists[playlist_id]
                tracks = self._get_playlist_tracks(playlist["owner"]["id"], playlist_id)
                self.subscribed_playlists[playlist_id] = SubscribedPlaylist(
                    playlist, tracks
                )
                new_subscriptions = True
                safe_print(
                    "Subscribed to playlist {} by {}".format(
                        playlist["name"], playlist["owner"]["id"]
                    )
                )

        # Lowercase pattern matching with the playlist name
        for pattern in contains:
            pattern = pattern.lower()
            for playlist in self.followed_playlists.values():
                if (
                    pattern in playlist["name"].lower()
                    and playlist["id"] not in self.subscribed_playlists.keys()
                ):
                    tracks = self._get_playlist_tracks(
                        playlist["owner"]["id"], playlist["id"]
                    )
                    self.subscribed_playlists[playlist["id"]] = SubscribedPlaylist(
                        playlist, tracks
                    )
                    new_subscriptions = True
                    safe_print(
                        "Subscribed to playlist {} by {}".format(
                            playlist["name"], playlist["owner"]["id"]
                        )
                    )

        # Only save if we actually changed something. TODO: Save these in a separate file.
        if new_subscriptions:
            self._save()

    # Unsubscribe from multiple playlists based on their ID or patterns in their names.
    def unsubscribe_from_playlists(self, playlist_ids: list = [], contains: list = []):
        removed_subscriptions = False

        for playlist_id in playlist_ids:
            if playlist_id not in self.subscribed_playlists.keys():
                raise Exception(
                    "Cannot unsubscribe from playlist with id {}, because the user is not subscripted to it.".format(
                        playlist_id
                    )
                )

            playlist = self.subscribed_playlists[playlist_id]
            removed_subscriptions = True
            safe_print(
                "Unsubscribed from playlist {} by {}".format(
                    playlist.name, playlist.owner_id
                )
            )
            del self.subscribed_playlists[playlist_id]

        # Lowercase pattern matching with the playlist name
        subscribed_playlists = list(self.subscribed_playlists.values())
        for pattern in contains:
            pattern = pattern.lower()
            for playlist in subscribed_playlists:
                if pattern in playlist.name.lower():
                    removed_subscriptions = True
                    safe_print(
                        "Unsubscribed from playlist {} by {}".format(
                            playlist.name, playlist.owner_id
                        )
                    )
                    del self.subscribed_playlists[playlist.id]

        # Only save if we actually changed something. TODO: Save these in a separate file.
        if removed_subscriptions:
            self._save()

    # Print an overview of the playlist the user owns, follows and is subscribed to.
    def print_playlists(self, own=False, follow=False, subscribed=True):
        if own:
            safe_print("Own playlists:")
            for playlist in self.user_playlists.values():
                safe_print(playlist["name"])

        if follow:
            safe_print("\nFollowed playlists:")
            for playlist in self.followed_playlists.values():
                safe_print(playlist["name"], playlist["owner"]["id"])

        if subscribed:
            safe_print("\nCurrently subscribed to the following playlists:")
            for playlist in self.subscribed_playlists.values():
                safe_print(playlist)

        safe_print()

    # Check the subscribed playlists for new songs and add them to the feed list.
    def update_feed(self, add_own=False):
        """
        Add_own denotes whether to add songs that the user added to a playlist themselves.
        This may happen for example in collaborative playlists.
        """

        last_update = self.subscription_feed.last_update

        track_ids = []
        num_added_tracks = 0

        for playlist_id, playlist in self.subscribed_playlists.items():
            # safe_print("Checking playlist {}".format(playlist.name))
            new_tracks, snapshot = self._get_playlist_tracks(
                playlist.owner_id,
                playlist_id,
                min_timestamp=last_update,
                compare_snapshot=playlist.snapshot_id,
                return_snapshot=True,
            )
            # Update the playlist snapshot so that we quickly know if it has changed next time
            playlist.snapshot_id = snapshot

            added = 0
            for track in new_tracks:
                if track.id == None:
                    print(f"Track with id None: {track}")
                if add_own or track.added_by != self.user_id:
                    try:
                        # Only add the track if it wasn't already in the list when we subbed
                        if track.id not in playlist.track_ids.keys():
                            track_ids.append(track.id)
                            # Add the ID to the track ID list so we know not to add it in the future
                            playlist.track_ids[track.id] = datetime.utcnow()
                            added += 1
                    # TODO: correctly upgrade objects if storage consists of SubscribedPlaylists without ID list.
                    except AttributeError:
                        track_ids.append(track.id)
                        added += 1

            if added > 0:
                safe_print(
                    "Obtained {} new tracks from playlist {}!".format(
                        added, playlist.name
                    )
                )

        if len(track_ids) > 0:
            unique_ids = np.unique(track_ids)

            # If a feed log exists, filter all track IDs that have already been added to the feed before.
            if os.path.exists(self._feed_log_path):
                feed_log = pickle.load(open(self._feed_log_path, "rb"))
                filtered_indices = np.where(~np.isin(unique_ids, feed_log["track_ids"]))
                unique_ids = unique_ids[filtered_indices]

            # We can add at most 100 tracks to a playlist in a single request.
            if unique_ids.size <= 100:
                self.sp.user_playlist_add_tracks(
                    self.user_id, self.subscription_feed.id, unique_ids
                )
            else:
                # Split array into near-equal sections that are smaller than 100 tracks
                for id_array in np.array_split(
                    unique_ids, np.ceil(unique_ids.size / 100).astype(int)
                ):
                    self.sp.user_playlist_add_tracks(
                        self.user_id, self.subscription_feed.id, id_array
                    )

            num_added_tracks = unique_ids.size
            self._log_feed_updates(unique_ids)

        # Update the timestamp and save to file
        self.subscription_feed.last_update = datetime.utcnow()
        self._save()

        return num_added_tracks

    # Get all tracks in the specified playlist, added after min_timestamp.
    # If snapshot is provided, ignore playlists of which the snapshot hasn't changed.
    def _get_playlist_tracks(
        self,
        playlist_owner_id: str,
        playlist_id: str,
        min_timestamp: datetime = None,
        compare_snapshot: str = None,
        return_snapshot=False,
    ):
        data = self.sp.user_playlist(
            playlist_owner_id, playlist_id, fields="tracks, snapshot_id"
        )

        return_tracks = []
        if not min_timestamp:
            min_timestamp = datetime.fromtimestamp(0)

        # If the snapshot is still the same, there is nothing interesting for us to see.
        # NOTE: certain playlists like 'Brain Food' seem to have a different snapshot every time.
        if compare_snapshot and data["snapshot_id"] == compare_snapshot:
            # safe_print("Snapshot still the same, ignoring list contents.")
            return [], data["snapshot_id"]

        tracks = data["tracks"]
        while tracks:
            for track in tracks["items"]:
                added_at = track["added_at"]

                # Somehow, it's possible that we receive an empty track. IDK if this is a spotipy bug or what
                if track["track"] is None or track["track"]["id"] is None:
                    print("WARNING: encountered None track! Ignoring.")
                    continue

                timestamp = datetime.strptime(added_at, "%Y-%m-%dT%H:%M:%SZ")
                if timestamp > min_timestamp:
                    return_tracks.append(Track(track, playlist_id))
                    # safe_print("Found track with name {} and timestamp {} ( > {})".format(track_name, timestamp, min_timestamp))

            if tracks["next"]:
                tracks = self.sp.next(tracks)
            else:
                break

        if return_snapshot:
            return return_tracks, data["snapshot_id"]

        return return_tracks

    # Get all tracks from the users library and own playlists (including sub feed).
    def _get_all_user_tracks(self):
        tracks = {}

        self._get_user_library_tracks()

        for playlist_id, playlist in self.user_playlists.items():
            tracks = self._get_playlist_tracks(playlist["owner"]["id"], playlist_id)
            for track in tracks:
                tracks[track.id] = track

    def _get_user_library_tracks(self):
        tracks = {}

        data = self.sp.current_user_saved_tracks()

        while data:
            for track in data["items"]:
                print(track["track"].keys())
            exit(0)
            exit(0)
            # for playlist in playlists_data['items']:
            #     # If we own a playlist but it's collaborative, we treat it as a followed one since we might be interested in updates.
            #     if playlist['owner']['id'] != self.user_id or playlist['collaborative']:
            #         self.followed_playlists[playlist['id']] = playlist
            #     else:
            #         self.user_playlists[playlist['id']] = playlist

            # # If there were more playlists than we just received, query the next batch
            # if playlists_data['next']:
            #     playlists_data = self.sp.next(playlists_data)
            # else:
            #     break

    # Store the track ids we just added to the feed in the log file.
    def _log_feed_updates(self, track_ids: np.ndarray):
        """
        Log is dict with the following info:
            track_ids: numpy array of track ids that were added to the feed
            timestamps: timestamp at which each of the tracks was added to the feed
        """
        if os.path.exists(self._feed_log_path):
            feed_log = pickle.load(open(self._feed_log_path, "rb"))
        else:
            feed_log = {"track_ids": [], "timestamps": []}

        # Create, append and overwrite timestamps
        new_timestamps = np.repeat(datetime.utcnow(), track_ids.size)
        timestamp_array = np.append(feed_log["timestamps"], new_timestamps)
        feed_log["timestamps"] = timestamp_array

        # Append and overwrite track_ids
        track_id_array = np.append(feed_log["track_ids"], track_ids)
        feed_log["track_ids"] = track_id_array

        pickle.dump(feed_log, open(self._feed_log_path, "wb"))

    # Print the tracks and timestamps saved in the feed log.
    def print_feed_log(self):
        if not os.path.exists(self._feed_log_path):
            print("No feed log exists yet!")
            return

        feed_log = pickle.load(open(self._feed_log_path, "rb"))
        num_tracks = len(feed_log["track_ids"])
        print("Found {} tracks in log.".format(num_tracks))

        batch_size = 50
        tracks = []
        start_idx = 0
        print("Requesting track info...")
        for start_idx in tqdm(range(0, num_tracks, batch_size)):
            end_idx = start_idx + batch_size
            track_ids = feed_log["track_ids"][start_idx:end_idx]
            tracks += self.sp.tracks(track_ids)["tracks"]
            start_idx = end_idx

        for track, timestamp in zip(tracks, feed_log["timestamps"]):
            safe_print(
                "{} - {} - {} - {}".format(
                    track["artists"][0]["name"], track["name"], timestamp, track["id"]
                )
            )

    # Follow a user
    def _follow_user(self, username: str):
        self.sp.user_follow_users([username])

    """    STUBS
    def _search(self):
        results = self.sp.search(q='weezer', limit=20)
        safe_print(results['tracks'].keys())


    def _get_all_user_songs(self):
        results = self.sp.current_user_saved_tracks(limit = 100)
        safe_print(results['limit'])
        # for item in results['items']:
        #     track = item['track']
        #     safe_print(track['name'] + ' - ' + track['artists'][0]['name'])
    """

