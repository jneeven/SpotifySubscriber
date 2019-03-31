import argparse
import os
import sys
import platform
import subprocess

from SpotifySubscriber import SpotifySubscriber


def delete_existing_windows_tasks():
    subprocess.call(r'schtasks /delete /tn "SpotifySubcriber Feed Updater daily" /f', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.call(r'schtasks /delete /tn "SpotifySubcriber Feed Updater onstart" /f', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


# Schedule update task in Windows Task Scheduler
def schedule_windows_tasks(run_as_exe = False):
    if run_as_exe:
        update_command = r'"{}\update.exe"'.format(os.path.dirname(sys.executable))
    else:
        update_command = r'"python {}\update.py"'.format(os.path.dirname(os.path.abspath(__file__)))
            
    # Delete any existing schedule tasks first
    delete_existing_windows_tasks()

    # Run daily ay 18:00
    schedule_command = r'schtasks /create /tn "SpotifySubcriber Feed Updater daily" /tr {} /sc DAILY /st 18:00:00'.format(update_command)
    scheduled_daily = subprocess.call(schedule_command, shell=True) == 0

    # Run every time the PC boots
    schedule_command = r'schtasks /create /tn "SpotifySubcriber Feed Updater onstart" /tr {} /sc ONSTART'.format(update_command)
    scheduled_on_start = subprocess.call(schedule_command, shell=True) == 0

    return scheduled_daily, scheduled_on_start


def main(args):
    run_as_exe = sys.executable.endswith("init.exe")
    subscribe_executable = 'subscribe.py'

    if args.username == "":
        username = input('Enter your Spotify username: ')
    else:
        username = args.username

    spotify = SpotifySubscriber(username)
    print('Successfully initialized SpotifySubscriber for username {}'.format(username))

    current_platform = platform.system()
    if current_platform == 'Windows':

        # If the current code is executed as an executable file, use update.exe instead of .py
        if run_as_exe:
            subscribe_executable = 'subscribe.exe'  

        daily, startup = schedule_windows_tasks(run_as_exe)
        if daily:
            print("Subscription feed will be updated daily at 18:00 (if your PC is on).")
        
        if startup:
            print("Subscription feed will be updated every time your PC starts.")
        else:
            print("WARNING: Tried scheduling subscription feed to be updated every " + \
            "time your PC starts, but did not have permission. Try executing this " + \
            "file as administrator.")

    else:
        print("Automatic updates are not implemented yet for your OS. " + \
        "To update your subscription feed automatically, please schedule\n" + \
        "python update.py \n" + \
        "With the desired frequency using tools appropriate for your OS (for example crontab).")


    print("To get started, subscribe to a few playlists with {}.".format(subscribe_executable))
    input()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = 'Check for new tracks & update the subscription feed.')
    parser.add_argument('--username', type = str, default = "", help = 'Spotify username')
    args = parser.parse_args()

    main(args)