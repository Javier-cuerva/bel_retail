import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

import datetime as dt

from get_data import get_data_from_api


# Getting data from STATBEL API
data = get_data_from_api()

# Doing some preprocessing
data["Formatted Month"] = data.apply(lambda row : row["Month"].strftime("%Y-%m"), axis="columns")
month_values = data["Month"].unique()
month_values = month_values[month_values.argsort()]
month_format_func = lambda month : month.strftime("%b %Y")

col1, col2 = st.columns(2)
first_month = col1.selectbox("From", options=month_values, format_func=month_format_func)
last_month = col2.selectbox("To", options=month_values, format_func=month_format_func)

below_col = st.columns(1)[0]
categories = data["NACE groups"].unique()
n_cats = len(categories)
selected_cats = below_col.multiselect("Select categories", options=categories)
chart_data = data[["Month", "Formatted Month", "NACE groups", "Gross index"]]
chart_data = chart_data[chart_data["NACE groups"].isin(selected_cats)]
chart_data = chart_data.sort_values(by="Month")
color_list = px.colors.qualitative.Bold[:n_cats]
color_map = {cat: color for cat, color in zip(categories, color_list)}
fig = px.line(
    chart_data,
    x="Formatted Month", y="Gross index",
    color="NACE groups",
    color_discrete_map=color_map,
    range_x=(first_month, last_month)
)
fig.update_layout(
    {
        "xaxis": {
            "fixedrange": True,
            "tickangle": -45,
            "type": "date"
        },
        "yaxis": {
            "fixedrange": True
        }
    }
)
fig.update_layout(legend=dict(x=0, y=-0.3, traceorder="normal", orientation="h"))
below_col.plotly_chart(fig)

st.sidebar.title("Sidebar titel")
month_names = data["Month Name"].unique()
selected_cat = st.sidebar.selectbox("Select category", options=categories)
cat_color = color_map[selected_cat]

sb_col1, sb_col2 = st.sidebar.columns(2)
month_aggs_opts = ("FY", "H1", "H2", "Q1", "Q2", "Q3", "Q4", "Custom")
selected_agg = sb_col1.selectbox("Month aggregation", options=month_aggs_opts)
selected_months_map = {
    "FY": month_names,
    "H1": month_names[:6],
    "H2": month_names[6:],
    "Q1": month_names[:3],
    "Q2": month_names[3:6],
    "Q3": month_names[6:9],
    "Q4": month_names[9:],
}
if selected_agg != "Custom":
    selected_months = list(selected_months_map[selected_agg])
    total_chart_title = "Total value in the period {} - {} by year".format(selected_months[0], selected_months[-1])
    growth_chart_title = "Growth of the period {} - {} vs. previous year".format(selected_months[0], selected_months[-1])
else:
    selected_months = sb_col2.multiselect("Select months", options=month_names, disabled=(selected_agg!="Custom"))
    total_chart_title = "Total value in selected months by year"
    growth_chart_title = "Growth in selected months vs. previous year"

total_chart_data = data[["NACE groups", "Year", "Month Name", "Gross index"]]
total_chart_data = total_chart_data[total_chart_data["Month Name"].isin(selected_months)]
total_chart_data = total_chart_data[total_chart_data["NACE groups"] == selected_cat]
total_chart_data = total_chart_data[["Year", "Gross index"]].groupby(["Year"], as_index=False).sum()
fig_total_chart = px.line(total_chart_data, x="Year", y="Gross index",markers=True, color_discrete_sequence=[cat_color])
fig_total_chart.update_layout(
    {
        "xaxis": {
            "fixedrange": True,
            "tickangle": -45,
            "dtick": 1,
            # "showspikes": True,
            "spikemode": 'toaxis',
            "spikesnap": 'data',
        },
        "yaxis": {
            "fixedrange": True
        },
        "title": {
            "text": total_chart_title,
            "xanchor": "center",
            "x": 0.5
        },
        "hovermode": "x unified"
    }
)
sb_tab1, sb_tab2 = st.sidebar.tabs(("Totals", "Growths vs. PY"))
sb_tab1.plotly_chart(fig_total_chart, use_container_width=True)

all_years = list(total_chart_data["Year"])
val_list = list(total_chart_data["Gross index"])
growths_data_dict = {
    "Year": all_years[1:],
    "Growth": [year_val - prev_year_val for year_val, prev_year_val in zip(val_list[1:], val_list[:-1])],
    "Growth (%)": [year_val/prev_year_val - 1 for year_val, prev_year_val in zip(val_list[1:], val_list[:-1])]
}
growth_chart_data = pd.DataFrame(growths_data_dict)
growths_color_seq = ["green" if growth > 0 else "red" for growth in growths_data_dict["Growth"]]
fig_growth_chart = go.Figure(
    data=go.Bar(
        x=growth_chart_data["Year"], y=growth_chart_data["Growth"], marker_color=growths_color_seq, width=0.5
    )
)
fig_growth_chart.update_layout(
    {
        "xaxis": {
            "fixedrange": True,
            "tickangle": -45,
            "dtick": 1
        },
        "yaxis": {
            "fixedrange": True
        },
        "title": {
            "text": growth_chart_title,
            "xanchor": "center",
            "x": 0.5
        }
    }
)
sb_tab2.plotly_chart(fig_growth_chart, use_container_width=True)
