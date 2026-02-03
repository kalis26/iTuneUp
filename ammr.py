from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import re
import os
import sys
import contextlib
import unicodedata
import urllib.parse
import datetime
import shutil
from colorama import Fore, Back, Style, init


# Function to sanitize filenames for Windows
def sanitize_filename(filename):
    """Remove or replace characters that are invalid in Windows filenames."""
    # Windows invalid characters: \ / : * ? " < > |
    invalid_chars = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    # Also strip leading/trailing spaces and dots
    filename = filename.strip(' .')
    return filename


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

# Yes/No input

def get_yes_no(prompt):
    while True:
        answer = input(prompt + " (yes/no): ").strip().lower()
        if answer in ("yes", "no"):
            return answer
        print("Please enter 'yes' or 'no'.")
        
# Function to extract the Albums ID

def ExtractAlbumID(url, id):

    options = webdriver.ChromeOptions()
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.add_argument("--headless")
    options.add_argument("--log-level=3")
    options.add_argument("--disable-logging")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    service = Service(log_path=os.devnull)
    with suppress_stderr():
        driver = webdriver.Chrome(service=service, options=options)

    driver.get(url)

    elements_with_class = driver.find_elements(
    By.CSS_SELECTOR,
    'a[data-testid="click-action"][href*="?i="]'
    )

    url = elements_with_class[id].get_attribute("href")

    parsed = urllib.parse.urlparse(url)
    last_segment = parsed.path.rstrip('/').split('/')[-1]
    if last_segment.isdigit():
        ALBUMID = last_segment
    else:
        match = re.search(r'(\d+)(?!.*\d)', parsed.path)
        ALBUMID = match.group(1) if match else ""

    return url, ALBUMID

# Function to extract the albums title

def ExtractAlbumTitle(argument):

    albumtitle_elem = argument.find_element(
    By.CSS_SELECTOR,
    '[data-testid="non-editable-product-title"] span[dir="auto"]'
    )
    ALBUM = albumtitle_elem.text.strip()

    return ALBUM

# Function to extract the artist name & ID
    
def ExtractArtistAndID(argument):
    albumartist_elems = argument.find_elements(
        By.CSS_SELECTOR,
        '[data-testid="product-subtitles"] > a'
    )

    if not albumartist_elems:
        return "", ""

    # Use the first <a> for the artist ID
    artist_url = albumartist_elems[0].get_attribute("href")

    parsed_artist = urllib.parse.urlparse(artist_url)
    last_artist_segment = parsed_artist.path.rstrip('/').split('/')[-1]
    if last_artist_segment.isdigit():
        ARTISTID = last_artist_segment
    else:
        match = re.search(r'(\d+)(?!.*\d)', parsed_artist.path)
        ARTISTID = match.group(1) if match else ""

    # Collect all artist names
    if len(albumartist_elems) > 1:
        ALBUMARTIST = ', '.join([elem.text.strip() for elem in albumartist_elems])
    else:
        ALBUMARTIST = albumartist_elems[0].text.strip()

    return ALBUMARTIST, ARTISTID

# Function to extract the genre

def ExtractGenre(argument):

    genre_elem = argument.find_element(
    By.CSS_SELECTOR,
    'div.headings__metadata-bottom'
    )
    GENRE = genre_elem.text.strip()
    GENRE = GENRE.split('·')[0].strip()
    GENRE = unicodedata.normalize('NFKD', GENRE).encode('ASCII', 'ignore').decode('utf-8')
    GENRE = GENRE.title()

    return GENRE

# Function to extract the genre ID

def GenreSelection(argument):
    match argument:
        case "Country":
            return 6
        case "Pop":
            return 14
        case "Hip-Hop/Rap":
            return 18
        case "Rock":
            return 21
        case "R&B/Soul":
            return 15
        case "Metal":
            return 1153
        case "Blues":
            return 2
        case "Jazz":
            return 11
        case "Electronic":
            return 7
        case "Alternative":
            return 20
        case "Indie Pop":
            return 20
        case "K-Pop":
            return 14
        case "French Pop":
            return 50000064
        case default:
            return 0

# Function to extract the Catalog ID (Song ID in the Apple Music library)

def ExtractCatalogID(argument):

    track_elem = argument.find_element(
    By.CSS_SELECTOR,
    '[data-testid="track-title"]'
    )
    song_url_elem = track_elem.find_element(By.XPATH, './ancestor::a')

    song_url = song_url_elem.get_attribute("href")

    parsed_song = urllib.parse.urlparse(song_url)
    last_song_segment = parsed_song.path.rstrip('/').split('/')[-1]
    if last_song_segment.isdigit():
        CATALOGID = last_song_segment
    else:
        match = re.search(r'(\d+)(?!.*\d)', parsed_song.path)
        CATALOGID = match.group(1) if match else ""

    return CATALOGID

# Function to extract the song title

def ExtractSongTitle(argument):

    song_name_elem = argument.find_element(
    By.CSS_SELECTOR,
    '[data-testid="track-title"]'
    )
    TITLE = song_name_elem.text.strip()

    return TITLE
    
# Function to extract the track number of the song

def ExtractTrackNumber(argument):

    track_elem = argument.find_element(By.CSS_SELECTOR, '[data-testid="track-number"]')
    TRACKNUMBER = track_elem.get_attribute("textContent").strip()

    return TRACKNUMBER

# Function to extract the Itunes advisory tag (Explicit or not)

def ExtractItunesAdvisory(argument):

    try:
        argument.find_element(
            By.CSS_SELECTOR,
            '[data-testid="track-list-item"] [data-testid="explicit-badge"]'
        )
        ITUNESADVISORY = 1
    except NoSuchElementException:
        ITUNESADVISORY = 0

    return ITUNESADVISORY

# Function to extract the various artists of one song (if there are)

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

def ExtractArtists(argument, fallback_artist):

    ARTISTS = []

    try:
        artists_list = argument.find_elements(
            By.CSS_SELECTOR,
            '[data-testid="track-title-by-line"] a[data-testid="click-action"]'
        )
        for artist_elem in artists_list:
            name = artist_elem.text.strip()
            if name:
                ARTISTS.append(name)
    except NoSuchElementException:
        pass

    if not ARTISTS:
        ARTIST = fallback_artist
    else:
        ARTIST = ', '.join(ARTISTS)

    return ARTIST, ARTISTS


# Function to extract the comment of the album (or Editor's Notes)

def ExtractComment(argument):

    try:
        comment_elem = argument.find_element(
            By.CSS_SELECTOR,
            '[data-testid="truncate-text"]'
        )
        COMMENT = comment_elem.text.strip()
    except NoSuchElementException:
        COMMENT = ""
    
    return COMMENT

def ExtractCopyrightAndDate(argument):

    footer_elem = argument.find_element(
        By.CSS_SELECTOR,
        '[data-testid="tracklist-footer-description"]'
    )
    footer_text = footer_elem.text.strip()

    lines = [line.strip() for line in footer_text.split('\n') if line.strip()]

    def parse_english_date(date_str):
        try:
            dt = datetime.datetime.strptime(date_str, "%B %d, %Y")
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            return date_str

    YEAR = lines[0]
    YEAR = parse_english_date(YEAR)
    YEAR = YEAR + "T12:00:00Z"

    COPYRIGHT = lines[2]

    return COPYRIGHT, YEAR

def ExtractMetadata(driver, id, metadata_dir):

    TOTALDISCS = 1
    DISCNUMBER = 1
    COMPILATION = 0
    ITUNESGAPLESS = 0
    ITUNESMEDIATYPE = "Normal"

    url, ITUNESALBUMID = ExtractAlbumID(driver, id)

    options = webdriver.ChromeOptions()
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.add_argument("--headless")
    options.add_argument("--log-level=3")
    options.add_argument("--disable-logging")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    service = Service(log_path=os.devnull)

    with suppress_stderr():
        driver = webdriver.Chrome(service=service, options=options)

    driver.get(url)

    # wait for the album page to load and the songs list to be present
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'songs-list-row'))
        )
    except Exception:
        # fallback short sleep if wait fails for any reason
        import time
        time.sleep(1)

    ALBUM = ExtractAlbumTitle(driver)
    ALBUM.replace('?', '_').replace('.', '@')
    ALBUMSORT = ALBUM
    ALBUMARTIST, ITUNESARTISTID = ExtractArtistAndID(driver)
    GENRE = ExtractGenre(driver)
    ITUNESGENREID = GenreSelection(GENRE)
    COPYRIGHT, YEAR = ExtractCopyrightAndDate(driver)
    COMMENT = ExtractComment(driver)

    # collect song row elements; ensure they are present and stable
    songs_elem = driver.find_elements(By.CLASS_NAME, 'songs-list-row')
    if not songs_elem:
        # try a short wait and requery
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'songs-list-row'))
            )
            songs_elem = driver.find_elements(By.CLASS_NAME, 'songs-list-row')
        except Exception:
            songs_elem = []

    TOTALTRACKS = len(songs_elem)

    for song in songs_elem:

        # extract scoped song data (use element.find_... so we stay within the row)
        ITUNESCATALOGID = ExtractCatalogID(song)
        TITLE = ExtractSongTitle(song)
        TITLE = TITLE.replace('?', '_')    
        TITLESORT = TITLE
        TRACKNUMBER = ExtractTrackNumber(song)
        # normalize track number
        TRACKNUMBER = TRACKNUMBER.strip()
        ITUNESADVISORY = ExtractItunesAdvisory(song)
        ARTIST, ARTISTS = ExtractArtists(song, ALBUMARTIST)
        ARTISTSORT = ARTIST

        SAFE_TITLE = sanitize_filename(TITLE)
        FILENAME = os.path.join(metadata_dir, TRACKNUMBER + " " + SAFE_TITLE + ".txt")
        print(f"Writing metadata for track {TRACKNUMBER}: {TITLE}")
        with open(FILENAME, "w", encoding="utf-8") as f:
            print("ALBUM           | ", ALBUM.replace('@', '.').replace('_', '?'), file=f)
            print("ALBUMARTIST     | ", ALBUMARTIST, file=f)
            print('ALBUMSORT       | ', ALBUMSORT, file=f)
            print('ARTIST          | ', ARTIST, file=f)
            print('ARTISTSORT      | ', ARTISTSORT, file=f)
            if ARTISTS:
                for artists in ARTISTS:
                    print('ARTISTS         | ', artists, file=f)
            print('COMMENT         | ', COMMENT, file=f)
            print('COMPILATION     | ', COMPILATION, file=f)
            print('COPYRIGHT       | ', COPYRIGHT, file=f)
            print('DISCNUMBER      | ', DISCNUMBER, file=f)
            print('GENRE           | ', GENRE, file=f)
            print("ITUNESADVISORY  | ", ITUNESADVISORY, file=f)
            print("ITUNESALBUMID   | ", ITUNESALBUMID, file=f)
            print("ITUNESARTISTID  | ", ITUNESARTISTID, file=f)
            print("ITUNESCATALOGID | ", ITUNESCATALOGID, file=f)
            print('ITUNESGENREID   | ', ITUNESGENREID, file=f)
            print('ITUNESGAPLESS   | ', ITUNESGAPLESS, file=f)
            print('ITUNESMEDIATYPE | ', ITUNESMEDIATYPE, file=f)
            print("TITLE           | ", TITLE.replace('_', '?'), file=f)
            print("TITLESORT       | ", TITLESORT, file=f)
            print("TOTALDISCS      | ", TOTALDISCS, file=f)
            print("TOTALTRACKS     | ", TOTALTRACKS, file=f)
            print("TRACK           | ", TRACKNUMBER, file=f)
            print("YEAR            | ", YEAR, file=f)

        # get album artwork (wait for source element to be available)
        try:
            WebDriverWait(driver, 8).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'source[type="image/jpeg"]'))
            )
            source_elem = driver.find_element(By.CSS_SELECTOR, 'source[type="image/jpeg"]')
            srcset = source_elem.get_attribute("srcset")
        except Exception:
            srcset = ''

        urls = re.findall(r'(https?://[^\s,]+)\s+\d+w', srcset)
        if urls:
            last_url = urls[-1]
            img_data = requests.get(last_url).content
            image_path = os.path.join(metadata_dir, 'artwork.jpg')

            with open(image_path, 'wb') as handler:
                handler.write(img_data)
    
    driver.quit()

    return ALBUM, ALBUMARTIST

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def contin():
    input(Fore.LIGHTWHITE_EX + '\nPress enter to continue...')

def startmess():

    clear()
    print(Fore.BLUE + '                _      __  __  __  __    ____  ')
    print(Fore.BLUE + '               / \\    |  \\/  ||  \\/  |  |  _ \\ ')
    print(Fore.BLUE + '              / _ \\   | |\\/| || |\\/| |  | |_) |')
    print(Fore.BLUE + '             / ___ \\  | |  | || |  | |  |  _ < ')
    print(Fore.BLUE + '            /_/   \\_\\ |_|  |_||_|  |_|  |_| \\_\\')
    print('');
    print(Fore.CYAN + '              Apple Music Metadata Retriever')

def menu():

    clear()
    print(Fore.CYAN + '        Apple Music Metadata Retriever\n')
    print('[1] - Search for a song/album to retrieve metadata from')
    print('[2] - Exit the program')
    print('')


if __name__ == "__main__":

    app_dir = os.path.dirname(os.path.abspath(__file__))
    metadata_dir = os.path.join(app_dir, "metadata")
    os.makedirs(metadata_dir, exist_ok=True)

    for filename in os.listdir(metadata_dir):
        file_path = os.path.join(metadata_dir, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f'Failed to delete {file_path}. Reason: {e}')

    init(autoreset=True) 
    quit = False

    startmess()
    contin()
    clear()
    while not quit:
        menu()
        choice = input('Choose an option: ')
        print('')
        match choice:
            case '1':


                title = input("Enter the name of the song/album: ")
                artist = input("Enter the name of the artist: ")
                print('\n')
                url = f"https://music.apple.com/us/search?term={title.replace(' ', '%20')}%20{artist.replace(' ', '%20')}"

                options = webdriver.ChromeOptions()
                options.add_experimental_option('excludeSwitches', ['enable-logging'])
                options.add_argument("--headless")
                options.add_argument("--log-level=3")
                options.add_argument("--disable-logging")
                options.add_argument("--disable-gpu")
                options.add_argument("--no-sandbox")

                service = Service(log_path=os.devnull)

                with suppress_stderr():
                    driver = webdriver.Chrome(service=service, options=options)

                driver.get(url)

                grid_elem = driver.find_elements(By.CSS_SELECTOR, '.grid-item.svelte-1a54yxp')
                id = 0
                found = False
                abort = False
                while not found:

                    if id == len(grid_elem):
                        print(Fore.RED + "\nNo results found for your search. Aborting...")
                        found = True
                        abort = True
                    else:
                        Name = grid_elem[id].find_element(By.CSS_SELECTOR, '.top-search-lockup__primary__title.svelte-bg2ql4[dir="auto"]').get_attribute("textContent").strip()
                        Details = grid_elem[id].find_element(By.CSS_SELECTOR, '.top-search-lockup__secondary.svelte-bg2ql4[data-testid="top-search-result-subtitle"]').get_attribute("textContent").strip()
                        prompt = "Did you search for : " + Name + " / " + Details
                        proceed = get_yes_no(prompt)
                        if proceed == "yes":
                            found = True
                        else:
                            id = id + 1
                    
                    pass

                if not abort:

                    ExtractMetadata(driver, id, metadata_dir)

                    print(Fore.GREEN + '\nMetadata retrieved successfully. Access it in the metadata folder.')

                contin()

            case '2':

                print(Fore.LIGHTWHITE_EX + '\nExiting...')
                quit = True

            case default:

                print(Fore.RED + 'Enter a valid choice\n')
                contin()
