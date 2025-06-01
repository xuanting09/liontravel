// ---------------------------------------------
// 1. alias_map（簡寫對應地點）
// ---------------------------------------------
const alias_map = {
  "德瑞": ["德國", "瑞士"],
  "新馬": ["新加坡", "馬來西亞"],
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
  "荷比法": ["荷蘭", "比利時", "法國"],
  "義瑞德": ["義大利", "瑞士", "德國"],
  "義瑞德法": ["義大利", "瑞士", "德國", "法國"]
};

// ---------------------------------------------
// 2. tags_dict（活動分類對應關鍵字）
//    只把「分類名稱」（key）當建議候選項
// ---------------------------------------------
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

// ---------------------------------------------
// 3. 全域變數
// ---------------------------------------------
let knownLocationKeywords = [];       // 扁平化後的地點關鍵字清單
let existingProducts = [];            // CSV 中所有「產品名稱」
let existingProductInfo = {};         // { name: { id, isForeign, price, activityType, locationSpot, locTags, actTags } }
let lastExtractedName = "";           // 當前操作的「產品名稱」

// ---------------------------------------------
// 4. 讀取 JSON 並扁平化 locationKeywords（新版）
// ---------------------------------------------
function flattenLocations(obj, collectorSet) {
  if (Array.isArray(obj)) {
    obj.forEach(item => {
      if (typeof item === 'string' && item.trim()) {
        collectorSet.add(item.trim());
      }
    });
  } else if (typeof obj === "object" && obj !== null) {
    Object.entries(obj).forEach(([key, value]) => {
      if (typeof key === "string" && key.trim()) {
        collectorSet.add(key.trim());
      }
      flattenLocations(value, collectorSet);
    });
  } else if (typeof obj === 'string' && obj.trim()) {
    collectorSet.add(obj.trim());
  }
}

async function loadLocationJSON() {
  try {
    console.log("🔄 開始載入地點 JSON...");
    
    const resp = await fetch("updated_international_location_tags.json");
    if (!resp.ok) {
      throw new Error(`HTTP錯誤: ${resp.status} ${resp.statusText}`);
    }
    const text = await resp.text();
    let jsonData;
    try {
      jsonData = JSON.parse(text);
    } catch (parseError) {
      console.error("❌ JSON 解析錯誤:", parseError);
      throw new Error("JSON 格式錯誤: " + parseError.message);
    }
    
    const locationSet = new Set();
    flattenLocations(jsonData, locationSet);
    knownLocationKeywords = Array.from(locationSet).sort();
    console.log("✅ 成功載入並扁平化地點關鍵字，共", knownLocationKeywords.length, "個");
    
    // 將地點關鍵字塞進 datalist 
    const locDatalist = document.getElementById("locationList");
    if (locDatalist) {
      locDatalist.innerHTML = "";
      knownLocationKeywords.forEach(loc => {
        const option = document.createElement("option");
        option.value = loc;
        locDatalist.appendChild(option);
      });
    } else {
      console.warn("⚠️ 找不到 locationList datalist 元素");
    }

  } catch (err) {
    console.error("❌ 讀取地點 JSON 失敗：", err);
    showMessage("讀取地點 JSON 失敗：" + err.message, "error");
    
    // 如果讀不到 JSON，就用這些備用地點
    knownLocationKeywords = [
      "杜拜", "帆船酒店", "哈里發塔", "七星帆船", "六星亞特蘭提斯", 
      "東京", "橫濱", "箱根", "鎌倉", "群馬", "大阪", "京都", "神戶"
    ].sort();
  }
}

// ---------------------------------------------
// 5. 讀取 產品資料.csv（支援 3 欄或 8 欄）
// ---------------------------------------------
async function loadProductCSV() {
  try {
    const resp = await fetch("產品資料.csv");
    if (!resp.ok) throw new Error("無法讀取 CSV：" + resp.status);
    const text = await resp.text();
    const lines = text.split("\n").filter(line => line.trim() !== "");
    if (lines.length <= 1) return;

    lines.slice(1).forEach(line => {
      const cells = line.split(",");
      if (cells.length >= 8) {
        // 8 欄格式：0:id,1:name,2:isForeign,3:price,4:activityType,5:locationSpot,6:locTags,7:actTags
        const _id = cells[0].trim();
        const name = cells[1].trim();
        const isForeign = cells[2].trim();
        const price = cells[3].trim();
        const activityType = cells[4].trim();
        const locationSpot = cells[5].trim();
        let rawLoc = cells[6].trim().replace(/^"(.*)"$/, "$1");
        let rawAct = cells[7].trim().replace(/^"(.*)"$/, "$1");
        const locTags = rawLoc ? rawLoc.split(",").map(x => x.trim()).filter(x => x) : [];
        const actTags = rawAct ? rawAct.split(",").map(x => x.trim()).filter(x => x) : [];

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
        // 3 欄格式：0:name,1:locTags,2:actTags
        const name = cells[0].trim();
        let rawLoc = cells[1].trim().replace(/^"(.*)"$/, "$1");
        let rawAct = cells[2].trim().replace(/^"(.*)"$/, "$1");
        const locTags = rawLoc ? rawLoc.split(",").map(x => x.trim()).filter(x => x) : [];
        const actTags = rawAct ? rawAct.split(",").map(x => x.trim()).filter(x => x) : [];

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
    console.log("已載入現有商品，共", existingProducts.length, "筆");
  } catch (err) {
    console.error("讀取產品 CSV 失敗：", err);
    showMessage("讀取產品 CSV 失敗：" + err.message, "error");
  }
}

// ---------------------------------------------
// 6. 顯示／清除訊息
// ---------------------------------------------
function showMessage(text, type = "success") {
  const msgDiv = document.getElementById("message");
  if (msgDiv) {
    msgDiv.textContent = text;
    msgDiv.className = "";
    msgDiv.classList.add(type);
    msgDiv.style.display = "block";
  }
}
function clearMessage() {
  const msgDiv = document.getElementById("message");
  if (msgDiv) {
    msgDiv.style.display = "none";
    msgDiv.textContent = "";
    msgDiv.className = "";
  }
}

// ---------------------------------------------
// 7. 擷取地點標籤（含 alias_map + 已扁平化關鍵字）
// ---------------------------------------------
function extractLocationTags(productName) {
  const found = new Set();
  const lowerName = productName.toLowerCase();

  // 先處理 alias_map
  Object.entries(alias_map).forEach(([aliasKey, expandedArray]) => {
    if (lowerName.includes(aliasKey.toLowerCase())) {
      expandedArray.forEach(expanded => found.add(expanded));
    }
  });

  // 再比對 knownLocationKeywords
  knownLocationKeywords.forEach(loc => {
    if (lowerName.includes(loc.toLowerCase())) {
      found.add(loc);
    }
  });

  return Array.from(found);
}

// ---------------------------------------------
// 8. 擷取活動標籤（回傳「分類名稱」）
// ---------------------------------------------
function extractActivityTags(productName) {
  const foundTags = [];
  const lowerName = productName.toLowerCase();

  Object.entries(tags_dict).forEach(([category, keywords]) => {
    for (const kw of keywords) {
      if (lowerName.includes(kw.toLowerCase())) {
        foundTags.push(category);
        break; // 同一分類只取一次
      }
    }
  });

  return foundTags;
}

// ---------------------------------------------
// 9. 點擊「擷取標籤」按鈕
// ---------------------------------------------
document.getElementById("extractBtn").addEventListener("click", () => {
  clearMessage();

  const inputID    = document.getElementById("productID").value.trim();
  const inputName  = document.getElementById("prodName").value.trim();
  const isForeign  = document.getElementById("isForeign").checked ? "True" : "False";
  const price      = document.getElementById("price").value.trim();

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
    // 對已存在產品，直接回帶舊的 locTags + actTags
    existingInfo = existingProductInfo[inputName];
    locTags = existingInfo.locTags || [];
    actTags = existingInfo.actTags || [];
  } else {
    // 新商品：以 AI 演算法自動擷取
    locTags = extractLocationTags(inputName); // e.g. ["馬六甲", "荷蘭紅屋", ...]
    actTags = extractActivityTags(inputName); // e.g. ["文化歷史", "美食", ...]
  }

  // ---------------------------------------------------
  // 9.1 活動標籤：去重後用 ", " 串起，填到 #activityTypeInput
  // ---------------------------------------------------
  const actCombined = [...new Set(actTags)]; // 去重
  document.getElementById("activityTypeInput").value = actCombined.join(", ");

  // ---------------------------------------------------
  // 9.2 地點標籤：去重後用 ", " 串起，填到 #locationSpotInput
  // ---------------------------------------------------
  const locCombined = [...new Set(locTags)]; // 去重
  document.getElementById("locationSpotInput").value = locCombined.join(", ");

  // ---------------------------------------------------
  // 9.3 顯示「已存在 / 新商品」提示 & 控制「複製 CSV 列」按鈕
  // ---------------------------------------------------
  const existMsgEl = document.getElementById("existMessage");
  const copyBtn    = document.getElementById("copyBtn");
  const copyMsg    = document.getElementById("copyMsg");

  if (isExisting) {
    if (existMsgEl) {
      existMsgEl.textContent =
        "⚠️ 此產品已存在於 產品資料.csv 中，已自動帶入先前的「活動類型」＆「地點／景點」。若需修改，請直接於下方欄位自行編輯，並自行更新 CSV。";
      existMsgEl.style.color = "#c62828";
    }
    if (copyBtn) copyBtn.style.display = "none";
    if (copyMsg) copyMsg.style.display = "none";
  } else {
    if (existMsgEl) {
      existMsgEl.textContent =
        "✅ 新商品！已以 AI 演算法擷取「活動類型」＆「地點／景點」。若標籤不足，可直接修改或新增，使用「,」分隔多筆。確認無誤後，點「複製 CSV 列」加入 CSV。";
      existMsgEl.style.color = "#2e7d32";
    }
    if (copyBtn) copyBtn.style.display = "inline-block";
    if (copyMsg) copyMsg.style.display = "none";
  }

  const resultDiv = document.getElementById("result");
  if (resultDiv) {
    resultDiv.style.display = "block";
  }

  showMessage(`已擷取標籤：地點 ${locCombined.length} 個，活動 ${actCombined.length} 個`, "success");
});

// ---------------------------------------------
// 10. 「複製 CSV 列」按鈕事件
//     → 產生 7 欄：產品編號, 產品名稱, 是否為國外產品, 價格, 活動類型, 地點/景點, 標籤
// ---------------------------------------------
document.getElementById("copyBtn").addEventListener("click", () => {
  const inputID   = document.getElementById("productID").value.trim();
  const inputName = document.getElementById("prodName").value.trim();
  const isForeign = document.getElementById("isForeign").checked ? "True" : "False";
  const price     = document.getElementById("price").value.trim();

  // 1) 拆解「活動類型」欄位
  const actRaw = document.getElementById("activityTypeInput").value.trim();
  const activityTypeList = actRaw
    ? actRaw.split(",").map(x => x.trim()).filter(x => x)
    : [];
  // 組成 CSV 格式：以逗號分隔，並用雙引號包起來
  const activityTypeCSV = activityTypeList.length > 0
    ? `"${activityTypeList.join(", ")}"`
    : `""`;

  // 2) 拆解「地點/景點」欄位
  const locRaw = document.getElementById("locationSpotInput").value.trim();
  const locationSpotList = locRaw
    ? locRaw.split(",").map(x => x.trim()).filter(x => x)
    : [];
  const locationSpotCSV = locationSpotList.length > 0
    ? `"${locationSpotList.join(", ")}"`
    : `""`;

  // 3) 組出「標籤」欄位：合併地點+活動標籤，用逗號分隔
  const allTagsArray = [...locationSpotList, ...activityTypeList];
  const uniqueTagsArray = [...new Set(allTagsArray)];
  const tagsCSV = uniqueTagsArray.length > 0
    ? `"${uniqueTagsArray.join(", ")}"`
    : `""`;

  // 組成最終 7 欄 CSV（各欄之間用逗號分隔）：
  // 1. 產品編號, 2. 產品名稱, 3. 是否為國外產品, 4. 價格,
  // 5. 活動類型, 6. 地點/景點, 7. 標籤
  const csvLine = [
    inputID,
    inputName,
    isForeign,
    price,
    activityTypeCSV,
    locationSpotCSV,
    tagsCSV
  ].join(",");

  // 複製到剪貼簿
  navigator.clipboard.writeText(csvLine).then(() => {
    const copyMsg = document.getElementById("copyMsg");
    if (copyMsg) {
      copyMsg.textContent = "✅ 已複製到剪貼簿！請貼回 CSV。";
      copyMsg.style.display = "block";
      copyMsg.style.color = "#2e7d32";
    }
    showMessage("CSV 行已複製到剪貼簿！", "success");
  }).catch(err => {
    console.error("複製到剪貼簿失敗：", err);
    showMessage("📋 複製失敗，請手動複製。CSV 行：" + csvLine, "error");
  });
});

// ---------------------------------------------
// 11. 清空表單按鈕
// ---------------------------------------------
function addClearFormButton() {
  const clearBtn = document.getElementById("clearBtn");
  if (clearBtn) {
    clearBtn.addEventListener("click", () => {
      // 清空所有輸入欄位
      document.getElementById("productID").value = "";
      document.getElementById("prodName").value = "";
      document.getElementById("isForeign").checked = false;
      document.getElementById("price").value = "";
      document.getElementById("activityTypeInput").value = "";
      document.getElementById("locationSpotInput").value = "";

      // 隱藏結果區域
      const resultDiv = document.getElementById("result");
      if (resultDiv) {
        resultDiv.style.display = "none";
      }

      // 清除訊息
      clearMessage();

      // 清除複製訊息
      const copyMsg = document.getElementById("copyMsg");
      if (copyMsg) {
        copyMsg.style.display = "none";
      }

      lastExtractedName = "";
    });
  }
}

// ---------------------------------------------
// 12. 初始化：載入 JSON + CSV，並把 tags_dict key 填入 <datalist id="activityList">
// ---------------------------------------------
window.addEventListener("load", () => {
  // 載入地點 JSON
  loadLocationJSON();
  // 載入現有產品 CSV
  loadProductCSV();

  // 把 tags_dict 的分類名稱填入 activityList (autocomplete)
  const actDatalist = document.getElementById("activityList");
  if (actDatalist) {
    actDatalist.innerHTML = "";
    Object.keys(tags_dict).forEach(category => {
      const option = document.createElement("option");
      option.value = category;
      actDatalist.appendChild(option);
    });
  }

  // 綁定「清空表單」按鈕
  addClearFormButton();
});
