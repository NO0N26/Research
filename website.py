import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# Function to load and process data for any crop
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

    # Add Percentage Change with arrows
    df['Percentage Change'] = df['Value'].pct_change().fillna(0)
    df['Percentage Change'] = df['Percentage Change'].map('{:.2%}'.format) + ' ' + np.where(df['Percentage Change'] > 0, '↑', np.where(df['Percentage Change'] < 0, '↓', ''))

    return df

# Function to display line chart based on selected crop
def display_line_chart(df, crop_name, selected_year):
    fig = go.Figure()

    if selected_year == 'All':
        # Line chart for all years
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
        # Line chart for a specific year
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

    # Update layout to add axis labels
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Price",
        hoverlabel_font=dict(size=16),
        height=550,  # Adjust the height as needed
        width=400,    # Adjust the width as needed
        dragmode='pan',  # Enable dragging
    )

    st.plotly_chart(fig)

# Function to apply color to Percentage Change column
def apply_color_to_percentage_change(val):
    color = 'green' if '↑' in val else ('red' if '↓' in val else '')
    return f'color: {color}'

# Main function
def main():
    st.markdown(
        f'<p style="font-size: 30px; color: black;"><strong>Historical Data for Selected Root Crops in National Capital Region (NCR), Philippines</strong></p>',
        unsafe_allow_html=True
    )

    # Create two columns
    col1, col2 = st.columns(2)

    # In the first column, display the DataFrame
    with col1:
        st.markdown('<div class="custom-selectbox1">', unsafe_allow_html=True)
        selected_crop = st.selectbox('Select Commodity:', ['Carrot', 'Cassava', 'Gabi', 'Potato', 'Sweet Potato'])
        st.markdown('</div>', unsafe_allow_html=True)

        # Additional code based on selected_crop
        if selected_crop in ['Carrot', 'Cassava', 'Gabi', 'Potato', 'Sweet Potato']:
            file_path = f'datasets/{selected_crop}.xlsx'

            df = process_data(file_path)

            # Display DataFrame with additional columns and modified headers
            st.markdown('<br>', unsafe_allow_html=True)
            st.markdown('<br>', unsafe_allow_html=True)
            st.markdown('<br>', unsafe_allow_html=True)
            st.markdown('<br>', unsafe_allow_html=True)
            df_display = df.assign(
                **{'Price (per kg)': df['Value'].map('₱{:.2f}'.format)},
                **{'Percentage Change': df['Percentage Change']}
            )

            # Drop the original 'Value' column
            df_display.drop(columns=['Value'], inplace=True)

            # Format the index without the time part
            df_display.index = df_display.index.strftime('%Y-%m-%d')

            # Reorder columns
            df_display = df_display[['Price (per kg)', 'Percentage Change']]

            # Apply color styling to Percentage Change column
            df_display_styled = df_display.style.applymap(apply_color_to_percentage_change, subset=['Percentage Change'])

            # Display the DataFrame with additional styling
            st.dataframe(df_display_styled, width=320, height=385)

    # In the second column, load and process data
    with col2:
        st.markdown('<div class="custom-selectbox2">', unsafe_allow_html=True)
        selected_year = st.selectbox('Select a Year:', ['All'] + [str(year) for year in range(2012, 2024)])
        st.markdown('</div>', unsafe_allow_html=True)

        # Additional code based on selected_crop and selected_year
        if 'df' in locals() and selected_crop in ['Carrot', 'Cassava', 'Gabi', 'Potato', 'Sweet Potato']:
            display_line_chart(df, selected_crop, selected_year)

    st.markdown(
        f'<p style="font-size: 30px; color: black;"><strong>Forecasted Value</strong></p>',
        unsafe_allow_html=True
    )

    st.markdown('<div class="custom-selectbox3">', unsafe_allow_html=True)
    selected_interval = st.selectbox('Select Forecasting Interval:', ['Monthly (12 months)', 'Weekly (10 weeks)'])
    st.markdown('</div>', unsafe_allow_html=True)

    # Additional code based on selected_interval
    if selected_interval == 'Monthly (12 months)':
        # Load the "monthly" sheet from the Excel file
        monthly_sheet_path = f'datasets/{selected_crop}.xlsx'
        df_monthly = pd.read_excel(monthly_sheet_path, sheet_name='monthly')

        # Reset index and format date without the time part
        df_monthly['Date'] = pd.to_datetime(df_monthly['Date']).dt.strftime('%Y-%m-%d')
        df_monthly.set_index('Date', inplace=True)

        # Calculate Percentage Change
        df_monthly['Percentage Change'] = df_monthly['Price(per kg)'].pct_change().fillna(0)
        df_monthly['Percentage Change'] = df_monthly['Percentage Change'].map('{:.2%}'.format) + ' ' + np.where(df_monthly['Percentage Change'] > 0, '↑', np.where(df_monthly['Percentage Change'] < 0, '↓', ''))

        # Create two columns for Monthly interval
        col1, col2 = st.columns(2)

        # Display the DataFrame in col1
        with col1:
            st.markdown('<br>', unsafe_allow_html=True)
            st.markdown('<br>', unsafe_allow_html=True)
            st.markdown('<br>', unsafe_allow_html=True)
            st.markdown('<br>', unsafe_allow_html=True)

            # Apply color styling to Percentage Change column
            df_monthly_styled = df_monthly.style.format({'Price(per kg)': '₱{:.2f}', 'Percentage Change': '{}'}).applymap(
                lambda val: 'color: green' if '↑' in val else ('color: red' if '↓' in val else ''),
                subset=['Percentage Change']
            )

            st.dataframe(df_monthly_styled, width=320, height=385)

        # Create a line chart for the monthly forecast in col2
        with col2:
            fig_monthly = go.Figure()

            fig_monthly.add_trace(go.Scatter(
                x=df_monthly.index,
                y=df_monthly['Price(per kg)'],
                mode='lines',
                name='',
                hovertemplate="<b>Date:</b> %{x|%Y-%m-%d}<br>"
                              "<b>Price:</b> ₱%{y:.2f}<br>"
                              "<b>Percentage Change:</b> %{customdata}<br>",
                customdata=df_monthly['Percentage Change'],
                hoverlabel_font_color=['green' if val > 0 else 'red' for val in df_monthly['Price(per kg)'].pct_change()]
            ))

            # Update layout to add axis labels
            fig_monthly.update_layout(
                xaxis_title="Date",
                yaxis_title="Price",
                hoverlabel_font=dict(size=16),
                height=550,  # Adjust the height as needed
                width=400    # Adjust the width as needed
            )

            st.plotly_chart(fig_monthly)

    elif selected_interval == 'Weekly (10 weeks)':
        # Load the "weekly" sheet from the Excel file
        weekly_sheet_path = f'datasets/{selected_crop}.xlsx'
        df_weekly = pd.read_excel(weekly_sheet_path, sheet_name='weekly')

        # Reset index and format date without the time part
        df_weekly['Date'] = pd.to_datetime(df_weekly['Date']).dt.strftime('%Y-%m-%d')
        df_weekly.set_index('Date', inplace=True)

        # Calculate Percentage Change
        df_weekly['Percentage Change'] = df_weekly['Price(per kg)'].pct_change().fillna(0)
        df_weekly['Percentage Change'] = df_weekly['Percentage Change'].map('{:.2%}'.format) + ' ' + np.where(df_weekly['Percentage Change'] > 0, '↑', np.where(df_weekly['Percentage Change'] < 0, '↓', ''))

        # Create two columns for Weekly interval
        col1, col2 = st.columns(2)

        # Display the DataFrame in col1
        with col1:
            st.markdown('<br>', unsafe_allow_html=True)
            st.markdown('<br>', unsafe_allow_html=True)
            st.markdown('<br>', unsafe_allow_html=True)
            st.markdown('<br>', unsafe_allow_html=True)
            
            # Apply color styling to Percentage Change column
            df_weekly_styled = df_weekly.style.format({'Price(per kg)': '₱{:.2f}', 'Percentage Change': '{}'}).applymap(
                lambda val: 'color: green' if '↑' in val else ('color: red' if '↓' in val else ''),
                subset=['Percentage Change']
            )

            st.dataframe(df_weekly_styled, width=320, height=385)

        # Create a line chart for the weekly forecast in col2
        with col2:
            fig_weekly = go.Figure()

            fig_weekly.add_trace(go.Scatter(
                x=df_weekly.index,
                y=df_weekly['Price(per kg)'],
                mode='lines',
                name='',
                hovertemplate="<b>Date:</b> %{x|%Y-%m-%d}<br>"
                              "<b>Price:</b> ₱%{y:.2f}<br>"
                              "<b>Percentage Change:</b> %{customdata}<br>",
                customdata=df_weekly['Percentage Change'],
                hoverlabel_font_color=['green' if val > 0 else 'red' for val in df_weekly['Price(per kg)'].pct_change()],
            ))

            
            # Update layout to add axis labels
            fig_weekly.update_layout(
                xaxis_title="Date",
                yaxis_title="Price",
                hoverlabel_font=dict(size=16),
                height=550,  # Adjust the height as needed
                width=400    # Adjust the width as needed
            )

            st.plotly_chart(fig_weekly)

if __name__ == '__main__':
    main()
