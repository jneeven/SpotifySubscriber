pyinstaller src/init.py -y --add-data 'src/client_data.json;.'
pyinstaller src/update.py -y --add-data 'src/client_data.json;.'
pyinstaller src/subscribe.py -y --add-data 'src/client_data.json;.'

cp dist/init dist/SpotifySubscriber
cp dist/subscribe/subscribe.exe dist/SpotifySubscriber
cp dist/update/update.exe dist/SpotifySubscriber

rm -rf dist/init dist/subscribe dist/update