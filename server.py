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

    # Numeric tags with conversion and error handling

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

    # Cover art
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

        # Get fresh elements every time
        grid_elem = driver.find_elements(By.CSS_SELECTOR, '.grid-item.svelte-1a54yxp')

        if not grid_elem:
            flash('No search results found.')
            return render_template('home.html', form=form, confirm_form=confirm_form, active_page='Home')

        if searchid >= len(grid_elem):
            flash('No more results found.')
            return render_template('home.html', form=form, confirm_form=confirm_form, active_page='Home')

        # Get the specific result
        current_element = grid_elem[searchid]
        
        try:
            Name = current_element.find_element(By.CSS_SELECTOR, '.top-search-lockup__primary__title.svelte-bg2ql4[dir="auto"]').get_attribute("textContent").strip()
            Details = current_element.find_element(By.CSS_SELECTOR, '.top-search-lockup__secondary.svelte-bg2ql4[data-testid="top-search-result-subtitle"]').get_attribute("textContent").strip()
            
            # Get image
            IMG = current_element.find_element(By.CSS_SELECTOR, '.svelte-uduhys')
            IMGCON = IMG.find_element(By.CSS_SELECTOR, 'source')
            srcset = IMGCON.get_attribute("srcset")
            imgurl = srcset.split(',')[1].split(' ')[0].strip()

            # Store the data in session for the "Yes" action
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

@app.route('/', methods=['GET', 'POST'])
def home():

    form = SearchForm()
    confirm_form = ConfirmForm()

    if request.method == 'GET' and not request.args.get('from_redirect'):

        session.pop('title', None)
        session.pop('artist', None)
        session.pop('current_search', None)
        session.pop('currentid', None)
        print("GET request - session cleared")

    if request.method == 'POST':
        
        if 'yes' in request.form or 'no' in request.form:

            if 'yes' in request.form:

                current_search = session.get('current_search')
                if not current_search:
                    flash('No search data found. Please search again.')
                    return render_template('home.html', form=form, confirm_form=confirm_form, active_page='Home')
                
                flash('Download started!')
                print("YES button clicked - download logic goes here")
                return redirect('/')
                
            elif 'no' in request.form:

                currentid = session.get('currentid', 0)
                nextid = currentid + 1
                session['currentid'] = nextid
                
                title = session.get('title')
                artist = session.get('artist')
                
                if not title or not artist:

                    flash('Search session expired. Please search again.')
                    return render_template('home.html', form=form, confirm_form=confirm_form, active_page='Home')
                
                print(f"NO button clicked - showing result {nextid}")
                return show_search_results(form, confirm_form, title, artist, nextid)
        
        elif form.validate_on_submit():

            title = form.album.data
            artist = form.artist.data
                
            if not title.strip() and not artist.strip():
                flash('Please enter an album or artist name to search.')
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
    app.run(debug=True)  # Add debug=True for easier testing