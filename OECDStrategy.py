from Backtesting.Backtesting import Strategy
import pandas as pd
import datetime

class OECDTest(Strategy):
    def __init__(self):
        self.oecdURL = ''
        self.location = ''
        self.oecdDate = None

        self.locations = ''
        self.oecdDate = None
    def CheckStrategy(self):
        # read OECDData
        dfOECD = pd.read_csv(self.oecdURL, encoding='cp949')
        # Date, Loc
        dfOECD = dfOECD[dfOECD['LOCATION'] == self.location]  # 나라 데이터 sorting
        # PCTchange
        dfOECD['ValueDiffPCT'] = dfOECD['Value'].pct_change() * 100  # 차이 percentage.
        # check Data.
        if dfOECD.loc[dfOECD['Time'] == self.oecdDate,'Value'] > 0:
            return True
        else:
            return False
    def GetDateForTrade(self):
        # read file
        # get date
        # read file
        # get date
        # extract duplicated date
        pass
    def CheckDateForTrade(self):
        return True
    def CalcRebalancing(self):
        pass
    # For this class
