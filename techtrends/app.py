import sqlite3

from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort
import logging

# Function to get a database connection.
# This function connects to database with the name `database.db`


db_file = "database.db"
number_of_connections = 0


def get_db_connection():
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    return connection

# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    connection.close()
    return post
    
def get_number_of_posts():
    connection = get_db_connection()
    post = connection.execute('SELECT COUNT(*) FROM posts').fetchall()
    connection.close()
    return post


# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

# Define the main route of the web application 
@app.route('/')
def index():
    global number_of_connections
    number_of_connections += 1
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    global number_of_connections
    number_of_connections += 1
    post = get_post(post_id)
    if post is None:
      app.logger.info("A non-existing article is accessed")
      return render_template('404.html'), 404
    else:

      app.logger.info('Article "%s" retrieved!', post[2])
      return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    app.logger.info('The "About Us" page is retrieved')
    return render_template('about.html')

# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            app.logger.info('Tentative to create an article without a title')
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            connection.close()
            global number_of_connections
            number_of_connections += 1
            app.logger.info('A new article "%s" is created ', title)

            return redirect(url_for('index'))

    return render_template('create.html')
    
@app.route('/healthz')
def healthcheck():
    response = app.response_class(
            response=json.dumps({"result":"OK - healthy"}),
            status=200,
            mimetype='application/json'
    )

    app.logger.info('Health request successfull')
    return response
    
@app.route('/metrics')
def metrics():
    posts = list(map(tuple, get_number_of_posts()))
    dict_data = {"db_connection_count": str(number_of_connections), "post_count": str(posts[0][0])}
    response = app.response_class(
            response=json.dumps(dict_data),
            status=200,
            mimetype='application/json'
    )

    app.logger.info('Metrics request successfull')
    return response

# start the application on port 3111
if __name__ == "__main__":
   app.run(host='0.0.0.0', port='3111', debug=True)
