# iTuneUp

<p align="center">
  <img src="resources/images/logo.png" width="64" alt="iTuneUp logo">
</p>

<p align="center">
  Windows desktop application for creating and organizing metadata-rich M4A music libraries with Apple Music metadata and artwork.
</p>

<div align="center">

[![Stars](https://img.shields.io/github/stars/kalis26/iTuneUp)](https://github.com/kalis26/iTuneUp/stargazers)
[![Forks](https://img.shields.io/github/forks/kalis26/iTuneUp)](https://github.com/kalis26/iTuneUp/forks)
[![Issues](https://img.shields.io/github/issues/kalis26/iTuneUp?color=orange)](https://github.com/kalis26/iTuneUp/issues)
[![License](https://img.shields.io/github/license/kalis26/iTuneUp)](https://github.com/kalis26/iTuneUp/blob/main/LICENSE)

</div>

## Overview

iTuneUp uses Apple Music as the metadata and artwork source, then uses Deezer catalog matching to locate the corresponding recording. Completed files are converted to M4A, tagged with Apple Music metadata, and organized into an album-based local library suitable for iTunes and compatible media players.

## Features

- Downloads full albums or individual tracks from Apple Music search results or direct Apple Music URLs.
- Matches tracks against Deezer using title, artist, album, and duration where available.
- Rejects uncertain matches instead of selecting an arbitrary recording.
- Connects a Deezer account through a browser-based sign-in flow; iTuneUp stores session data in Windows Credential Manager.
- Converts downloaded MP3 audio to M4A using FFmpeg.
- Adds Apple Music metadata, including title, artist, album, release date, artwork, track number, genre, and Apple-specific tags.
- Uses isolated job workspaces to prevent temporary files from different downloads from colliding.
- Provides a native Windows installer, Start Menu entry, optional desktop shortcut, and uninstaller.

## Requirements

- Windows 10 or later, 64-bit.
- Google Chrome, used for Apple Music metadata extraction and Deezer account sign-in.
- An authorized Deezer account.
- Internet access.

Python and project dependencies are not required when using the packaged installer.

## Installation

1. Download `iTuneUp-Setup.exe` from the [Releases](https://github.com/kalis26/iTuneUp/releases) page.
2. Run the installer and complete the setup steps.
3. Launch iTuneUp from the Start Menu or desktop shortcut.

To uninstall, use **Installed apps** in Windows Settings or select **Uninstall iTuneUp** from the Start Menu.

## Using iTuneUp

1. Launch iTuneUp and connect your Deezer account when prompted.
2. Search for an album or song, or paste an Apple Music URL.
3. Confirm the Apple Music result that should provide metadata and artwork.
4. Wait while iTuneUp matches, downloads, converts, and tags the selected tracks.
5. Open the **Library** tab to access the completed album folder.

If iTuneUp cannot find a high-confidence Deezer match, it stops the job and reports the affected track instead of downloading an uncertain recording.

## Adding Music to iTunes

1. In iTunes, select **File > Add Folder to Library**.
2. Select the album folder created by iTuneUp.
3. iTunes imports the M4A files with their title, artist, album, artwork, track order, genre, and release-date metadata.
4. Sync the imported music to a connected iPhone or iPad through iTunes if required.

## Technical Overview

- **Desktop shell:** Flask and PyWebView
- **Apple Music metadata extraction:** Selenium and requests
- **Deezer matching and acquisition:** Native Python adapter
- **Audio conversion:** FFmpeg
- **M4A metadata:** Mutagen
- **Credential storage:** Windows Credential Manager through `keyring`

## Limitations

- Deezer availability can vary by account entitlement and region.
- Chrome must be installed and kept up to date for browser-driven metadata extraction and Deezer sign-in.
- The application requires a network connection for metadata, catalog matching, and audio acquisition.

## License

iTuneUp is released under the [MIT License](LICENSE).
