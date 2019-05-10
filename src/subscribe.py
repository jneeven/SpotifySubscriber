import argparse
import sys

from SpotifySubscriber import SpotifySubscriber


def main(args):
    spotify = SpotifySubscriber()
    spotify.refresh_user_playlists()

    if args.unsubscribe:
        if args.id:
            spotify.unsubscribe_from_playlists(playlist_ids = [args.playlist])
        else:
            spotify.unsubscribe_from_playlists(contains = [args.playlist])
    else:
        if args.id:
            spotify.subscribe_to_playlists(playlist_ids = [args.playlist])
        else:
            spotify.subscribe_to_playlists(contains = [args.playlist])

    spotify.print_playlists()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = 'Subscribe or unsubscribe to one of your followed playlists.')
    parser.add_argument('playlist', type = str, help = 'Playlist name to subscribe to or unsubscribe from. \
        Partial name also works, for example "discover" will subscribe to discover weekly. Not case sensitive.')
    parser.add_argument('--unsubscribe', action = 'store_true', help = 'Unsubscribe from this playlist.')
    parser.add_argument('--id', action = 'store_true', help = 'The provided name is a playlist ID rather than a name pattern.')

    args = parser.parse_args()

    main(args)