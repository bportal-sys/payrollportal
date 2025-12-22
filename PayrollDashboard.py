# imports 

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import date, time, datetime, timedelta
from timesheet import *
import io
import time

# session state
if 'ts' not in st.session_state:
    st.session_state.ts = Timesheet()

ts = st.session_state.ts


# main body
st.title(':dollar: Payroll Calculator')
st.header('Calculate your payroll expense and/or your take home pay')
st.write('''
             1: Add shifts manually or load CSVs of data from the corresponding tabs \n
             2: If you made a mistake, edit or remove those shifts in the Edit Shift(s) tab \n
             3: Open the sidebar to edit your hourly wage and/or any tips you'd like to count \n
             4: Enter an employee's name (used in the exporting) and download your data from the Load Data tab \n
             5: See how much you made for the hours you worked (Woohoo button for your dopamine)
             ''')
st.divider()

# sidebar
st.sidebar.header('Key Assumptions')
wage = st.sidebar.number_input('Wage per hour', min_value=0, max_value=1000, value=20)
tips = st.sidebar.number_input('Tips',min_value=0, max_value=1000, value=0)
st.sidebar.space(100)
empid = st.sidebar.text_input('Employee Name', value='Bob')

# tab config
tab1, tab2, tab3 = st.tabs(['Add Shift(s)', 'Edit Shift(s)', 'Load Data'])
if tab1.button('Clear all shifts'):
    st.session_state.ts = Timesheet()
    tab1.success('All shifts cleared')
    st.rerun()
    

# tab1, Add shifts
with tab1.form('add_shift_form'):
    day = st.date_input('Day')
    time_in = st.time_input('Time In', value='09:00')
    time_out = st.time_input('Time Out', value='17:00')
    submitted = st.form_submit_button("Add shift")
    if submitted:
        try:
            ss = Shift(day, time_in, time_out, time_format_12=False)
            ts.add_shift(ss)
            # tsdf = ts.to_dataframe()
            tab1.success('Saved shift to dataframe')
        except ValueError as e:
            st.error(str(e))

# create df
tsdf = ts.to_dataframe()
# st.dataframe(tsdf)

if tsdf is None or tsdf.empty:
    tab2.write('Theres no data to edit, switch tabs to add data!')

# tab2, edit
tab2.subheader('Edit a shift')
if ts.shifts:
    options = [f'{i}: {s}' for i, s in enumerate(ts.shifts)]
    selected = tab2.selectbox("Select shift", options,key='edit_shift_select')
    index = int(selected.split(':')[0])
    shift = ts.shifts[index]
    
    with tab2.form('edit_shift_form'):
        new_day = st.date_input('Day', value=shift.day)
        new_time_in = st.time_input('Time In', value=shift.time_in)
        new_time_out = st.time_input('Time Out', value=shift.time_out)
        submitted = st.form_submit_button("Save changes")
        if submitted:
            if any(i != index and s.day == new_day for i, s in enumerate(ts.shifts)):
                st.error('Another shift already exists for that date')
            else:
                ts.shifts[index].day = new_day
                ts.shifts[index].time_in = new_time_in
                ts.shifts[index].time_out = new_time_out
                st.success('Saved edited shift to dataframe')
                tsdf = ts.to_dataframe()
                time.sleep(1)
                st.rerun()

tab2.divider()

# tab2, remove
tab2.subheader('Remove a shift')
if ts.shifts:
    options = [f'{i}: {s}' for i, s in enumerate(ts.shifts)]
    selected = tab2.selectbox("Select shift", options, key='remove_shift_select')
    index = int(selected.split(':')[0])
    shift = ts.shifts[index]
    
    with tab2.form('remove_shift_form'):
        submitted = st.form_submit_button("Delete Shift")
        if submitted:
                ts.remove_shift(index)
                st.success('Removed shift to dataframe')
                tsdf = ts.to_dataframe()
                time.sleep(1)
                st.rerun()

# tab3 upload csv
uploadedfile = tab3.file_uploader('Upload timesheet CSV', type='csv')
if tab3.button('Upload CSV'):
    if uploadedfile is not None:
        try: 
            st.session_state.ts, skipped = load_csv(
                st.session_state.ts, uploadedfile
        )
            
            tab3.success('CSV uploaded successfully!')
            if skipped: 
                tab3.warning(f'{skipped} duplicate day(s) were skipped.')
            
            time.sleep(1)
            st.rerun()
            

        except Exception as e:
            tab3.error(str(e))



# main display
if tsdf is not None and not tsdf.empty: 
    st.divider()
    st.dataframe(tsdf)
    ws = WorkSche()
    st.divider()
    summary = ws.calc(tsdf, wage, tips)
    st.write(summary)
    st.pyplot(ws.plot_hrs())
    st.divider()
    st.header(f'From above you earned $ {summary[1][1]}')
    csv_buffer = io.StringIO()
    tsdf[['day','time_in','time_out']].to_csv(csv_buffer, index=False)
    csv_data = csv_buffer.getvalue()


    tab3.download_button(
        label = 'Download Timesheet as CSV',
        data = csv_data,
        file_name = f'timesheet_{empid}_{pd.Timestamp.today().strftime('%Y%m%d')}.csv'
    )

# woohoo ( most important feature )
st.space()
st.divider()
if st.button('Woohoo :tada:'):
    st.balloons()

