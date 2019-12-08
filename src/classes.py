from datetime import datetime

from spotipy import Spotify

from utils import safe_print


class SubscribedPlaylist:
    """
    Convert subscribed playlist dictionary into more managable object.
    """

    def __init__(self, playlist: dict, tracks: list):
        self.name = playlist["name"]
        self.id = playlist["id"]
        self.owner_id = playlist["owner"]["id"]
        self.snapshot_id = playlist["snapshot_id"]
        self.subscribe_stamp = datetime.utcnow()

        # Store track IDs in dict so we won't think songs are new if they are
        # deleted and re-added to the list
        self.track_ids = {}
        for track in tracks:
            self.track_ids[track.id] = self.subscribe_stamp

    def __repr__(self):
        time_stamp = self.subscribe_stamp.strftime("%Y-%m-%dT%H:%M:%SZ")
        string = "'{}' by {} - Subscribe stamp: {} - ID: {} - Snapshot: {}".format(
            self.name, self.owner_id, time_stamp, self.id, self.snapshot_id
        )
        return string


class Track:
    """
    Convert track info dictionary into more managable object.
    """

    def __init__(self, track: dict, playlist_id="-1"):
        self.name = track["track"]["name"]
        self.id = track["track"]["id"]
        self.album = track["track"]["album"]
        self.artist_dicts = track["track"]["artists"]
        self.main_artist_name = self.artist_dicts[0]["name"]
        self.playlist_id = playlist_id
        self.added_by = track["added_by"]["id"]

    def __repr__(self):
        return (
            f"Track(name={self.name}, id={self.id}, artist_dicts={self.artist_dicts}, "
            + f"album={self.album}, playlist_id={self.playlist_id})"
        )


class SubscriptionFeed:
    """
    Represents the playlist to which all new songs from the subscribed playlists will be added.

    Attributes:
    id (str): the playlist ID
    name (str): the playlist name
    last_update (float): timestamp of the last update
    """

    default_name = "SpotifySubscriber"
    default_description = "SpotifySubscriber feed. Whenever one of your subscribed playlists changes, the new songs are added to this list. For more information, visit http://github.com/jneeven/SpotifySubscriber."

    def __init__(
        self,
        spotify: Spotify,
        user_id: str,
        name: str = default_name,
        description: str = default_description,
    ):
        safe_print(
            "Creating playlist with name {} and the following description:\n\t'{}'".format(
                name, description
            )
        )
        feed = spotify.user_playlist_create(
            user_id, name=name, public=False, description=description
        )

        self.id = feed["id"]
        self.name = feed["name"]
        self.last_update = datetime.utcnow()
