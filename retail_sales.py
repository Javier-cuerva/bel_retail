import streamlit as st
import plotly.express as px
import plotly.io as pio
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
selected_months = sb_col2.multiselect("Select months", options=month_names, disabled=(selected_agg!="Custom"))
total_chart_data = data[["NACE groups", "Year", "Month Name", "Gross index"]]
total_chart_data = total_chart_data[total_chart_data["Month Name"].isin(selected_months)]
total_chart_data = total_chart_data[total_chart_data["NACE groups"] == selected_cat]
total_chart_data = total_chart_data[["Year", "Gross index"]].groupby(["Year"], as_index=False).sum()
fig_total_chart = px.line(total_chart_data, x="Year", y="Gross index", markers=True, color_discrete_sequence=[cat_color])
fig_total_chart.update_layout(
    {
        "xaxis": {
            "fixedrange": True,
            "tickangle": -45,
            "dtick": 1
        },
        "yaxis": {
            "fixedrange": True
        }
    }
)
st.sidebar.plotly_chart(fig_total_chart, use_container_width=True)
