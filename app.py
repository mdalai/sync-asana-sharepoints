from flask import Flask, render_template
from flask import jsonify
import asana
import sys

key = sys.argv[1]
print('Key: {0}'.format(key))
api = asana.ASANA_API(key, debug=False)

app = Flask(__name__)

@app.route('/')
def asana_workspaces():  
    json_wss = api.list_workspaces()
    #return jsonify(json_wss)
    return render_template('workspace.html', workspaces = json_wss)

@app.route('/projects')
def asana_projects():
    json_prjs = api.list_projects()
    #return jsonify(json_prjs)
    return render_template('projects.html', projects = json_prjs)


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)