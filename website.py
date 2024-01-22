import streamlit as st
import pandas as pd
import altair as alt
import plotly.graph_objects as go
import numpy as np

# Set custom Streamlit theme
st.set_page_config(
    page_title="Root Crops Data",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

def process_data(crop_file_path):
    df = pd.read_excel(crop_file_path)
    df.set_index(pd.Index(['Month', 'Day', 'Value']), inplace=True)
    df = df.T
    df.reset_index(inplace=True)
    df.rename(columns={'index': 'Year'}, inplace=True)
    df['Year'].replace(r'^Unnamed.*', pd.NA, regex=True, inplace=True)
    df['Year'].fillna(method='ffill', inplace=True)
    df['Month'].fillna(method='ffill', inplace=True)
    df['Day'] = df['Day'].astype(int)
    df['Date'] = df['Year'].astype(str) + ' ' + df['Month'].astype(str) + ' ' + df['Day'].astype(str)
    df['Date'] = pd.to_datetime(df['Date'], format='%Y %B %d')
    df.set_index('Date', inplace=True)
    df.drop(['Year', 'Month', 'Day'], axis=1, inplace=True)
    df = df.astype(float)

    df['Percentage Change'] = df['Value'].pct_change().fillna(0)
    df['Percentage Change'] = df['Percentage Change'].map('{:.2%}'.format) + ' ' + np.where(df['Percentage Change'] > 0, '↑', np.where(df['Percentage Change'] < 0, '↓', ''))

    return df

def display_line_chart(df, crop_name, selected_year):
    fig = go.Figure()

    if selected_year == 'All':
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['Value'],
            mode='lines',
            name='',
            hovertemplate="<b>Date:</b> %{x|%b %d, %Y}<br>"
                          "<b>Price:</b> ₱%{y:.2f}<br>"
                          "<b>Percentage Change:</b> %{customdata}<br>",
            customdata=df['Percentage Change'],
            hoverlabel_font_color=['green' if val > 0 else 'red' for val in df['Value'].pct_change()]
        ))
    else:
        df_selected_year = df[df.index.year == int(selected_year)]
        fig.add_trace(go.Scatter(
            x=df_selected_year.index,
            y=df_selected_year['Value'],
            mode='lines',
            name='',
            hovertemplate="<b>Date:</b> %{x|%b %d, %Y}<br>"
                          "<b>Price:</b> ₱%{y:.2f}<br>"
                          "<b>Percentage Change:</b> %{customdata}<br>",
            customdata=df_selected_year['Percentage Change'],
            hoverlabel_font_color=['green' if val > 0 else 'red' for val in df_selected_year['Value'].pct_change()]
        ))

    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Price",
        hoverlabel_font=dict(size=16),
        height=550,
        width=400,
        dragmode='pan',
    )

    st.plotly_chart(fig)

def apply_color_to_percentage_change(val):
    color = 'green' if '↑' in val else ('red' if '↓' in val else '')
    return f'color: {color}'

def create_gauge_meter(value, max_value, color, title):
    gauge_chart = alt.Chart(pd.DataFrame({'value': [value]})).mark_bar().encode(
        alt.X('value:Q', scale=alt.Scale(domain=(0, max_value))),
        color=alt.ColorValue(color),
        size=alt.value(20),
    ).properties(
        width=300,
        height=150,
        title=title
    )

    return gauge_chart

def main():
    st.markdown(
        f'<p style="font-size: 30px; color: #3498db;"><strong>Historical Data for Selected Root Crops in National Capital Region (NCR), Philippines</strong></p>',
        unsafe_allow_html=True
    )

    st.sidebar.title('Select Options')
    selected_crop = st.sidebar.selectbox('Select Commodity:', ['Carrot', 'Cassava', 'Gabi', 'Potato', 'Sweet Potato'])
    selected_year = st.sidebar.selectbox('Select a Year:', ['All'] + [str(year) for year in range(2012, 2024)])
    selected_interval = st.sidebar.selectbox('Select Forecasting Interval:', ['Monthly (12 months)', 'Weekly (10 weeks)'])

    if selected_crop in ['Carrot', 'Cassava', 'Gabi', 'Potato', 'Sweet Potato']:
        file_path = f'datasets/{selected_crop}.xlsx'
        df = process_data(file_path)

        # Display lowest and highest prices in separate columns
        lowest_price = df['Value'].min()
        highest_price = df['Value'].max()

        col1, col2 = st.columns(2)

        with col1:
            st.altair_chart(create_gauge_meter(lowest_price, df['Value'].max(), 'red', 'Lowest Price'))

        with col2:
            st.altair_chart(create_gauge_meter(highest_price, df['Value'].max(), 'green', 'Highest Price'))

        col1, col2 = st.columns(2)
        with col1:
            df_display = df.assign(
                **{'Price (per kg)': df['Value'].map('₱{:.2f}'.format)},
                **{'Percentage Change': df['Percentage Change']}
            )
            df_display.drop(columns=['Value'], inplace=True)
            df_display.index = df_display.index.strftime('%Y-%m-%d')
            df_display = df_display[['Price (per kg)', 'Percentage Change']]
            df_display_styled = df_display.style.applymap(apply_color_to_percentage_change, subset=['Percentage Change'])
            st.dataframe(df_display_styled, width=750, height=520)

        with col2:
            if 'df' in locals() and selected_crop in ['Carrot', 'Cassava', 'Gabi', 'Potato', 'Sweet Potato']:
                display_line_chart(df, selected_crop, selected_year)

    st.markdown(
        f'<p style="font-size: 30px; color: #3498db;"><strong>Forecasted Value</strong></p>',
        unsafe_allow_html=True
    )

    if selected_interval == 'Monthly (12 months)':
        monthly_sheet_path = f'datasets/{selected_crop}.xlsx'
        df_monthly = pd.read_excel(monthly_sheet_path, sheet_name='monthly')
        df_monthly['Date'] = pd.to_datetime(df_monthly['Date']).dt.strftime('%Y-%m-%d')
        df_monthly.set_index('Date', inplace=True)
        df_monthly['Percentage Change'] = df_monthly['Price(per kg)'].pct_change().fillna(0)
        df_monthly['Percentage Change'] = df_monthly['Percentage Change'].map('{:.2%}'.format) + ' ' + np.where(df_monthly['Percentage Change'] > 0, '↑', np.where(df_monthly['Percentage Change'] < 0, '↓', ''))

        df_monthly_filtered = df_monthly[df_monthly.index != '2023-07-01']

        col1, col2 = st.columns(2)
        with col1:
            df_monthly_styled = df_monthly_filtered.style.format({'Price(per kg)': '₱{:.2f}', 'Percentage Change': '{}'}).applymap(
                lambda val: 'color: green' if '↑' in val else ('color: red' if '↓' in val else ''),
                subset=['Percentage Change']
            )
            st.table(df_monthly_styled)
        with col2:
            fig_monthly = go.Figure()
            fig_monthly.add_trace(go.Scatter(
                x=df_monthly_filtered.index,
                y=df_monthly_filtered['Price(per kg)'],
                mode='lines+markers',
                name='',
                hovertemplate="<b>Date:</b> %{x|%Y-%m-%d}<br>"
                              "<b>Price:</b> ₱%{y:.2f}<br>"
                              "<b>Percentage Change:</b> %{customdata}<br>",
                customdata=df_monthly_filtered['Percentage Change'],
                hoverlabel_font_color=['green' if val > 0 else 'red' for val in df_monthly_filtered['Price(per kg)'].pct_change()]
            ))
            fig_monthly.update_layout(
                xaxis_title="Date",
                yaxis_title="Price",
                hoverlabel_font=dict(size=16),
                height=550,
                width=400,
                dragmode='pan'
            )
            st.plotly_chart(fig_monthly)

    elif selected_interval == 'Weekly (10 weeks)':
        weekly_sheet_path = f'datasets/{selected_crop}.xlsx'
        df_weekly = pd.read_excel(weekly_sheet_path, sheet_name='weekly')
        df_weekly['Date'] = pd.to_datetime(df_weekly['Date']).dt.strftime('%Y-%m-%d')
        df_weekly.set_index('Date', inplace=True)
        df_weekly['Percentage Change'] = df_weekly['Price(per kg)'].pct_change().fillna(0)
        df_weekly['Percentage Change'] = df_weekly['Percentage Change'].map('{:.2%}'.format) + ' ' + np.where(df_weekly['Percentage Change'] > 0, '↑', np.where(df_weekly['Percentage Change'] < 0, '↓', ''))

        # Exclude the row with the date '2023-07-25'
        df_weekly_filtered = df_weekly[df_weekly.index != '2023-07-25']

        col1, col2 = st.columns(2)
        with col1:
            df_weekly_styled = df_weekly_filtered.style.format({'Price(per kg)': '₱{:.2f}', 'Percentage Change': '{}'}).applymap(
                lambda val: 'color: green' if '↑' in val else ('color: red' if '↓' in val else ''),
                subset=['Percentage Change']
            )
            st.table(df_weekly_styled)
        with col2:
            fig_weekly = go.Figure()
            fig_weekly.add_trace(go.Scatter(
                x=df_weekly_filtered.index,
                y=df_weekly_filtered['Price(per kg)'],
                mode='lines+markers',
                name='',
                hovertemplate="<b>Date:</b> %{x|%Y-%m-%d}<br>"
                              "<b>Price:</b> ₱%{y:.2f}<br>"
                              "<b>Percentage Change:</b> %{customdata}<br>",
                customdata=df_weekly_filtered['Percentage Change'],
                hoverlabel_font_color=['green' if val > 0 else 'red' for val in df_weekly_filtered['Price(per kg)'].pct_change()]
            ))
            fig_weekly.update_layout(
                xaxis_title="Date",
                yaxis_title="Price",
                hoverlabel_font=dict(size=16),
                height=550,
                width=400,
                dragmode='pan'
            )
            st.plotly_chart(fig_weekly)

if __name__ == '__main__':
    main()
