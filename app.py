import io

import pandas as pd
import requests
import streamlit as st
import urllib3

# verify=False 會產生警告，這裡關閉警告訊息
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="TWSE 開放資料", page_icon="📊", layout="wide")

st.title("📊 TWSE 開放資料檢視器")

# ---------------- 側邊欄 ----------------
st.sidebar.header("設定")
url = st.sidebar.text_input(
    "CSV 連結",
    value="https://mopsfin.twse.com.tw/opendata/t187ap46_L_1.csv",  # 換連結
)
verify_ssl = st.sidebar.checkbox("驗證 SSL 憑證", value=False)
drop_na = st.sidebar.checkbox("移除含空值的列 (dropna)", value=True)
timeout = st.sidebar.number_input("連線逾時 (秒)", min_value=5, max_value=120, value=30)


# ---------------- 資料讀取 ----------------
@st.cache_data(show_spinner="資料下載中...", ttl=3600)
def load_data(url: str, verify: bool, timeout: int) -> pd.DataFrame:
    response = requests.get(url, verify=verify, timeout=timeout)
    response.raise_for_status()
    # utf-8-sig 可處理繁體中文與 BOM
    return pd.read_csv(io.BytesIO(response.content), encoding="utf-8-sig")


if st.sidebar.button("🔄 重新下載"):
    load_data.clear()

try:
    df = load_data(url, verify_ssl, timeout)
except requests.exceptions.RequestException as e:
    st.error(f"下載失敗：{e}")
    st.stop()
except Exception as e:
    st.error(f"資料解析失敗：{e}")
    st.stop()

if drop_na:
    df = df.dropna()

# ---------------- 顯示資料 ----------------
col1, col2 = st.columns(2)
col1.metric("資料筆數", f"{len(df):,}")
col2.metric("欄位數", len(df.columns))

keyword = st.text_input("🔍 關鍵字搜尋（搜尋所有欄位）")
if keyword:
    mask = df.astype(str).apply(
        lambda col: col.str.contains(keyword, case=False, na=False)
    ).any(axis=1)
    df = df[mask]
    st.caption(f"符合 {len(df):,} 筆")

selected_cols = st.multiselect("顯示欄位", options=list(df.columns), default=list(df.columns))
show_df = df[selected_cols] if selected_cols else df

st.dataframe(show_df, use_container_width=True)

# ---------------- 下載 ----------------
csv_bytes = show_df.to_csv(index=False).encode("utf-8-sig")
st.download_button(
    "⬇️ 下載 CSV",
    data=csv_bytes,
    file_name="data01.csv",
    mime="text/csv",
)
