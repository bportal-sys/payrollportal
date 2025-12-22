import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import date, time, datetime, timedelta

    
class Shift:
    def __init__(self, day, time_in, time_out, time_format_12 = True):
        if not isinstance(day, date):
            raise TypeError('Day must be a datetime.date object')
        self.day = day 

        if isinstance(time_in, str):
            fmt = '%I:%M %p' if time_format_12 else '%H:%M'
            self.time_in = datetime.strptime(time_in.strip(), fmt).time()
        elif isinstance(time_in, time):
            self.time_in = time_in
        else:
            raise TypeError('time_in must be a datetime.time or str')

        if isinstance(time_out, str):
            fmt = '%I:%M %p' if time_format_12 else '%H:%M'
            self.time_out = datetime.strptime(time_out.strip(), fmt).time()
        elif isinstance(time_out, time):
            self.time_out = time_out
        else:
            raise TypeError('time_out must be a datetime.time or str')

        dt_in = datetime.combine(day, self.time_in)
        dt_out = datetime.combine(day, self.time_out)
        if dt_out <= dt_in:
            dt_out += timedelta(days=1)

        max_shift = 24
        hours = (dt_out - dt_in).total_seconds()/3600
        if hours > max_shift:
            raise ValueError('Shift can\' exceed max shift of {max_shift} hours')
        
    def __repr__(self):
        return f'Shift(day={self.day}, time_in={self.time_in.strftime('%H:%M')}, time_out={self.time_out.strftime('%H:%M')})'

    def to_dict(self):
        return {
            'day' : self.day.isoformat(),
            'time_in' : self.time_in.strftime('%H:%M'),
            'time_out' : self.time_out.strftime('%H:%M')
        }

class Timesheet:
    def __init__(self):
        self.shifts = []
    
    def add_shift(self, shift):
        if any(s.day == shift.day for s in self.shifts):
            raise ValueError(f'A shift for {shift.day} already exists')
        self.shifts.append(shift)

    def edit_shift(self, index, new_shift):
        if not (0 <= index < len(self.shifts)):
            raise IndexError(f'Shift index out of range')
        self.shifts[index] = new_shift
    
    def remove_shift(self, index):
        if not (0 <= index < len(self.shifts)):
            raise IndexError(f'Shift index out of range')
        del self.shifts[index]

    def list_shifts(self):
        shift_strings = []
        for i, s in enumerate(self.shifts):
            shift_strings.append(f'{i}: {s.day} {s.time_in.strftime('%H:%M %p')} - {s.time_out.strftime('%H;%M %p')}\n')
        return "\n".join(shift_strings)

    def to_dataframe(self):
        return pd.DataFrame([s.to_dict() for s in self.shifts])

    def save_csv(self, filename):
        self.to_dataframe().to_csv(filename, index=False)
        print(f'Saved file to {filename}')

    def load_csv(self, filename):
        df = pd.read_csv(filename)
        for _, row in df.iterrows():
            self.add_shift(
                Shift(
                    day=pd.to_datetime(row['day']).date(),
                    time_in = pd.to_datetime(row['time_in']).time(),
                    time_out = pd.to_datetime(row['time_out']).time()
                    )
            )
        return self


class WorkSche:
    def __init__(self):
        self.df = None
        self.wage = None 
        self.tips = None
        self.converted_df = None
        self.total_hours = None
        self.money = None
        self.wage_money = None

    def convert(self):
        '''
        Takes a df assuming it has columns day, in, out and formats them to a correctly formatted df for other functions
        '''
        df = self.df.copy()
        df['date'] = pd.to_datetime(df.day)
        df['timein'] = pd.to_datetime(df['day'].astype(str)+' '+df['time_in'].astype(str), format='mixed')
        df['timeout'] = pd.to_datetime(df['day'].astype(str)+' '+df['time_out'].astype(str), format='mixed')
        df.loc[df['timeout'] <= df['timein'], 'timeout'] += pd.Timedelta(days=1)
        df['time_diff'] = df.timeout - df.timein
        df = df.drop(['day', 'time_in', 'time_out'], axis=1)
        self.converted_df = df
        return df
        
    def calculatehours(self):
        '''
        Calculates the number of hours from the diff column of the dataframe, Pass in a df returnds total hours. 
        '''
        if self.converted_df is None: 
            raise ValueError(f'DataFrame {self.df} must be converted first.')
        df = self.converted_df.copy()

        delta = df['time_diff'].sum()
        totalhours = delta.total_seconds()/3600
        self.total_hours = totalhours
        return totalhours

    def get_dollars(self):
        if self.wage == 0: 
            raise ValueError(f'Wage is 0, Why are you working for free? More importantly and quite frankly attention worthy, why are you running this program?')
        wage = self.wage
        if self.tips < 0:
            raise ValueError(f'You can\'t input negative tips')
        tips = self.tips
        if self.total_hours is None: 
            raise ValueError(f'Calculate hours before running.')
        total_hours = self.total_hours
        wmoney = (total_hours * wage)
        tmoney = (total_hours * wage) + tips
        self.money = tmoney
        self.wage_money = wmoney
        return tmoney, wmoney

    def plot_hrs(self):
        if self.converted_df is None:
            raise ValueError(f'Run the calculation first.')
        df = self.converted_df
        fig, ax = plt.subplots(figsize=(6,4))
        hours = df['time_diff'].dt.total_seconds()/3600
        ax.bar(df['date'], hours)

        n = len(df['date'])
        if n <= 10:
            ax.set_xticks(df['date'])
        elif n <= 15:
            ax.set_xticks(df['date'][::2])
        elif n <= 30:
            ax.set_xticks(df['date'][::3])
        elif n <= 50:
            ax.set_xticks(df['date'][::5])
            ax.xaxis.set_major_locator(mdates.AutoDateLocator())   
        elif n <= 100:
            ax.set_xticks(df['date'][::10])
            ax.xaxis.set_major_locator(mdates.AutoDateLocator())                                         
        
        
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.tick_params(axis='x', labelsize=9)
        fig.autofmt_xdate()
        ax.set_title('Daily hours worked')
        ax.set_xlabel('Date')
        ax.set_ylabel('Hours worked')
        return fig


    def calc(self, df, wage=10, tips=0):

        # Validation DF
        df = df.copy()
        required_cols = ['day','time_in','time_out']

        if not all(col in df.columns for col in required_cols):
            missing_cols = set(required_cols) - set(df.columns)
            raise ValueError(f'DataFrame provided is not valid. Missing column(s): {missing_cols}.')
        self.df = df
        self.wage = wage
        self.tips = tips

        # Logic
        self.convert()
        self.calculatehours()
        money = self.get_dollars()
        summary_df = pd.DataFrame([[f'{self.total_hours:.3f} hours, at a rate of ${self.wage}/hr. Earning ', self.wage_money],[f'Adding tips of ${self.tips}, In total you earned ', self.money]])

        return summary_df
    
def load_csv(sheet, filename):
    df = pd.read_csv(filename)

    df.columns = df.columns.str.strip().str.lower().str.replace(" ","")

    if "Unnamed: 0" in df.columns:
        df = df.drop(columns=['Unnamed: 0'])

    required_cols = {'day','time_in','time_out'}
    
    if not required_cols.issubset(df.columns):
        raise ValueError(f'CSV must contain columns: {required_cols} {df.columns}')

    skipped = 0

    for _, row in df.iterrows():
        shift = Shift(
            day=pd.to_datetime(row['day']).date(),
            time_in = pd.to_datetime(row['time_in']).time(),
            time_out = pd.to_datetime(row['time_out']).time()
            )

        try:
            sheet.add_shift(shift)
        except ValueError:
            skipped += 1

    return sheet, skipped