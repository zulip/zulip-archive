from datetime import datetime

# I don't love this format, feel free to change (I just
# extracted it from prior code).
def format_date1(ts):
    ''' Nov 05 2019 at 02:51'''
    return datetime.utcfromtimestamp(ts).strftime('%b %d %Y at %H:%M')
