from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField
from wtforms.validators import Optional

class SearchForm(FlaskForm):
    album = StringField('Album', validators=[Optional()], render_kw={"placeholder": "Album or song title..."})
    artist = StringField('Artist', validators=[Optional()], render_kw={"placeholder": "Artist..."})
    apple_url = StringField('Apple URL', validators=[Optional()], render_kw={"placeholder": "https://music.apple.com/..."})
    single_song_only = BooleanField('Single song only')
    search = SubmitField('Search')
    download_from_url = SubmitField('Download From URL')

class ConfirmForm(FlaskForm):
    yes = SubmitField('Yes')
    no = SubmitField('No')