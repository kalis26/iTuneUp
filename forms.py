from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import Optional

class SearchForm(FlaskForm):
    album = StringField('Album', validators=[Optional()], render_kw={"placeholder": "Album or song title..."})
    artist = StringField('Artist', validators=[Optional()], render_kw={"placeholder": "Artist..."})
    search = SubmitField('Search')

class ConfirmForm(FlaskForm):
    yes = SubmitField('Yes')
    no = SubmitField('No')