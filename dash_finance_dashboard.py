# dash_finance_dashboard_app.py
"""
Dash Financial Dashboard — Dixon Technologies vs Honeywell Automation
Single-file Dash app (Plotly + Dash + Pandas).
Save as dash_finance_dashboard.py, install dependencies (dash, pandas, plotly) and run.
"""

import pkgutil
if not hasattr(pkgutil, "find_loader"):
    import importlib.util
    pkgutil.find_loader = lambda name: importlib.util.find_spec(name)


import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import pandas as pd

# ----- Data (user-provided) -----
years = ['Mar-21', 'Mar-22', 'Mar-23', 'Mar-24', 'Mar-25']
year_numbers = [2021, 2022, 2023, 2024, 2025]

dixon = {
    'Current Ratio': [1.17, 1.15, 1.07, 1.48, 1.33],
    'Quick Ratio':   [1.12, 1.14, 1.27, 1.12, 1.01],
    'Gross Profit Margin': [4.04, 3.04, 4.33, 3.91, 3.25],
    'Net Profit Margin':   [2.48, 1.78, 2.09, 2.08, 2.82],
    'Inventory Turnover':  [15.48176253, 10.41597944, 10.42333314, 12.16973252, 12.69463956],
    'Asset Turnover':      [2.27, 2.49, 2.60, 2.52, 2.30],
    'Trade Receivable Turnover': [11.84, 8.73, 7.93, 8.73, 8.31]
}

honeywell = {
    'Current Ratio': [2.72, 3.26, 3.41, 3.66, 3.45],
    'Quick Ratio':   [2.61, 3.13, 3.22, 3.49, 3.24],
    'Gross Profit Margin': [17.75, 12.91, 13.54, 13.20, 12.65],
    'Net Profit Margin':   [15.11, 11.50, 12.70, 12.35, 12.49],
    'Inventory Turnover':  [31.89, 29.90, 20.94, 25.51, 17.66],
    'Asset Turnover':      [1.28, 1.09, 1.14, 1.19, 1.10],
    'Trade Receivable Turnover': [3.58, 3.62, 4.28, 4.35, 4.20]
}

# Build tidy dataframe
rows = []
for i, y in enumerate(years):
    for k, v in dixon.items():
        rows.append({'Company': 'Dixon', 'Metric': k, 'Value': v[i], 'YearLabel': y, 'Year': year_numbers[i]})
    for k, v in honeywell.items():
        rows.append({'Company': 'Honeywell', 'Metric': k, 'Value': v[i], 'YearLabel': y, 'Year': year_numbers[i]})
df = pd.DataFrame(rows)

# Metric groups for UI
metric_groups = {
    'liquidity': ['Current Ratio', 'Quick Ratio'],
    'profitability': ['Gross Profit Margin', 'Net Profit Margin'],
    'turnover': ['Inventory Turnover', 'Asset Turnover', 'Trade Receivable Turnover']
}

# Helper to fetch latest KPI
def kpi_latest(df_local, company, metric):
    sub = df_local[(df_local['Company'] == company) & (df_local['Metric'] == metric)]
    if sub.empty: 
        return None
    return sub.sort_values('Year')['Value'].iloc[-1]

# ----- Dash app -----
app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server

app.layout = html.Div(style={'font-family': 'Inter, Arial, sans-serif', 'padding': '18px'}, children=[
    html.H2("Financial Dashboard — Dixon vs Honeywell"),
    html.Div("Compare liquidity, profitability and turnover metrics (Mar-21 → Mar-25).", style={'color': '#666'}),

    # Controls
    html.Div(style={'display': 'flex', 'gap': '12px', 'align-items': 'center', 'margin-top': '12px'}, children=[
        html.Div([
            html.Label("Company"),
            dcc.Dropdown(
                id='company-select',
                options=[
                    {'label': 'Dixon Technologies', 'value': 'Dixon'},
                    {'label': 'Honeywell Automation', 'value': 'Honeywell'},
                    {'label': 'Both Companies', 'value': 'Both'}
                ],
                value='Both',
                clearable=False,
                style={'width': '260px'}
            )
        ]),
        html.Div([
            html.Label("Metric group"),
            dcc.Dropdown(
                id='metric-group',
                options=[
                    {'label': 'Liquidity Ratios', 'value': 'liquidity'},
                    {'label': 'Profitability Ratios', 'value': 'profitability'},
                    {'label': 'Turnover Ratios', 'value': 'turnover'}
                ],
                value='liquidity',
                clearable=False,
                style={'width': '260px'}
            )
        ]),
        html.Div(style={'min-width': '280px'}, children=[
            html.Label("Year range"),
            dcc.RangeSlider(
                id='year-range',
                min=min(year_numbers),
                max=max(year_numbers),
                value=[min(year_numbers), max(year_numbers)],
                marks={y: str(y) for y in year_numbers},
                step=None,
                tooltip={'placement': 'bottom'}
            )
        ])
    ]),

    # Executive summary KPI cards container (populated by callback)
    html.Div(id='kpi-cards', style={'display': 'flex', 'gap': '12px', 'flex-wrap': 'wrap', 'margin-top': '16px'}),

    # Main chart + right pane
    html.Div(style={'display': 'flex', 'gap': '18px', 'margin-top': '18px'}, children=[
        html.Div(dcc.Graph(id='main-chart', config={'displayModeBar': True}, style={'min-width': '640px', 'height': '560px'}), style={'flex': '1 1 70%'}),
        html.Div(style={'flex': '0 0 360px'}, children=[
            html.H4("Mini-trend & data"),
            dcc.Graph(id='spark-chart', config={'displayModeBar': False}, style={'height': '240px'}),
            html.Div(id='data-table', style={'margin-top': '12px', 'font-size': '13px', 'white-space': 'pre-wrap', 'font-family': 'monospace'})
        ])
    ]),

    html.Div(style={'margin-top': '12px', 'color': '#999', 'font-size': '12px'}, children=[
        html.Span("Data source: user-provided values (Mar-21 → Mar-25).")
    ])
])

# ----- Callbacks -----
@app.callback(
    Output('kpi-cards', 'children'),
    Input('company-select', 'value')
)
def update_kpis(company):
    # KPI list (6 cards)
    kpis = ['Current Ratio', 'Quick Ratio', 'Gross Profit Margin', 'Net Profit Margin', 'Inventory Turnover', 'Asset Turnover']
    cards = []
    for metric in kpis:
        if company == 'Both':
            d_val = kpi_latest(df, 'Dixon', metric)
            h_val = kpi_latest(df, 'Honeywell', metric)
            body = html.Div([
                html.Div(metric, style={'font-size': '12px', 'color': '#333'}),
                html.Div(style={'display':'flex','gap':'10px','margin-top':'6px'}, children=[
                    html.Div([html.Div("Dixon", style={'font-size':'11px','color':'#666'}), html.Div(f"{d_val:.2f}" if d_val is not None else "—", style={'font-weight':'700'})]),
                    html.Div([html.Div("Honeywell", style={'font-size':'11px','color':'#666'}), html.Div(f"{h_val:.2f}" if h_val is not None else "—", style={'font-weight':'700'})])
                ])
            ], style={'padding': '8px'})
        else:
            val = kpi_latest(df, company, metric)
            body = html.Div([
                html.Div(metric, style={'font-size': '12px', 'color': '#333'}),
                html.Div(f"{val:.2f}" if val is not None else "—", style={'font-size': '18px', 'font-weight': '700', 'margin-top': '6px'})
            ], style={'padding': '8px'})
        card = html.Div(body, style={
            'border': '1px solid #e6e6e6', 'border-radius': '8px',
            'min-width': '170px', 'background': '#fff', 'box-shadow': '0 1px 3px rgba(0,0,0,0.04)'
        })
        cards.append(card)
    return cards

@app.callback(
    Output('main-chart', 'figure'),
    Output('spark-chart', 'figure'),
    Output('data-table', 'children'),
    Input('company-select', 'value'),
    Input('metric-group', 'value'),
    Input('year-range', 'value')
)
def update_charts(company, group, year_range):
    yr_min, yr_max = year_range
    metrics = metric_groups[group]
    # Filtered DF
    dff = df[(df['Metric'].isin(metrics)) & (df['Year'] >= yr_min) & (df['Year'] <= yr_max)]

    # Main chart
    fig = go.Figure()
    if company == 'Both':
        for metric in metrics:
            for comp in ['Dixon', 'Honeywell']:
                s = dff[(dff['Metric'] == metric) & (dff['Company'] == comp)].sort_values('Year')
                fig.add_trace(go.Bar(
                    x=s['YearLabel'],
                    y=s['Value'],
                    name=f"{comp} — {metric}",
                    text=[f"{v:.2f}" for v in s['Value']],
                    textposition='auto'
                ))
        fig.update_layout(barmode='group', title="Comparison — grouped by metric & company", xaxis_title="Year", yaxis_title="Value")
    else:
        for metric in metrics:
            s = dff[(dff['Company'] == company) & (dff['Metric'] == metric)].sort_values('Year')
            fig.add_trace(go.Bar(
                x=s['YearLabel'],
                y=s['Value'],
                name=metric,
                text=[f"{v:.2f}" for v in s['Value']],
                textposition='auto'
            ))
        fig.update_layout(barmode='group', title=f"{company} — {group.title()}", xaxis_title="Year", yaxis_title="Value")

    # Sparkline (first metric)
    spark = go.Figure()
    primary = metrics[0]
    if company == 'Both':
        for comp in ['Dixon', 'Honeywell']:
            s = dff[(dff['Metric'] == primary) & (dff['Company'] == comp)].sort_values('Year')
            spark.add_trace(go.Scatter(x=s['YearLabel'], y=s['Value'], mode='lines+markers', name=comp))
    else:
        s = dff[(dff['Metric'] == primary) & (dff['Company'] == company)].sort_values('Year')
        spark.add_trace(go.Scatter(x=s['YearLabel'], y=s['Value'], mode='lines+markers', name=company))

    spark.update_layout(title=f"Trend — {primary}", margin={'t':30, 'b':10, 'l':30, 'r':10}, height=240)

    # Data table (CSV text)
    table_df = dff.pivot_table(index='YearLabel', columns=['Company', 'Metric'], values='Value')
    table_text = table_df.round(3).to_csv()
    return fig, spark, html.Pre(table_text)

if __name__ == "__main__":
    # Option 1: Debug mode off (safe)
    app.run(debug=False)



