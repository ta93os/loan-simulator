# import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from calculator import Calculator


def df_trim(df):
    df = df.loc[
        :,
        ["pmt_all", "ppmt_all", "ipmt_all", "balance", "balance_ppmt"],
    ]

    df["payment_all"] = df["pmt_all"].cumsum()
    df = df[
        ["pmt_all", "ppmt_all", "ipmt_all", "balance_ppmt", "payment_all"]
    ].reset_index()

    df.columns = [
        "date",
        "返済額",
        "返済額(元本)",
        "返済額(利息)",
        "借入残高",
        "返済総額",
    ]
    df["date"] = df["date"].dt.strftime("%Y年%m月")
    return df


# streamlitのレイアウトをwideにする
st.set_page_config(
    page_title="住宅ローン比較シミュレータ", layout="wide", page_icon="🏠"
)

# titleをつける
st.title(
    "住宅ローン比較シミュレータ",
)

# 概要

expander = st.expander("Information", icon=":material/info:")
expander.write(
    """
    - 住宅ローンについて、手数料や利率を考慮して比較することができます
    - 完済時だけではなく、5年後や10年後等、短期で考えた場合の比較も可能です
    - 端数処理の関係で支払総額に1円程度の誤差が発生する可能性があるため、あくまでシミュレーション用としてご活用ください"""
)

# 条件指定とシミュレーションの2つに分割
main_col1, main_col2 = st.columns([2, 3], border=True)

# 条件の設定
main_col1.header("条件", divider="gray")

main_col1.subheader("共通条件")

minicol1, minicol2 = main_col1.columns([1, 1])
# 手数料を除いた借入額
amount = minicol1.number_input(
    "手数料を除いた借入額（円）",
    min_value=0,
    value=80_000_000,
    step=1000000,
    key="amount",
)
# ボーナス返済比率
rate_bonus = minicol2.number_input(
    "ボーナス返済比率（%）",
    min_value=0,
    max_value=100,
    value=10,
    step=5,
    key="rate_bonus",
)
# 返済期間
n_year = minicol1.number_input("返済期間（年）", min_value=1, value=35, key="n_year")
# 返済開始時期
start_date = minicol2.number_input(
    "返済開始時期（年）", min_value=2025, max_value=2100, value=2025, key="start_date"
)


# パターン1,2に分ける
col1, col2 = main_col1.columns([1, 1])

col1.subheader("パターン1")

label1 = col1.text_input("出力用ラベル", "パターン1", key="label1")

# パターン1の手数料
margin1 = col1.number_input(
    "手数料（円）", min_value=0, value=1760000, step=100000, key="margin1", format="%d"
)
# パターン1の利率
rate1 = col1.number_input(
    "利率（%）",
    min_value=0.0,
    max_value=100.0,
    value=0.425,
    format="%.3f",
    key="rate1",
)

col2.subheader("パターン2")

label2 = col2.text_input("出力用ラベル", "パターン2", key="label2")
# パターン2の手数料
margin2 = col2.number_input(
    "手数料（円）", min_value=0, value=330000, step=100000, key="margin2", format="%d"
)
# パターン2の利率
rate2 = col2.number_input(
    "利率（%）",
    min_value=0.0,
    max_value=100.0,
    value=0.836,
    format="%.3f",
    key="rate2",
)

main_col1.caption(
    """
- 注意点
    - 元利均等返済となります
    - 返済開始は1月開始としています
    - 出力用ラベルはシミュレーション結果の出力に反映されます
"""
)


# シミュレーション
main_col2.header("シミュレーション", divider="gray")
calc1 = Calculator(
    amount + margin1,
    int((amount + margin1) * (rate_bonus) / 100),
    rate1 / 100,
    n_year,
    start_date,
)
calc2 = Calculator(
    amount + margin2,
    int((amount + margin2) * (rate_bonus) / 100),
    rate2 / 100,
    n_year,
    start_date,
)
df1 = calc1.create_table()
df2 = calc2.create_table()

df1 = df_trim(df1)
df2 = df_trim(df2)

# シミュレーション画面を4分割に分ける
tab_graph, tab1, tab2, tab3 = main_col2.tabs(
    [
        "グラフ",
        "比較",
        f"{label1}のシミュレーション結果",
        f"{label2}のシミュレーション結果",
    ]
)

# グラフ
tab_graph.write(
    "各パターンにおける借入残高や返済総額、パターン1とパターン2を比較したメリットをグラフで出力します"
)
fig_radio = tab_graph.radio(
    "比較項目", ["借入残高", "返済総額", "メリット"], horizontal=True
)
if fig_radio == "借入残高":
    layout = go.Layout(yaxis=dict(tickformat=".n"))
    fig = go.Figure(layout=layout)
    fig.add_trace(
        go.Scatter(x=df1["date"], y=df1["借入残高"], mode="lines", name=label1)
    )
    fig.add_trace(
        go.Scatter(x=df2["date"], y=df2["借入残高"], mode="lines", name=label2)
    )
    fig.update_layout(title="借入残高")
    tab_graph.plotly_chart(fig, use_container_width=True)
elif fig_radio == "返済総額":
    layout = go.Layout(yaxis=dict(tickformat=".n"))
    fig = go.Figure(layout=layout)
    fig.add_trace(
        go.Scatter(
            x=df1["date"],
            y=df1["返済総額"],
            mode="lines",
            name=label1,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df2["date"],
            y=df2["返済総額"],
            mode="lines",
            name=label2,
        )
    )
    fig.update_layout(title="返済総額")
    tab_graph.plotly_chart(fig, use_container_width=True)
else:
    layout = go.Layout(yaxis=dict(tickformat=".n"))
    fig = go.Figure(layout=layout)
    fig.add_trace(
        go.Scatter(
            x=df1["date"],
            y=(amount - df1["借入残高"] - df1["返済総額"])
            - (amount - df2["借入残高"] - df2["返済総額"]),
            mode="lines",
            name=label1,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df1["date"],
            y=(amount - df2["借入残高"] - df2["返済総額"])
            - (amount - df1["借入残高"] - df1["返済総額"]),
            mode="lines",
            name=label2,
        )
    )
    fig.update_layout(title="メリット")
    tab_graph.plotly_chart(fig, use_container_width=True)


# 比較
tab1.write(
    "借入額、将来の借入残高と総支払額の関係から、パターン1とパターン2のどちらにメリットがあるかを比較します"
)
set_year = tab1.number_input("比較する年数", min_value=1, value=n_year, key="set_year")

sim1 = (
    amount
    - df1.iloc[12 * set_year - 1]["借入残高"]
    - df1.iloc[12 * set_year - 1]["返済総額"]
)
sim2 = (
    amount
    - df2.iloc[12 * set_year - 1]["借入残高"]
    - df2.iloc[12 * set_year - 1]["返済総額"]
)

if sim1 > sim2:
    tab1.write(f"{set_year}年後では{label1}の方が{sim1-sim2:,}円メリットがあります")
    tab1.markdown(
        f"""
- {label1} ... 借入残高 : {df1.iloc[12 * set_year - 1]["借入残高"]:,}円
（{amount - df1.iloc[12 * set_year - 1]["借入残高"]:,}円減少） ,
        返済総額 : {df1.iloc[12 * set_year - 1]["返済総額"]:,}円
- {label2} ... 借入残高 : {df2.iloc[12 * set_year - 1]["借入残高"]:,}円
（{amount - df2.iloc[12 * set_year - 1]["借入残高"]:,}円減少） ,
        返済総額 : {df2.iloc[12 * set_year - 1]["返済総額"]:,}円"""
    )
elif sim1 < sim2:
    tab1.write(f"{set_year}年後では{label2}の方が{sim2-sim1:,}円メリットがあります")
    tab1.markdown(
        f"""
- {label1} ... 借入残高 : {df1.iloc[12 * set_year - 1]["借入残高"]:,}円
（{amount - df1.iloc[12 * set_year - 1]["借入残高"]:,}円減少） ,
        返済総額 : {df1.iloc[12 * set_year - 1]["返済総額"]:,}円
- {label2} ... 借入残高 : {df2.iloc[12 * set_year - 1]["借入残高"]:,}円
（{amount - df2.iloc[12 * set_year - 1]["借入残高"]:,}円減少） ,
        返済総額 : {df2.iloc[12 * set_year - 1]["返済総額"]:,}円"""
    )
else:
    tab1.write(f"{set_year}年後では{label1}と{label2}ではどちらも同じとなります")
    tab1.markdown(
        f"""
- {label1} ... 借入残高 : {df1.iloc[12 * set_year - 1]["借入残高"]:,}円
（{amount - df1.iloc[12 * set_year - 1]["借入残高"]:,}円減少） ,
        返済総額 : {df1.iloc[12 * set_year - 1]["返済総額"]:,}円
- {label2} ... 借入残高 : {df2.iloc[12 * set_year - 1]["借入残高"]:,}円
（{amount - df2.iloc[12 * set_year - 1]["借入残高"]:,}円減少） ,
        返済総額 : {df2.iloc[12 * set_year - 1]["返済総額"]:,}円"""
    )
tab1_expander = tab1.expander("補足", icon=":material/calculate:")
tab1_expander.write(
    """
    - ここでは、「借入残高+返済総額の差分」をメリットと定義しています
    - 「借入残高+返済総額」が低いほど、住み替え時等にメリットがあると考えられます
    """
)


# パターン1
csv1 = df1.to_csv(index=False)
tab2.download_button(
    label="CSVファイルのDownload",
    data=csv1.encode("utf-8-sig"),
    file_name=f"simulation_{label1}.csv",
)
tab2.dataframe(df1, height=600)


# パターン2
csv2 = df2.to_csv(index=False)
tab3.download_button(
    label="CSVファイルのDownload",
    data=csv2.encode("utf-8-sig"),
    file_name=f"simulation_{label2}.csv",
)
tab3.dataframe(df2, height=600)
