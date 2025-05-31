// 1. alias_map 定義（簡寫對應）
const alias_map = {
  "德瑞": ["德國", "瑞士"],
  "京板": ["京都", "大阪"],
  "京阪神": ["京都", "大阪", "神戶"],
  "德法": ["德國", "法國"],
  "德法瑞": ["德國", "法國", "瑞士"],
  "德瑞法": ["德國", "瑞士", "法國"],
  "德法義": ["德國", "法國", "義大利"],
  "德義": ["德國", "義大利"],
  "義瑞": ["義大利", "瑞士"],
  "義法": ["義大利", "法國"],
  "義瑞法": ["義大利", "瑞士", "法國"],
  "義德": ["義大利", "德國"],
  "義德瑞": ["義大利", "德國", "瑞士"],
  "義德法": ["義大利", "德國", "法國"],
  "義德瑞法": ["義大利", "德國", "瑞士", "法國"],
  "義瑞法": ["義大利", "瑞士", "法國"],
  "義瑞德": ["義大利", "瑞士", "德國"],
  "義瑞德法": ["義大利", "瑞士", "德國", "法國"]
};

// 2. tags_dict 定義（活動分類對應關鍵詞），其中「文化歷史」已依要求新增 "大社"、"院" 等字串
const tags_dict = {
  "主題樂園": ["環球影城", "迪士尼", "樂園", "遊樂園"],
  "自然景觀": ["峽灣", "森林", "湖", "溫泉", "瀑布", "山", "海灘", "草原", "自然", "極光", "星空", "雲海", "楓", "櫻", "櫻花", "楓葉", "觀景", "落羽松"],
  "文化歷史": ["博物館", "神社", "寺", "古城", "遺跡", "文化", "大社", "院", "歷史", "古蹟", "宮殿", "皇宮", "教堂", "城堡", "古老", "古代", "古文明", "古文物", "祭典", "世界遺產"],
  "美食": ["螃蟹", "美食", "饗宴", "餐廳", "料理", "海鮮", "燒肉", "壽司", "拉麵", "咖哩", "甜點"],
  "購物": ["購物", "市場", "商場", "百貨"],
  "親子旅遊": ["親子", "動物園", "兒童", "家庭", "水族館"],
  "豪華": ["五星", "高級", "豪華", "度假", "渡假"],
  "海島旅遊": ["海灘", "潛水", "島", "度假村", "海島", "海洋", "浮潛", "海底"],
  "雪景": ["滑雪", "冰川", "極光", "雪景", "戲雪", "冰上活動"],
  "火車旅遊": ["火車", "列車", "鐵道"],
  "溫泉之旅": ["溫泉", "溫泉鄉", "溫泉區", "溫泉街"],
  "藝文體驗": ["音樂會", "表演", "劇場", "歌劇", "美術館", "藝文", "展覽", "藝術"],
  "戶外活動": ["登山", "健行", "露營", "野餐", "攀岩", "滑索", "泛舟", "獨木舟"],
  "網美打卡": ["打卡", "網美", "IG", "拍照", "玻璃屋", "天空之鏡"],
  "婚禮蜜月": ["蜜月", "婚禮", "情侶", "戀人", "浪漫", "紀念日"],
  "夜間活動": ["夜景", "夜市", "夜生活", "燈光秀", "夜拍", "夜遊"]
};

// 3. 全域變數：扁平化後的地點關鍵詞、CSV 中既有商品資訊
let knownLocationKeywords = [];       // 來自 JSON 扁平化後的所有地點字串
let existingProducts = [];            // CSV 中所有「產品名稱」
let existingProductInfo = {};         // 存放 { 產品名稱: { id, isForeign, price, activityType, locationSpot, locTags:[...], actTags:[...] } }
let lastExtractedName = "";           // 當前操作的產品名稱

// 4. 讀取 JSON 並扁平化 location keywords
function flattenLocations(obj, collectorSet) {
  if (Array.isArray(obj)) {
    obj.forEach(item => collectorSet.add(item));
  } else if (typeof obj === "object" && obj !== null) {
    Object.values(obj).forEach(child => flattenLocations(child, collectorSet));
  }
}

async function loadLocationJSON() {
  try {
    // 若 updated_international_location_tags.json 位於同一層，直接 fetch("updated_international_location_tags.json")
    // 若它在 ProductRecommendations 資料夾，請改成："ProductRecommendations/updated_international_location_tags.json"
    const resp = await fetch("updated_international_location_tags.json");
    if (!resp.ok) throw new Error("無法讀取 JSON：" + resp.status);
    const jsonData = await resp.json();
    const s = new Set();
    flattenLocations(jsonData, s);
    knownLocationKeywords = Array.from(s);
    console.log("已載入並扁平化地點關鍵詞，共 " + knownLocationKeywords.length + " 個。");
  } catch (err) {
    console.error(err);
    showMessage("讀取地點 JSON 失敗：" + err.message, "error");
  }
}

// 5. 讀取 產品資料.csv，支援新版（8 欄）或舊版（3 欄）
async function loadProductCSV() {
  try {
    // 若 產品資料.csv 位於同一層，就直接 fetch("產品資料.csv")
    // 若在 ProductRecommendations 資料夾，請用 fetch("ProductRecommendations/產品資料.csv")
    const resp = await fetch("產品資料.csv");
    if (!resp.ok) throw new Error("無法讀取 CSV：" + resp.status);
    const text = await resp.text();
    const lines = text.split("\n").filter(line => line.trim() !== "");
    if (lines.length <= 1) {
      console.warn("CSV 只有表頭或無其他資料。");
      return;
    }
    lines.slice(1).forEach(line => {
      const cells = line.split(",");
      if (cells.length >= 8) {
        // 新版：8欄：0:id,1:name,2:isForeign,3:price,4:activityType,5:locationSpot,6:locTags,7:actTags
        const _id = cells[0].trim();
        const name = cells[1].trim();
        const isForeign = cells[2].trim();
        const price = cells[3].trim();
        const activityType = cells[4].trim();
        const locationSpot = cells[5].trim();

        // 先去掉左右成對的引號，再拆 ";"
        let rawLoc = cells[6].trim().replace(/^"(.*)"$/, "$1");
        let rawAct = cells[7].trim().replace(/^"(.*)"$/, "$1");
        const locTags = rawLoc
          .split(";")
          .map(x => x.trim())
          .filter(x => x);
        const actTags = rawAct
          .split(";")
          .map(x => x.trim())
          .filter(x => x);

        if (name) {
          existingProducts.push(name);
          existingProductInfo[name] = {
            id: _id,
            isForeign: isForeign,
            price: price,
            activityType: activityType,
            locationSpot: locationSpot,
            locTags: locTags,
            actTags: actTags
          };
        }
      } else if (cells.length >= 3) {
        // 舊版：3欄：0:name,1:locTags,2:actTags
        const name = cells[0].trim();

        let rawLoc = cells[1].trim().replace(/^"(.*)"$/, "$1");
        let rawAct = cells[2].trim().replace(/^"(.*)"$/, "$1");
        const locTags = rawLoc
          .split(";")
          .map(x => x.trim())
          .filter(x => x);
        const actTags = rawAct
          .split(";")
          .map(x => x.trim())
          .filter(x => x);

        if (name) {
          existingProducts.push(name);
          existingProductInfo[name] = {
            id: "",
            isForeign: "",
            price: "",
            activityType: "",
            locationSpot: "",
            locTags: locTags,
            actTags: actTags
          };
        }
      } else {
        console.warn("跳過無法辨識的 CSV 行：", line);
      }
    });
    console.log("已載入現有商品，共 " + existingProducts.length + " 筆。");
  } catch (err) {
    console.error(err);
    showMessage("讀取產品 CSV 失敗：" + err.message, "error");
  }
}

// 6. 顯示／清除訊息
function showMessage(text, type = "success") {
  const msgDiv = document.getElementById("message");
  msgDiv.textContent = text;
  msgDiv.className = "";
  msgDiv.classList.add(type);
  msgDiv.style.display = "block";
}
function clearMessage() {
  const msgDiv = document.getElementById("message");
  msgDiv.style.display = "none";
  msgDiv.textContent = "";
  msgDiv.className = "";
}

// 7. 擷取地點標籤（包含 alias_map 處理）
function extractLocationTags(productName) {
  const found = new Set();
  // 處理 alias_map
  Object.keys(alias_map).forEach(aliasKey => {
    if (productName.includes(aliasKey)) {
      alias_map[aliasKey].forEach(expanded => found.add(expanded));
    }
  });
  // 用扁平化後的 knownLocationKeywords 比對
  knownLocationKeywords.forEach(loc => {
    if (productName.includes(loc)) {
      found.add(loc);
    }
  });
  return Array.from(found);
}

// 8. 擷取活動標籤
function extractActivityTags(productName) {
  const foundTags = [];
  Object.entries(tags_dict).forEach(([category, keywords]) => {
    for (const kw of keywords) {
      if (productName.includes(kw)) {
        foundTags.push(category);
        break;
      }
    }
  });
  return foundTags;
}

// 9. 按下「擷取標籤」按鈕
document.getElementById("extractBtn").addEventListener("click", () => {
  clearMessage();
  // 先取所有欄位值
  const inputID = document.getElementById("productID").value.trim();
  const inputName = document.getElementById("prodName").value.trim();
  const isForeign = document.getElementById("isForeign").checked ? "Y" : "N";
  const price = document.getElementById("price").value.trim();
  // 下方兩行留給使用者自行編輯，不要覆蓋：
  // const activityType = document.getElementById("activityType").value.trim();
  // const locationSpot = document.getElementById("locationSpot").value.trim();

  if (!inputName) {
    showMessage("請先輸入產品名稱。", "error");
    return;
  }
  lastExtractedName = inputName;

  const isExisting = existingProducts.includes(inputName);
  let locTags = [];
  let actTags = [];
  let existingInfo = null;

  if (isExisting) {
    // CSV 裡已有：只把「地點標籤」和「活動標籤」帶入
    existingInfo = existingProductInfo[inputName];
    locTags = existingInfo.locTags || [];
    actTags = existingInfo.actTags || [];
    // 千萬不要自動填 activityType、locationSpot，保留使用者原本輸入
    // document.getElementById("activityType").value = existingInfo.activityType || "";
    // document.getElementById("locationSpot").value = existingInfo.locationSpot || "";
  } else {
    // 新商品：使用者自己填的 activityType、locationSpot 原樣保留
    locTags = extractLocationTags(inputName);
    actTags = extractActivityTags(inputName);
  }

  // 9.1 顯示標籤到下方可編輯區，分號分隔
  document.getElementById("locationTags").textContent =
    locTags.length > 0 ? locTags.join("; ") : "";
  document.getElementById("activityTags").textContent =
    actTags.length > 0 ? actTags.join("; ") : "";

  // 9.2 顯示「新商品 / 已存在」訊息，並控制「複製 CSV 列」按鈕
  const existMsgEl = document.getElementById("existMessage");
  const copyBtn = document.getElementById("copyBtn");
  const copyMsg = document.getElementById("copyMsg");

  if (isExisting) {
    existMsgEl.textContent =
      "⚠️ 此產品已存在於 產品資料.csv 中，已自動帶入「地點標籤」「活動標籤」。若需修改，請自行到 CSV 編輯該筆。";
    existMsgEl.style.color = "#c62828";
    copyBtn.style.display = "none"; // 已存在就不需要複製新增
    copyMsg.style.display = "none";
  } else {
    existMsgEl.textContent =
      "✅ 新商品！系統自動擷取標籤，若有誤可在上方直接編輯各欄位後，再點「複製 CSV 列」加入 CSV。";
    existMsgEl.style.color = "#2e7d32";
    copyBtn.style.display = "inline-block"; // 顯示「複製 CSV 列」按鈕
    copyMsg.style.display = "none"; // 重置複製提示
  }

  document.getElementById("result").style.display = "block";
});

// 10. 「複製 CSV 列」按鈕事件：組出完整 8 欄並複製到剪貼簿
document.getElementById("copyBtn").addEventListener("click", () => {
  // 先讀取使用者在 UI 上所有欄位 (編輯後的結果)
  const inputID = document.getElementById("productID").value.trim();
  const inputName = document.getElementById("prodName").value.trim();
  const isForeign = document.getElementById("isForeign").checked ? "Y" : "N";
  const price = document.getElementById("price").value.trim();
  const activityType = document.getElementById("activityType").value.trim();
  const locationSpot = document.getElementById("locationSpot").value.trim();
  // 讀取可編輯的標籤 (textContent)
  let locText = document.getElementById("locationTags").textContent.trim();
  let actText = document.getElementById("activityTags").textContent.trim();
  // 如果使用者把其中一欄留空，則給空字串
  locText = locText || "";
  actText = actText || "";
  // 組出 CSV 八欄：
  // 1.ID, 2.名稱, 3.是否國外, 4.價格, 5.活動類型, 6.地點景點, 7.地點標籤, 8.活動標籤
  const csvLine = `${inputID},${inputName},${isForeign},${price},${activityType},${locationSpot},${locText},${actText}`;
  // 複製到剪貼簿
  navigator.clipboard.writeText(csvLine).then(() => {
    const copyMsg = document.getElementById("copyMsg");
    copyMsg.textContent = "✅ 已複製到剪貼簿！請貼至 CSV。";
    copyMsg.style.display = "block";
  }).catch(err => {
    console.error("複製到剪貼簿失敗：", err);
    showMessage("📋 複製失敗，請手動複製上述文字。", "error");
  });
});

// 11. 頁面載入時先讀取 JSON 和 CSV
window.addEventListener("load", () => {
  loadLocationJSON();
  loadProductCSV();
});
