import os
import sys
from flask import Flask, render_template, request, flash, session, jsonify
from forms import SearchForm, ConfirmForm
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from mutagen.mp4 import MP4, MP4FreeForm, MP4Cover
import yt_dlp
from pydub import AudioSegment
from ammr import ExtractMetadata
import re
import threading
import time
import uuid
import secrets
import threading
import webview
import json
import subprocess
import platform

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def create_safe_driver():
    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        options.add_argument("--log-level=3")
        service = Service(log_path=os.devnull)
        
        driver = webdriver.Chrome(options=options, service=service)
        return driver
    except Exception as e:
        print(f"Failed to create WebDriver: {e}")
        return None

app = Flask(__name__, template_folder=resource_path('templates'), static_folder=resource_path('static'))
app.config['SECRET_KEY'] = secrets.token_urlsafe(32)

def add_metadata(file_path, image_path, artists, album, albumartist, albumsort, artist, artistsort, comment, compilation, copyright, 
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
    if comment:
        audio["\xa9cmt"] = [comment]

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
    current_key = None
    current_value = ""

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    for line in lines:
        line = line.rstrip('\n\r')

        if ' | ' in line and not line.startswith(' '):

            if current_key:
                metadata[current_key] = current_value.strip()
            
            parts = line.split(' | ', 1)
            if len(parts) == 2:
                current_key = parts[0].strip()
                current_value = parts[1]
            else:
                current_key = None
                current_value = ""
        else:
            if current_key:
                current_value += '\n' + line

    if current_key:
        metadata[current_key] = current_value.strip()

    return metadata

def download_as_mp3(youtube_url, library_dir, title, tracktitle, index):

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(library_dir, f'{title}/{index} {tracktitle}.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320',
        }],
        'quiet': True,
        'noplaylist': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.extract_info(youtube_url, download=True)

def convert_all_mp3_to_m4a(folder_path, task_id, delete_original=False):

    mp3_files = [f for f in os.listdir(folder_path) if f.lower().endswith(".mp3")]
    total_files = len(mp3_files)
    converted_count = 0

    for filename in mp3_files:
        mp3_path = os.path.join(folder_path, filename)
        m4a_path = os.path.join(folder_path, os.path.splitext(filename)[0] + ".m4a")
            
        try:
            if converted_count % 5 == 0 or converted_count == total_files - 1:
                progress_percent = 60 + (converted_count / total_files * 20)
                update_progress(task_id, f"Converting files... {converted_count + 1}/{total_files}", int(progress_percent))

            audio = AudioSegment.from_mp3(mp3_path)
            audio.export(m4a_path, format="ipod")
                
            if delete_original:
                os.remove(mp3_path)

            converted_count += 1

        except Exception as e:
            print(f"Failed to convert {filename}: {e}")
            converted_count += 1
    
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

def get_user_data_directory():

    app_data = os.environ.get('LOCALAPPDATA', os.path.join(os.path.expanduser('~'), 'AppData', 'Local'))
    app_dir = os.path.join(app_data, 'iTuneUp')
    
    os.makedirs(app_dir, exist_ok=True)
    return app_dir

def setup_directories():

    if getattr(sys, 'frozen', False):
        user_data_dir = get_user_data_directory()
        metadata_dir = os.path.join(user_data_dir, "metadata")
        library_dir = os.path.join(user_data_dir, "library")

        print(f"Using user data directory: {user_data_dir}")
    else:
        app_dir = os.path.dirname(os.path.abspath(__file__))
        metadata_dir = os.path.join(app_dir, "metadata")
        library_dir = os.path.join(app_dir, "library")

    os.makedirs(metadata_dir, exist_ok=True)
    os.makedirs(library_dir, exist_ok=True)

    print(f"Library directory: {library_dir}")
    print(f"Metadata directory: {metadata_dir}")

    return metadata_dir, library_dir

def show_search_results(form, confirm_form, title, artist, searchid):

    driver = create_safe_driver()
    if not driver:
        flash('Failed to create WebDriver. Please check your Chrome installation.')
        return render_template('home.html', form=form, confirm_form=confirm_form, active_page='Home')

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

        filecount = 0

        for filename in os.listdir(metadata_dir):
            if filename.endswith('.txt'):
                filecount += 1

        update_progress(task_id, "Searching for content...", 20)

        if filecount > 1:

            processed = 0
            update_progress(task_id, "Downloading album tracks...", 30)

            albumtitle = title

            for filename in os.listdir(metadata_dir):
                if filename.endswith('.txt'):

                    index = int(filename.split('.txt')[0].split(' ')[0])
                    title = filename.split('.txt')[0].split(' ', 1)[1]
                    title_query = title.replace(' ', '+').replace("'", '%27')
                    artist_query = artist.replace(' ', '+').replace("'", '%27')
                    url = f"https://www.youtube.com/results?search_query={title_query}+{artist_query}"

                    driver = create_safe_driver()
                    if not driver:
                        update_progress(task_id, 'Failed to create WebDriver. Please check your Chrome installation.', -1)
                        return
                    driver.get(url)

    
                    songs = driver.find_elements(By.ID, 'video-title')
                    for todlsong in songs:
                        if 'official video' in todlsong.get_attribute('title').lower():
                            continue
                        else:
                            noclip = todlsong
                            break
                    song = noclip.get_attribute('href')
                    download_as_mp3(song, library_dir, albumtitle, title, index)
                    processed += 1

                    update_progress(task_id, f"Downloaded {processed}/{filecount} tracks", int(30 + (processed / filecount * 30)))
                    
                    driver.quit()

            update_progress(task_id, "Converting files to M4A...", 60)
            album_folder = os.path.join(library_dir, albumtitle)

            convert_all_mp3_to_m4a(album_folder, task_id, delete_original=True)

            update_progress(task_id, "Adding metadata...", 80)

            metadata_files = []
            for filename in os.listdir(metadata_dir):
                if filename.endswith('.txt'):
                    try:
                        track_num = int(filename.split(' ')[0])
                        metadata_files.append((track_num, filename))
                    except ValueError:
                        continue

            metadata_files.sort(key=lambda x: x[0])

            total_metadata_files = len(metadata_files)
            processed = 0    

            for track_num, filename in metadata_files:
                try:
                    metadata_filepath = os.path.join(metadata_dir, filename)
                    metadata = recover_metadata(metadata_filepath)

                    artists = metadata.get("ARTISTS")
                    if artists is None:
                        artists_list = []
                    elif isinstance(artists, list):
                        artists_list = artists
                    else:
                        artists_list = [artists]

                    song_filepath = os.path.join(album_folder, filename.split('.txt')[0] + '.m4a')

                    if os.path.exists(song_filepath):

                        add_metadata(
                            song_filepath,
                            os.path.join(metadata_dir, 'artwork.jpg'),
                            artists_list,
                            metadata.get("ALBUM"),
                            metadata.get("ALBUMARTIST"),
                            metadata.get("ALBUMSORT"),
                            metadata.get("ARTIST"),
                            metadata.get("ARTISTSORT"),
                            metadata.get("COMMENT"),
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
                        progress_percent = 80 + (processed / total_metadata_files * 15)
                        update_progress(task_id, f"Applied metadata to {processed}/{total_metadata_files}", progress_percent)

                    else:
                        update_progress(task_id, f'Error: Music file not found for metadata: {filename}', -1)

                except Exception as e:
                    print(f"Error processing metadata file {filename}: {str(e)}")
                    update_progress(task_id, f'Error processing metadata file {filename}: {str(e)}', -1)
                    continue

        else:

            update_progress(task_id, "Downloading single track...", 30)

            albumtitle = title
            
            for filename in os.listdir(metadata_dir):
                if filename.endswith('.txt'):

                    title = filename.split('.txt')[0].split(' ', 1)[1]
                    title_query = title.replace(' ', '+').replace("'", '%27')
                    artist_query = artist.replace(' ', '+').replace("'", '%27')
                    url = f"https://www.youtube.com/results?search_query={title_query}+{artist_query}"

                    driver = create_safe_driver()
                    if not driver:
                        update_progress(task_id, 'Failed to create WebDriver. Please check your Chrome installation.', -1)
                        return
                    driver.get(url)

                    songs = driver.find_elements(By.ID, 'video-title')
                    for todlsong in songs:
                        if 'official video' in todlsong.get_attribute('title').lower():
                            continue
                        else:
                            noclip = todlsong
                            break
                    song = noclip.get_attribute('href')
                    download_as_mp3(song, library_dir, albumtitle, title, 1)

                    driver.quit()

            album_folder = os.path.join(library_dir, albumtitle)
            update_progress(task_id, "Converting to M4A...", 60)
            convert_all_mp3_to_m4a(album_folder, task_id, delete_original=True)

            update_progress(task_id, "Adding metadata...", 80)

            for filename in os.listdir(metadata_dir):
                if filename.endswith('.txt'):
                    metadata_filepath = os.path.join(metadata_dir, filename)
                    music_filepath = os.path.join(album_folder, filename.split('.txt')[0] + '.m4a')

            metadata = recover_metadata(metadata_filepath)

            artists = metadata.get("ARTISTS")
            if artists is None:
                artists_list = []
            elif isinstance(artists, list):
                artists_list = artists
            else:
                artists_list = [artists]

            add_metadata(
                music_filepath,
                os.path.join(metadata_dir, 'artwork.jpg'),
                artists_list,
                metadata.get("ALBUM"),
                metadata.get("ALBUMARTIST"),
                metadata.get("ALBUMSORT"),
                metadata.get("ARTIST"),
                metadata.get("ARTISTSORT"),
                metadata.get("COMMENT"),
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
     
        update_progress(task_id, "Cleaning up...", 95)
        cleanup_metadata_dir(metadata_dir)

        update_progress(task_id, "Download completed", 100)

        time.sleep(30)
        if task_id in download_progress:
            del download_progress[task_id]

    except Exception as e:
        update_progress(task_id, f'Error: {str(e)}', -1)

def calculate_album_duration(folder_path):

    total_duration = 0.0

    for filename in os.listdir(folder_path):
        if filename.lower().endswith(('.m4a')):
            file_path = os.path.join(folder_path, filename)
            try:
                audio = MP4(file_path)
                duration = audio.info.length
                total_duration += duration
            except Exception as e:
                print(f"Error reading {file_path}: {e}")

    if total_duration > 0:
        total_duration = int(total_duration / 60)
    else:
        total_duration = 0

    return total_duration

def scan_library():

    if getattr(sys, 'frozen', False):

        user_data_dir = get_user_data_directory()
        library_dir = os.path.join(user_data_dir, "library")
    else:

        app_dir = os.path.dirname(os.path.abspath(__file__))
        library_dir = os.path.join(app_dir, "library")

    if not os.path.exists(library_dir):
        print("Library directory does not exist.")
        return []
    
    albums = []

    for folder in os.listdir(library_dir):
        folder_path = os.path.join(library_dir, folder)
        if os.path.isdir(folder_path):

            total_duration = calculate_album_duration(folder_path)

            album_info = None
            track_count = 0
            track_list = []

            for filename in os.listdir(folder_path):
                if filename.lower().endswith(('.m4a')):
                    track_list.append(filename.split('.m4a')[0])
                    track_count += 1
                    if album_info is None:
                        file_path = os.path.join(folder_path, filename)
                        try:
                            audio = MP4(file_path)

                            def clean_string(value):
                                if not value:
                                    return 'Unknown'
                                cleaned = str(value).replace('\x00', '').replace('\n', ' ').replace('\r', ' ')
                                return cleaned.strip()
                                
                            album_info = {
                                'folder_name': clean_string(folder),
                                'album': clean_string(audio.tags.get('\xa9alb', ['Unknown Album'])[0]),
                                'artist': clean_string(audio.tags.get('\xa9ART', ['Unknown Artist'])[0]),
                                'year': clean_string(audio.tags.get('\xa9day', ['Unknown'])[0]),
                                'genre': clean_string(audio.tags.get('\xa9gen', ['Unknown'])[0]),
                                'copyright': clean_string(audio.tags.get('cprt', ['Unknown'])[0]),
                                'track_count': 0,
                                'total_tracks': audio.tags.get('trkn', [(0, 0)])[0][1] if audio.tags.get('trkn') else track_count,
                                'duration': total_duration,
                                'track_list': track_list
                            }

                        except Exception as e:
                            print(f"Error reading {file_path}: {e}")
                            album_info = {
                                'folder_name': folder,
                                'album': folder,
                                'artist': 'Unknown Artist',
                                'year': 'Unknown',
                                'genre': 'Unknown',
                                'copyright': 'Unknown',
                                'track_count': 0,
                                'total_tracks': 0,
                                'duration': 0.0,
                                'track_list': []
                            }

            if album_info:
                album_info['track_count'] = track_count
                albums.append(album_info)

    return albums

@app.route('/Library')
def library():
    albums = scan_library()
    return render_template('library.html', active_page='Library', albums=albums)

@app.route('/album_cover/<album_folder>')
def album_cover(album_folder):

    if getattr(sys, 'frozen', False):

        user_data_dir = get_user_data_directory()
        library_dir = os.path.join(user_data_dir, "library")
    else:
        app_dir = os.path.dirname(os.path.abspath(__file__))
        library_dir = os.path.join(app_dir, "library")

    folder_path = os.path.join(library_dir, album_folder)
    
    if not os.path.exists(folder_path):
        return "", 404
    
    for file_name in os.listdir(folder_path):
        if file_name.lower().endswith('.m4a'):
            file_path = os.path.join(folder_path, file_name)
            try:
                audio = MP4(file_path)
                if 'covr' in audio.tags and audio.tags['covr']:
                    cover_data = audio.tags['covr'][0]
                    from flask import Response
                    return Response(cover_data, mimetype='image/jpeg')
            except Exception:
                pass
    
    return "", 404

@app.route('/progress/<task_id>')
def progress(task_id):

    progress_data = download_progress.get(task_id, {'message': 'Starting...', 'percentage': 0})
    return progress_data

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

                def run_download():
                    try:
                        download_with_progress(current_search, task_id)
                    except Exception as e:
                        print(f"Download thread error: {str(e)}")
                        update_progress(task_id, f'Error: {str(e)}', -1)

                thread = threading.Thread(target=run_download)
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

@app.route('/settings')
def settings():
    return render_template('settings.html', active_page='Settings')

@app.route('/api/minimize')
def api_minimize():
    try:
        import webview
        webview.windows[0].minimize()
        return {'status': 'success'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

window_maximized = False

@app.route('/api/maximize')
def api_maximize():
    global window_maximized
    try:
        import webview
        window = webview.windows[0]
        
        if window_maximized:
            window.restore()
            window_maximized = False
        else:
            window.maximize()
            window_maximized = True
            
        return {'status': 'success', 'maximized': window_maximized}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}
    
@app.route('/api/close')
def api_close():
    try:
        import webview
        webview.windows[0].destroy()
        return {'status': 'success'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}
    
@app.route('/api/save_setting', methods=['POST'])
def save_setting():
    try:
        data = request.get_json()
        key = data.get('key')
        value = data.get('value')
        
        if not key:
            return {'status': 'error', 'message': 'Key is required'}
        
        if getattr(sys, 'frozen', False):
            user_data_dir = get_user_data_directory()
            settings_file = os.path.join(user_data_dir, 'user_settings.json')
        else:
            app_dir = os.path.dirname(os.path.abspath(__file__))
            settings_file = os.path.join(app_dir, 'user_settings.json')
        
        settings = {}
        if os.path.exists(settings_file):
            try:
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
            except:
                settings = {}
        
        settings[key] = value

        with open(settings_file, 'w') as f:
            json.dump(settings, f)
        
        return {'status': 'success'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}
    
@app.route('/api/load_settings')
def load_settings():
    try:
        if getattr(sys, 'frozen', False):
            user_data_dir = get_user_data_directory()
            settings_file = os.path.join(user_data_dir, 'user_settings.json')
        else:
            app_dir = os.path.dirname(os.path.abspath(__file__))
            settings_file = os.path.join(app_dir, 'user_settings.json')

        settings = {}
        if os.path.exists(settings_file):
            try:
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
            except:
                settings = {}
        
        return {'status': 'success', 'settings': settings}
    except Exception as e:
        return {'status': 'error', 'message': str(e), 'settings': {}}
    
@app.route('/open-library-folder', methods=['POST'])
def open_library_folder():
    try:
        if getattr(sys, 'frozen', False):
            user_data_dir = get_user_data_directory()
            library_path = os.path.join(user_data_dir, "library")
        else:
            app_dir = os.path.dirname(os.path.abspath(__file__))
            library_path = os.path.join(app_dir, "library")
        
        if not os.path.exists(library_path):
            os.makedirs(library_path, exist_ok=True)
        
        if platform.system() == 'Windows':
            subprocess.run(['explorer', library_path], check=True)
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Unsupported operating system'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def run_flask():
    app.run(host='127.0.0.1', port=5000, debug=False)

if __name__ == '__main__':

    if os.name == 'nt':
        import subprocess
        original_popen = subprocess.Popen
        def hidden_popen(*args, **kwargs):
            if 'creationflags' not in kwargs:
                kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
            return original_popen(*args, **kwargs)
        subprocess.Popen = hidden_popen
    
    threading.Thread(target=run_flask, daemon=True).start()

    window = webview.create_window(
        "iTuneUp",
        "http://127.0.0.1:5000",
        width=1440,
        height=820,
        resizable=True,
        frameless=True,
        on_top=False,
        shadow=True,
    )

    webview.start(gui='edgechromium', debug=False, private_mode=False, storage_path=None)