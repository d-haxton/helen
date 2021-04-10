import time
import bisect

class Exchange:
    orderSells = [] # list of orderID of sell orders in ascending order of price
    orderBuys = []
    SellPrices = [] # used to locate where to edit order
    BuyPrices = []
    orderId = 0
    fillId = 0
    orderMap = {} # Hashmap of all orders with orderId as key
    standingBuys = [] # list of standing buyings orders in ascending time
    
    msgs = []

    def __init__(self):
        pass

    def create_orderId(self):
        self.orderId += 1
        return (self.orderId)
    
    def new_fillId(self):
        self.fillId -= 1
        return (self.fillId)
    
    def orderCancel(self, order_id):
        if len(self.orderMap) > 0 and order_id in self.orderMap:
            order = self.orderMap[order_id]
            self.orderMap.pop(order_id)
            print(order.side == "buy")
            if order.side == "buy":
                price_loc = self.BuyPrices.index(order.price)
                order_loc = self.orderBuys[price_loc].index(order_id)
                self.orderBuys[price_loc].pop(order_loc)
                # remove price and the element in orderBuy if it become empty
                if len(self.orderBuys[price_loc]) == 0:
                    self.orderBuys.pop[price_loc]
                    self.BuyPrices.pop[price_loc]
                # Find where the order is and remove in standing buys
                self.standingBuys.pop(self.standingBuys.index(order_id))
                
            else: # order.side == "sell"
                price_loc = self.SellPrices.index(order.price)
                order_loc = self.SellPrices[price_loc].index(order_id)
                self.orderSellsprice_loc.pop[order_loc]
                # remove price and the element in orderBuy if it become empty
                if len(self.orderSells[price_loc]) == 0:
                    self.orderSells.pop[price_loc]
                    self.SellPrices.pop[price_loc]
            cancelStatus = "Order " + str(order_id) + " has been canceled."
        else:
            cancelStatus = "Order " + str(order_id) + " cannot be canceled."
        return(cancelStatus)

    def orderAdd(self, order):
        new_orderId = self.create_orderId()
        print("created order id is " + str(new_orderId))
        order = Order(order.trader, order.side, order.price, order.qty, new_orderId)
        
        if order.side == "buy":
            self.orderMap[order.orderId] = order
            self.standingBuys.append(order.orderId) # update standing order for buys
                
            # If price exist, add to the current index
            if order.price in self.BuyPrices:
                self.orderBuys[self.BuyPrices.index(order.price)].append(order.orderId)
            else: # new price
                price_ind = bisect.bisect(self.BuyPrices, order.price)
                self.BuyPrices.insert(price_ind, order.price)
                self.orderBuys.insert(price_ind, [order.orderId])
                    
        else: # order.side == "sell"
            self.orderMap[order.orderId] = order
            if order.price in self.SellPrices:
                self.orderSells[self.SellPrices.index(order.price)].append(order.orderId)
            else:
                price_ind = bisect.bisect(self.SellPrices, order.price)
                self.SellPrices.insert(price_ind, order.price)
                self.orderSells.insert(price_ind, [order.orderId])
        
        return(self.orderProcess(order))
          
    def makeTrade(self, buy_order, sell_order):
        fill_qty = min(buy_order.qty, sell_order.qty)
        buy_order.qty -= fill_qty
        sell_order.qty -= fill_qty
        fill_id = self.new_fillId()
        fill_timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(time.time()))
        fill_msg_buyer = fillMessage(buy_order.orderId, fill_id, fill_timestamp, fill_qty)
        fill_msg_seller = fillMessage(sell_order.orderId, fill_id, fill_timestamp, fill_qty)
        ## Still need to send fill_msg out to traders !!!

        buy_order.trader.fillRequest(fill_msg_buyer)
        sell_order.trader.fillRequest(fill_msg_seller)

        if buy_order.qty == 0:
            loc_buyPrice = self.BuyPrices.index(buy_order.price)
            loc_order = self.orderBuys[loc_buyPrice].index(buy_order.orderId)
            self.orderBuys[loc_buyPrice].pop(loc_order)
            if len(self.orderBuys[loc_buyPrice]) == 1:
                self.BuyPrices.pop(loc_buyPrice)
            self.orderMap.pop(buy_order.orderId)
            self.standingBuys.pop(self.standingBuys.index(buy_order.orderId))
            
        if sell_order.qty == 0:
            loc_sellPrice = self.SellPrices.index(sell_order.price)
            loc_order = self.orderBuys[loc_sellPrice].index(sell_order.orderId)
            self.orderMap.pop(sell_order.orderId)
            if len(self.orderSells[loc_sellPrice]) == 1:
                self.SellPrices.pop(loc_sellPrice)
            self.orderMap.pop(sell_order.orderId)
        
        return([buy_order, sell_order])
                           
            
    def orderProcess(self, recent_order):
        if recent_order.side == "buy" and len(self.SellPrices)>0 and self.SellPrices[0] <= recent_order.price:
            while recent_order.qty > 0:
                cheapest_sell = self.orderMap[self.orderSells[0][0]]
                recent_order = self.makeTrade(recent_order, cheapest_sell)[0]
                
        elif recent_order.side == "sell" and len(self.BuyPrices)>0 and self.BuyPrices[-1] >= recent_order.price:
            while recent_order.qty > 0:
                first_buy_ind = self.orderSells[bisect.bisect_left(self.BuyPrices, recent_order.price)][0]
                recent_order = self.makeTrade(self.orderMap[first_buy_ind], recent_order)[1]
                
        else: # if no trade can be made, send Acknowledgement, otherwise fillMessage
            order_timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(time.time()))
            new_orderAck = orderAcknowledgement(recent_order.orderId, order_timestamp)
            self.msgs.append(new_orderAck)
            return(new_orderAck)
 
        
class Order:
    def __init__(self, trader, side, price, qty, orderId=None):
        self.trader = trader
        self.side = side
        self.price = price
        self.qty = qty
        self.orderId = orderId

class orderAcknowledgement:
    def __init__(self, orderId, timestamp):
        self.orderId = orderId
        self.timestamp = timestamp

class fillMessage:
     def __init__(self, orderId, fillId, timestamp, qty):
        self.orderId = orderId
        self.fillId = fillId
        self.timestamp = timestamp
        self.qty = qty


class Trader:
     
    def show_orderId(self):
        return(list(self.orders.keys()))

    def __init__(self, traderId, orders=None, orderAck=None, orderFilled=None, cancel_hist=None):
        # orders, orderAck, orderFillled, cancel_hist are hashmap of orderId and order, 
        # hashmap of orderId and orderAcknowledgement, hashmap of orderId and fillMessage.
        self.id = traderId
        self.orders = {}
        self.orderAck = {}
        self.orderFilled = {}
        self.cancel_hist = {}

    def add_request(self, order, exchange):
        # get orderID from exchange then append order
        msg_back = exchange.orderAdd(order)
        new_orderId = msg_back.orderId # since both orderAcknowledgement and fillMessage have orderId
        print(new_orderId)
        order_wId = Order(order.trader, order.side, order.price, order.qty, new_orderId)
        self.orders[msg_back.orderId] = order_wId 
        self.orders[new_orderId] = order_wId 
        if isinstance(msg_back, orderAcknowledgement):
            self.orderAck[new_orderId] = msg_back
        elif isinstance(msg_back, fillMessage):
            new_orderId = msg_back.orderId
            self.orderFillled[new_orderId] = msg_back
    
    def cancel_request(self, orderId, exchange):
        cancel_feedback = exchange.orderCancel(orderId)
        print(cancel_feedback)
        self.cancel_hist[orderId] = cancel_feedback

    def fillRequest(self, fillMessage):
        new_orderId = fillMessage.orderId
        self.orderFillled[new_orderId] = fillMessage
    


if __name__ == '__main__':
    
    trader1 = Trader(1)
    trader2 = Trader(2)
    orderReq1 = Order(trader1, "buy", 23, 10)
    orderReq2 = Order(trader1, "sell", 23, 10)
    
    e = Exchange()
    # e.orderAdd(orderReq1)

    trader1.add_request(orderReq2, e)
    trader1.add_request(orderReq1, e)
    
    # trader2.add_request(Order(trader2, "buy", 23, 15), e)
    # trader2.add_request(Order(trader2, "sell", 25, 10), e)
    # trader1.add_request(orderReq1, e)
    
    # trader1.add_request(Order(trader1, "sell", 22, 5), e)
    
    # trader1.add_request(orderReq2, e)
    # trader1.show_orderId()
    
    # trader1.cancel_request(2, e)

    
    # e.orderAdd(orderReq1)
    # e.orderCancel(orderReq2)
    
    