from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException
from mutagen.mp4 import MP4, MP4FreeForm, MP4Cover
import os
import contextlib
import sys
from yt_dlp import YoutubeDL
from pydub import AudioSegment

# To take off all the logs

@contextlib.contextmanager
def suppress_stderr():
    with open(os.devnull, 'w') as devnull:
        old_stderr = sys.stderr
        sys.stderr = devnull
        try:
            yield
        finally:
            sys.stderr = old_stderr

def add_metadata(file_path, image_path, artists, album, albumartist, albumsort, artist, artistsort, compilation, copyright, 
                 discnumber, genre, itunesadvisory, itunesalbumid, itunesartistid, itunescatalogid, itunesgenreid,
                 itunesgapless, itunesmediatype, title, titlesort, totaltracks, track, year):

    audio = MP4(file_path)

    if artists:
        freeform_artists = [MP4FreeForm(artistelem.encode('utf-8')) for artistelem in artists]
        audio["----:com.apple.iTunes:ARTISTS"] = freeform_artists

    if album:
        audio["\xa9alb"] = [album]
    if albumartist:
        audio["aART"] = [albumartist]
    if albumsort:
        audio["soal"] = [albumsort]
    if artist:
        audio["\xa9ART"] = [artist]
    if artistsort:
        audio["soar"] = [artistsort]
    if copyright:
        audio["cprt"] = [copyright]
    if genre:
        audio["\xa9gen"] = [genre]
    if title:
        audio["\xa9nam"] = [title]
    if titlesort:
        audio["sonm"] = [titlesort]
    if year:
        audio["\xa9day"] = [year]

    # Numeric tags with conversion and error handling

    audio["cpil"] = [0]

    if discnumber is not None:
        try:
            audio["disk"] = [(int(discnumber), 1)]
        except Exception:
            pass

    if itunesadvisory is not None:
        try:
            audio["rtng"] = [int(itunesadvisory)]
        except Exception:
            pass

    if itunesalbumid:
        try:
            audio["plID"] = [int(itunesalbumid)]
        except Exception:
            pass

    if itunesartistid:
        try:
            audio["atID"] = [int(itunesartistid)]
        except Exception:
            pass

    if itunescatalogid:
        try:
            audio["cnID"] = [int(itunescatalogid)]
        except Exception:
            pass

    if itunesgenreid:
        try:
            audio["geID"] = [int(itunesgenreid)]
        except Exception:
            pass

    audio["pgap"] = [0]

    if itunesmediatype is not None:
        try:
            audio["stik"] = [int(itunesmediatype)]
        except Exception:
            if itunesmediatype == "Normal":
                audio["stik"] = [1]
                
    if track is not None and totaltracks is not None:
        try:
            audio["trkn"] = [(int(track), int(totaltracks))]
        except Exception:
            pass

    # Cover art
    if image_path and os.path.exists(image_path):
        with open(image_path, 'rb') as f:
            cover = f.read()
        audio["covr"] = [MP4Cover(cover, imageformat=MP4Cover.FORMAT_JPEG)]

    audio.save()

def recover_metadata(file_path):
    metadata = {}
    with open(file_path, 'r') as f:
        for line in f:
            key, value = line.strip().split('| ', 1)
            key = key.strip()  # <-- Strip whitespace from key
            value = value.strip()  # (optional) Strip whitespace from value
            if key in metadata:
                if isinstance(metadata[key], list):
                    metadata[key].append(value)
                else:
                    metadata[key] = [metadata[key], value]
            else:
                metadata[key] = value
    return metadata

def download_playlist(url, audio_format='mp3', quality='192'):

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': '%(playlist_title)s/%(playlist_index)d %(title)s.%(ext)s',
        'ignoreerrors': True,
        'quiet': False,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': audio_format,
            'preferredquality': quality,
        }],
        'noplaylist': False,
    }

    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

def find_matching_folder(search_title, directory):

    normalized_search = search_title.lower().replace(' ', '')
    for folder in os.listdir(directory):

        if os.path.isdir(os.path.join(directory, folder)):

            normalized_folder = folder.lower().replace(' ', '')
            if normalized_folder == normalized_search:

                return folder
            
    return None

def convert_all_mp3_to_m4a(folder_path, delete_original=False):
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(".mp3"):
            mp3_path = os.path.join(folder_path, filename)
            m4a_path = os.path.join(folder_path, os.path.splitext(filename)[0] + ".m4a")
            
            try:
                print(f"Converting: {filename} → {os.path.basename(m4a_path)}")
                audio = AudioSegment.from_mp3(mp3_path)
                audio.export(m4a_path, format="ipod")
                
                if delete_original:
                    os.remove(mp3_path)
                    print(f"Deleted original: {filename}")
            except Exception as e:
                print(f"Failed to convert {filename}: {e}")


app_dir = os.path.dirname(os.path.abspath(__file__))
metadata_dir = os.path.join(app_dir, "metadata")
os.makedirs(metadata_dir, exist_ok=True)

title = input("Enter the name of the song/album: ")
artist = input("Enter the name of the artist: ")
print('\n')
title_query = title.replace(' ', '+').replace("'", '%27')
artist_query = artist.replace(' ', '+').replace("'", '%27')
url = f"https://www.youtube.com/results?search_query={title_query}+{artist_query}"

options = webdriver.ChromeOptions()
options.add_argument("--headless")

service = Service(log_path=os.devnull)

with suppress_stderr():
    driver = webdriver.Chrome(service=service, options=options)

driver.get(url)

try:

    album_playlist = driver.find_element(By.CSS_SELECTOR, '.yt-simple-endpoint.style-scope.ytd-watch-card-rich-header-renderer')
    playlist_url = album_playlist.get_attribute('href')

except NoSuchElementException:

    songs = driver.find_elements(By.CSS_SELECTOR, '.style-scope.ytd-video-renderer')

if playlist_url:

    # print(f"Downloading playlist from: {playlist_url}")
    # download_playlist(playlist_url)

    matched_folder = find_matching_folder(title, app_dir)
    file_count = len([f for f in os.listdir(matched_folder) if os.path.isfile(os.path.join(matched_folder, f))])

    convert_all_mp3_to_m4a(matched_folder, delete_original=True)

    prefix = 1
    processed = 0
    while processed < file_count:

        metadata_filepath = None
        for filename in os.listdir(metadata_dir):
            if filename.startswith(str(prefix)):
                metadata_filepath = os.path.join(metadata_dir, filename)
                break

        if metadata_filepath is None:
            prefix += 1
            continue

        metadata = recover_metadata(metadata_filepath)

        artists = metadata.get("ARTISTS")
        if artists is None:
            artists_list = []
        elif isinstance(artists, list):
            artists_list = artists
        else:
            artists_list = [artists]

        # Find the music file for this prefix
        for filename in os.listdir(matched_folder):
            if filename.startswith(str(prefix)):
                music_filepath = os.path.join(matched_folder, filename)
                new_music_filepath = os.path.join(
                    matched_folder,
                    os.path.splitext(os.path.basename(metadata_filepath))[0] + os.path.splitext(music_filepath)[1]
                )
                if music_filepath != new_music_filepath:
                    os.rename(music_filepath, new_music_filepath)
                    music_filepath = new_music_filepath

                add_metadata(
                    music_filepath,
                    os.path.join(metadata_dir, 'artwork.jpg'),
                    artists_list,
                    metadata.get("ALBUM"),
                    metadata.get("ALBUMARTIST"),
                    metadata.get("ALBUMSORT"),
                    metadata.get("ARTIST"),
                    metadata.get("ARTISTSORT"),
                    metadata.get("COMPILATION"),
                    metadata.get("COPYRIGHT"),
                    metadata.get("DISCNUMBER"),
                    metadata.get("GENRE"),
                    metadata.get("ITUNESADVISORY"),
                    metadata.get("ITUNESALBUMID"),
                    metadata.get("ITUNESARTISTID"),
                    metadata.get("ITUNESCATALOGID"),
                    metadata.get("ITUNESGENREID"),
                    metadata.get("ITUNESGAPLESS"),
                    metadata.get("ITUNESMEDIATYPE"),
                    metadata.get("TITLE"),
                    metadata.get("TITLESORT"),
                    metadata.get("TOTALTRACKS"),
                    metadata.get("TRACK"),
                    metadata.get("YEAR")
                )
                processed += 1
                break  # Only process one file per prefix
        prefix += 1
