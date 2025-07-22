from mutagen.mp4 import MP4, MP4FreeForm

def add_metadata(file_path, artists, album=None, albumartist=None, albumsort=None, artist=None, artistsort=None, compilation=None, copyright=None, 
                 discnumber=None, genre=None, itunesadvisory=None, itunesalbumid=None, itunesartistid=None, itunescatalogid=None, itunesgenreid=None,
                 itunesgapless=None, itunesmediatype=None, title=None, titlesort=None, totaltracks=None, track=None, year=None):

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

    audio["cpil"] = [compilation]

    if copyright:
        audio["cprt"] = [copyright]

    audio["disk"] = [(discnumber, 1)]

    if genre:
        audio["\xa9gen"] = [genre]

    audio["rtng"] = [itunesadvisory]

    if itunesalbumid:
        audio["plID"] = [itunesalbumid]

    if itunesartistid:
        audio["atID"] = [itunesartistid]

    if itunescatalogid:
        audio["cnID"] = [itunescatalogid]

    if itunesgenreid:
        audio["geID"] = [itunesgenreid]

    audio["pgap"] = [itunesgapless]

    audio["stik"] = [itunesmediatype]

    if title:
        audio["\xa9nam"] = [title]

    if titlesort:
        audio["sonm"] = [titlesort]

    audio["trkn"] = [(track, totaltracks)]
    
    if year:
        audio["\xa9day"] = [year]

    audio.save()
