import csv  # 匯入 csv 模組
import json
import os
import requests
from bs4 import BeautifulSoup
import time
import random
import re
import urllib.parse
import datetime  # 引入 datetime 模組

# --- Configuration ---
# 使用 raw string (r'') 或雙反斜線來處理 Windows 路徑
CSV_FILE_PATH = r'../產品資料.csv'  # 改為 CSV 檔案路徑
IMAGE_OUTPUT_DIR = r'./img/product-grid'  # 相對於 html 資料夾
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# --- Unsplash API Configuration ---
# !!! 安全警告：將 API 金鑰直接寫入程式碼有風險，建議使用環境變數等方式管理 !!!
UNSPLASH_ACCESS_KEYS = [
    "MLe8-3fEKUWmeqVV6FtLSobVAlSEsLSpzxDEEyV7ohQ",  # 原本的金鑰
    "q8fEsYBmGESDB7F8AjXWmbCcE0Sb_-5zAdy6NtToA9w",  # 新金鑰 1
    "u-wtWoM4VNZ--qESbwaltWj6KrowYIxJxlUmYkrUek4"   # 新金鑰 2
]
UNSPLASH_API_URL = "https://api.unsplash.com/search/photos"
API_REQUEST_LIMIT = 50  # 每個金鑰每小時的請求上限
CURRENT_API_KEY_INDEX = 0
API_REQUEST_COUNTERS = [0] * len(UNSPLASH_ACCESS_KEYS)  # 每個金鑰的請求計數器
GLOBAL_COOLDOWN_UNTIL = None  # 全域冷卻結束時間
API_WAIT_SECONDS = 3660  # 全域冷卻時間 (61 分鐘)

# --- End Configuration ---


def process_product_data_from_csv(filepath):
    """從 CSV 檔案載入產品資料，根據【產品編號】去重。"""
    unique_products = {}
    print(f"正在從 CSV 檔案讀取產品資料: {filepath}")

    try:
        with open(filepath, mode='r', encoding='utf-8-sig') as f:  # utf-8-sig to handle BOM
            reader = csv.reader(f)
            headers = next(reader, None)

            if not headers:
                print("錯誤：CSV 檔案為空或沒有標頭。")
                return {}

            try:
                product_id_col = headers.index('產品編號')
                search_query_col = headers.index('地點／景點')
            except ValueError:
                print(f"錯誤：CSV 標頭中未找到 '【產品編號】' 或 '【地點／景點】' 欄位。找到的標頭: {headers}")
                return {}

            for row_num, row in enumerate(reader):
                if len(row) <= max(product_id_col, search_query_col):
                    print(f"警告：跳過 CSV 第 {row_num + 2} 行，欄位數不足。行內容: {row}")
                    continue

                product_id = row[product_id_col].strip()
                search_query = row[search_query_col].strip()

                if not product_id:
                    print(f"警告：跳過 CSV 第 {row_num + 2} 行，【產品編號】為空。")
                    continue
                if not search_query:
                    print(f"警告：跳過 CSV 第 {row_num + 2} 行 (產品編號: {product_id})，【地點／景點】為空。")
                    continue

                if product_id not in unique_products:
                    unique_products[product_id] = {
                        'product_id': product_id,
                        'search_query': search_query
                    }

            print(f"處理完成，從 CSV 找到 {len(unique_products)} 個唯一的產品 (基於【產品編號】)。")

    except FileNotFoundError:
        print(f"錯誤：找不到 CSV 檔案於 {filepath}")
        return {}
    except Exception as e:
        print(f"錯誤：讀取或處理 CSV 檔案時發生意外錯誤 {filepath} - {e}")
        return {}

    return unique_products


def find_image_url_unsplash_api(query):
    """使用 Unsplash API 輪替金鑰搜尋圖片 URL。"""
    global CURRENT_API_KEY_INDEX, API_REQUEST_COUNTERS, GLOBAL_COOLDOWN_UNTIL
    global UNSPLASH_ACCESS_KEYS, UNSPLASH_API_URL, API_REQUEST_LIMIT, API_WAIT_SECONDS

    current_time = datetime.datetime.now()

    # 1. 檢查全域冷卻時間
    if GLOBAL_COOLDOWN_UNTIL and current_time < GLOBAL_COOLDOWN_UNTIL:
        remaining_wait = (GLOBAL_COOLDOWN_UNTIL - current_time).total_seconds()
        print(f"\n所有 API 金鑰均達到速率上限。全域冷卻中，需等待 {remaining_wait:.0f} 秒...")
        time.sleep(remaining_wait + 1)  # 等待剩餘時間
        # 冷卻結束後重置狀態
        GLOBAL_COOLDOWN_UNTIL = None
        API_REQUEST_COUNTERS = [0] * len(UNSPLASH_ACCESS_KEYS)
        CURRENT_API_KEY_INDEX = 0
        print("全域冷卻結束。嘗試使用第一個 API 金鑰繼續...")

    # 2. 尋找可用的 API 金鑰
    original_key_index_for_cycle = CURRENT_API_KEY_INDEX
    selected_key_for_this_request = None

    for i in range(len(UNSPLASH_ACCESS_KEYS)):
        prospective_key_index = (original_key_index_for_cycle + i) % len(UNSPLASH_ACCESS_KEYS)
        if API_REQUEST_COUNTERS[prospective_key_index] < API_REQUEST_LIMIT:
            CURRENT_API_KEY_INDEX = prospective_key_index
            selected_key_for_this_request = UNSPLASH_ACCESS_KEYS[CURRENT_API_KEY_INDEX]
            break

    if selected_key_for_this_request is None:
        # 所有金鑰在本輪都已達到請求上限
        if not GLOBAL_COOLDOWN_UNTIL:  # 僅在尚未設定全域冷卻時設定
            print(f"\n所有 API 金鑰在本輪均已達到請求上限。開始全域冷卻 {API_WAIT_SECONDS // 60} 分鐘 {API_WAIT_SECONDS % 60} 秒。")
            GLOBAL_COOLDOWN_UNTIL = current_time + datetime.timedelta(seconds=API_WAIT_SECONDS)
            # 計數器將在下一次冷卻結束後重置

        # 即使設定了冷卻，此請求也無法立即處理，需等待下一次呼叫時由步驟1處理等待
        print(f"  注意：目前無可用 API 金鑰，等待全域冷卻。")
        return None

    access_key_to_use = selected_key_for_this_request
    current_key_display_num = CURRENT_API_KEY_INDEX + 1

    # --- 執行 API 請求 ---
    print(f"正在透過 Unsplash API (金鑰 #{current_key_display_num}) 搜尋圖片：{query}")
    params = {
        'query': query,
        'per_page': 1,
        'orientation': 'landscape'
    }
    api_headers = {
        'Authorization': f'Client-ID {access_key_to_use}',
        'Accept-Version': 'v1'
    }

    try:
        response = requests.get(UNSPLASH_API_URL, headers=api_headers, params=params, timeout=15)
        API_REQUEST_COUNTERS[CURRENT_API_KEY_INDEX] += 1
        print(f"  (使用 API 金鑰 #{current_key_display_num}，請求 {API_REQUEST_COUNTERS[CURRENT_API_KEY_INDEX]}/{API_REQUEST_LIMIT})")

        response.raise_for_status()
        data = response.json()

        if data['results'] and len(data['results']) > 0:
            urls = data['results'][0]['urls']
            image_url = urls.get('regular') or urls.get('small') or urls.get('thumb') or urls.get('raw')
            if image_url:
                print(f"  透過 API (金鑰 #{current_key_display_num}) 找到 URL：{image_url[:60]}...")
                return image_url
            else:
                print(f"  警告：API (金鑰 #{current_key_display_num}) 回應中未找到有效的圖片 URL。")
                return None
        else:
            print(f"  警告：API (金鑰 #{current_key_display_num}) 未找到與 '{query}' 相關的圖片。")
            return None

    except requests.exceptions.Timeout:
        print(f"  錯誤：呼叫 Unsplash API (金鑰 #{current_key_display_num}) 超時 '{query}'")
        return None
    except requests.exceptions.RequestException as e:
        print(f"  錯誤：呼叫 Unsplash API (金鑰 #{current_key_display_num}) 時發生錯誤 '{query}': {e}")
        if e.response is not None:
            print(f"      狀態碼: {e.response.status_code}")
            try:
                print(f"      回應內容: {e.response.json()}")
            except json.JSONDecodeError:
                print(f"      回應內容: {e.response.text}")

            if e.response.status_code == 403:  # 特定針對速率限制的處理
                print(f"  警告：API 金鑰 #{current_key_display_num} (尾碼: ...{access_key_to_use[-6:]}) 遭遇 403 錯誤。將此金鑰標記為本輪已用盡。")
                API_REQUEST_COUNTERS[CURRENT_API_KEY_INDEX] = API_REQUEST_LIMIT  # 標記為已用盡
        return None
    except Exception as e:
        print(f"  錯誤：處理 Unsplash API (金鑰 #{current_key_display_num}) 回應時發生錯誤 '{query}': {e}")
        return None


def download_image(image_url, product_id_for_filename, save_dir):
    """從 URL 下載圖片並儲存。"""
    if not image_url:
        print("  錯誤：未提供 image_url。")
        return False

    safe_filename_id = re.sub(r'[\\/*?:"<>|]', "_", str(product_id_for_filename))
    safe_filename_id = safe_filename_id.strip('. ')
    if not safe_filename_id:
        safe_filename_id = f"invalid_product_id_{random.randint(1000,9999)}"

    filename = f"{safe_filename_id}.jpg"
    filepath = os.path.join(save_dir, filename)

    if os.path.exists(filepath):
        print(f"  跳過下載，檔案已存在：{filename}")
        return True

    print(f"  準備下載產品編號 {safe_filename_id} 的圖片從 {image_url[:60]}...")
    try:
        img_response = requests.get(image_url, headers=HEADERS, stream=True, timeout=30)
        img_response.raise_for_status()

        content_type = img_response.headers.get('content-type', '').lower()
        is_image = content_type.startswith('image/')
        content_length = img_response.headers.get('content-length')
        is_reasonable_size = True
        if content_length:
            try:
                if int(content_length) < 1024:
                    is_reasonable_size = False
                    print(f"  警告：圖片大小 ({content_length} bytes) 過小，可能無效。")
            except ValueError:
                pass

        if not is_image and is_reasonable_size:
            print(f"  警告：URL 的 Content-Type ({content_type}) 看起來不是圖片。正在嘗試下載...")
        elif not is_image and not is_reasonable_size:
            print(f"  錯誤：URL 的 Content-Type ({content_type}) 不是圖片且大小可疑。取消下載。")
            return False

        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        with open(filepath, 'wb') as f:
            for chunk in img_response.iter_content(8192):
                f.write(chunk)
        print(f"  成功儲存：{filename}")
        return True

    except requests.exceptions.Timeout:
        print(f"  錯誤：下載圖片超時，產品編號 {safe_filename_id}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"  錯誤：下載圖片時發生錯誤，產品編號 {safe_filename_id}: {e}")
        if isinstance(e, requests.exceptions.HTTPError) and e.response.status_code == 403:
            print("      收到 403 Forbidden 錯誤，可能無法直接下載此圖片 URL。")
        return False
    except IOError as e:
        print(f"  錯誤：儲存圖片時發生 I/O 錯誤，產品編號 {safe_filename_id}: {e}")
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except OSError:
                pass
        return False
    except Exception as e:
        print(f"  儲存圖片時發生未知錯誤，產品編號 {safe_filename_id}: {e}")
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except OSError:
                pass
        return False


def main():
    """主函數，處理日誌並下載圖片。"""
    print("開始圖片下載程序...")
    products_to_process = process_product_data_from_csv(CSV_FILE_PATH)

    if not products_to_process:
        print("找不到要處理的產品。正在結束。")
        return

    try:
        os.makedirs(IMAGE_OUTPUT_DIR, exist_ok=True)
        print(f"圖片將儲存到：{IMAGE_OUTPUT_DIR}")
    except OSError as e:
        print(f"錯誤：無法建立輸出目錄 {IMAGE_OUTPUT_DIR}: {e}")
        return

    download_count = 0
    failed_count = 0
    total_products = len(products_to_process)

    product_list = list(products_to_process.values())

    for i, product_data in enumerate(product_list):
        product_id = product_data['product_id']
        search_query = product_data['search_query']

        print(f"\n處理產品 {i+1}/{total_products}: 產品編號: {product_id} (搜尋關鍵字: {search_query})")

        # 檢查圖片是否已存在 (使用 product_id 命名)
        safe_product_id_filename = re.sub(r'[\\/*?:"<>|]', "_", str(product_id))
        safe_product_id_filename = safe_product_id_filename.strip('. ')
        if not safe_product_id_filename:
            # 如果產品編號清理後為空（不太可能，但以防萬一）
            safe_product_id_filename = f"invalid_id_{random.randint(1000,9999)}"

        filename_check = f"{safe_product_id_filename}.jpg"
        filepath_check = os.path.join(IMAGE_OUTPUT_DIR, filename_check)

        if os.path.exists(filepath_check):
            print(f"  圖片已存在，跳過搜尋與下載：{filename_check}")
            download_count += 1  # 已存在的也算成功處理
            continue

        if not search_query:
            print(f"  產品編號 {product_id} 的搜尋關鍵字為空，跳過圖片搜尋。")
            failed_count += 1
            continue

        # 使用 search_query (地點／景點) 搜尋圖片
        image_url = find_image_url_unsplash_api(search_query)

        if image_url:
            # 使用 product_id 下載並儲存圖片
            if download_image(image_url, product_id, IMAGE_OUTPUT_DIR):
                download_count += 1
            else:
                failed_count += 1
        else:
            print(f"  未能為產品編號 {product_id} (搜尋: '{search_query}') 找到圖片 URL。")
            failed_count += 1

        sleep_time = random.uniform(0.5, 1.5)  # 保持禮貌的請求間隔
        print(f"  等待 {sleep_time:.2f} 秒...")
        time.sleep(sleep_time)

    print(f"\n程序完成。")
    print(f"總共處理 {total_products} 個唯一產品。")
    print(f"成功下載或已存在 {download_count} 張圖片。")
    print(f"未能下載或跳過 {failed_count} 張圖片。")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n偵測到使用者中斷 (KeyboardInterrupt)。正在結束程序...")
    except Exception as e:
        print(f"\n發生未預期的錯誤：{e}")
        import traceback
        traceback.print_exc()
