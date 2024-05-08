from dash import Dash, html, dcc, Input, Output  # pip install dash
import plotly.express as px
import dash_ag_grid as dag                       # pip install dash-ag-grid
import dash_bootstrap_components as dbc          # pip install dash-bootstrap-components
import pandas as pd                              # pip install pandas

import matplotlib                                # pip install matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
import base64
from io import BytesIO

# df = pd.read_csv("https://raw.githubusercontent.com/plotly/datasets/master/solar.csv")
# df = pd.read_csv("../resources/solar.csv")

df_raw = pd.read_csv("../resources/API_CHN_DS2_en_csv_v2_2097.csv")

# generate list of year based on column names which are only digit
years = [col for col in df_raw.columns if col.isdigit()]
# generate list of column names based on column names which are not digit
other = [col for col in df_raw.columns if not col.isdigit()]
# convert all year columns into a single colum named 'Years' and values of each colums into another colum named 'Amount'
df = pd.melt(df_raw, id_vars = other, value_vars = years, var_name = "Years", value_name = "Amount")
# drop empty columns
df.dropna(how='all', axis=1, inplace=True)
print(df)

# this will be used to populate dropdown list for year rnages
ranges = {'1960-1980': list(range(1960,1981)), '1981-2000': list(range(1981,2001)), '2001-2020': list(range(2001,2021)),
          '2021-2023': list(range(2021,2024)), '1960-2023': list(range(1960,2024))}


app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.layout = dbc.Container([
    html.H1("Economic dashboard of China", className='mb-2', style={'textAlign':'center'}),

    dbc.Row([
        dbc.Col([
            dcc.Dropdown(
                id='category',
                value=df['Indicator Name'].iloc[0],
                clearable=False,
                options=df['Indicator Name'])
        ], width=4, md=6),
        dbc.Col([
                    dcc.Dropdown(
                        id='category2',
                        value=list(ranges.keys())[0],
                        clearable=False,
                        options=list(ranges.keys()))
                ], width=4, md=6)
    ]),

    dbc.Row([
        dbc.Col([
            html.Img(id='bar-graph-matplotlib')
        ], width=12)
    ]),

    dbc.Row([
        dbc.Col([
            dcc.Graph(id='bar-graph-plotly', figure={})
        ], width=12, md=6),
        dbc.Col([
            dag.AgGrid(
                id='grid',
                rowData=df.to_dict("records"),
                columnDefs=[{"field": i} for i in df.columns],
                columnSize="sizeToFit",
            )
        ], width=12, md=6),
    ], className='mt-4'),

])

# Create interactivity between dropdown component and graph
@app.callback(
    Output(component_id='bar-graph-matplotlib', component_property='src'),
    Output('bar-graph-plotly', 'figure'),
    Output('grid', 'defaultColDef'),
    [Input('category', 'value'), Input('category2', 'value')],
)
def plot_data(selected_yaxis, selected_range):
    print(selected_yaxis)
    print(selected_range)
    df_selected = df[(df['Years'].isin([str(x) for x in ranges[selected_range]]))
                     & (df['Indicator Name'].isin([selected_yaxis]))]
    # df_selected = df[(df['Indicator Name'].isin([selected_yaxis]))]
    yaxis = 'Amount'
    # Build the matplotlib figure
    fig = plt.figure(figsize=(14, 5))
    plt.bar(df_selected['Years'], df_selected[yaxis])
    plt.ylabel(yaxis)
    plt.xticks(rotation=30)

    # Save it to a temporary buffer.
    buf = BytesIO()
    fig.savefig(buf, format="png")
    # Embed the result in the html output.
    fig_data = base64.b64encode(buf.getbuffer()).decode("ascii")
    fig_bar_matplotlib = f'data:image/png;base64,{fig_data}'

    # Build the Plotly figure
    fig_bar_plotly = px.bar(df_selected, x='Years', y=yaxis).update_xaxes(tickangle=330)

    my_cellStyle = {
        "styleConditions": [
            {
                "condition": f"params.colDef.field == '{yaxis}'",
                "style": {"backgroundColor": "#d3d3d3"},
            },
            {   "condition": f"params.colDef.field != '{yaxis}'",
                "style": {"color": "black"}
            },
        ]
    }

    return fig_bar_matplotlib, fig_bar_plotly, {'cellStyle': my_cellStyle}


if __name__ == '__main__':
    app.run_server(debug=False, port=8002)