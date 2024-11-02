'''@author : Aloyse PHULPIN'''

from dash import Dash, html, dash_table, dcc, callback, Output, Input, State, clientside_callback, ClientsideFunction, ctx, Patch, ALL, MATCH, State
from datetime import datetime, timedelta
from dash.exceptions import PreventUpdate
from threading import Timer
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
import io 
import webbrowser
import base64


import dash_mantine_components as dmc
from dash_iconify import DashIconify

############################ DEFINITION DES PARAMETRES ############################
# Nombre de mois a remonter pour l'analyse
period_in_month = 24
invdate_mark= {str(datetime.today().replace(day=1,hour=0,minute=0, second=0, microsecond=0)-pd.DateOffset(months=23-i))[0:7] : i for i in range(24)}
date_mark={v: k for k, v in invdate_mark.items()}

def preprocessing(df, period_in_month):
    """ 
    Encodage des données monétaire (initialement textuelle..)
    Attribution du type datetime
    Attribution de la catégorie épargne aux dépenses entre compte courant et compte d'épargne (bleu/jeune/epargne populaire)    
    Création de la colonne Année-Mois opération

    Input : 
        df : dataframe
        périod_in_month : entier naturel 

    Output : 
        df_s : dataframe
    """
    ############################ Attribution de catégorie ############################
    ind=df[df['Libellé opération'].str.contains("VIR DE M ALOYSE PHULPIN")].index
    df['Catégorie'].iloc[ind]='Epargne'

    ind=df[df['Libellé opération'].str.contains("VIR LIVRET JEUNE")].index
    df['Catégorie'].iloc[ind]='Epargne'

    ind=df[df['Libellé opération'].str.contains("VIR LIVRET BLEU")].index
    df['Catégorie'].iloc[ind]='Epargne'

    ind=df[df['Libellé opération'].str.contains("VIR LIVRET D'EPARGNE POPULAIRE")].index
    df['Catégorie'].iloc[ind]='Epargne'

    ############################ Formatage des données ############################
    df['Date opération']=pd.to_datetime(df['Date opération'], format='%d/%m/%Y')
    df['Montant']=df['Montant'].replace('\,', '.', regex=True).astype('float')
    df['Année-Mois opération']=df['Date opération'].apply(lambda x: str(x)[:7])

    # Sélection période max(df['Date opération'])
    df_s=df[df['Date opération'].between(datetime.today()-pd.DateOffset(months=period_in_month), datetime.today())]

    return df_s

def sep_cost_income_ep(df_s):
    """
    Input :
        df_s : dataframe

    Output :
        df_e : dataframe de l'épargne
        df_c : dataframe des coûts
        df_i : dataframe des revenus
        df_ec : dataframe de l'épargne & des revenus  
    """
    ##################### DONNES HISTOGRAMME #####################
    # Séparation coût / revenue / épargne
    df_e=df_s[df_s['Catégorie']=='Epargne']
    df_s=df_s[df_s['Catégorie']!='Epargne']
    df_e['Montant']=df_e['Montant']*(-1)

    df_c=df_s[df_s['Montant']<0]
    df_c=df_c[df_c['Sous-catégorie']!='Virements internes']
    df_c['Montant']= df_s['Montant']*(-1)

    df_i=df_s[df_s['Montant']>=0]

    df_ec=pd.concat([df_e,df_c], axis=0)  
    
    return df_e, df_c, df_i, df_ec

def data_conversion(df_c, df_ec, df_e, df_i, df_crec, dm, all_date):
    """
    Input :
        df_c : dataframe des coûts
        df_ec : dataframe de l'épargne & des revenus 
        df_e : dataframe de l'épargne
        df_i : dataframe des revenus
        dm : dictionnaire de l'index d'Année Mois sur RangeSlider {'Année Mois' : Index}
        all_date : liste de la borne inf et sup d'Année Mois 

    Output :
        df_c : dataframe des coûts filtré sur Année-Mois opération converti en date selon all_date
        df_e : dataframe de l'épargne filtré sur Année-Mois opération converti en date selon all_date
        df_ec : dataframe de l'épargne & des revenus filtré sur Année-Mois opération converti en date selon all_date
        df_i : dataframe des revenus filtré sur Année-Mois opération converti en date selon all_date
    """
    df_c['Année-Mois opération']=pd.to_datetime(df_c['Année-Mois opération'])
    df_ec['Année-Mois opération']=pd.to_datetime(df_ec['Année-Mois opération'])
    df_e['Année-Mois opération']=pd.to_datetime(df_e['Année-Mois opération'])
    df_i['Année-Mois opération']=pd.to_datetime(df_i['Année-Mois opération'])
    df_crec['Année-Mois opération']=pd.to_datetime(df_crec['Année-Mois opération'])
    
    df_e=df_e[df_e['Année-Mois opération'].between(pd.to_datetime(dm[all_date[0]]),pd.to_datetime(dm[all_date[1]]))]
    df_c=df_c[df_c['Année-Mois opération'].between(pd.to_datetime(dm[all_date[0]]),pd.to_datetime(dm[all_date[1]]))]
    df_i=df_i[df_i['Année-Mois opération'].between(pd.to_datetime(dm[all_date[0]]),pd.to_datetime(dm[all_date[1]]))]
    df_e=df_e[df_e['Année-Mois opération'].between(pd.to_datetime(dm[all_date[0]]),pd.to_datetime(dm[all_date[1]]))]
    df_crec=df_crec[df_crec['Année-Mois opération'].between(pd.to_datetime(dm[all_date[0]]),pd.to_datetime(dm[all_date[1]]))]
    return df_c, df_ec, df_e, df_i, df_crec

def sunburst_data(df_e, df_c):
    """
    Input :
        df_e : dataframe de l'épargne
        df_c : dataframe des dépenses
    Output :
        df_sunburst : dataframe dont les sous-catégories de l'épargnes sont corrigées pour le sunburst
    """
    ##################### DONNES SUNBURST #####################
    # Répartition des dépenses
    df_selec1=df_e.groupby(['Année-Mois opération', 'Catégorie']).sum('Montant')
    df_selec1['Sous-catégorie']=['Sans sous cat']*len(df_selec1)
    df_selec1[df_selec1.index.names[0]]=[df_selec1.index[i][0] for i in range(len(df_selec1))]
    df_selec1[df_selec1.index.names[1]]=[df_selec1.index[i][1] for i in range(len(df_selec1))]
    df_selec1.index=[i for i in range(len(df_selec1))]

    df_sunburst=pd.concat([df_selec1, df_c[['Année-Mois opération', 'Catégorie', 'Sous-catégorie', 'Montant']]], axis=0)

    df_sunburst['Année-Mois opération']=np.array(pd.to_datetime(df_sunburst['Année-Mois opération']))
    
    return df_sunburst

def depense_recurrente(df_c):
    
    res=pd.DataFrame(columns=['Année-Mois opération', 'Libellé opération', 'Catégorie', 'Sous-catégorie', 'Montant'])
    for i in range(2, df_c['Année-Mois opération'].nunique()):
        month1=df_c[df_c['Année-Mois opération']==np.sort(df_c['Année-Mois opération'].unique())[i-2]]
        month2=df_c[df_c['Année-Mois opération']==np.sort(df_c['Année-Mois opération'].unique())[i-1]]
        month3=df_c[df_c['Année-Mois opération']==np.sort(df_c['Année-Mois opération'].unique())[i]]
        
        commun=month2[month2['Montant'].isin(month1['Montant'].unique())]
        commun=month3[month3['Montant'].isin(commun['Montant'].unique())]
        commun=commun[['Année-Mois opération', 'Libellé opération', 'Catégorie', 'Sous-catégorie','Montant']]
        #commun=commun[['Année-Mois opération']==np.sort(df['Année-Mois opération'].unique())[i]]
        #commun=commun[commun['Année-Mois opération']==np.sort(df['Année-Mois opération'].unique())[i]]
        res=pd.concat([res,commun], axis=0)

    #res['Id']=res['Montant'].astype(str)+'€'   
    return res.groupby(['Année-Mois opération', 'Libellé opération', 'Catégorie', 'Sous-catégorie']).sum('Montant').reset_index()

def parse_data(contents, filename):
    """
    Input :
    Output :
    """
    content_type, content_string = contents.split(",")
    decoded = base64.b64decode(content_string)
    decoded=decoded.decode("utf-8")
    data=decoded.split('\r\n')
    data=[data[i].split(';') for i in range(len(data))]
    df = pd.DataFrame(data[1:len(data)-1], columns=data[0])
    return df
    
app = Dash(__name__)
server = app.server

colors = {
    'background': '#111111',
    'text': '#7FDBFF'
}

app.layout = html.Div([
    
    html.Div(
        [   
            html.H1("Upload", style={
                'textAlign': 'center',
                'color': colors['text']
            }),
            dcc.Upload(
                id="upload-data",
                children=html.Div(["Glisser & déposer ou cliquer pour sélectionner un fichier .csv à analyser."]),
                style={
                    "width": "98%",
                    "height": "60px",
                    "lineHeight": "60px",
                    "borderWidth": "1px",
                    "borderStyle": "dashed",
                    "borderRadius": "5px",
                    "textAlign": "center",
                    "margin": "10px",
                    'background': '#111111',
                    'text': '#7FDBFF',
                    'color': colors['text'],
                },
                multiple=True,
            ),
            html.Ul(id="file-list"),
        ],
        style= {'background': '#111111','text': '#7FDBFF'},
    ),

    html.Div(

        [
            dcc.RangeSlider(
                0,
                23,
                marks=date_mark,
                step=None,
                value=[0, 23],
                id='all_date'
            ),
        ], style= {'background': '#111111','text': '#7FDBFF'}),
    
    html.Div(
        [   
            dash_table.DataTable(
                id = 'dt1', 
                columns =  [{"name": i, "id": i,} for i in (['a','b','c','d','e','f'])],   
                fixed_rows={'headers': True},
                sort_action='native',
                filter_action='native',
                style_as_list_view=True,
                style_header={
                    'backgroundColor': 'rgb(30, 30, 30)',
                    'color': 'white',
                    'textAlign':'center'
                },
                style_data={
                    'backgroundColor': 'rgb(50, 50, 50)',
                    'color': 'white'
                },
                style_cell={
                    'height': 'auto',
                    'overflow': 'hidden',
                    'minWidth': '180px'
                },
                style_cell_conditional=[
                    {
                        'if' :{'column_id':'Opération pointée'},
                        'textAlign':'center'
                    },
                    {
                        'if' :{'column_id':'Catégorie'},
                        'textAlign':'center'
                    },
                    {
                        'if' :{'column_id':'Sous-catégorie'},
                        'textAlign':'center'
                    },
                    {
                        'if' :{'column_id':'Date opération'},
                        'textAlign':'left'
                    },
                    {
                        'if' :{'column_id':'Libellé opération'},
                        'textAlign':'left'
                    }
                ]
            ),
        ],
        style= {'background': '#111111','text': '#7FDBFF'},
    ),

    html.Div(

        [
            html.H1('Evolution mensuelle des dépenses', style={
                'textAlign': 'center',
                'color': colors['text']
            }),
            

            dcc.Dropdown(
                id="all_category",
                options=sorted(['Alimentation', 'Loisirs', 'Numérique', 'Autres dépenses',
                    'Vie quotidienne', 'Santé', 'Logement / maison', 'Véhicule',
                    'A catégoriser', 'Vacances / weekend', 'Hors budget']+['All']),
                value=['All'],
                multi=True,
                clearable=False,
                searchable=False,
                placeholder="Choose a category",
                    style={
                        'background': '#111111',
                        'text': '#7FDBFF',
                    }
            ),
            dcc.Graph(id="graph"),
        ], style= {'background': '#111111','text': '#7FDBFF'}
    ),

    html.Div(
        [
            html.H1("Evolution mensuelle des dépenses récurrentes détectées", style={
                'textAlign': 'center',
                'color': colors['text']
            }),

            dcc.Graph(id='costrec')
        ],style= {'background': '#111111','text': '#7FDBFF'},
    ),

    html.Div(

        [ 
            dcc.Dropdown(
                id="category",
                options=sorted(['Epargne', 'Alimentation', 'Loisirs', 'Numérique',
                    'Autres dépenses', 'Vie quotidienne', 'Santé', 'Logement / maison',
                    'Véhicule', 'A catégoriser', 'Vacances / weekend', 'Hors budget']),
                value='Alimentation',
                clearable=False,
                searchable=False,
                placeholder="Choose a category",
                style={
                    'background': '#111111',
                    'text': '#7FDBFF',
                    'width':'70%',
                }
            ),
        ]
    ),
    
    html.Div(
        [
            dcc.Graph(id="boxplot", style={'display': 'inline-block', 'width':'48%'}),
            dcc.Graph(id="sunburst_grouped", style={'display': 'inline-block', 'width':'48%'}),   
        ],style= {'background': '#111111','text': '#7FDBFF'},
    ),

    html.Div(
        [
            html.H1("Evolution mensuelle de l'épargne", style={
                'textAlign': 'center',
                'color': colors['text']
            }),

            dcc.Graph(id='epargne')
        ],style= {'background': '#111111','text': '#7FDBFF'},
    ),
    
],style= {'background': '#111111','text': '#7FDBFF'})

@app.callback(
    Output("dt1", "data"),
    Output("dt1","columns"),
    Output("graph", "figure"), 
    Output("sunburst_grouped","figure"),
    Output("boxplot", "figure"),
    Output('costrec', 'figure'),
    Output("epargne", "figure"),
    [Input("upload-data", "contents"), Input("upload-data", "filename")],
    Input("all_category", "value"),
    Input("all_date", "value"),
    Input("category", "value"),
)

def update_bar_chart(contents, filename, all_category, all_date, category):

    df_bar_cost = pd.DataFrame([],columns=['Catégorie', "Sous-catégorie", 'Montant', 'Année-Mois opération'])
    df_sunburst = pd.DataFrame([],columns=['Catégorie', "Sous-catégorie", 'Montant', 'Année-Mois opération']) 
    df_boxplot_epcost = pd.DataFrame([],columns=['Catégorie', "Sous-catégorie", 'Montant', 'Année-Mois opération'])
    df_bar_ep = pd.DataFrame([],columns=['Catégorie', "Sous-catégorie", 'Montant', 'Année-Mois opération'])
    df_selec_table = pd.DataFrame(np.array([[0,0,0,0,0,0,0],[0,0,0,0,0,0,0],[0,0,0,0,0,0,0],[0,0,0,0,0,0,0]]),columns=["Libellé opération", 'Catégorie', "Sous-catégorie", 'Montant', 'Date opération',"Opération pointée", 'Année-Mois opération'])
    df_bar_costrec = pd.DataFrame([],columns=['Catégorie', "Sous-catégorie", 'Montant', 'Année-Mois opération'])

    if contents:
        contents = contents[0]
        filename = filename[0]
        df = parse_data(contents, filename)  # decoding file
        df_courant = preprocessing(df,24) # selecting period 
        df_ep, df_cost, df_income, df_epcost = sep_cost_income_ep(df_courant) # create different dataframe
        
        ########### HISTOGRAMM DES DEPENSES MENSUELLES SELECTION CATEGORIE ET SOUS-CATEGORIE ###########
        if 'All' in all_category :
            df_selec=df_cost
            df_selec_table=df_epcost
        else :
            df_selec=df_cost[df_cost['Catégorie'].isin(all_category)]
            df_selec_table=df_epcost[df_epcost['Catégorie'].isin(all_category)]

        df_costrec=depense_recurrente(df_cost)
        df_cost, df_epcost, df_ep, df_income, df_costrec = data_conversion(df_cost, df_epcost, df_ep, df_income, df_costrec, date_mark, all_date) # converting datetime
        df_sunburst = sunburst_data(df_ep, df_cost)    

        df_bar_cost=df_selec.groupby(['Catégorie','Sous-catégorie','Année-Mois opération']).sum('Montant').reset_index()
        
        df_sunburst=df_sunburst[df_sunburst['Année-Mois opération'].between(pd.to_datetime(date_mark[all_date[0]]),pd.to_datetime(date_mark[all_date[1]]))]

        df_boxplot_epcost=df_epcost[df_epcost['Catégorie']==category]
        
        
        df_bar_costrec=df_costrec[df_costrec['Année-Mois opération'].between(pd.to_datetime(date_mark[all_date[0]]),pd.to_datetime(date_mark[all_date[1]]))]
        

        df_bar_ep=df_ep.groupby('Année-Mois opération').sum('Montant').reset_index()
        df_bar_ep['Catégorie']=["Epargne consommée" if s<0 else "Epargne acquise" for s in df_bar_ep['Montant']]   

        ########### DATATABLE SELECTION DES DONNES ###########
        cols=[]
        for col in [ 'Opération pointée', 'Date opération', 'Libellé opération', 'Catégorie', 'Sous-catégorie','Montant', 'Année-Mois opération']:
            if col=='Montant':
                cols+=[{'name': col, 'id': col, 'type':'numeric', 'format':dash_table.Format.Format(
                    scheme=dash_table.Format.Scheme.fixed, 
                    precision=2,
                    group=dash_table.Format.Group.yes,
                    groups=3,
                    group_delimiter='.',
                    decimal_delimiter=',',
                    symbol=dash_table.Format.Symbol.yes, 
                    symbol_suffix=u'€')}]
            elif col=="Date opération":
                cols+=[{'name': col, 'id': col, 'type':'datetime'}]
            else:
                cols+=[{'name': col, 'id': col}]
    else:
        cols=[{'name': col, 'id': col} for col in (['Opération pointée', 'Date opération', 'Libellé opération', 'Catégorie', 'Sous-catégorie','Montant', 'Année-Mois opération'])]

    df_selec_table['Année-Mois opération']=pd.to_datetime(df_selec_table['Année-Mois opération'])
    df_selec_table=df_selec_table[df_selec_table['Année-Mois opération'].between(pd.to_datetime(date_mark[all_date[0]]),pd.to_datetime(date_mark[all_date[1]]))]
    df_selec_table=df_selec_table[[ 'Opération pointée', 'Date opération', 'Libellé opération', 'Catégorie', 'Sous-catégorie','Montant']]
    data=df_selec_table.to_dict('records')
    
    
    ###########
    fig1 = px.bar(df_bar_cost, x="Année-Mois opération", y="Montant", color='Sous-catégorie', barmode="stack")
    
    ########### SUNBURST DES DEPENSES SUR UNE PERIODE DONNEES : CATEGORIE ET SOUS-CATEGORIE ###########
    fig2 = px.sunburst(df_sunburst, path=['Catégorie', 'Sous-catégorie'] ,values='Montant', title='Dépenses', height=700).update_traces(textinfo="label+percent parent")

    ########### BOXPLOT DES DEPENSES PAR CATEGORIES ET SOUS-CATEGORIE ###########
    fig3 = px.box(df_boxplot_epcost, x="Sous-catégorie", y="Montant", title='Boxplot', color='Sous-catégorie', height=700)
    
    fig5 = px.bar(df_bar_costrec, x="Année-Mois opération", y="Montant", color='Sous-catégorie', barmode="stack")
    ########### DONNES EPARGNES ###########
    fig4=px.bar(df_bar_ep, x='Année-Mois opération', y='Montant')
    #fig4.add_hline(y=df_epgrouped['Montant'].mean(), line_dash="dot", color='red', annotation_text="épargne moyenne", annotation_position="bottom right")

    fig1.update_layout(
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        font_color=colors['text']
    )
    
    fig2.update_layout(
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        font_color=colors['text']
    )

    fig3.update_layout(
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        font_color=colors['text'],
        legend=dict(yanchor="top", xanchor='right'),
    )

    fig4.update_layout(
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        font_color=colors['text']
    )

    fig5.update_layout(
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        font_color=colors['text']
    )
 
    return data, cols, fig1, fig2, fig3, fig5, fig4

    
if __name__ == '__main__':
    app.run_server(debug=True, port=8050)

