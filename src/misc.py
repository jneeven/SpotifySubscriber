from SpotifySubscriber import SpotifySubscriber


def main():
    spotify = SpotifySubscriber()
    spotify.refresh_user_playlists()
    spotify.print_feed_log()


if __name__ == "__main__":
    main()