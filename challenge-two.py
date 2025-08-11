# challenge-two.py

import re
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.figure_factory as ff
import ssl
import urllib.request

ssl._create_default_https_context = ssl._create_unverified_context

# Page layout
st.set_page_config(
    page_title="Views on Gender Roles Across the United States in 2018",
    page_icon="📊",
    layout="wide"
)

# Load data
@st.cache_data(show_spinner=False)
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

    # Clean age
    gss_clean["age"] = gss_clean["age"].replace({"89 or older": "89"}).astype(float)

    # Order for male_breadwinner responses used in the static bar
    gss_clean["male_breadwinner"] = pd.Categorical(
        gss_clean["male_breadwinner"],
        categories=["strongly agree", "agree", "disagree", "strongly disagree"],
        ordered=True,
    )

    # Prep education class & satjob harmonization for extra credit controls
    gss_clean["education_class"] = pd.cut(
        gss_clean["education"],
        bins=[0, 11, 12, 14, 16, 20],
        labels=[
            "No HS Diploma",
            "High School Grad",
            "Some College",
            "Bachelor's Degree",
            "Graduate or more",
        ],
        include_lowest=True,
    )
    gss_clean["satjob"] = gss_clean["satjob"].replace(
        ["mod. satisfied", "a little dissat"],
        ["moderately satisfied", "moderately dissatisfied"],
    )
    
    return gss_clean

gss_clean = load_data()

# Define statements for each variable
variable_statements = {
    'satjob': 'On the whole, how satisfied are you with the work you do?',
    'relationship': 'A working mother can establish just as warm and secure a relationship with her children as a mother who does not work.',
    'male_breadwinner': 'It is much better for everyone involved if the man is the achiever outside the home and the woman takes care of the home and family.',
    'men_bettersuited': 'Most men are better suited emotionally for politics than are most women.',
    'child_suffer': 'A preschool child is likely to suffer if his or her mother works.',
    'men_overwork': 'Family life often suffers because men concentrate too much on their work.'
}

# Title and description
st.title("Views on Gender Roles Across the United States in 2018")

st.markdown("""
<p style='font-size: 16px; line-height: 1.6; color: #555; margin-bottom: 25px;'>
This interactive dashboard explores American attitudes on gender roles and work-life balance using data from the 
<strong>2018 General Social Survey (GSS)</strong>. Select different survey questions from the dropdown menu to see how 
responses vary across gender, geographic region, or education level. The data reveals patterns in how different 
demographic groups view traditional gender roles, working mothers, and job satisfaction.
</p>
""", unsafe_allow_html=True)

st.markdown("---")

st.header("Select a Survey Question and Demographic Group")
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("**Explore attitudes about:**")
    feature_options = {
        'satjob': 'How satisfied are you with your work?',
        'relationship': 'Can working mothers have warm relationships with children?',
        'male_breadwinner': 'Should men work while women care for home?',
        'men_bettersuited': 'Are men better suited for politics than women?',
        'child_suffer': 'Do children suffer when mothers work?',
        'men_overwork': 'Does family suffer when men focus on work?'
    }
    chosen_feature = st.selectbox(
        "",
        options=list(feature_options.keys()),
        format_func=lambda x: feature_options[x],
        label_visibility="collapsed"
    )

with col2:
    st.markdown("**Compare by:**")
    group_options = {
        'sex': 'Sex',
        'region': 'Region',
        'education_class': 'Education Level'
    }
    chosen_group = st.selectbox(
        "",
        options=list(group_options.keys()),
        format_func=lambda x: group_options[x],
        label_visibility="collapsed"
    )

# Display statement
statement = variable_statements.get(chosen_feature, '')
if chosen_feature == 'satjob':
    st.info(f"**Survey Question:** \"{statement}\"")
else:
    st.info(f"**Respondents were asked to agree or disagree with:**  \n\"{statement}\"")

category_orders = {}

if chosen_feature == 'satjob':
    category_orders[chosen_feature] = ["very satisfied", "moderately satisfied", "moderately dissatisfied", "very dissatisfied"]
elif chosen_feature == 'men_bettersuited':
    category_orders[chosen_feature] = ["strongly agree", "agree", "disagree", "strongly disagree"]
elif chosen_feature == 'men_overwork':
    category_orders[chosen_feature] = ["strongly agree", "agree", "neither agree nor disagree", "disagree", "strongly disagree"]
elif chosen_feature in ['male_breadwinner', 'relationship', 'child_suffer']:
    category_orders[chosen_feature] = ["strongly agree", "agree", "disagree", "strongly disagree"]

if chosen_group == 'education_class':
    category_orders['education_class'] = ['No HS Diploma', 'High School Grad', 'Some College', "Bachelor's Degree", 'Graduate or more']

# Color map
color_map = {}
if chosen_group == 'sex':
    color_map = {'male': '#2E86AB', 'female': '#A23B72'}
elif chosen_group == 'region':
    color_map = {
        'south atlantic': '#FF0000',
        'e. nor. central': '#0000FF',
        'pacific': '#00FF00',
        'w. sou. central': '#800080',
        'middle atlantic': '#FFA500',
        'mountain': '#008080',
        'e. sou. central': '#FFC0CB',
        'w. nor. central': '#964B00',
        'new england': '#FFFF00'
    }
elif chosen_group == 'education_class':
    color_map = {
        'Graduate or more': '#004c6d',
        "Bachelor's Degree": '#3a7391',
        'Some College': '#649baf',
        'High School Grad': '#93c6cd',
        'No HS Diploma': '#c8f2f2'
    }

fig = px.histogram(
    gss_clean,
    x=chosen_feature,
    color=chosen_group,
    barmode='group',
    category_orders=category_orders,
    color_discrete_map=color_map,
    labels={
        chosen_feature: 'Response',
        chosen_group: group_options[chosen_group],
        'count': 'Number of Respondents'
    }
)

fig.update_layout(
    xaxis_title="",
    yaxis_title="Number of Respondents",
    legend_title_text=group_options[chosen_group],
    margin=dict(l=40, r=20, t=20, b=40),
    hoverlabel=dict(bgcolor="white", font_size=12),
    font=dict(size=12),
    showlegend=True,
    height=500
)

st.plotly_chart(fig, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #888; font-size: 14px;'>
Data source: General Social Survey 2018 | Dashboard created by Angelo Orciuoli
</div>
""", unsafe_allow_html=True)
