from jinja2.filters import FILTERS as jinja_filter

MINUTES = 60
HOUR = MINUTES*60
DAY = HOUR*24
YEAR = DAY*365

def date_format(timezone_date,format="short"):
    formated = ""
    if ( format == "short" ):
        formated = timezone_date.strftime("%d/%m/%y")
    else:
        formated = timezone_date.strftime("%d/%m/%y %H:%M")
    return formated
def delta_time(delta_time):
    final_string = ""
    time_total = delta_time.days*DAY+delta_time.seconds
    years,rest = divmod(delta_time.seconds,YEAR)
    if( years ):
        final_string+= ("%d anos, "% years)
    days,rest = divmod(rest,DAY)
    if (days):
        final_string+=("%d dias, "% days)
    hour,rest = divmod(rest,HOUR)
    minutes,seconds = divmod(rest,MINUTES)
    final_string+="%02d:%02d:%02d:%04d" % (hour,minutes,seconds,delta_time.microseconds)
    return final_string
def filters():
    jinja_filter['dateformat'] = date_format
    jinja_filter['deltaformat'] = delta_time


