from base import app
from flask import render_template

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(423)
def locked(e):
    #this error is primarily used by the registration toggle to allow/block new registrants
    return render_template('423.html'), 423

if __name__ == '__main__':
    app.run()