import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
from datetime import date

# Set page to wide mode
st.set_page_config(layout="wide")

# Cache data for quicker loading
@st.cache 

def load_data():
    ''' Load the most recent COVID-19 data from the Ontario Government.'''
    
    df = pd.read_csv('https://data.ontario.ca/dataset/f4f86e54-872d-43f8-8a86-3892fd3cb5e6/resource/ed270bb8-340b-41f9-a7c6-e8ef587e6d11/download')
    df = df.fillna(0)
    return df 

def format_data(source_data):
    ''' Format the COVID-19 data to:
    1) shorten long column names, 2) replace spaces with underscores and
    3) remove columns not in use 

    Parameters:
    source_data: the source data called by load_data()
    '''
    # Load data
    df = source_data

    # Rename lengthier column names
    df_formatted = df.rename(columns = {
        "Percent positive tests in last day": "Percent_positive_tests", 
        "Number of patients hospitalized with COVID-19": "Number_hospitalized",
        "Number of patients in ICU on a ventilator with COVID-19": "Number_ventilator",
        "Number of patients in ICU with COVID-19": "Number_ICU",
        "Reported Date": "Date",
        'Total patients approved for testing as of Reporting Date': 'Patients_approved_for_testing',
        'Total tests completed in the last day': 'Total tests completed'})
    
    # Replace spaces with underscores
    df_formatted.columns = df_formatted.columns.str.replace(' ', '_')

    # Remove columns with LTC (long-term care)
    df_formatted = df_formatted[df_formatted.columns.drop(list(df_formatted.filter(regex='LTC')))]
    # Remove defunct columns (haven't been updated in a long time)
    df_formatted = df_formatted.drop(columns=['Confirmed_Negative', 'Presumptive_Negative', 'Presumptive_Positive'])
    # Remove unused columns in application
    df_formatted = df_formatted.drop(columns=['Under_Investigation', 'Patients_approved_for_testing'])

    # Create Active Cases column
    df_formatted['Active_Cases'] = df_formatted['Total_Cases'] - df_formatted['Resolved'] - df_formatted['Deaths']

    return df_formatted

def create_diff_columns(formatted_data, list_of_columns):
    '''Create columns using .diff to calculate the difference between numbers today and yesterday.
    
    Paramaters:
    formatted_data: DataFrame that is the result of the function format_data
    list_of_columns: List of columns that you'd like to know the difference
    '''

    df = formatted_data
    column_list = list_of_columns
    for column_name in column_list:
        df['New_'+str(column_name)] = df[str(column_name)].diff()

    return df

def refer_data(source_data, column_name, date):
    '''Function to obtain specific data point in data.'''
    df = source_data

    if date == 'today':
        # Obtain last updated 
        data_point = df[column_name].iloc[-1]
    elif date == 'yesterday':
        data_point = df[column_name].iloc[-2]

    return data_point

def date_selection(summary_data, date_range):
    '''Filter based on date range selection from 
    daterange_selection selection'''

    df = summary_data
    
    if date_range == 'Today':
        df_filtered = df
    elif date_range == 'Last Week':
        df_filtered = df.tail(7)
    elif date_range == 'Last 2 weeks':
        df_filtered = df.tail(14)
    elif date_range == 'Last Month':
        df_filtered = df.tail(30)
    elif date_range == 'Last 3 Months':
        df_filtered = df.tail(90)
    else:
        df_filtered = df.tail(180)
    
    return df_filtered    

def change_dtypes(summary_data):

    df = summary_data

    date_col = df.pop('Date')
    perc_col = df.pop('Percent_positive_tests')

    df_formatted = df.replace(np.nan, 0)
    df_formatted = df_formatted.astype('int64')

    df_formatted.insert(0, 'Date', date_col)
    df_formatted.insert(6, 'Percent_positive_tests', perc_col)

    return df_formatted

def create_pie_chart_df(summary_data):

    df = summary_data

    pie_chart_df = df.iloc[:, [0, 11, 12, 15]]
    pie_chart_df = pie_chart_df.rename(columns={
        'New_Resolved':'Resolved Cases',
        'New_Total_Cases':'New Cases',
        'New_Deaths':'Deaths'})
    pie_chart_df = pie_chart_df.melt(id_vars = ['Date'])
    pie_chart_df = pie_chart_df[pie_chart_df['Date'].str.contains(today.strftime('%Y-%m-%d'))]
    
    
    return pie_chart_df

## Streamlit Date Range Selector ##
daterange_selection = st.sidebar.selectbox(
    "Date range to visualize:",
    ('Today', 'Last Week', 'Last 2 weeks', 
    'Last Month', 'Last 3 Months', 
    'Last 6 Months')
)

# Load in and format data
covid_data = load_data()
formatted_data = format_data(covid_data)

# Columns for summary
summary_columns = ['Total_Cases', 'Deaths', 'Number_hospitalized','Number_ICU', 'Resolved', 'Total_tests_completed', 'Active_Cases']
summary_data = create_diff_columns(formatted_data, summary_columns)
# Subset the summary data by user selection from daterange_selection
subset_summary_data = date_selection(summary_data, daterange_selection)

# Change all column type to int64 except Date and Percent positive cases
subset_summary_data = change_dtypes(subset_summary_data)


# Initialize lists to run for loops for summary_columns
data_points_today = []
data_points_yesterday = []
columns_to_refer = [col for col in summary_data if 'New' in col]

for i in columns_to_refer:
    data_points_today.append(refer_data(summary_data, i, 'today'))
    data_points_yesterday.append(refer_data(summary_data, i, 'yesterday'))

# Convert lists to numpy arrays
data_points_today = np.array(data_points_today, dtype='int64')
data_points_yesterday = np.array(data_points_yesterday, dtype='int64')

### Streamlit UI ###

## Daily Summary section ##

st.title('Ontario COVID-19 Dashboard')

# Set container
daily_summary = st.beta_container() 
col1, col2, col3 = st.beta_columns(3)
# Write data inside container
with daily_summary:
    st.header('Summary of today')
    today = date.today() 
    st.subheader(today.strftime('%B %d, %Y'))

    with col1: 
        st.text('')
        st.text('')
        st.text('')
        st.markdown(':small_blue_diamond: ' + 'New cases: ' + str(data_points_today[0]))
        st.markdown(':small_blue_diamond: ' + 'Resolved cases: ' + str(data_points_today[4]))
        st.markdown(':small_blue_diamond: ' + 'Active cases: ' + str(subset_summary_data.iloc[-1, 10]))
        st.markdown(':small_blue_diamond: ' + 'Deaths: ' + str(data_points_today[1]))
        st.markdown(':small_blue_diamond: ' + 'Hospitalizations: ' + str(subset_summary_data.iloc[-1, 13]))
        st.markdown(':small_blue_diamond: ' + 'New patients in the ICU: ' + str(subset_summary_data.iloc[-1, -4]))
        st.markdown(':small_blue_diamond: ' + 'Tests today: ' + str(subset_summary_data.iloc[-1, -2]))
        st.markdown(':small_blue_diamond: ' + 'Percent positive tests today: ' + str(subset_summary_data.iloc[-1, 6]) + '%')
    
    with col2:
        pie_chart_df = create_pie_chart_df(subset_summary_data)
        pie_chart = px.pie(pie_chart_df, values = 'value', names = 'variable')
        st.plotly_chart(pie_chart)

## Last 5 days table ##
# Set container #
data_table = st.beta_container()
# Write data inside container: #
with data_table:
    # Set header #
    st.header('Last 5 days')
    # Empty spaces #
    st.text('')
    st.text('')

    # Create table
    col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.beta_columns(9)
    with col1: st.markdown('**Date**')
    with col2: st.markdown('**Cases**')
    with col3: st.markdown('**Resolved cases**')
    with col4: st.markdown('**Active cases**')
    with col5: st.markdown('**Deaths**')
    with col6: st.markdown('**Hospitalizations**')
    with col7: st.markdown('**ICU patients**')
    with col8: st.markdown('**Tests conducted**')
    with col9: st.markdown('**% positive tests**')

    for i in range(1, 6):
        cols = st.beta_columns(9)
        cols[0].markdown(subset_summary_data.iloc[-i, 0])
        cols[1].markdown(subset_summary_data.iloc[-i, 4])
        cols[2].markdown(subset_summary_data.iloc[-i, 2])
        cols[3].markdown(subset_summary_data.iloc[-i, 10])
        cols[4].markdown(subset_summary_data.iloc[-i, 3])
        cols[5].markdown(subset_summary_data.iloc[-i, 7])
        cols[6].markdown(subset_summary_data.iloc[-i, 8])
        cols[7].markdown(subset_summary_data.iloc[-i, 5])
        cols[8].markdown(subset_summary_data.iloc[-i, 6])

## Graph Section ##
# Set container #
graph_container = st.beta_container()
# Write data inside container: #

with graph_container:  
    st.text('')
    st.header('Graphs')
    st.text('')

    new_cases_fig = px.bar(subset_summary_data, x = "Date", y = "New_Total_Cases")
    new_cases_fig.update_layout(title = 'New Total Cases', xaxis_title='',yaxis_title='')

    new_deaths_fig = px.bar(subset_summary_data, x = "Date", y = "New_Deaths")
    new_deaths_fig.update_layout(title='New Deaths', xaxis_title='',yaxis_title='')

    new_hosp_fig = px.bar(subset_summary_data, x = "Date", y = "New_Number_hospitalized")
    new_hosp_fig.update_layout(title='New number of patients hospitalized', xaxis_title='',yaxis_title='')

    new_ICU_fig = px.bar(subset_summary_data, x = "Date", y = "New_Number_ICU")
    new_ICU_fig.update_layout(title='New number of patients in the ICU', xaxis_title='',yaxis_title='')

    new_resolved_fig = px.bar(subset_summary_data, x = "Date", y = "New_Resolved")
    new_resolved_fig.update_layout(title='New number of cases resolved', xaxis_title='',yaxis_title='')


    st.plotly_chart(new_cases_fig, use_container_width=True)
    st.plotly_chart(new_deaths_fig, use_container_width=True)
    st.plotly_chart(new_hosp_fig, use_container_width=True)
    st.plotly_chart(new_ICU_fig, use_container_width=True)
    st.plotly_chart(new_resolved_fig, use_container_width=True)
