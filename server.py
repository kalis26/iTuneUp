from flask import Flask, render_template, redirect, request, flash, session
from forms import SearchForm, ConfirmForm
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException
from mutagen.mp4 import MP4, MP4FreeForm, MP4Cover
import os
import contextlib
import sys
import yt_dlp
from yt_dlp import YoutubeDL
from pydub import AudioSegment
from ammr import ExtractMetadata
import re
import difflib
import threading
import time
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Password1594826kjk!'

@contextlib.contextmanager
def suppress_stderr():

    with open(os.devnull, 'w') as devnull:
        old_stderr = sys.stderr
        sys.stderr = devnull
        try:
            yield
        finally:
            sys.stderr = old_stderr

def get_yes_no(prompt):

    while True:
        answer = input(prompt + " (yes/no): ").strip().lower()
        if answer in ("yes", "no"):
            return answer
        print("Please enter 'yes' or 'no'.")

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

    if compilation is not None:
        try:
            audio["cpil"] = [int(compilation)]
        except Exception:
            pass

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

    if itunesgapless is not None:
        try:
            audio["pgap"] = [int(itunesgapless)]
        except Exception:
            pass

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

    if image_path and os.path.exists(image_path):
        with open(image_path, 'rb') as f:
            cover = f.read()
        audio["covr"] = [MP4Cover(cover, imageformat=MP4Cover.FORMAT_JPEG)]

    audio.save()

def recover_metadata(file_path):

    metadata = {}
    with open(file_path, 'r', encoding='utf-8') as f:  # <-- Add encoding
        for line in f:
            key, value = line.strip().split('| ', 1)
            key = key.strip()
            value = value.strip()
            if key in metadata:
                if isinstance(metadata[key], list):
                    metadata[key].append(value)
                else:
                    metadata[key] = [metadata[key], value]
            else:
                metadata[key] = value

    return metadata

def download_as_mp3(youtube_url, library_dir):

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl':  os.path.join(library_dir, '%(title)s/1 %(title)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320',
        }],
        'quiet': False,
        'noplaylist': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=True)

    return info['title']

def download_playlist(url, library_dir, audio_format='mp3', quality='320'):

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(library_dir, '%(playlist_title)s/%(playlist_index)d %(title)s.%(ext)s'),
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

                return os.path.join(directory, folder)
            
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

def normalize(s):

    s = s.lower()
    for word in ["(clipofficiel)", "(officialvideo)", "(officialaudio)", "(visualizer)"]:
        s = s.replace(word, "")
    s = re.sub(r"[.,\-’']", "", s)
    s = s.replace(" ", "")

    return s

def find_best_metadata_file(title_folder, metadata_dir):

    title_folder_norm = normalize(title_folder)
    best_match = None
    highest_ratio = 0

    for filename in os.listdir(metadata_dir):
        filename_norm = normalize(filename)
        ratio = difflib.SequenceMatcher(None, title_folder_norm, filename_norm).ratio()
        print(f"Comparing '{title_folder_norm}' with '{filename_norm}' => ratio: {ratio:.2f}")
        if ratio > highest_ratio:
            highest_ratio = ratio
            best_match = filename

    if best_match and highest_ratio > 0.5:
        return os.path.join(metadata_dir, best_match)
    else:
        return None
    
def cleanup_metadata_dir(metadata_dir):

    for filename in os.listdir(metadata_dir):
        file_path = os.path.join(metadata_dir, filename)
        if os.path.isfile(file_path):

            if (filename.lower().endswith(('.txt', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')) 
                and filename != 'README.md'):
                try:
                    os.remove(file_path)
                    print(f"Cleaned up: {filename}")
                except Exception as e:
                    print(f"Failed to remove {filename}: {e}")

def setup_directories():

    app_dir = os.path.dirname(os.path.abspath(__file__))
    metadata_dir = os.path.join(app_dir, "metadata")
    library_dir = os.path.join(app_dir, "library")
    os.makedirs(metadata_dir, exist_ok=True)
    os.makedirs(library_dir, exist_ok=True)

    return metadata_dir, library_dir

def show_search_results(form, confirm_form, title, artist, searchid):

    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    service = Service(log_path=os.devnull)
    
    with suppress_stderr():
        driver = webdriver.Chrome(service=service, options=options)

    try:

        urlApple = f"https://music.apple.com/us/search?term={title.replace(' ', '%20')}%20{artist.replace(' ', '%20')}"
        driver.get(urlApple)

        grid_elem = driver.find_elements(By.CSS_SELECTOR, '.grid-item.svelte-1a54yxp')

        if not grid_elem:
            flash('No search results found.')
            return render_template('home.html', form=form, confirm_form=confirm_form, active_page='Home')

        if searchid >= len(grid_elem):
            flash('No more results found.')
            return render_template('home.html', form=form, confirm_form=confirm_form, active_page='Home')

        current_element = grid_elem[searchid]
        
        try:
            Name = current_element.find_element(By.CSS_SELECTOR, '.top-search-lockup__primary__title.svelte-bg2ql4[dir="auto"]').get_attribute("textContent").strip()
            Details = current_element.find_element(By.CSS_SELECTOR, '.top-search-lockup__secondary.svelte-bg2ql4[data-testid="top-search-result-subtitle"]').get_attribute("textContent").strip()

            IMG = current_element.find_element(By.CSS_SELECTOR, '.svelte-uduhys')
            IMGCON = IMG.find_element(By.CSS_SELECTOR, 'source')
            srcset = IMGCON.get_attribute("srcset")
            imgurl = srcset.split(',')[1].split(' ')[0].strip()

            session['current_search'] = {
                'name': Name,
                'details': Details,
                'img': imgurl,
                'title': title,
                'artist': artist,
                'id': searchid,
                'total_results': len(grid_elem)
            }

            return render_template('home.html', form=form, confirm_form=confirm_form, active_page='Home', 
                                 Name=Name, Details=Details, IMG=imgurl)
                                 
        except Exception as e:
            flash(f'Error extracting search result: {str(e)}')
            return render_template('home.html', form=form, confirm_form=confirm_form, active_page='Home')

    except Exception as e:
        flash(f'Error during search: {str(e)}')
        return render_template('home.html', form=form, confirm_form=confirm_form, active_page='Home')
    
    finally:
        driver.quit()

download_progress = {}

def update_progress(task_id, message, percentage):

    download_progress[task_id] = {
        'message': message,
        'percentage': percentage,
        'timestamp': time.time()
    }

def download_with_progress(current_search, task_id):

    try:

        update_progress(task_id, 'Initializing download...', 5)

        title = current_search['title']
        artist = current_search['artist']

        url = f"https://music.apple.com/us/search?term={title.replace(' ', '%20')}%20{artist.replace(' ', '%20')}"
        id = current_search['id']

        metadata_dir, library_dir = setup_directories()
        update_progress(task_id, "Setting up directories...", 10)

        title, artist = ExtractMetadata(url, id, metadata_dir)

        title = title.replace(" - Single", "").strip()

        title_query = title.replace(' ', '+').replace("'", '%27')
        artist_query = artist.replace(' ', '+').replace("'", '%27')

        url = f"https://www.youtube.com/results?search_query={title_query}+{artist_query}"

        update_progress(task_id, "Searching for content...", 20)

        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        service = Service(log_path=os.devnull)

        driver = webdriver.Chrome(options=options, service=service)
        driver.get(url)

        try:

            album_playlist = driver.find_element(By.CSS_SELECTOR, '.yt-simple-endpoint.style-scope.ytd-watch-card-rich-header-renderer')
            playlist_url = album_playlist.get_attribute('href')

        except NoSuchElementException:
            playlist_url = None

            songs = driver.find_elements(By.CSS_SELECTOR, '.style-scope.ytd-video-renderer')

        if playlist_url:

            update_progress(task_id, "Downloading album...", 30)

            print(f"Downloading playlist from: {playlist_url}")
            download_playlist(playlist_url, library_dir)

            matched_folder = find_matching_folder(title, library_dir)
            file_count = len([f for f in os.listdir(matched_folder) if os.path.isfile(os.path.join(matched_folder, f))])

            update_progress(task_id, "Converting files...", 60)
            convert_all_mp3_to_m4a(matched_folder, delete_original=True)

            update_progress(task_id, "Adding metadata...", 80)
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

                delete_others = False

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
                        break

                prefix += 1

                if processed == int(metadata.get("TOTALTRACKS")):
                    delete_others = True
                    break

                if delete_others:
                    for filename in os.listdir(matched_folder):
                        if filename.startswith(str(prefix)):
                            file_path = os.path.join(matched_folder, filename)
                            try:
                                os.remove(file_path)
                                print(f"Deleted leftover mp3: {filename}")
                            except Exception as e:
                                print(f"Failed to delete {filename}: {e}")

        else:

            update_progress(task_id, "Downloading single track...", 30)
            song = songs[0].find_element(By.CSS_SELECTOR, '.yt-simple-endpoint.style-scope.ytd-video-renderer')
            song_url = song.get_attribute('href')

            print(f"Downloading song from: {song_url}")
            title_folder = download_as_mp3(song_url, library_dir)
            matched_folder = find_matching_folder(title_folder, library_dir)
            update_progress(task_id, "Converting to M4A...", 60)
            convert_all_mp3_to_m4a(matched_folder, delete_original=True)

            update_progress(task_id, "Adding metadata...", 80)

            metadata_filepath = None
            metadata_filepath = find_best_metadata_file(title_folder, metadata_dir)

            metadata = recover_metadata(metadata_filepath)
            filename = os.listdir(matched_folder)[0]

            artists = metadata.get("ARTISTS")
            if artists is None:
                artists_list = []
            elif isinstance(artists, list):
                artists_list = artists
            else:
                artists_list = [artists]

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

        first_song = None
        for f in os.listdir(matched_folder):
            if f.lower().endswith(('.m4a')):
                first_song = os.path.join(matched_folder, f)
                break

        if first_song:
            audio = MP4(first_song)
            album_tag = audio.tags.get('\xa9alb')
            if album_tag and album_tag[0]:
                album_name = album_tag[0]

                safe_album_name = re.sub(r'[\\/:*?"<>|]', '', album_name).strip()
                parent_dir = os.path.dirname(matched_folder)
                new_folder_path = os.path.join(parent_dir, safe_album_name)
                if not os.path.exists(new_folder_path):
                    os.rename(matched_folder, new_folder_path)
                    print(f"Renamed folder to: {safe_album_name}")
                else:
                    print(f"Folder '{safe_album_name}' already exists, not renamed.")

        
        update_progress(task_id, "Cleaning up...", 95)
        cleanup_metadata_dir(metadata_dir)

        driver.quit()
        update_progress(task_id, "Download completed", 100)

        time.sleep(30)
        if task_id in download_progress:
            del download_progress[task_id]

    except Exception as e:
        update_progress(task_id, f'Error: {str(e)}', -1)

@app.route('/progress/<task_id>')
def progress(task_id):

    progress = download_progress.get(task_id, {'message': 'Starting...', 'percentage': 0})
    return {
        'message': progress['message'],
        'percentage': progress['percentage']
    }

@app.route('/', methods=['GET', 'POST'])
def home():

    form = SearchForm()
    confirm_form = ConfirmForm()

    if request.method == 'GET':
        if request.args.get('download') == 'success':
            flash('Download completed successfully')

        if not request.args.get('from_redirect'):
            session.pop('title', None)
            session.pop('artist', None)
            session.pop('current_search', None)
            session.pop('currentid', None)
            session.pop('current_task', None)
            print("GET request - session cleared")

    if request.method == 'POST':
        
        if 'yes' in request.form or 'no' in request.form:

            if 'yes' in request.form:

                current_search = session.get('current_search')
                if not current_search:
                    flash('No search data found. Please search again.')
                    return render_template('home.html', form=form, confirm_form=confirm_form, active_page='Home')

                task_id = str(uuid.uuid4())
                session['current_task'] = task_id

                thread = threading.Thread(target=download_with_progress, args=(current_search, task_id))
                thread.daemon = True
                thread.start()

                return render_template('progress.html', active_page='Home', task_id=task_id)

            elif 'no' in request.form:

                currentid = session.get('currentid', 0)
                nextid = currentid + 1
                session['currentid'] = nextid
                
                title = session.get('title')
                artist = session.get('artist')
                
                if not title or not artist:

                    flash('Search session expired. Please search again.')
                    return render_template('home.html', form=form, confirm_form=confirm_form, active_page='Home')
                
                return show_search_results(form, confirm_form, title, artist, nextid)
        
        elif form.validate_on_submit():

            title = form.album.data
            artist = form.artist.data
                
            if not title.strip() or not artist.strip():
                flash('Please enter an album & artist name to search. Both are required.')
                return render_template('home.html', form=form, confirm_form=confirm_form, active_page='Home')
                
            session['title'] = title
            session['artist'] = artist
            session['currentid'] = 0
                
            return show_search_results(form, confirm_form, title, artist, 0)

    return render_template('home.html', form=form, confirm_form=confirm_form, active_page='Home')

@app.route('/Library')
def library():
    return render_template('library.html', active_page='Library')

@app.route('/settings')
def settings():
    return render_template('settings.html', active_page='Settings')

if __name__ == '__main__':
    app.run(debug=True)