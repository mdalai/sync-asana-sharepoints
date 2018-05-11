# all the imports
import os
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from werkzeug.utils import secure_filename

import re
import datetime

######## Upload files #############
# Have to use absolute path to upload files
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(APP_ROOT, 'upload')
ALLOWED_EXTENSIONS = set(['xlsx', 'xls', 'xlsm'])


app = Flask(__name__) # create the application instance :)

########## Configuration ##############################################
app.config.from_object(__name__) # load config from this file , flaskr.py

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'payroll.db'),
    SECRET_KEY='development key',
    USERNAME='sandy',
    PASSWORD='1234'
))
app.config.from_envvar('FLASKR_SETTINGS', silent=True)


app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024


########## DATABASE ###################################################
def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

## command line database initialization
def init_db():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()

@app.cli.command('initdb')
def initdb_command():
    """Initializes the database."""
    init_db()
    print('Initialized the database.')


def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

########## CRUD ##################################################
## Show Entris
@app.route('/payroll', methods=['GET', 'POST'])
def show_payroll():
    ## if not logged in, show ERROR 
    if not session.get('logged_in'):
        flash('Please log in first!')
        #abort(401) # Unauthorized URL
        return redirect(url_for('login'))

    
    lname = '' # Instructor's last name
    fname = '' # Instructor's first name
    
    db = get_db()
    if request.method == 'POST':
        if request.form['ilname'] and request.form['ifname']:
            cur = db.execute('select * from payroll WHERE lower(InstLastName) = ? and lower(InstFirstName) = ?  order by process_date desc',
                             [request.form['ilname'].lower().strip(),request.form['ifname'].lower().strip()]) 
        elif request.form['ilname']:
            cur = db.execute('select * from payroll WHERE lower(InstLastName) = ? order by process_date desc',[request.form['ilname'].lower().strip()])
        else:
            cur = db.execute('select * from payroll order by process_date desc LIMIT 50')
            #cur = db.execute('select * from payroll where InstLastName="Busch" ')

        lname = request.form['ilname']
        fname = request.form['ifname']

    else:
        ## Show top 50 rows
        cur = db.execute('select * from payroll2 ORDER BY process_date DESC LIMIT 50')
        #cur = db.execute('select * from payroll ORDER BY process_date DESC LIMIT 50')
        #cur = db.execute('select * from payroll')
        
    payrolls = cur.fetchall()
    return render_template('show_payroll.html', items=payrolls, lastname=lname, firstname=fname, login_user = session.get('login_user'))

## Add New Entry - check if logged in
@app.route('/add', methods=['POST'])
def add_entry():
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    db.execute('insert into entries (title, text) values (?, ?)',
                 [request.form['title'], request.form['text']])
    db.commit()
    flash('New entry was successfully posted')
    return redirect(url_for('show_payroll'))



########## LOGIN and Logout #########################################
@app.route('/', methods=['GET', 'POST'])
def login():
    # if already logged in, just show the data directly
    if session.get('logged_in'):
        return redirect(url_for('show_payroll'))
    
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            session['login_user'] = request.form['username']
            flash('You were logged in')
            return redirect(url_for('show_payroll'))
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('login'))



######### Upload Excel data ##########################################
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            #file.save(os.path.abspath(app.config['UPLOAD_FOLDER']+filename))
            return redirect(url_for('uploaded_file',
                                    filename=filename))
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <p><input type=file name=file>
         <input type=submit value=Upload>
    </form>
    '''

@app.route('/upload/<filename>')
def uploaded_file(filename):
    # import function
    from excel2sqlite_single import excel2sqlite
    
    print "----------------",filename
    filepath = os.path.join(app.config['UPLOAD_FOLDER'],filename)
    print filepath
    # pick only paydate with format 'for 1-15-15'
    paydate = re.search('for_[0-9]{1,2}-[0-9]{1,2}-[0-9]{2}',filename)
    payday = paydate.group()[4:]
    paydate = datetime.datetime.strptime(payday, "%m-%d-%y").date()
    # pick only process date with format '1-15-15'
    process_date = re.search('[0-9]{1,2}-[0-9]{1,2}-[0-9]{2}',filename)
    process_date = datetime.datetime.strptime(process_date.group(), "%m-%d-%y").date()
    
    #conn = sqlite3.connect(app.config['DATABASE'])
    db = get_db()
    excel2sqlite(db,filepath,paydate,process_date,filename)
    #conn.close()

    #print "Success!!!"
    #return "Data Successfully Stored into the Database!!!"
    flash("Data Successfully Stored into the Database!!!")
    return redirect(url_for('show_payroll'))



if __name__ == '__main__':
	app.debug = True  # Flask auto refresh the code update without restarting
	app.run(host = '0.0.0.0', port=5000)
