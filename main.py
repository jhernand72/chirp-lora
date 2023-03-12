from flask import Flask,request
import requests
import dash
from dash import html,Input, Output,dcc
import plotly.graph_objects as go
import numpy as np
import sqlite3
import time
import dash_bootstrap_components as dbc
import base64


conn = sqlite3.connect(r"db\chirp_data.sqlite")
c = conn.cursor()

def create_table():
    c.execute("CREATE TABLE IF NOT EXISTS chirp_info(TIME REAL, DR REAL, TEMP_MOT REAL, TEMP_HS REAL, VCAP REAL)")
    #c.execute("CREATE TABLE IF NOT EXISTS chirp_info(DR REAL,FR REAL)")
    conn.commit()
create_table()
#c = conn.cursor()
c.execute("SELECT COUNT(*) FROM chirp_info")
rowcount = c.fetchone()[0]
#print(rowcount)
N_disp=5

app=Flask(__name__)
app1= dash.Dash(__name__,server=app, external_stylesheets=[dbc.themes.BOOTSTRAP])

@app.route("/",methods={'POST'})
def index():
    global rowcount
    args = request.args
    if args['event']=='up':
        myjson=request.get_json()
        puerto=myjson['fPort']
 #       print(puerto)
        if(puerto==1):
            datos=myjson['object']
            deltaRn=datos['deltaRn']
            temp_motor=datos['temp_motor']
            temp_heat=datos['temp_heat']
            volt_scap=datos['volt_scap']
            #print(datos)
            
            time_s = time.time()
            conn = sqlite3.connect(r"db\chirp_data.sqlite")
            c = conn.cursor()
            '''
            if rowcount>150:
                c.execute("DELETE * FROM chirp_info WHERE ROWID=1")
                conn.commit() 
            else:
                rowcount=rowcount+1
                c.execute("INSERT INTO chirp_info(TIME, DR,TEMP_MOT,TEMP_HS,VCAP) VALUES (?, ?,?,?,?)", [time_s, deltaRn,temp_motor,temp_heat,volt_scap])    
                conn.commit() 
            '''
            rowcount=rowcount+1
            c.execute("INSERT INTO chirp_info(TIME, DR,TEMP_MOT,TEMP_HS,VCAP) VALUES (?, ?,?,?,?)", [time_s, deltaRn,temp_motor,temp_heat,volt_scap])    
            conn.commit() 

            headers0 = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            }

            json_data0 = {
                'email': 'admin',
                'password': 'admin',
            }
            resp_token = requests.post('http://lorawan.domodigitalmerida.com:8080/api/internal/login', headers=headers0, json=json_data0)
            json_resp= resp_token.json()
            token=json_resp['jwt']
            token_header='Bearer '+token
            #print(token_header)

            headers = {
                # Already added when you pass json=
                # 'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Grpc-Metadata-Authorization': token_header,
            }

            tsleep='55'
            tsleep_bytes=tsleep.encode('ascii')
            base64_bytes=base64.b64encode(tsleep_bytes)
            base64_Tsleep=base64_bytes.decode('ascii')
            #print(base64_Tsleep)
            #'NTU='
            json_data = {
                'deviceQueueItem': {
                    'confirmed': False,
                    'data': base64_Tsleep,
                    'devEUI': '0000000000000004',
                    'fPort': 1,
                    #'jsonObject':"{'T':55}",
                },
            }

            resp_encola = requests.post(
                'http://lorawan.domodigitalmerida.com:8080/api/devices/0000000000000004/queue',
                headers=headers,
                json=json_data,
            )
            #print(resp_encola)                  
    return '''Todo bien'''

app1.layout = html.Div([
    dbc.Row([
        dbc.Col([
                dcc.Graph(id="graph1"),
                dcc.Interval(
                id='interval-component',
                interval=30 * 1000,# in miliseconds
                n_intervals=0
                )    
        ],'Column1',width='auto'),
        dbc.Col(dcc.Graph(id="graph2"),'Column2',width='auto'),
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id="graph3"),'Column3',width='auto'),
        dbc.Col(dcc.Graph(id="graph4"),'Column4',width='auto'),
    ])
])


@app1.callback(
  [Output("graph1", "figure"),Output("graph2", "figure"),Output("graph3", "figure"),Output("graph4", "figure")],
  Input("interval-component", "n_intervals"))
def update_graph(interval):
    global rowcount
    global N_disp
    if rowcount != 0:
        conn = sqlite3.connect(r"db\chirp_data.sqlite")
        c=conn.cursor()
        orden="SELECT DR,TEMP_MOT,TEMP_HS,VCAP FROM chirp_info LIMIT "+ "{}".format(N_disp) + " OFFSET "+"{}".format(rowcount-6)
        res = c.execute(orden)
        datos_tup=res.fetchmany(N_disp)
        #print(rowcount)
        #print(datos_tup)
        datos_DR=np.asarray(datos_tup)
        #print(datos_DR)
        x=[1,2,3,4,5]
        #print(datos_DR)
        #eje_x=list(range(N_disp))
        fig_1 = go.Figure(
            data=[go.Scatter(x=x,y=datos_DR[:,0],name='Cambio de Resistencia MWCNT')],
            layout_title_text="Resistencia"
        )
        fig_1.layout.title="Resistencia MWCNT"
        fig_1.layout.xaxis.title='tiempo'
        fig_1.layout.yaxis.title='DRn'

        fig_2 = go.Figure(
            data=[go.Scatter(x=x,y=datos_DR[:,1],name='Temperatura del motor')],
            layout_title_text="Temperatura del motor",
        )
        fig_2.layout.title="Temperatura del motor"
        fig_2.layout.xaxis.title='tiempo'
        fig_2.layout.yaxis.title='°C'

        fig_3 = go.Figure(
            data=[go.Scatter(x=x,y=datos_DR[:,2],name='Temperatura del disipador')],
            layout_title_text="Temperatura del disipador1"
        )
        fig_3.layout.title="Temperatura del disipador"
        fig_3.layout.xaxis.title='tiempo'
        fig_3.layout.yaxis.title='°C'

        fig_4 = go.Figure(
            data=[go.Scatter(x=x,y=datos_DR[:,3],name='Carga del Supercapacitor')],
            layout_title_text="Voltaje del supercapacitor"
        )
        fig_4.layout.title="Voltaje del Supercapacitor"
        fig_4.layout.xaxis.title='tiempo'
        fig_4.layout.yaxis.title='Volts'

        return [fig_1,fig_2,fig_3,fig_4]
    else:
        return [go.Figure(),go.Figure(),go.Figure(),go.Figure()]

if __name__ == '__main__':
    app1.run_server(debug=True)
