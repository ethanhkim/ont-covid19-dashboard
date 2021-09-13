def load_data(type):
    ''' Load the most recent COVID-19 data from the Ontario Government.'''

    if type == 'COVID':
        url = 'https://data.ontario.ca/api/3/action/datastore_search?resource_id=ed270bb8-340b-41f9-a7c6-e8ef587e6d11'  
        http = urllib3.PoolManager()
        response = http.request('GET', url)
        data = json.loads(response.data.decode('utf-8'))
        df = pd.json_normalize(data['result']['records'])
        df = df.fillna(0)
    elif type == 'Vaccine':
        df = pd.read_csv("https://data.ontario.ca/dataset/752ce2b7-c15a-4965-a3dc-397bf405e7cc/resource/8a89caa9-511c-4568-af89-7f2174b4378c/download/vaccine_doses.csv")
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