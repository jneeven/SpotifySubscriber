import argparse

from SpotifySubscriber import SpotifySubscriber


def main(args):
    spotify = SpotifySubscriber(args.username)
    print('Successfully initialized SpotifySubscriber for username {}. To get started, subscribe to a few playlists with subscribe.py and then periodically run update.py.'.format(args.username))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = 'Check for new tracks & update the subscription feed.')
    parser.add_argument('username', type = str, help = 'Spotify username')
    args = parser.parse_args()

    main(args)