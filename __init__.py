from flask import Flask, render_template, flash, request, jsonify
import pandas as pd
import numpy as np
import datetime
import sqlite3
from fact.analysis.statistics import li_ma_significance
from wtforms import Form, TextField, TextAreaField, validators, StringField, SubmitField

dbpath = "rta.db"
theta_cut = 0.16
previousdays = 5

run = []
events = []

global last_source
global last_night_minus
lastnight = '''SELECT MAX(night) FROM events;'''
conn = sqlite3.connect(dbpath)
last_night = pd.read_sql_query(lastnight, conn)
last_night = last_night.at[0, 'MAX(night)']
lastsource = '''SELECT source FROM events WHERE night = "{last_night}" ORDER BY timestamp;'''
last_source = pd.read_sql(lastsource.format(last_night=last_night), conn)
last_source = last_source.at[len(last_source)-1, 'source']
last_night_minus = int((datetime.datetime.strptime(str(last_night),"%Y%m%d") - datetime.timedelta(days=previousdays)).strftime("%Y%m%d"))

#DEBUG = True
app = Flask(__name__)
app.config.from_object(__name__)
app.config['SECRET_KEY'] = '7d441f27d441f27567d441f2b6176a'

select_source = 'Live'
select_from = None
select_to = None
auto_timestamp = None
auto_lasttimefrom = None
form_count = 0
form_count_run = 0 

sql = '''SELECT timestamp, source, dec_prediction, event_num, gamma_energy_prediction, gamma_prediction, night, ra_prediction, run_id, theta_deg, theta_deg_off_1, theta_deg_off_2, theta_deg_off_3, theta_deg_off_4, theta_deg_off_5
FROM events
WHERE source = "{last_source}" AND night >= "{last_night_minus}"
ORDER BY timestamp
;'''

sql_timestamp = '''SELECT timestamp, source, dec_prediction, event_num, gamma_energy_prediction, gamma_prediction, night, ra_prediction, run_id, theta_deg, theta_deg_off_1, theta_deg_off_2, theta_deg_off_3, theta_deg_off_4, theta_deg_off_5
FROM events
WHERE source = "{last_source}" AND timestamp > "{timestamp}"
ORDER BY timestamp
;'''

sql_form = '''SELECT timestamp, source, dec_prediction, event_num, gamma_energy_prediction, gamma_prediction, night, ra_prediction, run_id, theta_deg, theta_deg_off_1, theta_deg_off_2, theta_deg_off_3, theta_deg_off_4, theta_deg_off_5
FROM events
WHERE night >= "{select_from}" AND night <= "{select_to}" AND source = "{select_source}"
ORDER BY timestamp
;'''

sql_e = '''SELECT night, source, rate, timefrom
FROM run
WHERE night >= "{select_from}" AND source = "{select_source}"
ORDER BY timefrom
;'''

sql_timestamp_e = '''SELECT night, source, rate, timefrom
FROM run
WHERE source = "{last_source}" AND timefrom > "{lasttimefrom}"
ORDER BY timefrom
;'''

sql_form_e = '''SELECT night, source, rate, timefrom
FROM run
WHERE night >= "{select_from}" AND night <= "{select_to}" AND source = "{select_source}"
ORDER BY timefrom
;'''



class SelectedForm(Form):
    select_source = TextField('Source:', validators=[validators.required()])
    select_from = TextField('From:', validators=[validators.required()])
    select_to = TextField('To:', validators=[validators.required()])
 
@app.route("/", methods=['GET', 'POST'])
def select():   
    form = SelectedForm(request.form)
    print(form.errors)
    if request.method == 'POST':
        global select_source
        global select_to
        global select_from
        global form_count
        global form_count_run
        form_count = 0
        form_count_run = 0 
        select_source = request.form['select_source']
        s_to = request.form['select_to']
        s_from = request.form['select_from']
        select_to = s_to.replace("-", "")
        select_from = s_from.replace("-", "")
        swap = ''
        #Swap timeselection if selected false.
        if select_to < select_from:
            save = select_from
            select_from = select_to
            select_to = save
            save = s_from
            s_from = s_to
            s_to = save
            swap = " | Time selection has been swapped."
            
        if select_source == 'Live':
            flash('You are seeing live data from '+ last_source)
        else:
            if form.validate():
                flash(' Source: ' + select_source + ' - from ' + s_from + ' to ' + s_to + swap)
            else:
                flash('Error: All the form fields are required. ')
            
    return render_template('index.html', form=form)

@app.route('/events')
def get_events(): 
    conn = sqlite3.connect(dbpath)
    global auto_timestamp
    auto_timestamp = request.args.get('timestamp')
    global form_count
    
    if select_source == 'Live':
        if auto_timestamp is not None:
            event = pd.read_sql(sql_timestamp.format(timestamp=auto_timestamp, last_source=last_source), conn)
            events = event[event.night >= last_night_minus]
        else:
            events = pd.read_sql(sql.format(last_night_minus=last_night_minus, last_source=last_source), conn)
    else:
        if form_count == 0:
            events = pd.read_sql(sql_form.format(select_from=select_from,select_to=select_to,select_source=select_source), conn)
            form_count = 1
    conn.close()    
    """
    n_on = np.sum(events.theta_deg <= theta_cut)
    n_off = sum(
                np.sum(events['theta_deg_off_{}'.format(i)] <= theta_cut)
                for i in range(1, 6)
                )
    print(n_on, n_off)
    print('LiMa Significance: ', li_ma_significance(n_on, n_off, 0.2))
    """
    return jsonify(events.to_dict(orient='records'))


@app.route('/run')
def get_run():    
    conn = sqlite3.connect(dbpath)
    global auto_lasttimefrom
    auto_lasttimefrom = request.args.get('lasttimefrom')
    global form_count_run
    if select_source == 'Live':
        if auto_lasttimefrom != None:
            ru = pd.read_sql(sql_timestamp_e.format(lasttimefrom=auto_lasttimefrom, last_source=last_source), conn)
            run = ru[ru.night >= last_night_minus]
        else:
            run = pd.read_sql(sql_e.format(select_from=last_night_minus, last_source=last_source), conn)
    else:
        if form_count_run == 0:
            run = pd.read_sql(sql_form_e.format(select_from=select_from,select_to=select_to,select_source=select_source), conn)
            form_count_run = 1
    conn.close()    
    return jsonify(run.to_dict(orient='records'))

if __name__ == '__main__':
    app.run()
