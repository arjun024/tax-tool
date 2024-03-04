import csv
from datetime import datetime, timedelta

MERGE_DATE = "11/22/2023"

# default ratio, can be refined by user input
VMW_SHARES_TO_CASH_RATIO = 0.479
VMW_SHARES_TO_STOCK_RATIO = 0.521

AVGO_FMV = 979.5  # avg of high/low on merge date
ONE_VMW_TO_CASH = 142.5
ONE_VMW_TO_AGVO_SHARE = 0.252

VMW_CASH_COMPONENT_VALUE = VMW_SHARES_TO_CASH_RATIO * ONE_VMW_TO_CASH
VMW_AVGO_SHARE_COMPONENT_RATIO = VMW_SHARES_TO_STOCK_RATIO * ONE_VMW_TO_AGVO_SHARE
VMW_FMV_AFTER_MERGE = VMW_CASH_COMPONENT_VALUE + VMW_AVGO_SHARE_COMPONENT_RATIO * AVGO_FMV

DIVIDEND_2021_DATE = "11/01/2021"
DIVIDEND_2021_COST_BASE_REDUCTION = 16.87
DIVIDEND_2018_DATE = "12/28/2018"
DIVIDEND_2018_COST_BASE_REDUCTION = DIVIDEND_2021_COST_BASE_REDUCTION + 10.18

VMW_PRICE_FILE = "vmw-historical-price.csv"
ESPP_DATE_FILE = "espp-date.csv"
DAYS_IN_YEAR = 365

merge_date = datetime.strptime(MERGE_DATE, "%m/%d/%Y")
dividend_date_2018 = datetime.strptime(DIVIDEND_2018_DATE, "%m/%d/%Y")
dividend_date_2021 = datetime.strptime(DIVIDEND_2021_DATE, "%m/%d/%Y")
stock_prices = {}
espp_dates = {}


# refine vmw share to cash/stock conversion ratio
def update_global_variable(vmw_to_cash_share, vmw_to_avgo_share):
    global VMW_SHARES_TO_CASH_RATIO
    global VMW_SHARES_TO_STOCK_RATIO
    global VMW_CASH_COMPONENT_VALUE
    global VMW_AVGO_SHARE_COMPONENT_RATIO
    global VMW_FMV_AFTER_MERGE

    cash_ratio = vmw_to_cash_share / (vmw_to_cash_share + vmw_to_avgo_share)
    stock_ratio = vmw_to_avgo_share / (vmw_to_cash_share + vmw_to_avgo_share)

    print("Use computed conversion ratio, cash_ratio=%.6f, stock_ratio=%.6f" % (cash_ratio, stock_ratio))

    VMW_SHARES_TO_CASH_RATIO = cash_ratio
    VMW_SHARES_TO_STOCK_RATIO = stock_ratio
    VMW_CASH_COMPONENT_VALUE = VMW_SHARES_TO_CASH_RATIO * ONE_VMW_TO_CASH
    VMW_AVGO_SHARE_COMPONENT_RATIO = VMW_SHARES_TO_STOCK_RATIO * ONE_VMW_TO_AGVO_SHARE
    VMW_FMV_AFTER_MERGE = VMW_CASH_COMPONENT_VALUE + VMW_AVGO_SHARE_COMPONENT_RATIO * AVGO_FMV


def display_global_variable(output_file):
    output_file.write('{:<35s}{:<.2f}\n'.format("AVGO FMV (%s):" % MERGE_DATE, AVGO_FMV))
    output_file.write('{:<35s}{:<.6f}\n'.format("VMW per share cash value:", VMW_CASH_COMPONENT_VALUE))
    output_file.write('{:<35s}{:<.6f}\n'.format("VMW per share AVGO ratio:", VMW_AVGO_SHARE_COMPONENT_RATIO))
    output_file.write('{:<35s}{:<.6f}\n\n'.format("VMW per share value after merge:", VMW_FMV_AFTER_MERGE))

    output_file.write("Special dividend 2018: date=%s, reduce cost base by %.2f\n" % (
        DIVIDEND_2018_DATE, DIVIDEND_2018_COST_BASE_REDUCTION))
    output_file.write("Special dividend 2021: date=%s, reduce cost base by %.2f\n\n" % (
        DIVIDEND_2021_DATE, DIVIDEND_2021_COST_BASE_REDUCTION))


def load_historical_price():
    with open(VMW_PRICE_FILE) as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',')
        for row in csvreader:
            stock_prices[row[0]] = row[4]


def load_espp_dates():
    with open(ESPP_DATE_FILE) as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',')
        for row in csvreader:
            espp_dates[row[0]] = row[1]


def get_stock_price(date_str):
    # when date not found in dictionary, lookup previous days
    while date_str not in stock_prices:
        date = datetime.strptime(date_str, "%m/%d/%Y")
        date = date - timedelta(days=1)
        date_str = date.strftime("%m/%d/%Y")

    return float(stock_prices[date_str])


def get_espp_offer_date(date_str):
    if date_str in espp_dates:
        return espp_dates[date_str]
    else:
        return None


def populate_espp_data(lot):
    acquire_date_str = lot["acquire_date"]

    # lookup offer date
    offer_date_str = get_espp_offer_date(acquire_date_str)

    offer_date_fmv = get_stock_price(offer_date_str)
    acquire_date_fmv = get_stock_price(acquire_date_str)
    min_price = min(offer_date_fmv, acquire_date_fmv)
    purchase_price = min_price * 0.85

    lot["offer_date"] = offer_date_str
    lot["offer_date_fmv"] = offer_date_fmv
    lot["acquire_date_fmv"] = acquire_date_fmv
    lot["purchase_price"] = purchase_price


def calc_espp_cost_base(lot):
    populate_espp_data(lot)

    offer_date = datetime.strptime(lot["offer_date"], "%m/%d/%Y")
    acquire_date = datetime.strptime(lot["acquire_date"], "%m/%d/%Y")

    # calc tax
    if ((merge_date - acquire_date).days > DAYS_IN_YEAR) and ((merge_date - offer_date).days > DAYS_IN_YEAR * 2):
        lot["qualifying_disposition"] = True

        offer_date_discount = lot["offer_date_fmv"] * 0.15
        gain = ONE_VMW_TO_CASH - lot["purchase_price"]
        ordinary_income = max(min(offer_date_discount, gain), 0)
        cost_base = lot["purchase_price"] + ordinary_income
    else:
        lot["qualifying_disposition"] = False

        ordinary_income = lot["acquire_date_fmv"] - lot["purchase_price"]
        cost_base = lot["acquire_date_fmv"]

    lot["ordinary_income"] = ordinary_income
    lot["cost_base"] = cost_base

    return lot


def calc_rs_cost_base(lot):
    acquire_date_fmv = get_stock_price(lot["acquire_date"])

    lot["acquire_date_fmv"] = acquire_date_fmv
    lot["purchase_price"] = acquire_date_fmv
    lot["ordinary_income"] = acquire_date_fmv
    lot["cost_base"] = acquire_date_fmv

    return lot


def calc_other_cost_base(lot):
    lot["ordinary_income"] = 0
    lot["cost_base"] = lot["purchase_price"]


def adjust_special_dividend(lot):
    cost_base = lot["cost_base"]
    acquire_date_str = lot["acquire_date"]

    acquire_date = datetime.strptime(acquire_date_str, "%m/%d/%Y")
    delta2018 = dividend_date_2018 - acquire_date
    delta2021 = dividend_date_2021 - acquire_date

    lot["pre_div_adj_cost_base"] = cost_base

    if delta2018.days > 0:
        lot["cost_base"] = cost_base - DIVIDEND_2018_COST_BASE_REDUCTION
    elif delta2021.days > 0:
        lot["cost_base"] = cost_base - DIVIDEND_2021_COST_BASE_REDUCTION


def calc_merge_tax_and_avgo_cost_base(lot):
    cost_base = lot["cost_base"]

    merge_gain = VMW_FMV_AFTER_MERGE - cost_base
    lot["merge_gain"] = merge_gain
    capital_gain = max(min(merge_gain, VMW_CASH_COMPONENT_VALUE), 0)
    lot["capital_gain"] = capital_gain

    avgo_cost_base = (cost_base + capital_gain - VMW_CASH_COMPONENT_VALUE) / VMW_AVGO_SHARE_COMPONENT_RATIO
    lot["avgo_cost_base"] = avgo_cost_base


def check_capital_gain_term(lot):
    acquire_date_str = lot["acquire_date"]

    acquire_date = datetime.strptime(acquire_date_str, "%m/%d/%Y")
    if (merge_date - acquire_date).days > DAYS_IN_YEAR:
        lot["long_term"] = True
    else:
        lot["long_term"] = False


def calc_total(lot):
    lot["total_ordinary_income"] = lot["ordinary_income"] * lot["share"]
    lot["total_proceeds"] = VMW_CASH_COMPONENT_VALUE * lot["share"]
    lot["total_capital_gain"] = lot["capital_gain"] * lot["share"]
    lot["total_cost_base"] = lot["total_proceeds"] - lot["total_capital_gain"]
    lot["avgo_share"] = VMW_AVGO_SHARE_COMPONENT_RATIO * lot["share"]
    lot["avgo_total_cost_base"] = lot["avgo_cost_base"] * lot["avgo_share"]


def calc_fractional_share(lot):
    # add 38 fee to cost base
    lot["fractional_share_cost_base"] = lot["avgo_cost_base"] * lot["fractional_share"] + 38
    lot["fractional_share_capital_gain"] = lot["fractional_share_proceeds"] - lot["fractional_share_cost_base"]

    lot["total_proceeds"] = lot["total_proceeds"] + lot["fractional_share_proceeds"]
    lot["avgo_share"] = lot["avgo_share"] - lot["fractional_share"]
    lot["avgo_total_cost_base"] = lot["avgo_total_cost_base"] - lot["fractional_share_cost_base"]


def display_lot_tax(lot, output_file, verbose):
    output_file.write('{:<35s}{:<s}\n'.format("type:", lot["type"]))
    output_file.write('{:<35s}{:<.3f}\n'.format("share:", lot["share"]))
    output_file.write('{:<35s}{:<s}\n'.format("acquire_date:", lot["acquire_date"]))
    output_file.write('{:<35s}{:<s}\n'.format("long_term:", str(lot["long_term"])))
    output_file.write('{:<35s}{:<.2f}\n'.format("total_proceeds:", lot["total_proceeds"]))
    output_file.write('{:<35s}{:<.2f}\n'.format("total_cost_base:", lot["total_cost_base"]))
    output_file.write('{:<35s}{:<.2f}\n'.format("total_capital_gain:", lot["total_capital_gain"]))

    if lot["type"] == "RS":
        output_file.write('{:<35s}{:<.2f}\n'.format("total_w2_income:", lot["total_ordinary_income"]))
    else:
        output_file.write('{:<35s}{:<.2f}\n'.format("total_pending_ordinary_income:", lot["total_ordinary_income"]))

    output_file.write('{:<35s}{:<.3f}\n'.format("avgo_share:", lot["avgo_share"]))
    output_file.write('{:<35s}{:<.2f}\n'.format("avgo_total_cost_base:", lot["avgo_total_cost_base"]))

    if "fractional_share_cost_base" in lot:
        display_fractiona_share(output_file, lot)

    if verbose:
        output_file.write("\nper share info:\n")

        output_file.write('{:<35s}{:<.2f}\n'.format("purchase_price:", lot["purchase_price"]))
        output_file.write('{:<35s}{:<.2f}\n'.format("cost_base:", lot["cost_base"]))
        output_file.write('{:<35s}{:<.2f}\n'.format("pre_div_adj_cost_base:", lot["pre_div_adj_cost_base"]))
        output_file.write('{:<35s}{:<.2f}\n'.format("merge_gain:", lot["merge_gain"]))
        output_file.write('{:<35s}{:<.2f}\n'.format("capital_gain:", lot["capital_gain"]))
        output_file.write('{:<35s}{:<.2f}\n'.format("ordinary_income:", lot["ordinary_income"]))

        if lot["type"] == "ESPP":
            output_file.write('{:<35s}{:<s}\n'.format("qualifying_disposition:", str(lot["qualifying_disposition"])))
            output_file.write('{:<35s}{:<s}\n'.format("offer_date:", lot["offer_date"]))
            output_file.write('{:<35s}{:<.2f}\n'.format("offer_date_fmv:", lot["offer_date_fmv"]))
            output_file.write('{:<35s}{:<s}\n'.format("acquire_date:", lot["acquire_date"]))
            output_file.write('{:<35s}{:<.2f}\n'.format("acquire_date_fmv:", lot["acquire_date_fmv"]))
        elif lot["type"] == "RS":
            output_file.write('{:<35s}{:<s}\n'.format("acquire_date:", lot["acquire_date"]))
            output_file.write('{:<35s}{:<.2f}\n'.format("acquire_date_fmv:", lot["acquire_date_fmv"]))

        output_file.write('{:<35s}{:<.2f}\n'.format("avgo_cost_base:", lot["avgo_cost_base"]))


def display_fractiona_share(output_file, lot):
    output_file.write('{:<35s}{:<.3f}\n'.format("fractional_share:", lot["fractional_share"]))
    output_file.write('{:<35s}{:<.2f}\n'.format("fractional_share_proceeds:", lot["fractional_share_proceeds"]))
    output_file.write('{:<35s}{:<.2f} including $38 fee\n'.format("fractional_share_cost_base:",
                                                                  lot["fractional_share_cost_base"]))
    output_file.write('{:<35s}{:<.2f}\n'.format("fractional_share_capital_gain:",
                                                lot["fractional_share_capital_gain"]))