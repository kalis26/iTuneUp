# iTuneUp
iTuneUp is a Python-powered utility designed to streamline the process of building a rich, Apple-like local music library. It allows users to download songs and albums from YouTube, convert them to high-efficiency `.m4a` audio files **(encoded with the AAC codec)**, and embed rich metadata scraped directly from the Apple Music website — including artwork, track listings, and artist details.\
Whether you’re looking to preserve your favorite albums with authentic presentation, or automate the transformation of YouTube content into Apple Music–style files, **iTuneUp** merges content sourcing, transcoding, and metadata injection into a single intuitive tool.

<div align="center">
  
  [![stars](https://img.shields.io/github/stars/kalis26/iTuneUp)](https://github.com/kalis26/iTuneUp/stargazers)
  [![forks](https://img.shields.io/github/forks/kalis26/iTuneUp)](https://github.com/kalis26/iTuneUp/forks)
  [![issues](https://img.shields.io/github/issues/kalis26/iTuneUp?color=orange)](https://github.com/kalis26/iTuneUp/issues)
  [![license](https://img.shields.io/github/license/kalis26/iTuneUp)](https://github.com/kalis26/iTuneUp/blob/main/LICENSE)
  
</div>

## Core Features
- Download full albums or individual tracks from YouTube via simple search queries.
- Convert audio streams into `.m4a` (MPEG-4 Part 14) format using the **Advanced Audio Coding (AAC)** codec — the same audio compression used by Apple Music.
- Enrich downloaded files with Apple Music metadata, including:
  * Track title
  * Album and artist name
  * Release date
  * Album artwork (632×632px high-quality JPEG)
  * Track order, genre, and Apple Music-specific tags
- Automatically name and organize files for proper integration with iTunes or third-party players.
- Create a truly **"Apple Music–like" experience** for your local music collection — without subscriptions.

## Technologies Used
- Python 3.12+
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) -- for high-accuracy YouTube media downloading
- [ffmpeg](https://ffmpeg.org/) -- for audio conversion and stream extraction
- [mutagen](https://mutagen.readthedocs.io/) -- for embedding metadata into `.m4a` files
- Selenium + requests – to scrape and retrieve metadata from Apple Music’s public web pages

## System Requirements
- **Python:** 3.9 or higher
- **Operating System:** Windows 10+ (Linux/macOS support possible with minor tweaks)
- **FFmpeg:** Must be installed and accessible via system PATH
- **Google Chrome:** Required for Apple Music scraping (headless via Selenium)

### Python Dependencies
Install required packages using:
```
pip install yt-dlp selenium mutagen requests
```

## How to run?
1. Open a terminal in the project folder.
   
2. Launch the app:
  ```
  python iTuneUp.py
  ```
3. Follow prompts to:
  * Input an Apple Music song or album
  * Provide the artist info (used to find matching Apple Music metadata)
4. iTuneUp will:
  * Download and convert the media to `.m4a`
  * Scrape and match metadata from Apple Music
  * Embed metadata and artwork into each track
5. Final `.m4a` files will be saved in the `{album_name}/` folder in the programs directory, ready to be added to iTunes.

## Use Cases
- Build a curated, metadata-rich `.m4a` library using free online content.
- Sync personalized albums with iTunes, iOS devices, or third-party players.
- Archive rare or live recordings with high-efficiency encoding and clean metadata.
- Combine streaming convenience with local ownership and detailed music info.

## How to Add to iTunes and Sync with iPhone/iPad
Once you've used **iTuneUp** to download and tag `.m4a` tracks with rich metadata, you can seamlessly add them to your iTunes library on PC and sync them to your iPhone or iPad for a native Apple Music–like experience.
### 1st - Add Songs to iTunes Library
1. Go to the iTunes <img src="https://help.apple.com/assets/65F888B2B2F4A0D0EA005BE5/65F888B35B54CF6A740B68EA/en_US/f344938417f8d295c94901b517e140f1.png" alt="" height="16" width="16" originalimagename="GlobalArt/xicnitns.png"> app on your Windows PC (latest version recommended).
2. In the menu bar, go to: **File > Add Folder to Library...** 
   
