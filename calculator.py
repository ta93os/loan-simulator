import math
from datetime import datetime

import numpy as np
import numpy_financial as np_f
import pandas as pd


def calc_payment(rate, n_month, balance):
    # 月々の返済額
    payment = math.floor(np_f.pmt(rate, n_month, -balance, when="end"))
    pmt = np.full((n_month,), payment)

    # 利息を格納
    ipmt = []
    # 各時点での残債を保存
    tmp_balance = balance
    for i in range(1, n_month + 1):
        # 利息の計算
        tmp_ipmt = math.floor(
            np_f.ipmt(
                rate,
                1,
                n_month - i + 1,
                -tmp_balance,
                fv=0,
                when="end",
            )
        )
        ipmt.append(tmp_ipmt)
        # 残債から元本を差し引く
        tmp_balance = tmp_balance - payment + tmp_ipmt
    ipmt = np.array(ipmt)
    # 支払額における元本分を保存
    ppmt = pmt - ipmt
    # 最後の支払いについては元本をすべて払う
    ppmt[-1] = balance - ppmt[:-1].sum()
    pmt[-1] = ppmt[-1] + ipmt[-1]

    return payment, pmt, ppmt, ipmt


class Calculator:
    def __init__(self, amount, amount_bonus, rate, n_year, start_year):
        # 返済開始日（1月1日とする）
        self.start_date = datetime(start_year, 1, 1).strftime(format="%Y-%m-%d")
        self.start_date_bonus = datetime(start_year, 6, 1).strftime(format="%Y-%m-%d")
        # 借入金額
        self.amount = amount
        self.amount_bonus = amount_bonus
        self.amount_monthly = self.amount - self.amount_bonus
        # 利率
        self.rate = rate
        self.rate_monthly = self.rate / 12
        self.rate_bonus = self.rate / 2
        # 返済期間
        self.n_year = n_year
        self.n_month_monthly = self.n_year * 12
        self.n_month_bonus = self.n_year * 2
        self.range_monthly = range(1, self.n_month_monthly + 1)
        self.range_bonus = range(1, self.n_month_bonus + 1)

    def show_setting(self):
        print("====入力情報====")
        print(f"借入金額 : {self.amount}円 (内ボーナス : {self.amount_bonus}円)")
        print(f"利率 : {np.round(self.rate*100, 3)}%")
        print(f"返済年数 : {self.n_year}年")

    def calc_monthly(self):
        (
            self.payment_monthly,
            self.pmt_monthly,
            self.ppmt_monthly,
            self.ipmt_monthly,
        ) = calc_payment(self.rate_monthly, self.n_month_monthly, self.amount_monthly)
        return

    def calc_bonus(self):
        (
            self.payment_bonus,
            self.pmt_bonus,
            self.ppmt_bonus,
            self.ipmt_bonus,
        ) = calc_payment(self.rate_bonus, self.n_month_bonus, self.amount_bonus)
        return

    def show_amount(self):
        self.calc_monthly()
        self.calc_bonus()
        print("====支払額====")
        print(f"総額 : {self.pmt_monthly.sum()+self.pmt_bonus.sum()}円")
        print(f"元本 : {self.ppmt_monthly.sum()+self.ppmt_bonus.sum()}円")
        print(f"利息 : {self.ipmt_monthly.sum()+self.ipmt_bonus.sum()}円")
        print("====毎月の支払額====")
        print(f"月々の支払額 : {self.payment_monthly}円")
        print(f"ボーナス月の支払額(6月,12月) : {self.payment_bonus}円")

    def create_table(self):
        self.calc_monthly()
        self.calc_bonus()
        range_monthly = pd.date_range(
            start=self.start_date, periods=self.n_month_monthly, freq="ME"
        )
        range_bonus = pd.date_range(
            start=self.start_date_bonus, periods=self.n_month_bonus, freq="6ME"
        )
        df_monthly = pd.DataFrame(
            {
                "YYYYMM": range_monthly,
                "pmt_monthly": self.pmt_monthly,
                "ppmt_monthly": self.ppmt_monthly,
                "ipmt_monthly": self.ipmt_monthly,
            }
        )
        df_bonus = pd.DataFrame(
            {
                "YYYYMM": range_bonus,
                "pmt_bonus": self.pmt_bonus,
                "ppmt_bonus": self.ppmt_bonus,
                "ipmt_bonus": self.ipmt_bonus,
            }
        )
        df = (
            pd.merge(df_monthly, df_bonus, how="left", on="YYYYMM")
            .set_index("YYYYMM")
            .fillna(0)
            .astype(int)
        )
        df["pmt_all"] = df["pmt_monthly"] + df["pmt_bonus"]
        df["ppmt_all"] = df["ppmt_monthly"] + df["ppmt_bonus"]
        df["ipmt_all"] = df["ipmt_monthly"] + df["ipmt_bonus"]
        df["balance"] = df["pmt_all"].sum() - df["pmt_all"].cumsum()
        df["balance_ppmt"] = self.amount - df["ppmt_all"].cumsum()
        df["balance_ippmt"] = df["ipmt_all"].sum() - df["ipmt_all"].cumsum()

        return df


if __name__ == "__main__":
    start_date = 2025
    n_year = 35
    amount = 80_000_000
    amount_bonus = amount * 0.1
    rate = 0.005
    calculator = Calculator(amount, amount_bonus, rate, n_year, start_date)
    calculator.show_setting()
    calculator.show_amount()
    df = calculator.create_table()
    df.to_csv("loan.csv")
