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
JSON_FILE_PATH = r'c:\Users\jk121\文件\Code\LION\replica_website\log_202409.json'
IMAGE_OUTPUT_DIR = r'c:\Users\jk121\文件\Code\LION\replica_website\img\product-grid'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# --- Unsplash API Configuration ---
# !!! 安全警告：將 API 金鑰直接寫入程式碼有風險，建議使用環境變數等方式管理 !!!
UNSPLASH_ACCESS_KEY = "MLe8-3fEKUWmeqVV6FtLSobVAlSEsLSpzxDEEyV7ohQ"
UNSPLASH_API_URL = "https://api.unsplash.com/search/photos"
API_REQUEST_LIMIT = 50
API_REQUEST_COUNTER = 0
API_LIMIT_RESET_TIME = None  # 記錄速率限制重置的時間
API_WAIT_SECONDS = 3660  # 1 小時 1 分鐘

# --- End Configuration ---


def process_logs(filepath):
    """載入日誌，根據 ProdName 進行篩選和去重。"""
    unique_products = {}
    logs = []
    malformed_json_count = 0

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read().strip()  # 讀取並移除前後空白

        # 嘗試標準 JSON 解析 (如果文件是有效的 JSON 陣列)
        try:
            if content.startswith('[') and content.endswith(']'):
                logs = json.loads(content)
                print("成功將文件解析為 JSON 陣列。")
            else:
                raise json.JSONDecodeError("文件不是標準 JSON 陣列格式", content, 0)
        except json.JSONDecodeError as e:
            print(f"警告：無法將整個文件解析為標準 JSON 陣列 ({e})。嘗試逐個解析物件...")
            logs = []  # 重置 logs 列表
            malformed_json_count = 0

            # 備用策略：假設物件大致由換行符或 },{ 分隔
            # 移除外層的 [] (如果存在)
            if content.startswith('[') and content.endswith(']'):
                content = content[1:-1].strip()

            # 嘗試按 },{ 分割，然後清理並補全 {}
            potential_json_strings = []
            split_parts = content.split('},{')
            if len(split_parts) > 1:
                print(f"嘗試按 '}},{{' 分割，得到 {len(split_parts)} 部分。")
                for i, part in enumerate(split_parts):
                    part = part.strip()
                    if not part:
                        continue
                    if i == 0 and not part.startswith('{'):  # 第一部分
                        part = '{' + part
                    elif i == len(split_parts) - 1 and not part.endswith('}'):  # 最後一部分
                        part = part + '}'
                    elif i > 0 and i < len(split_parts) - 1:  # 中間部分
                        if not part.startswith('{'):
                            part = '{' + part
                        if not part.endswith('}'):
                            part = part + '}'
                    potential_json_strings.append(part)
            else:
                # 如果按 },{ 分割效果不好，嘗試按換行符分割
                print("嘗試按換行符分割...")
                lines = content.splitlines()
                current_obj_str = ""
                brace_level = 0
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    current_obj_str += line
                    brace_level += line.count('{')
                    brace_level -= line.count('}')
                    # 簡單地假設一個物件結束於大括號平衡且非零時
                    if brace_level == 0 and current_obj_str.startswith('{') and current_obj_str.endswith('}'):
                        potential_json_strings.append(current_obj_str)
                        current_obj_str = ""
                if current_obj_str:  # 添加最後一個未閉合的部分（可能不完整）
                    potential_json_strings.append(current_obj_str)

            print(f"找到 {len(potential_json_strings)} 個潛在的 JSON 物件字串進行解析。")

            for i, obj_str in enumerate(potential_json_strings):
                try:
                    # 再次嘗試清理，移除可能的結尾逗號
                    obj_str = obj_str.strip().rstrip(',')
                    if not (obj_str.startswith('{') and obj_str.endswith('}')):
                        malformed_json_count += 1
                        continue

                    log_entry = json.loads(obj_str)
                    logs.append(log_entry)
                except json.JSONDecodeError as e_inner:
                    malformed_json_count += 1
                    if malformed_json_count <= 20 or i % 100 == 0:
                        print(f"警告：無法解析第 {i+1} 個潛在 JSON 物件 - 錯誤：{e_inner}")
                    continue

    except FileNotFoundError:
        print(f"錯誤：找不到 JSON 檔案於 {filepath}")
        return {}
    except Exception as e:
        print(f"錯誤：讀取或處理檔案時發生意外錯誤 {filepath} - {e}")
        return {}

    if malformed_json_count > 0:
        print(f"警告：總共有 {malformed_json_count} 個潛在 JSON 物件無法解析。")

    print(f"成功解析了 {len(logs)} 條記錄。")

    processed_count = 0
    for log in logs:
        # 檢查 log 是否為字典
        if not isinstance(log, dict):
            continue

        prod_info = log.get('prod_info')

        # 檢查 prod_info 是否存在且為字典
        if not isinstance(prod_info, dict):
            continue

        prod_name = prod_info.get('ProdName')
        prod_price = prod_info.get('ProdPrice')
        prod_detail = prod_info.get('ProdDetail')
        tour_id = None
        if isinstance(prod_detail, dict):
            tour_id = prod_detail.get('TourID')
        if not tour_id:
            tour_id = prod_info.get('TourID')

        if (prod_name and
                isinstance(prod_name, str) and len(prod_name) >= 15 and
                prod_price is not None and
                tour_id and
                prod_name not in unique_products):
            unique_products[prod_name] = {
                'TourID': tour_id,
                'ProdName': prod_name
            }
            processed_count += 1

    print(f"處理完成，找到 {len(unique_products)} 個符合條件的唯一產品。")
    return unique_products


def find_image_url_unsplash_api(query, access_key):
    """使用 Unsplash API 搜尋圖片 URL。"""
    global API_REQUEST_COUNTER, API_LIMIT_RESET_TIME  # 允許修改全域變數

    # --- 速率限制檢查 ---
    current_time = datetime.datetime.now()
    if API_REQUEST_COUNTER >= API_REQUEST_LIMIT:
        if API_LIMIT_RESET_TIME is None or current_time >= API_LIMIT_RESET_TIME:
            wait_until = current_time + datetime.timedelta(seconds=API_WAIT_SECONDS)
            print(f"\n達到 Unsplash API 請求上限 ({API_REQUEST_LIMIT} 次)。")
            print(f"將暫停執行直到 {wait_until.strftime('%Y-%m-%d %H:%M:%S')} ({API_WAIT_SECONDS // 60} 分鐘 {API_WAIT_SECONDS % 60} 秒後)。")
            API_LIMIT_RESET_TIME = wait_until
            time.sleep(API_WAIT_SECONDS)
            print(f"等待結束，繼續執行...")
            API_REQUEST_COUNTER = 0
        else:
            remaining_wait = (API_LIMIT_RESET_TIME - current_time).total_seconds()
            if remaining_wait > 0:
                print(f"\n仍在 Unsplash API 請求冷卻期間，還需等待 {remaining_wait:.0f} 秒...")
                time.sleep(remaining_wait + 1)
                print("等待結束，繼續執行...")
                API_REQUEST_COUNTER = 0
            else:
                API_REQUEST_COUNTER = 0

    # --- 執行 API 請求 ---
    print(f"正在透過 Unsplash API 搜尋圖片：{query}")
    params = {
        'query': query,
        'per_page': 1,
        'orientation': 'landscape'
    }
    api_headers = {
        'Authorization': f'Client-ID {access_key}',
        'Accept-Version': 'v1'
    }

    try:
        response = requests.get(UNSPLASH_API_URL, headers=api_headers, params=params, timeout=15)
        API_REQUEST_COUNTER += 1
        print(f"  (API 請求計數: {API_REQUEST_COUNTER}/{API_REQUEST_LIMIT})")

        response.raise_for_status()

        data = response.json()

        if data['results'] and len(data['results']) > 0:
            urls = data['results'][0]['urls']
            image_url = urls.get('regular') or urls.get('small') or urls.get('thumb') or urls.get('raw')
            if image_url:
                print(f"  透過 API 找到 URL：{image_url[:60]}...")
                return image_url
            else:
                print(f"  警告：API 回應中未找到有效的圖片 URL。")
                return None
        else:
            print(f"  警告：API 未找到與 '{query}' 相關的圖片。")
            return None

    except requests.exceptions.Timeout:
        print(f"  錯誤：呼叫 Unsplash API 超時 '{query}'")
        return None
    except requests.exceptions.RequestException as e:
        print(f"  錯誤：呼叫 Unsplash API 時發生錯誤 '{query}': {e}")
        if e.response is not None:
            print(f"      狀態碼: {e.response.status_code}")
            try:
                print(f"      回應內容: {e.response.json()}")
            except json.JSONDecodeError:
                print(f"      回應內容: {e.response.text}")
        return None
    except Exception as e:
        print(f"  錯誤：處理 Unsplash API 回應時發生錯誤 '{query}': {e}")
        return None


def download_image(image_url, tour_id, save_dir):
    """從 URL 下載圖片並儲存。"""
    if not image_url:
        print("  錯誤：未提供 image_url。")
        return False

    safe_tour_id = re.sub(r'[\\/*?:"<>|]', "_", str(tour_id))
    safe_tour_id = safe_tour_id.strip('. ')
    if not safe_tour_id:
        safe_tour_id = f"invalid_tourid_{random.randint(1000,9999)}"

    filename = f"{safe_tour_id}.jpg"
    filepath = os.path.join(save_dir, filename)

    if os.path.exists(filepath):
        print(f"  跳過下載，檔案已存在：{filename}")
        return True

    print(f"  準備下載 TourID {safe_tour_id} 的圖片從 {image_url[:60]}...")
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
        print(f"  錯誤：下載圖片超時 TourID {safe_tour_id}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"  錯誤：下載圖片時發生錯誤 TourID {safe_tour_id}: {e}")
        if isinstance(e, requests.exceptions.HTTPError) and e.response.status_code == 403:
            print("      收到 403 Forbidden 錯誤，可能無法直接下載此圖片 URL。")
        return False
    except IOError as e:
        print(f"  錯誤：儲存圖片時發生 I/O 錯誤 TourID {safe_tour_id}: {e}")
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except OSError:
                pass
        return False
    except Exception as e:
        print(f"  儲存圖片時發生未知錯誤 TourID {safe_tour_id}: {e}")
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except OSError:
                pass
        return False


def main():
    """主函數，處理日誌並下載圖片。"""
    print("開始圖片下載程序...")
    unique_products = process_logs(JSON_FILE_PATH)

    if not unique_products:
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
    total_products = len(unique_products)

    product_list = list(unique_products.values())

    for i, product_data in enumerate(product_list):
        tour_id = product_data['TourID']
        prod_name = product_data['ProdName']

        print(f"\n處理產品 {i+1}/{total_products}: {prod_name} (TourID: {tour_id})")

        safe_tour_id = re.sub(r'[\\/*?:"<>|]', "_", str(tour_id))
        safe_tour_id = safe_tour_id.strip('. ')
        if not safe_tour_id:
            safe_tour_id = f"invalid_tourid_{random.randint(1000,9999)}"
        filename = f"{safe_tour_id}.jpg"
        filepath = os.path.join(IMAGE_OUTPUT_DIR, filename)
        if os.path.exists(filepath):
            print(f"  圖片已存在，跳過搜尋與下載：{filename}")
            download_count += 1
            continue

        image_url = find_image_url_unsplash_api(prod_name, UNSPLASH_ACCESS_KEY)

        if image_url:
            if download_image(image_url, tour_id, IMAGE_OUTPUT_DIR):
                download_count += 1
            else:
                failed_count += 1
        else:
            print(f"  未能為 TourID {tour_id} 找到圖片 URL。")
            failed_count += 1

        sleep_time = random.uniform(0.5, 1.5)
        time.sleep(sleep_time)

    print(f"\n程序完成。")
    print(f"總共處理 {total_products} 個唯一產品。")
    print(f"成功下載或已存在 {download_count} 張圖片。")
    print(f"未能下載 {failed_count} 張圖片。")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n偵測到使用者中斷 (KeyboardInterrupt)。正在結束程序...")
    except Exception as e:
        print(f"\n發生未預期的錯誤：{e}")
        import traceback
        traceback.print_exc()
