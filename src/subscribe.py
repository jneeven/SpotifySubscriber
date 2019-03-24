import argparse

from SpotifySubscriber import SpotifySubscriber


def main(args):
    spotify = SpotifySubscriber()
    if args.unsubscribe:
        spotify.unsubscribe_from_playlists(contains = [args.playlist])
    else:
        spotify.subscribe_to_playlists(contains = [args.playlist])

    spotify.print_playlists()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = 'Subscribe to a ')
    parser.add_argument('playlist', type = str, help = 'Playlist name to subscribe to or unsubscribe from. \
        Partial name also works, for example "discover" will subscribe to discover weekly. Not case sensitive.')
    parser.add_argument('--unsubscribe', action = 'store_true', help = 'Unsubscribe from this playlist.')

    args = parser.parse_args()

    main(args)