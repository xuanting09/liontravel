import tkinter as tk
from tkinter import ttk, messagebox
# from login_interface import LoginApp
import random  # 暫時用來生成模擬商品數據

class SearchApp:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("雄獅旅遊 推薦系統介面")
        self.window.geometry('1000x600')
        
        # 商品數據 - 稍後會從API或資料庫獲取，現在先用模擬數據
        self.all_products = []  # 用於保存所有原始產品數據
        self.products = []      # 用於顯示當前過濾後的產品
        self.current_page = 0
        self.products_per_page = 28  # 橫排4個，直排7個，共28個商品
        self.total_pages = 0
        
        self.create_search_interface()
        
    def create_search_interface(self):
        # 設定整體佈局
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 上方搜尋區域
        search_frame = ttk.Frame(main_frame)
        search_frame.pack(fill=tk.X, pady=10)
        
        # 搜尋欄位
        ttk.Label(search_frame, text="目的地搜尋:", font=('Helvetica', 12)).pack(side=tk.LEFT, padx=5)
        self.search_entry = ttk.Entry(search_frame, width=30, font=('Helvetica', 12))
        self.search_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 搜尋按鈕
        search_button = ttk.Button(search_frame, text="搜尋", command=self.search_products, 
                                  style='Search.TButton')
        search_button.pack(side=tk.LEFT, padx=5)
        
        # 顯示全部按鈕
        show_all_button = ttk.Button(search_frame, text="顯示全部", command=self.show_all_products, 
                                     style='Search.TButton')
        show_all_button.pack(side=tk.LEFT, padx=5)
        
        # 建立包含捲軸的商品展示區域容器
        products_container = ttk.Frame(main_frame)
        products_container.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 建立捲軸
        scrollbar = ttk.Scrollbar(products_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 建立Canvas以支援捲動
        self.canvas = tk.Canvas(products_container)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 連接捲軸和Canvas
        scrollbar.config(command=self.canvas.yview)
        self.canvas.config(yscrollcommand=scrollbar.set)
        
        # 建立內部框架用於放置商品
        self.products_frame = ttk.Frame(self.canvas)
        self.canvas_frame = self.canvas.create_window((0, 0), window=self.products_frame, anchor="nw")
        
        # 設定Canvas大小隨內容變化
        self.products_frame.bind("<Configure>", self.on_frame_configure)
        self.canvas.bind("<Configure>", self.on_canvas_configure)
        
        # 綁定滑鼠滾輪事件
        self.canvas.bind_all("<MouseWheel>", self.on_mousewheel)
        
        # 分頁控制區域
        pagination_frame = ttk.Frame(main_frame)
        pagination_frame.pack(fill=tk.X, pady=10)
        
        self.prev_button = ttk.Button(pagination_frame, text="上一頁", command=self.prev_page)
        self.prev_button.pack(side=tk.LEFT, padx=5)
        
        self.page_label = ttk.Label(pagination_frame, text="第 1 頁 / 共 1 頁", font=('Helvetica', 10))
        self.page_label.pack(side=tk.LEFT, padx=20)
        
        self.next_button = ttk.Button(pagination_frame, text="下一頁", command=self.next_page)
        self.next_button.pack(side=tk.LEFT, padx=5)
        
        # 設定樣式
        style = ttk.Style()
        style.configure('Search.TButton', font=('Helvetica', 12))
        style.configure('ProductCard.TFrame', background='#f0f0f0')
        style.configure('ProductTitle.TLabel', font=('Helvetica', 10, 'bold'))
        style.configure('ProductPrice.TLabel', font=('Helvetica', 10), foreground='#E77817')
        style.configure('ProductTag.TLabel', font=('Helvetica', 8), background='#E0E0E0', foreground='#555555')
        
        # 生成一些測試商品數據
        self.generate_test_products(100)  # 生成100個測試商品，跨越多頁
        
        # 顯示商品 (初始狀態顯示所有商品)
        self.show_all_products()
        
        self.window.mainloop()
    
    def on_frame_configure(self, event=None):
        """當內部frame大小改變時，更新canvas的捲動區域"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def on_canvas_configure(self, event=None):
        """當canvas大小改變時，調整內部frame的寬度"""
        self.canvas.itemconfig(self.canvas_frame, width=event.width)
    
    def on_mousewheel(self, event=None):
        """處理滑鼠滾輪事件"""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def generate_test_products(self, count):
        """生成測試商品數據"""
        destinations = ["日本東京", "韓國首爾", "泰國曼谷", "新加坡", "馬來西亞", "印尼峇里島", 
                       "美國紐約", "美國洛杉磯", "法國巴黎", "英國倫敦", "義大利羅馬", "澳洲雪梨",
                       "台北", "台中", "台南", "高雄", "花蓮", "宜蘭", "金門", "澎湖"]
        
        # 定義可能的標籤類型
        tags = ["促銷", "熱門", "親子", "自由行", "跟團", "機加酒", "美食", "購物", "文化", "海灘", "賞楓", "賞櫻"]
        
        for i in range(count):
            # 隨機選擇1-3個標籤
            product_tags = random.sample(tags, k=random.randint(1, 3))
            
            product = {
                "id": i + 1,
                "title": f"{random.choice(destinations)}自由行",
                "price": random.randint(10000, 50000),
                "days": random.randint(3, 10),
                "image": "default_image.jpg",  # 實際使用時替換成真實圖片路徑
                "tags": product_tags
            }
            self.all_products.append(product)
    
    def show_all_products(self):
        """顯示所有商品"""
        self.products = self.all_products.copy()  # 複製所有原始商品數據
        self.current_page = 0
        self.total_pages = (len(self.products) + self.products_per_page - 1) // self.products_per_page
        self.update_page_label()
        self.display_products()
        
    def display_products(self):
        """顯示當前頁的商品"""
        # 清除現有商品
        for widget in self.products_frame.winfo_children():
            widget.destroy()
        
        # 計算此頁要顯示的商品索引
        start_idx = self.current_page * self.products_per_page
        end_idx = min(start_idx + self.products_per_page, len(self.products))
        page_products = self.products[start_idx:end_idx]
        
        # 設定網格佈局 (4x7)
        for i in range(7):  # 7行
            self.products_frame.rowconfigure(i, weight=1)
        for i in range(4):  # 4列
            self.products_frame.columnconfigure(i, weight=1)
        
        # 顯示商品卡片
        for idx, product in enumerate(page_products):
            row = idx // 4
            col = idx % 4
            
            # 創建商品卡片
            card = ttk.Frame(self.products_frame, style='ProductCard.TFrame', relief=tk.RAISED, borderwidth=1)
            card.grid(row=row, column=col, padx=5, pady=5, sticky='nsew')
            
            # 圖片框 (實際應用中可以使用 PIL 顯示圖片)
            img_frame = ttk.Frame(card, width=200, height=120)
            img_frame.pack(fill=tk.X, padx=2, pady=2)
            img_placeholder = ttk.Label(img_frame, text="商品圖片", background='#cccccc')
            img_placeholder.place(relwidth=1, relheight=1)
            
            # 商品資訊區域
            info_frame = ttk.Frame(card)
            info_frame.pack(fill=tk.X, padx=5, pady=5)
            
            # 商品標題
            title_label = ttk.Label(info_frame, text=product["title"], style='ProductTitle.TLabel', wraplength=180)
            title_label.pack(anchor='w')
            
            # 標籤區域
            tags_frame = ttk.Frame(info_frame)
            tags_frame.pack(fill=tk.X, pady=3)
            
            # 顯示標籤
            for tag in product["tags"]:
                tag_label = ttk.Label(tags_frame, text=tag, style='ProductTag.TLabel', padding=(3, 0))
                tag_label.pack(side=tk.LEFT, padx=2)
                
                # 為標籤設置不同的背景顏色
                if tag == "促銷":
                    tag_label.configure(background="#FF6B6B", foreground="white")
                elif tag == "熱門":
                    tag_label.configure(background="#FFD166", foreground="black")
                elif tag == "親子":
                    tag_label.configure(background="#06D6A0", foreground="white")
                elif tag == "自由行":
                    tag_label.configure(background="#118AB2", foreground="white")
                elif tag == "跟團":
                    tag_label.configure(background="#073B4C", foreground="white")
            
            # 行程天數
            days_label = ttk.Label(info_frame, text=f"{product['days']}天", wraplength=180)
            days_label.pack(anchor='w')
            
            # 價格
            price_label = ttk.Label(info_frame, text=f"NT$ {product['price']:,}", style='ProductPrice.TLabel')
            price_label.pack(anchor='w')
            
            # 商品卡片點擊事件
            card.bind('<Button-1>', lambda e, p=product: self.show_product_details(p))
        
        # 更新Canvas的捲動區域
        self.on_frame_configure()
        
        # 更新分頁按鈕狀態
        self.prev_button["state"] = "disabled" if self.current_page == 0 else "normal"
        self.next_button["state"] = "disabled" if self.current_page >= self.total_pages - 1 else "normal"
    
    def prev_page(self):
        """顯示上一頁商品"""
        if self.current_page > 0:
            self.current_page -= 1
            self.update_page_label()
            self.display_products()
    
    def next_page(self):
        """顯示下一頁商品"""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.update_page_label()
            self.display_products()
    
    def update_page_label(self):
        """更新頁碼標籤"""
        self.page_label.config(text=f"第 {self.current_page + 1} 頁 / 共 {self.total_pages} 頁")
    
    def search_products(self):
        """根據搜尋條件過濾商品"""
        search_term = self.search_entry.get().lower()
        
        if not search_term:
            messagebox.showinfo("提示", "請輸入搜尋條件！")
            return
        
        # 從所有商品中過濾符合條件的商品
        filtered_products = []
        for product in self.all_products:
            if search_term in product["title"].lower():
                filtered_products.append(product)
        
        if not filtered_products:
            messagebox.showinfo("搜尋結果", "沒有找到符合條件的商品！")
            return
        
        # 更新商品列表並顯示結果
        self.products = filtered_products
        self.current_page = 0
        self.total_pages = (len(self.products) + self.products_per_page - 1) // self.products_per_page
        self.update_page_label()
        self.display_products()
    
    def show_product_details(self, product):
        """顯示商品詳細資訊"""
        # 在實際應用中，會跳到商品詳情頁或彈出詳情視窗
        tags_text = ", ".join(product["tags"])
        
        messagebox.showinfo("商品詳情", 
                           f"商品ID: {product['id']}\n"
                           f"商品名稱: {product['title']}\n"
                           f"價格: NT$ {product['price']:,}\n"
                           f"行程天數: {product['days']}天\n"
                           f"標籤: {tags_text}")

def start_app():
    app = SearchApp()

if __name__ == "__main__":
    # 直接啟動搜尋介面，不需要登入
    start_app()
    # 啟動登入介面，成功登入後啟動主應用程式
    # LoginApp(on_successful_login=start_app)