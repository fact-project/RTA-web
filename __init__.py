from flask import Flask, render_template, jsonify, request
import pandas as pd
import numpy as np
import sqlite3
from fact.analysis.statistics import li_ma_significance


sql = '''SELECT timestamp, source, dec_prediction, event_num, gamma_energy_prediction, gamma_prediction, night, ra_prediction, run_id, theta_deg, theta_deg_off_1, theta_deg_off_2, theta_deg_off_3, theta_deg_off_4, theta_deg_off_5
FROM data 
ORDER BY timestamp
;'''

sql_timestamp = '''SELECT timestamp, source, dec_prediction, event_num, gamma_energy_prediction, gamma_prediction, night, ra_prediction, run_id, theta_deg, theta_deg_off_1, theta_deg_off_2, theta_deg_off_3, theta_deg_off_4, theta_deg_off_5
FROM data
WHERE timestamp > "{timestamp}"
ORDER BY timestamp
;'''

sql_form = '''SELECT timestamp, source, dec_prediction, event_num, gamma_energy_prediction, gamma_prediction, night, ra_prediction, run_id, theta_deg, theta_deg_off_1, theta_deg_off_2, theta_deg_off_3, theta_deg_off_4, theta_deg_off_5
FROM data
WHERE "{formfrom}" > night > "{formto}"
ORDER BY timestamp
;'''


sql_e = '''SELECT rate, timefrom
FROM excess
ORDER BY timefrom
;'''

sql_timestamp_e = '''SELECT rate, timefrom
FROM excess
WHERE timefrom > "{lasttimefrom}"
ORDER BY timefrom
;'''


app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/excess')
def get_excess():    
    
    conn = sqlite3.connect("rtadataanimated.db")
    #lasttimefrom = request.args.get('lasttimefrom')
    lasttimefrom = None
    print('Last time:',lasttimefrom)
    if lasttimefrom is not None:
        excess = pd.read_sql_query(sql_timestamp_e, conn)
    else:
        excess = pd.read_sql_query(sql_e, conn)
    conn.close()    
    return jsonify(excess.to_dict(orient='records'))


@app.route('/events')
def get_events():
    formsource = request.args.get('formsource')
    formfrom = request.args.get('formfrom')
    formto = request.args.get('formto')
    conn = sqlite3.connect("rtadataanimated.db")
    if formsource is not None:
        print('you selected something')
        #select(formsource, formfrom, formto)
    timestamp = request.args.get('timestamp')
    if timestamp is not None:
        events = pd.read_sql(sql_timestamp.format(timestamp=timestamp), conn)
    else:
        events = pd.read_sql_query(sql, conn)
    conn.close()    
    
    theta_cut = np.sqrt(0.025)
    n_on = np.sum(events.theta_deg <= theta_cut)
    n_off = sum(
        np.sum(events['theta_deg_off_{}'.format(i)] <= theta_cut)
        for i in range(1, 6)
    )
    print(n_on, n_off)
    print('LiMa Significance: ', li_ma_significance(n_on, n_off, 0.2))
    
    return jsonify(events.to_dict(orient='records'))

"""
@app.route('/select')
def select(formsource, formfrom, formto):
    conn = sqlite3.connect("rtadataanimated.db")
    events = pd.read_sql(sql_form.format(formsource=formsource, formfrom=formfrom, formto=formto), conn)
    conn.close()
    return jsonify(events.to_dict(orient='records'))
"""

if __name__ == '__main__':
    app.run()

