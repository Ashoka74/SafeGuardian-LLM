import json
import streamlit as st
from keplergl import keplergl
import pandas as pd
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from stqdm import stqdm
stqdm.pandas()
from dateutil import parser
import squarify
import matplotlib.colors as mcolors
import textwrap
from streamlit_extras.stateful_button import button as stateful_button
from streamlit_keplergl import keplergl_static
from keplergl import KeplerGl


import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import json
import os
import datetime
import pandas as pd
time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
cred = credentials.Certificate("rescue_tools/disasterrescueai-firebase-adminsdk.json")
try:
    firebase_admin.initialize_app(credential=cred,options={'databaseURL': 'https://disasterrescueai-default-rtdb.firebaseio.com'}, name='RescueTeam_RealTimeDatabase')
except Exception as e:
    print(f'{e} error')
    pass

ref = db.reference('rescue_team_dataset', app=firebase_admin.get_app(name='RescueTeam_RealTimeDatabase'))
db = firebase_admin.db

def responses_to_df(data,col):
    data = pd.DataFrame.from_records(data).T
    if col is not None:
        json_df = pd.json_normalize(data[col])
        json_df.set_index(data.index, inplace=True)
    else:
        json_df = pd.json_normalize(data)
        json_df.set_index(data.index, inplace=True)
    return json_df


st.set_option('deprecation.showPyplotGlobalUse', False)

from pandas.api.types import (
    is_categorical_dtype,
    is_datetime64_any_dtype,
    is_numeric_dtype,
    is_object_dtype,
)

st.title('Interactive Map')

# Initialize session state
if 'analyzers' not in st.session_state:
    st.session_state['analyzers'] = []
if 'col_names' not in st.session_state:
    st.session_state['col_names'] = []
if 'clusters' not in st.session_state:
    st.session_state['clusters'] = {}
if 'new_data' not in st.session_state:
    st.session_state['new_data'] = pd.DataFrame()
if 'dataset' not in st.session_state:
    st.session_state['dataset'] = pd.DataFrame()
if 'data_processed' not in st.session_state:
    st.session_state['data_processed'] = False
if 'stage' not in st.session_state:
    st.session_state['stage'] = 0
if 'filtered_data' not in st.session_state:
    st.session_state['filtered_data'] = None
if 'gemini_answer' not in st.session_state:
    st.session_state['gemini_answer'] = None
if 'parsed_responses' not in st.session_state:
    st.session_state['parsed_responses'] = None
if 'map_generated' not in st.session_state:
    st.session_state['map_generated'] = False
if 'date_loaded' not in st.session_state:
    st.session_state['data_loaded'] = False


if "datasets" not in st.session_state:
    st.session_state.datasets = []




def plot_treemap(df, column, top_n=32):
        # Get the value counts and the top N labels
        value_counts = df[column].value_counts()
        top_labels = value_counts.iloc[:top_n].index
        
        # Use np.where to replace all values not in the top N with 'Other'
        revised_column = f'{column}_revised'
        df[revised_column] = np.where(df[column].isin(top_labels), df[column], 'Other')

        # Get the value counts including the 'Other' category
        sizes = df[revised_column].value_counts().values
        labels = df[revised_column].value_counts().index

        # Get a gradient of colors
        # colors = list(mcolors.TABLEAU_COLORS.values())

        n_colors = len(sizes)
        colors = plt.cm.Oranges(np.linspace(0.3, 0.9, n_colors))[::-1]


        # Get % of each category
        percents = sizes / sizes.sum()

        # Prepare labels with percentages
        labels = [f'{label}\n {percent:.1%}' for label, percent in zip(labels, percents)]

        fig, ax = plt.subplots(figsize=(20, 12))

        # Plot the treemap
        squarify.plot(sizes=sizes, label=labels, alpha=0.7, pad=True, color=colors, text_kwargs={'fontsize': 10})

        ax = plt.gca()
        # Iterate over text elements and rectangles (patches) in the axes for color adjustment
        for text, rect in zip(ax.texts, ax.patches):
            background_color = rect.get_facecolor()
            r, g, b, _ = mcolors.to_rgba(background_color)
            brightness = np.average([r, g, b])
            text.set_color('white' if brightness < 0.5 else 'black')

            # Adjust font size based on rectangle's area and wrap long text
            coef = 0.8
            font_size = np.sqrt(rect.get_width() * rect.get_height()) * coef
            text.set_fontsize(font_size)
            wrapped_text = textwrap.fill(text.get_text(), width=20)
            text.set_text(wrapped_text)

        plt.axis('off')
        plt.gca().invert_yaxis()
        plt.gcf().set_size_inches(20, 12)

        fig.patch.set_alpha(0)

        ax.patch.set_alpha(0)
        return fig

def plot_hist(df, column, bins=10, kde=True):
        fig, ax = plt.subplots(figsize=(12, 6))
        sns.histplot(data=df, x=column, kde=True, bins=bins,color='orange')
        # set the ticks and frame in orange
        ax.spines['bottom'].set_color('orange')
        ax.spines['top'].set_color('orange')
        ax.spines['right'].set_color('orange')
        ax.spines['left'].set_color('orange')
        ax.xaxis.label.set_color('orange')
        ax.yaxis.label.set_color('orange')
        ax.tick_params(axis='x', colors='orange')
        ax.tick_params(axis='y', colors='orange')
        ax.title.set_color('orange')

        # Set transparent background
        fig.patch.set_alpha(0)
        ax.patch.set_alpha(0)
        return fig


def plot_line(df, x_column, y_columns, figsize=(12, 10), color='orange', title=None, rolling_mean_value=2):
    import matplotlib.cm as cm
    # Sort the dataframe by the date column
    df = df.sort_values(by=x_column)

    # Calculate rolling mean for each y_column
    if rolling_mean_value:
        df[y_columns] = df[y_columns].rolling(len(df) // rolling_mean_value).mean()

    # Create the plot
    fig, ax = plt.subplots(figsize=figsize)

    colors = cm.Oranges(np.linspace(0.2, 1, len(y_columns)))

    # Plot each y_column as a separate line with a different color
    for i, y_column in enumerate(y_columns):
        df.plot(x=x_column, y=y_column, ax=ax, color=colors[i], label=y_column, linewidth=.5)

    # Rotate x-axis labels
    ax.set_xticklabels(ax.get_xticklabels(), rotation=30, ha='right')

    # Format x_column as date if it is
    if np.issubdtype(df[x_column].dtype, np.datetime64) or np.issubdtype(df[x_column].dtype, np.timedelta64):
        df[x_column] = pd.to_datetime(df[x_column]).dt.date

    # Set title, labels, and legend
    ax.set_title(title or f'{", ".join(y_columns)} over {x_column}', color=color, fontweight='bold')
    ax.set_xlabel(x_column, color=color)
    ax.set_ylabel(', '.join(y_columns), color=color)
    ax.spines['bottom'].set_color('orange')
    ax.spines['top'].set_color('orange')
    ax.spines['right'].set_color('orange')
    ax.spines['left'].set_color('orange')
    ax.xaxis.label.set_color('orange')
    ax.yaxis.label.set_color('orange')
    ax.tick_params(axis='x', colors='orange')
    ax.tick_params(axis='y', colors='orange')
    ax.title.set_color('orange')

    ax.legend(loc='upper right', bbox_to_anchor=(1, 1), facecolor='black', framealpha=.4, labelcolor='orange', edgecolor='orange')

    # Remove background
    fig.patch.set_alpha(0)
    ax.patch.set_alpha(0)

    return fig

def plot_bar(df, x_column, y_column, figsize=(12, 10), color='orange', title=None):
    fig, ax = plt.subplots(figsize=figsize)

    sns.barplot(data=df, x=x_column, y=y_column, color=color, ax=ax)

    ax.set_title(title if title else f'{y_column} by {x_column}', color=color, fontweight='bold')
    ax.set_xlabel(x_column, color=color)
    ax.set_ylabel(y_column, color=color)

    ax.tick_params(axis='x', colors=color)
    ax.tick_params(axis='y', colors=color)

    # Remove background
    fig.patch.set_alpha(0)
    ax.patch.set_alpha(0)
    ax.spines['bottom'].set_color('orange')
    ax.spines['top'].set_color('orange')
    ax.spines['right'].set_color('orange')
    ax.spines['left'].set_color('orange')
    ax.xaxis.label.set_color('orange')
    ax.yaxis.label.set_color('orange')
    ax.tick_params(axis='x', colors='orange')
    ax.tick_params(axis='y', colors='orange')
    ax.title.set_color('orange')
    ax.legend(loc='upper right', bbox_to_anchor=(1, 1), facecolor='black', framealpha=.4, labelcolor='orange', edgecolor='orange')

    return fig

def plot_grouped_bar(df, x_columns, y_column, figsize=(12, 10), colors=None, title=None):
    fig, ax = plt.subplots(figsize=figsize)

    width = 0.8 / len(x_columns)  # the width of the bars
    x = np.arange(len(df))  # the label locations

    for i, x_column in enumerate(x_columns):
        sns.barplot(data=df, x=x, y=y_column, color=colors[i] if colors else None, ax=ax, width=width, label=x_column)
        x += width  # add the width of the bar to the x position for the next bar

    ax.set_title(title if title else f'{y_column} by {", ".join(x_columns)}', color='orange', fontweight='bold')
    ax.set_xlabel('Groups', color='orange')
    ax.set_ylabel(y_column, color='orange')

    ax.set_xticks(x - width * len(x_columns) / 2)
    ax.set_xticklabels(df.index)

    ax.tick_params(axis='x', colors='orange')
    ax.tick_params(axis='y', colors='orange')

    # Remove background
    fig.patch.set_alpha(0)
    ax.patch.set_alpha(0)
    ax.spines['bottom'].set_color('orange')
    ax.spines['top'].set_color('orange')
    ax.spines['right'].set_color('orange')
    ax.spines['left'].set_color('orange')
    ax.xaxis.label.set_color('orange')
    ax.yaxis.label.set_color('orange')
    ax.title.set_color('orange')
    ax.legend(loc='upper right', bbox_to_anchor=(1, 1), facecolor='black', framealpha=.4, labelcolor='orange', edgecolor='orange')

    return fig

def generate_kepler_map(data):
    map_config = keplergl(data, height=400)
    return map_config

def filter_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds a UI on top of a dataframe to let viewers filter columns

    Args:
        df (pd.DataFrame): Original dataframe

    Returns:
        pd.DataFrame: Filtered dataframe
    """

    title_font = "Arial"
    body_font = "Arial"
    title_size = 32
    colors = ["red", "green", "blue"]
    interpretation = False
    extract_docx = False
    title = "My Chart"
    regex = ".*"
    img_path = 'default_image.png'

    df_ = df.copy()
    try:
        to_filter_columns = st.multiselect("Filter dataframe on", df_.columns)
    except:
        try:
            to_filter_columns = st.multiselect("Filter dataframe", df_.columns)
        except:
            try:
                to_filter_columns = st.multiselect("Filter the dataframe on", df_.columns)
            except:
                pass

    date_column = None
    filtered_columns = []

    for column in to_filter_columns:
        left, right = st.columns((1, 20))
        # Treat columns with < 200 unique values as categorical if not date or numeric
        if is_categorical_dtype(df_[column]) or (df_[column].nunique() < 120 and not is_datetime64_any_dtype(df_[column]) and not is_numeric_dtype(df_[column])):
            user_cat_input = right.multiselect(
                f"Values for {column}",
                df_[column].value_counts().index.tolist(),
                default=list(df_[column].value_counts().index)
            )
            df_ = df_[df_[column].isin(user_cat_input)]
            filtered_columns.append(column)

            with st.status(f"Category Distribution: {column}", expanded=False) as stat:
                st.pyplot(plot_treemap(df_, column))

        elif is_numeric_dtype(df_[column]):
            _min = float(df_[column].min())
            _max = float(df_[column].max())
            step = (_max - _min) / 100
            user_num_input = right.slider(
                f"Values for {column}",
                min_value=_min,
                max_value=_max,
                value=(_min, _max),
                step=step,
            )
            df_ = df_[df_[column].between(*user_num_input)]
            filtered_columns.append(column)

            # Chart_GPT = ChartGPT(df_, title_font, body_font, title_size,
            #      colors, interpretation, extract_docx, img_path)

            with st.status(f"Numerical Distribution: {column}", expanded=False) as stat_:
                st.pyplot(plot_hist(df_, column, bins=int(round(len(df_[column].unique())-1)/2)))

        elif is_object_dtype(df_[column]):
            try:
                df_[column] = pd.to_datetime(df_[column], infer_datetime_format=True, errors='coerce')
            except Exception:
                try:
                    df_[column] = df_[column].apply(parser.parse)
                except Exception:
                    pass

            if is_datetime64_any_dtype(df_[column]):
                df_[column] = df_[column].dt.tz_localize(None)
                min_date = df_[column].min().date()
                max_date = df_[column].max().date()
                user_date_input = right.date_input(
                    f"Values for {column}",
                    value=(min_date, max_date),
                    min_value=min_date,
                    max_value=max_date,
                )
                # if len(user_date_input) == 2:
                #     start_date, end_date = user_date_input
                #     df_ = df_.loc[df_[column].dt.date.between(start_date, end_date)]
                if len(user_date_input) == 2:
                    user_date_input = tuple(map(pd.to_datetime, user_date_input))
                    start_date, end_date = user_date_input
                    df_ = df_.loc[df_[column].between(start_date, end_date)]

                date_column = column

                if date_column and filtered_columns:
                    numeric_columns = [col for col in filtered_columns if is_numeric_dtype(df_[col])]
                    if numeric_columns:
                        fig = plot_line(df_, date_column, numeric_columns)
                        #st.pyplot(fig)
                    # now to deal with categorical columns
                    categorical_columns = [col for col in filtered_columns if is_categorical_dtype(df_[col])]
                    if categorical_columns:
                        fig2 = plot_bar(df_, date_column, categorical_columns[0])
                        #st.pyplot(fig2)
                    with st.status(f"Date Distribution: {column}", expanded=False) as stat:
                        try:
                            st.pyplot(fig)
                        except Exception as e:
                            st.error(f"Error plotting line chart: {e}")
                            pass
                        try:
                            st.pyplot(fig2)
                        except Exception as e:
                            st.error(f"Error plotting bar chart: {e}")


        else:
            user_text_input = right.text_input(
                f"Substring or regex in {column}",
            )
            if user_text_input:
                df_ = df_[df_[column].astype(str).str.contains(user_text_input)]
    # write len of df after filtering with % of original
    st.write(f"{len(df_)} rows ({len(df_) / len(df) * 100:.2f}%)")
    return df_

def color_risk(val):
    if val == 5:
        color = 'purple'
    elif val == 4:
        color = 'red'
    elif val == 3:
        color = 'orange'
    elif val == 2:
        color = 'yellow'
    elif val == 1:
        color = 'green'
    else:
        # leave blank
        color = 'white'

my_dataset = responses_to_df(ref.get(), 'victim_data')


risk_map = {
    'critical': 4,
    'very_urgent': 3,
    'urgent' : 2,
    'stable' : 1,
    'unknown' : 0,
}

# add to json
my_dataset['risk_nb'] = my_dataset['emergency_status'].map(risk_map)
# default to 0
my_dataset['risk_nb'] = my_dataset['risk_nb'].fillna(0)
# add a widget select



map_1 = KeplerGl(height=800)

rescue = pd.read_csv('datasets/sf_rescue_dep.csv')
synth_data = pd.read_csv('datasets/health_check_descriptions.csv')

map_1.add_data(
            data=rescue, name="rescue_departments"
        )

map_1.add_data(
    data=synth_data, name='synth_victims'
)


if my_dataset is not None :
    parser = filter_dataframe(my_dataset)
    
    st.session_state['parsed_responses'] = parser
    my_dataset.style.applymap(color_risk, subset=['risk_nb'])
    st.dataframe(my_dataset)
    #st.success(f"Successfully loaded and displayed data from {my_dataset.name}")
    st.session_state['data_loaded'] = True
    # Load the base config
    with open('configs/rescue_conf.kgl', 'r') as f:
        base_config = json.load(f)

    with open('configs/victims_config.kgl', 'r') as f:
        victims_config = json.load(f)

    if parser.columns.str.contains('date').any():
        # Get the date column name
        date_column = parser.columns[parser.columns.str.contains('date')].values[0]

        # Create a new filter
        new_filter = {
            "dataId": "victims_config",
            "name": date_column
        }

        # Append the new filter to the existing filters
        base_config['config']['visState']['filters'].append(new_filter)

        # Update the map config
        map_1.config = base_config

    map_1.add_data(
        data=parser, name="victims_config"
        )
    
    base_config['config']['visState']['layers'].extend([layer for layer in victims_config['config']['visState']['layers']])

    map_1.config = base_config
    
    keplergl_static(map_1, center_map=True)
    st.session_state['map_generated'] = True