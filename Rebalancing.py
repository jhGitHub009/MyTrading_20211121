def Rebalancing3():
    pass
def Rebalancing(_totalValue,_priceList,_nowStockNum):
    oneValue = _totalValue/len(_priceList)
    diffStockNum = []
    targetStockNum = []
    for price,num in zip(_priceList,_nowStockNum):
        actualPrice = GetTradePrice(price, num, oneValue)
        # priceTax = price + (price*0.35/100)
        # targetNum = int(oneValue / priceTax)
        targetNum = int(oneValue / actualPrice)
        actualNum = targetNum - num
        diffStockNum.append(actualNum)
        targetStockNum.append(targetNum)
    return diffStockNum,targetStockNum
def Rebalancing2(_totalValue,_priceList,_nowStockNum,_nowPortfolio):
    # 가격을 조정
    emptyNum = len([portfolio for portfolio in _nowPortfolio if portfolio==0])
    oneBalance = (_totalValue - sum(_nowPortfolio))/emptyNum
    if oneBalance<0:
        return [0,0], _nowStockNum
    balance = []
    for portfolio in _nowPortfolio:
        if portfolio!=0:
            balance.append(portfolio)
        else:
            balance.append(oneBalance)
    diffStockNum = []
    targetStockNum = []
    for price, num, thisBal in zip(_priceList, _nowStockNum, balance):
        # check sell or buy
        # 현재 가치를 check
        actualPrice = GetTradePrice(price,num,thisBal)
        targetNum = int(thisBal / actualPrice)
        actualNum = targetNum - num
        diffStockNum.append(actualNum)
        targetStockNum.append(targetNum)
    return diffStockNum, targetStockNum
def Rebalancing5(_totalValue,_priceList,_nowStockNum,portfolioRatio):
    balances = [int(_totalValue*ratio/100) for ratio in portfolioRatio]
    diffStockNum = []
    targetStockNum = []
    for price, num, balance in zip(_priceList, _nowStockNum,balances):
        actualPrice = GetTradePrice(price, num, balance)
        targetNum = int(balance / actualPrice)
        actualNum = targetNum - num
        diffStockNum.append(actualNum)
        targetStockNum.append(targetNum)
    return diffStockNum, targetStockNum
def GetTradePrice(price,num,balance):
    if GetNowValue(0, [price], [num]) > balance:
        # sell
        actualPrice = price
    else:
        # buy
        actualPrice = price + (price * 0.35 / 100)
    return actualPrice
def TradeStock(_balance,_stockValues,_diffStockNums,tradeFee=0.35):
    for diffNum, price in zip(_diffStockNums, _stockValues):
        priceTax = price + (price * tradeFee / 100)
        if diffNum >= 0:
            _balance -= (priceTax * diffNum)
        else:
            _balance -= (price * diffNum)
    return _balance
def GetNowValue(_balance,_priceList,_nowStockNum):
    totalValue = sum([a * b for a, b in zip(_priceList, _nowStockNum)]) + _balance
    return totalValue