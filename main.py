from flask import Flask, render_template, redirect, request, url_for
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms.fields import *
from wtforms.validators import *
import requests

# import sqlite3
#
# NOTE: Used this to edit my table as SQLAlchemy can't easily do that.
# db = sqlite3.connect('my-top-movies.db')
# cursor = db.cursor()
# cursor.execute("ALTER TABLE movies DROP COLUMN ranking")


app = Flask(__name__)
app.config['SECRET_KEY'] = 'YOUR_SECRET_KEY'
Bootstrap(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///my-top-movies.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# The Movie DataBase API Key (need to make a free account with them first)
TMDB_API_KEY = "YOUR_MOVIE_DATABASE_API_KEY"


class UpdateForm(FlaskForm):
    rating = DecimalField('Rating', validators=[Optional()])
    review = TextAreaField('Review')
    title = StringField('Title')
    year = IntegerField('Year', validators=[Optional()])
    description = TextAreaField('Description')
    # CHANGE TO URLField ****
    img_url = StringField('Image URL')
    submit = SubmitField('Submit')


class SearchForm(FlaskForm):
    title = StringField('Movie Title', validators=[DataRequired()])
    submit = SubmitField('Search')


class AddMovieForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    year = IntegerField('Year', validators=[DataRequired()])
    description = StringField('Description', validators=[DataRequired()])
    rating = DecimalField('Rating', validators=[DataRequired()])
    review = StringField('Review', validators=[DataRequired()])
# CHANGE TO URLField ****
    img_url = StringField('Image URL', validators=[DataRequired()])
    submit = SubmitField('Submit')


class Movies(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Float, nullable=False)
    review = db.Column(db.String(80), nullable=False)
    img_url = db.Column(db.String(80), nullable=True)


db.create_all()


@app.route("/")
def home():
    all_movies = Movies.query.order_by(Movies.rating).all()
    return render_template("index.html", all_movies=all_movies)


@app.route("/search", methods=["GET", "POST"])
def search_movies():
    search_form = SearchForm()
    if search_form.validate_on_submit():
        movie_to_search = search_form.title.data
        search_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&language=en-US&query={movie_to_search}&page=1&include_adult=false"
        response = requests.get(search_url)
        movie_data_list = response.json()["results"]
        return render_template("select.html", movie_data_list=movie_data_list)
    return render_template("search.html", search_form=search_form)


@app.route('/confirm', methods=["GET", "POST"])
def confirm_movie():
    title = request.args.get("title")
    year = request.args.get("year")
    description = request.args.get("description")
    img_url = request.args.get("img_url")
    if year == "?":
        year = 9999
    if img_url is None:
        img_url = "no_pic_available"
    # the image url they provide as a result is not the full url, so need to add it on at the end below
    full_url = f"https://www.themoviedb.org/t/p/w1280/{img_url}"
    new_movie = Movies(title=title,
                       year=year,
                       description=description,
                       rating=0,
                       review="ADD REVIEW",
                       img_url=full_url)
    db.session.add(new_movie)
    db.session.commit()
    movie = Movies.query.all()[-1]
    return redirect(url_for('update', id=movie.id))


@app.route("/add", methods=["GET", "POST"])
def add_movie():
    add_form = AddMovieForm()
    if add_form.validate_on_submit():
        m = {key: value for key, value in add_form.data.items() if key not in ("submit", "csrf_token")}
        new_movie = Movies(title=m["title"],
                           year=m["year"],
                           description=m["description"],
                           rating=str(m["rating"]),
                           review=m["review"],
                           img_url=m["img_url"])
        db.session.add(new_movie)
        db.session.commit()
        return redirect("/")
    return render_template("add.html", add_form=add_form)


@app.route("/update", methods=["GET", "POST"])
def update():
    # Can use this, or put it up in the route path and function arguments
    id = request.args.get("id")
    movie_to_update = Movies.query.get(id)
    update_form = UpdateForm()
    if update_form.validate_on_submit():
        m = {key: value for key, value in update_form.data.items() if key not in ("submit", "csrf_token")}
        if len(m["title"]) > 0:
            movie_to_update.title = m["title"]
        if m["year"] is not None:
            movie_to_update.year = m["year"]
        if len(m["description"]) > 0:
            movie_to_update.description = m["description"]
        if len(str(m["rating"])) > 0 and str(m["rating"]) != "None":
            movie_to_update.rating = str(m["rating"])
        if len(m["review"]) > 0:
            movie_to_update.review = m["review"]
        if len(m["img_url"]) > 0:
            movie_to_update.img_url = m["img_url"]
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("update.html", update_form=update_form, movie_to_update=movie_to_update)


@app.route("/delete/<id>")
def delete(id):
    movie_to_delete = Movies.query.get(id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


if __name__ == "__main__":
    app.run()
