from flask import Flask, render_template
from flask import jsonify
import asana
import sys
import webbrowser, threading, random
import db
import json


key = sys.argv[1]
print('Key: {0}'.format(key))
api = asana.ASANA_API(key, debug=False)

app = Flask(__name__)

@app.route('/workpaces')
def asana_workspaces():  
    json_wss = api.list_workspaces()
    #return jsonify(json_wss)
    return render_template('workspace.html', workspaces = json_wss)
"""
@app.route('/projects')
def asana_projects():
    json_prjs = api.list_projects(workspace=2204037302945, archived='false')
    #return jsonify(json_prjs)
    return render_template('projects.html', projects = json_prjs)  
"""

@app.route('/')
def asana_projects():
    json_prjs = api.list_projects(workspace=2204037302945, archived='false')
    db_i = db.DB()
    db_i.json_to_db(json_prjs)
    db_i.cur.execute('select * from projects')
    prjs = db_i.cur.fetchall()
    db_i.db_close()
    #print(prjs)
    #return jsonify(json_prjs)
    return render_template('projects.html', projects = prjs)

@app.route('/project/<project_id>')
def get_project_tasks(project_id):
    #print(">>>>>>>project: {}".format(project_id))
    mTotal,mCompleted,mPercentage = api.get_project_percentage(project_id)
    db_i = db.DB()
    db_i.update_project_percentage(project_id,mTotal,mCompleted)
    db_i.db_close()
    return json.dumps({'total':mTotal, 'completed':mCompleted, 'percentage':mPercentage})


# random port
#port = 5000 + random.randint(0,999)
port = 5000
url = "http://127.0.0.1:{0}".format(port)

if __name__ == '__main__':
    #webbrowser.open_new(url)
    #threading.Timer(1.25, lambda: webbrowser.open(url)).start()
    app.debug = True
    app.run(host='0.0.0.0', port=port)
    