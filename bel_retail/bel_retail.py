import os

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from get_data import get_data_from_api


# Changing python working directory to the one of the script for opening files
base_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(base_dir)


# Getting data from STATBEL API and defining data variables
data = get_data_from_api()
data["Formatted Month"] = data.apply(lambda row : row["Month"].strftime("%Y-%m"), axis="columns")
month_values = data["Month"].unique()
month_values = month_values[month_values.argsort()]
month_format_func = lambda month : month.strftime("%b %Y")
month_names = data["Month Name"].unique()
categories = data["NACE groups"].unique()
n_cats = len(categories)
color_list = px.colors.qualitative.Bold[:n_cats]
color_map = {cat: color for cat, color in zip(categories, color_list)}
indices = [
    "Gross index", "Trend of the index",
    "Index (WDA)", "Index (SA-WDA)",
    "Deflated gross index", "Trend of the deflated index", 
    "Deflated index (WDA)", "Deflated index (SA-WDA)"
]

text_folderpath = "text/"
with open(text_folderpath + "cover.md", "r") as cover_file:
    cover_str = cover_file.read()
with open(text_folderpath + "sb_cover.md", "r") as sb_cover_file:
    sb_cover_str = sb_cover_file.read()
with open(text_folderpath + "data_desc.md", "r") as data_desc_file:
    data_desc_str = data_desc_file.read()

# Generating containers
st_cover = st.container()
st_ts = st.container() # ts = time series
st_sidebar = st.sidebar.container()

def cover(st_cover):
    st_cover.markdown(cover_str)
    st_dd = st_cover.expander("See for detailed dataset description", expanded=False)
    st_dd.markdown(data_desc_str)
    st_cover.divider()


def ts(st_ts):
    st_ts.header("Time Series Chart")

    col1, col2, col3 = st_ts.columns(3)
    selected_index = col1.selectbox("Select index", options=indices)
    first_month = col2.selectbox("From", options=month_values, format_func=month_format_func)
    last_month = col3.selectbox("To", options=month_values, format_func=month_format_func, )

    below_col = st_ts.columns(1)[0]
    selected_cats = below_col.multiselect("Select categories", options=categories)
    chart_data = data[["Month", "Formatted Month", "NACE groups", selected_index]]
    chart_data = chart_data[chart_data["NACE groups"].isin(selected_cats)]
    chart_data = chart_data.sort_values(by="Month")
    ts_chart_title = "Total value time series in period {} - {}".format(
        first_month.strftime("%b %Y"), last_month.strftime("%b %Y")
    )
    fig = px.line(
        chart_data,
        x="Formatted Month", y=selected_index,
        color="NACE groups",
        color_discrete_map=color_map,
        range_x=(first_month, last_month),
        title=ts_chart_title
    )
    fig.update_layout(
        {
            "xaxis": {
                "fixedrange": True,
                "tickangle": -45,
                "type": "date",
                "showline": True,
                "linewidth": 2,
                "tickformat": "%b %y",
                "title": ""
            },
            "yaxis": {
                "fixedrange": True,
                "showline": True,
                "linewidth": 1,
            },
            "title": {
                "text": ts_chart_title,
                "xanchor": "center",
                "x": 0.5
            },
            "legend": {
                "x": 0,
                "y": -0.3,
                "traceorder": "normal",
                "orientation": "h"
            },
            "hovermode": "x unified"
        }
    )
    fig.update_traces(hovertemplate=None)
    below_col.plotly_chart(fig)


def sidebar(st_sidebar):
    st_sidebar.markdown(sb_cover_str)
    st_sidebar.warning(
        body=(
            "If the last year is not complete up to December "
            "and the non-updated months are included, the charts may show a sharp decline!"
        ),
        icon="⚠️"
    )
    st_sidebar.divider()

    selected_index = st_sidebar.selectbox("Select index", key="index_sb", options=indices)
    selected_cat = st_sidebar.selectbox("Select category", options=categories)
    cat_color = color_map[selected_cat]

    sb_col1, sb_col2 = st_sidebar.columns(2)
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

    total_chart_data = data[["NACE groups", "Year", "Month Name", selected_index]]
    total_chart_data = total_chart_data[total_chart_data["Month Name"].isin(selected_months)]
    total_chart_data = total_chart_data[total_chart_data["NACE groups"] == selected_cat]
    total_chart_data = total_chart_data[["Year", selected_index]].groupby(["Year"], as_index=False).sum()
    fig_total_chart = px.line(total_chart_data, x="Year", y=selected_index, markers=True, color_discrete_sequence=[cat_color], )
    fig_total_chart.update_layout(
        {
            "xaxis": {
                "fixedrange": True,
                "tickangle": -45,
                "dtick": 1,
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
    sb_tab1, sb_tab2 = st_sidebar.tabs(("Totals", "Growths vs. PY"))
    sb_tab1.plotly_chart(fig_total_chart, use_container_width=True)

    all_years = list(total_chart_data["Year"])
    val_list = list(total_chart_data[selected_index])
    growths_data_dict = {
        "Year": all_years[1:],
        "Growth": [year_val - prev_year_val for year_val, prev_year_val in zip(val_list[1:], val_list[:-1])],
        "Growth (%)": [year_val/prev_year_val - 1 for year_val, prev_year_val in zip(val_list[1:], val_list[:-1])]
    }
    growth_chart_data = pd.DataFrame(growths_data_dict)
    growths_color_seq = ["green" if growth > 0 else "red" for growth in growths_data_dict["Growth"]]
    toggle_pct = sb_tab2.checkbox(label="Y-axis in %", value=False)
    selected_growth = "Growth (%)" if toggle_pct else "Growth"
    fig_growth_chart = go.Figure(
        data=go.Bar(
            x=growth_chart_data["Year"], y=growth_chart_data[selected_growth], marker_color=growths_color_seq, width=0.5
        )
    )
    fig_growth_chart.update_layout(
        {
            "xaxis": {
                "fixedrange": True,
                "tickangle": -45,
                "dtick": 1,
            },
            "yaxis": {
                "fixedrange": True,
                "tickformat": "+,.0%" if toggle_pct else ">+,.0f"
            },
            "title": {
                "text": growth_chart_title,
                "xanchor": "center",
                "x": 0.5
            }
        }
    )
    year_vs_hover_label = ["{}v{}".format(str(year)[-2:], str(prev_year)[-2:]) for year, prev_year in zip(all_years[:-1], all_years[1:])]
    fig_growth_chart.update_traces({
        "hovertemplate": '<b>%{customdata[1]} Growth: </b><span style="color: %{customdata[0]}">%{customdata[2]:>+,.2f} (%{customdata[3]:>+,.2%})</span> <extra></extra>',
        "customdata": list(zip(growths_color_seq, year_vs_hover_label, growth_chart_data["Growth"], growth_chart_data["Growth (%)"]))
    })
    sb_tab2.plotly_chart(fig_growth_chart, use_container_width=True)


# Rendering dashboard
cover(st_cover); ts(st_ts); sidebar(st_sidebar)





