import argparse

from SpotifySubscriber import SpotifySubscriber


def main(args):
    spotify = SpotifySubscriber()

    # Print all playlists
    spotify.print_playlists()

    # Obtain any new songs since the last update
    new_tracks = spotify.update_feed(add_own = False)
    print("Added {} new tracks.".format(new_tracks))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = 'Check for new tracks & update the subscription feed.')
    args = parser.parse_args()

    main(args)