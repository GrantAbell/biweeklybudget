import settings
import pandas as pd
from pandas.tseries.offsets import DateOffset
import numpy as np
from fuzzywuzzy import fuzz
#from fuzzywuzzy import process
#import uuid
import hashlib
from tqdm import tqdm
#from datetime import datetime



def description_ratio(desc1, desc2):
    return fuzz.token_set_ratio(desc1, desc2)

# How can these transactions be sorted into their own periods besides manually filtering the months? This would resolve bills that occur on the 1st and 31st of the month occasionally- resulting in duplicates in one month.
# Create fingerprint?
def find_repeating_transactions(data):
    columns = {}
    data['date'] = pd.to_datetime(data['date'], format='mixed')
    data['Repeating'] = False
    column_index = 0
    columns['index'] = column_index
    column_index += 1
    for i in data.columns:  # This Loop creates a mapping for the columns so we can iterate through the DataFrame with the 'itertuples()' method without sacrificing descriptive code, since this is quicker than 'itterrows()'.
        columns[i] = column_index
        column_index += 1
    for row in tqdm(data[list(columns.keys())[1:]].sort_values(by='date', ascending=True).itertuples(), total=data.shape[0]):
        if row[columns['Repeating']] is False:
            current_date = row[columns['date']]
            current_amount = row[columns['amount']]
            current_name = row[columns['name']]
            if settings.PAYROLL_STRING in current_name.split(" "):
                data.loc[row[columns['index']], 'Repeating'] = True  # Marks transaction as repeating automatically if description contains 'settings.PAYROLL_STRING'.
            else:
                amount_condition_range = ((data['amount'] >= current_amount - 50) & \
                                        (data['amount'] <= current_amount + 50))
                amount_condition_same = ((data['amount'] >= current_amount - .01) & \
                                        (data['amount'] <= current_amount + .01))
                # Check for transactions occurring 25-35 days later or sooner 
                two_month_range = ((data['date'] >= current_date + DateOffset(days=27)) & \
                    (data['date'] <= current_date + DateOffset(days=33))) | \
                    ((data['date'] <= current_date - DateOffset(days=27)) & \
                    (data['date'] >= current_date - DateOffset(days=33)))
                    
                if current_amount > 500:
                    other_transactions = data[two_month_range & amount_condition_range].copy()
                else:
                    other_transactions = data[two_month_range & amount_condition_same].copy()
                if (other_transactions.shape[0] >= 1):
                    other_transactions.loc[:,'Name Ratio'] = other_transactions['name'].map(lambda x: description_ratio(x, current_name))

                    # If transaction match from adjacent month does not occur both before and after, a function is used to check the similarity of names
                    other_transactions = other_transactions[other_transactions['Name Ratio'] > 50]


                    # Check for transactions occurring within the same 3-day period
                    if other_transactions.shape[0] >= 1:
                        same_period_amount_condition = (data['amount'] == current_amount)
                        repeating_transactions = data[(data['date'] >= current_date - DateOffset(days=2)) &
                                                    (data['date'] <= current_date + DateOffset(days=2)) &
                                                    same_period_amount_condition &
                                                    (data['name'] == current_name)].copy()
                        # Find the most recent transaction from repeating_transactions

                        most_recent_same_period = repeating_transactions[
                            (repeating_transactions['date'] == repeating_transactions['date'].min())].drop_duplicates(subset=['amount'])
                        # Include the current row and most recent same_period transaction in
                        # the results
                        repeating_indices = most_recent_same_period.index.tolist()
                        
                        
                        # Mark the selected rows as repeating
                        data.loc[repeating_indices, 'Repeating'] = True
    return data[data['Repeating']].copy()


from sqlalchemy import create_engine

engine = create_engine(settings.DB_CONNSTRING)
conn = engine.connect().connection
sql = "select name, amount, date_posted as 'date' from ofx_trans;"
transactions = pd.read_sql(sql, conn).sort_values(by=['amount'])
transactions.loc[:, 'name'] = transactions['name'].str.lower()
transactions.loc[:, 'name'] = transactions['name'].map(lambda x: x.replace('point of sale', ''))
transactions.loc[:, 'name'] = transactions['name'].map(lambda x: x.replace('withdrawal', ''))
transactions.loc[:, 'name'] = transactions['name'].map(lambda x: x.replace('external', ''))
transactions.loc[:, 'name'] = transactions['name'].str.strip()
#old = pd.read_csv('exports/Transactions from Plaid.csv')
#new = pd.concat((old, transactions))
transactions.to_csv("exports/Transactions from Plaid.csv", index=False)
#transactions['Description'] = transactions['Description'].str.lower()
monthy_transactions = find_repeating_transactions(transactions)
monthy_transactions['date'] = pd.to_datetime(monthy_transactions['date'])
monthy_transactions.loc[:, 'Day of Month'] = monthy_transactions['date'].map(lambda x: x.day)

bills = monthy_transactions[monthy_transactions['amount'] > 0]

monthy_transactions.to_csv('exports/monthly_transactions.csv', index=False)
bills.to_csv('exports/bills.csv', index=False)
