from base import app
from flask import render_template, request
from base.lumberjack.views import lumberjack_do
from flask_login import current_user
from datetime import datetime

#this module covers the core of the site - home page, toolbox directory, and error pages

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/toolbox')
def toolbox():
    # tool_modules = ['gibbergen.gibbergen', 'lumberjack.lumberjack']
    # need to autogenerate tool modules
    tool_modules = []
    blueprints = app.blueprints.items()
    for name, url in blueprints:
        tool_modules.append(
            {
                'name': name,
                'display_name': name.replace("_", " ").title(),
                'url': f"{name}.{name}" or '/'
            }
        )
    lumberjack_do(datetime.utcnow(), current_user, "toolbox", "rummaged through the toolbox" )
    return render_template('toolbox.html', tool_modules=tool_modules)

@app.errorhandler(404)
def page_not_found(e):
    #log what they were trying to do
    lumberjack_do(datetime.utcnow(), current_user, "error", {"error": 404, "target": request.url})
    return render_template('404.html'), 404

@app.errorhandler(423)
def locked(e):
    #this error is primarily used by the registration toggle to allow/block new registrants
    return render_template('423.html'), 423

@app.errorhandler(500)
def oopsie(e):
    # log what they were trying to do
    lumberjack_do(datetime.utcnow(), current_user, "error", {"error": 500, "target": request.url})
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run()