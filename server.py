from flask import Flask, render_template, redirect, request
from forms import SearchForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Password1594826kjk!'

@app.route('/', methods=['GET', 'POST'])
def home():
    form = SearchForm()
    if form.is_submitted():
        title = form.album.data
        artist = form.artist.data
    return render_template('home.html', form=form, active_page='Home')

@app.route('/Library')
def library():
    return render_template('library.html', active_page='Library')

@app.route('/settings')
def settings():
    return render_template('settings.html', active_page='Settings')

if __name__ == '__main__':
    app.run()