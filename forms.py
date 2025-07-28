from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

class SearchForm(FlaskForm):
    album = StringField(validators=[DataRequired()], render_kw={"placeholder": "Album or song title..."})
    artist = StringField(validators=[DataRequired()], render_kw={"placeholder": "Artist..."})
    search = SubmitField('Search')