import streamlit as st
import numpy as np
import pandas as pd
import re
import plotly.graph_objects as go
import plotly.express as px
import plotly.figure_factory as ff
import ssl
import urllib.request

ssl._create_default_https_context = ssl._create_unverified_context

# Page layout
st.set_page_config(
    page_title="GSS 2018 Dashboard",
    page_icon="📊",
    layout="wide"
)

# Load and clean data
@st.cache_data
def load_data():
    gss = pd.read_csv("https://github.com/jkropko/DS-6001/raw/master/localdata/gss2018.csv",
                     encoding='cp1252', na_values=['IAP','IAP,DK,NA,uncodeable', 'NOT SURE',
                                                   'DK', 'IAP, DK, NA, uncodeable', '.a', "CAN'T CHOOSE"])
    
    gss_clean = gss[['id', 'wtss', 'sex', 'educ', 'region', 'age', 'coninc', 'prestg10', 'mapres10', 'papres10', 'sei10', 'satjob', 'fechld', 'fefam', 'fepol', 'fepresch', 'meovrwrk']]
    gss_clean = gss_clean.rename({'wtss':'weight', 
                                  'educ':'education', 
                                  'coninc':'income', 
                                  'prestg10':'job_prestige',
                                  'mapres10':'mother_job_prestige', 
                                  'papres10':'father_job_prestige', 
                                  'sei10':'socioeconomic_index', 
                                  'fechld':'relationship', 
                                  'fefam':'male_breadwinner', 
                                  'fehire':'hire_women', 
                                  'fejobaff':'preference_hire_women', 
                                  'fepol':'men_bettersuited', 
                                  'fepresch':'child_suffer',
                                  'meovrwrk':'men_overwork'},axis=1)
    gss_clean.age = gss_clean.age.replace({'89 or older':'89'})
    gss_clean.age = gss_clean.age.astype('float')
    return gss_clean

# Load data
gss_clean = load_data()

# Sidebar
st.sidebar.title("GSS 2018 Dashboard")
st.sidebar.markdown("By Angelo Orciuoli")
st.sidebar.markdown("---")

# Navigation
page = st.sidebar.radio(
    "   ",
    ["Overview", "Summary Table", "Breadwinner Barplot", 
     "Prestige vs Income", "Boxplots by Gender", "Income by Prestige Range"]
)

# Main content based on selection
if page == "Overview":
    st.header("Overview")
    
    text = """
## The Gender Wage Gap in the U.S.

In the United States, women on average continue to earn less than men. According to a 2023 analysis by the **Pew Research Center**, women earned about 82% of what men earned in 2022 – a gap that has narrowed only slightly over the past two decades (in 2002, women earned roughly 80% as much as men). The gender wage gap has decreased significantly since the early 1980s (when the disparity was much larger), but progress has largely stalled in recent years.

Official data from the **U.S. Bureau of Labor Statistics** (BLS) show a similar pay gap. In 2021, for example, the median weekly earnings of full-time female workers were roughly 83% of those of male workers – meaning the typical woman earned about 83 cents for every dollar earned by a man. This disparity persists across most industries and occupations, indicating that the wage gap is a widespread phenomenon and not confined to a single sector.

## About the GSS

The **General Social Survey (GSS)** is a long-running sociological survey of American adults, conducted by NORC at the University of Chicago. Since 1972, the GSS has collected data on a wide range of topics—from demographics and education to behaviors and attitudes on social issues—using in-person interviews (and more recently, online surveys) with a nationally representative sample of the U.S. population. The survey is typically conducted every one to two years, which allows researchers to track changes in U.S. society over time. GSS findings are widely used in social science research and public policy discussions as a benchmark for Americans' attitudes and experiences.
"""
    st.markdown(text)

elif page == "Summary Table":
    st.header("Average Economic & Education Metrics by Gender")
    
    gss_gender_summary = (
        gss_clean
          .groupby('sex')
          .agg({
              'income': 'mean',
              'job_prestige': 'mean',
              'socioeconomic_index': 'mean',
              'education': 'mean'
          })
          .round(2).reset_index()
    )
    
    gss_gender_summary = gss_gender_summary.rename(columns={
        'sex': 'Sex',
        'income': 'Average Income ($)',
        'job_prestige': 'Average Job Prestige Score',
        'socioeconomic_index': 'Average Socioeconomic Index',
        'education': 'Average Years of Education'
    })
    
    fig_table = ff.create_table(gss_gender_summary)
    st.plotly_chart(fig_table, use_container_width=True)

elif page == "Breadwinner Barplot":
    st.header("Agreement with 'Male Breadwinner' by Group")
    
    gss_clean['male_breadwinner'] = pd.Categorical(
        gss_clean['male_breadwinner'],
        categories=["strongly agree", "agree", "disagree", "strongly disagree"],
        ordered=True
    )
    
    fig_bar = px.histogram(
        gss_clean,
        x="male_breadwinner",
        color="sex",
        barmode="group",
        color_discrete_map={"male": "#2E86AB", "female": "#A23B72"}
    )
    
    fig_bar.update_layout(
        xaxis_title="Agreement with 'Male Breadwinner' Statement",
        yaxis_title="Number of Respondents",
        legend_title_text="Sex"
    )
    
    st.plotly_chart(fig_bar, use_container_width=True)

elif page == "Prestige vs Income":
    st.header("Occupational Prestige vs. Income")
    
    fig_scatter = px.scatter(
        gss_clean,
        x="job_prestige",
        y="income",
        color="sex",
        trendline="ols",
        trendline_scope="trace",
        hover_data={
            "education": True,
            "socioeconomic_index": True,
            "job_prestige": False,
            "income": False,
            "sex": False
        },
        labels={
            "education": "Years of Education",
            "socioeconomic_index": "Socioeconomic Index"
        },
        color_discrete_map={"male": "#2E86AB", "female": "#A23B72"}
    )
    
    fig_scatter.update_layout(
        xaxis_title="Occupational Prestige Score",
        yaxis_title="Income ($)",
        legend_title_text="Sex",
        height=600
    )
    
    st.plotly_chart(fig_scatter, use_container_width=True)

elif page == "Boxplots by Gender":
    st.header("Income & Job Prestige Distributions by Gender")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_income = px.box(
            gss_clean,
            x="sex",
            y="income",
            color="sex",
            color_discrete_map={"male": "#2E86AB", "female": "#A23B72"}
        )
        fig_income.update_layout(
            showlegend=False,
            xaxis_title="",
            yaxis_title="Income ($)"
        )
        st.plotly_chart(fig_income, use_container_width=True)
    
    with col2:
        fig_prestige = px.box(
            gss_clean,
            x="sex",
            y="job_prestige",
            color="sex",
            color_discrete_map={"male": "#2E86AB", "female": "#A23B72"}
        )
        fig_prestige.update_layout(
            showlegend=False,
            xaxis_title="",
            yaxis_title="Job Prestige Score"
        )
        st.plotly_chart(fig_prestige, use_container_width=True)

elif page == "Income by Prestige Range":
    st.header("Income by Job Prestige Range & Gender")
    
    gss_reduced = gss_clean[['income', 'sex', 'job_prestige']].dropna()
    gss_reduced['prestige_bin'] = pd.cut(
        gss_reduced['job_prestige'], 
        bins=6, 
        include_lowest=True
    )
    
    fig_facets = px.box(
        gss_reduced,
        x='sex',
        y='income',
        color='sex',
        facet_col='prestige_bin',
        facet_col_wrap=2,
        color_discrete_map={'male': '#2E86AB', 'female': '#A23B72'},
        labels={
            'sex': '',
            'income': 'Income ($)',
            'prestige_bin': 'Job Prestige Range'
        }
    )
    
    fig_facets.update_layout(height=900)
    st.plotly_chart(fig_facets, use_container_width=True)

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("*Tip: Use the menu above to switch views.*")
