<div align="center">
  <img src="assets/main_icon.png" alt="AMScrobbler logo" width="200"/>
</div>
<p align="center"><strong style="font-size: 2em;">AMScrobbler</strong></p>
<p align="center" style="font-size: 1.3em;">Last.fm scrobbler for Apple Music Windows App</p>


## Overview
**AMScrobbler** monitors the Apple Music desktop application on Windows to detect currently playing tracks, fetches additional metadata from the Apple Music web pages and Last.fm API, and scrobbles them to your Last.fm profile. It features a GUI built with CustomTkinter, supporting both a full interface and a minimal mode.


## Features
- **Real-time Scrobbling**: Automatically detects and scrobbles tracks playing in the Apple Music Windows App.
- **Now Playing Updates**: Sets the "now playing" status on Last.fm as soon as a track starts.
- **Metadata Enrichment**: Pulls accurate track duration, album artwork, and corrections from Apple Music web pages and Last.fm API.
- **GUI Modes**:
  - **Full GUI**: Displays user avatar, username (clickable, links to Last.fm profile), animated play/pause indicators, track artwork, title, and artist.
  - **Minimal GUI**: A lightweight version showing only username and current track info.
- **System Tray Integration**: Runs in the background with a tray icon for quick access to open the window or quit.
- **Authentication**: Secure Last.fm login via web auth, with session key stored locally for future use.


## Installation
### Option 1: Using pre-built executables
1. **Download the Executable**

    Go to the [**Releases**](https://github.com/blackmidinewroad/am-scrobbler/releases) page and download `AMScrobbler.exe` from `Assets` in the latest release.

2. **Create `.env` file**

    Create a file with the name `.env` in the same folder as `AMScrobbler.exe`. Open it using Notepad or any other text editor and and put this inside of the file:
    ```env
    API_KEY='your_lastfm_api_key'
    API_SECRET='your_lastfm_api_secret'
    MINIMAL_GUI='true'
    ```
  
    - Replace `your_lastfm_api_key` and `your_lastfm_api_secret` with your actual Last.fm API credentials. If you don't have them yet, go to [Last.fm "Create API account" page](https://www.last.fm/api/account/create) and sign up for an API account, you can just fill `Contact email` and `Application name` (any name). After creating an API account you will see `API key` and `Shared secret`.
    - Replace `MINIMAL_GUI='true'` with `MINIMAL_GUI='false'` if you want full GUI version.

3. **Run the downloaded `.exe` file.**
  

### Option 2: From source
1. **Clone the Repository**:
    ```shell
    git clone https://github.com/blackmidinewroad/am-scrobbler.git
    cd am-scrobbler
    ```

2. **Install Dependencies**
    - Using pipenv:
      
        ```shell
        pipenv install
        ```
     - Using pip:

        ```shell
        pip install -r requirements.txt
        ```

3. **Set Up Environment Variables**

    Create a `.env` file in the project root with the following:
    ```env
    API_KEY='your_lastfm_api_key'
    API_SECRET='your_lastfm_api_secret'
    MINIMAL_GUI='true'  # or 'false' for full GUI mode
    ```

    Replace `your_lastfm_api_key` and `your_lastfm_api_secret` with your actual Last.fm API credentials. If you don't have them yet, go to [Last.fm "Create API account" page](https://www.last.fm/api/account/create) and sign up for an API account.

4. **Run the Application**:

     ```shell
     python -m scrobbler.main
     ```


## Building the Executable
You can build the `.exe` yourself using PyInstaller. Ensure you have PyInstaller installed (`pip install pyinstaller`).

  ```shell
  pyinstaller --noconfirm --onefile --windowed --name AMScrobbler --copy-metadata pylast -i "assets/main_icon.ico" --add-data "assets/*;assets" scrobbler/main.py
  ```

The `.exe` will be in the `dist` directory.


## How It Works
- **Song Detection**: Uses `pywinauto` to scrape the Apple Music app's GUI for track title, artist, album, play status, and progress.
- **Metadata Fetching**: Queries Apple Music web pages for duration and artwork (if needed), and Last.fm API for corrections and additional duration.
- **Scrobbling Logic**: Tracks playtime in a background loop, scrobbles via `pylast` when conditions are met.
- **GUI**: Built with CustomTkinter for a modern dark-themed interface. Supports animated GIFs for avatars and play/pause states.


## Scrobble Conditions
Song is eligible for a scrobble if you have listened to more than a half of the song. The scrobble itself will happen either when the song is changes, Apple Music app closes, or AMScrobbler closes.


## Screenshots



## Notes
- This project is specifically designed for the **Apple Music Windows App**.
- To fully quit the AMScrobbler you will need to quit using system tray icon.
- Background scrobbling works best with minimal GUI.
- Supports only dark mode.