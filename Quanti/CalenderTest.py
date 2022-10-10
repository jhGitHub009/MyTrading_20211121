import calendar
import datetime
from workalendar.asia import south_korea
def GetNearWorkingDayDate(_thisday):
    if type(_thisday)==str:
        _thisday = datetime.datetime.strptime(_thisday,'%Y-%m-%d')
    cal = south_korea.SouthKorea()
    while not cal.is_working_day(_thisday):
        _thisday = _thisday + datetime.timedelta(days=-1)
    return _thisday
if __name__ == "__main__":
    # today = datetime.datetime.today() - datetime.timedelta(days=1)
    today='2018-11-04'
    GetNearWorkingDayDate(today)
    print()