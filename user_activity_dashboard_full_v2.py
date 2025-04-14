
import streamlit as st
import pandas as pd
import json
from collections import defaultdict
import matplotlib.pyplot as plt

# ---------- 載入資料 ----------
with open("log_202409_part1.json", "r", encoding="utf-8") as file:
    log_data = json.load(file)

with open("location_dict.json", "r", encoding="utf-8") as f:
    location_dict = json.load(f)

tags_dict = {
    "主題樂園": ["環球影城", "迪士尼", "樂園", "遊樂園"],
    "自然景觀": ["峽灣", "森林", "湖", "溫泉", "瀑布", "山", "海灘", "草原", "自然", "極光", "星空", "雲海", "楓", "櫻", "櫻花", "楓葉", "觀景", "落羽松"],
    "文化歷史": ["博物館", "神社", "寺", "古城", "遺跡", "文化", "歷史", "古蹟", "宮殿", "皇宮", "教堂", "城堡", "古老", "古代", "古文明", "古文物", "祭典", "世界遺產"],
    "美食": ["螃蟹", "美食", "饗宴", "餐廳", "料理", "海鮮", "燒肉", "壽司", "拉麵", "咖哩", "甜點"],
    "購物": ["購物", "市場", "商場", "百貨"],
    "親子旅遊": ["親子", "動物園", "兒童", "家庭", "水族館"],
    "豪華": ["五星", "高級", "豪華", "度假", "渡假"],
    "海島旅遊": ["海灘", "潛水", "島", "度假村", "海島", "海洋", "浮潛", "海底"],
    "雪景": ["滑雪", "冰川", "極光", "雪景", "戲雪", "冰上活動"],
    "火車旅遊": ["火車", "列車", "鐵道"],
    "溫泉之旅": ["溫泉", "溫泉鄉", "溫泉區", "溫泉街"]
}

# ---------- 整理 DataFrame ----------
records = []
for entry in log_data:
    logtime = entry.get("logtime")
    luid = entry.get("luid")
    prod_info = entry.get("prod_info", {})
    prod_name = prod_info.get("ProdName", "")
    prod_price = prod_info.get("ProdPrice", None)
    prod_no = prod_info.get("ProdNo", "")
    ptype = entry.get("ptype", "")
    search_info = entry.get("search_info", {})
    order_info = entry.get("order_info", {})

    records.append({
        "logtime": logtime,
        "user_id": luid,
        "ptype": ptype,
        "product_name": prod_name,
        "product_price": prod_price,
        "product_id": prod_no,
        "search_keywords": search_info.get("keyword", None),
        "order_info": order_info,
    })

df = pd.DataFrame(records)
df["logtime"] = pd.to_datetime(df["logtime"])

# ---------- Streamlit UI ----------
st.title("使用者互動紀錄分析")

selected_user = st.selectbox("選擇使用者", df["user_id"].dropna().unique())
user_data = df[df["user_id"] == selected_user]

# 時間區間篩選
min_date, max_date = user_data["logtime"].min(), user_data["logtime"].max()
start_date, end_date = st.date_input("選擇時間區間", [min_date.date(), max_date.date()])
filtered_data = user_data[(user_data["logtime"].dt.date >= start_date) & (user_data["logtime"].dt.date <= end_date)]

st.subheader("📘 瀏覽紀錄")
st.dataframe(filtered_data[filtered_data["ptype"].str.contains("ProductDetail", na=False)][["logtime", "product_name", "product_price"]])

st.subheader("🔍 搜尋紀錄")
search_df = filtered_data[filtered_data["search_keywords"].notna()]
st.dataframe(search_df[["logtime", "search_keywords"]])

st.subheader("🛒 購買紀錄")
order_df = filtered_data[filtered_data["order_info"].astype(str) != "{}"]
st.dataframe(order_df[["logtime", "product_name", "product_price", "order_info"]])

# ---------- 地區標籤統計 ----------
def extract_tags(name, tag_map):
    matched_tags = []
    for tag, keywords in tag_map.items():
        if any(keyword in name for keyword in keywords):
            matched_tags.append(tag)
    return matched_tags

st.subheader("📍 地區標籤統計")
region_counter = defaultdict(int)
for name in filtered_data["product_name"].dropna():
    for tag in extract_tags(name, location_dict):
        region_counter[tag] += 1

region_df = pd.DataFrame(region_counter.items(), columns=["標籤分類", "次數"]).sort_values("次數", ascending=False)
st.dataframe(region_df)

# ---------- 主題標籤統計 ----------
st.subheader("🏷 主題標籤統計")
theme_counter = defaultdict(int)
for name in filtered_data["product_name"].dropna():
    for tag in extract_tags(name, tags_dict):
        theme_counter[tag] += 1

theme_df = pd.DataFrame(theme_counter.items(), columns=["主題標籤", "次數"]).sort_values("次數", ascending=False)
st.dataframe(theme_df)

# ---------- 視覺化 ----------
st.subheader("📊 地區標籤長條圖")
if not region_df.empty:
    fig1, ax1 = plt.subplots()
    region_df.plot.bar(x="標籤分類", y="次數", ax=ax1, legend=False)
    st.pyplot(fig1)

st.subheader("🧁 主題標籤圓餅圖")
if not theme_df.empty:
    fig2, ax2 = plt.subplots()
    ax2.pie(theme_df["次數"], labels=theme_df["主題標籤"], autopct="%1.1f%%")
    ax2.axis("equal")
    st.pyplot(fig2)
