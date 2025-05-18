// 更新數據函數
function updateCounters() {
    // 模擬數據獲取，實際使用時可以從API獲取數據
    document.getElementById('visitors-count').textContent = '1245';
    document.getElementById('orders-count').textContent = '368';
    document.getElementById('revenue-amount').textContent = '8765432';
}

// 初始化圖表
function initCharts() {
    // 水平長條圖
    const barCtx = document.getElementById('barChart').getContext('2d');
    const barChart = new Chart(barCtx, {
        type: 'bar',
        data: {
            labels: ['AAA', 'BBB', 'CCC', 'DDD', 'EEE'],
            datasets: [{
                label: '數據值',
                data: [150, 220, 100, 280, 400],
                backgroundColor: '#7986cb'
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    grid: {
                        color: '#e0e0e0'
                    }
                },
                y: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });

    // 圓餅圖
    const pieCtx = document.getElementById('pieChart').getContext('2d');
    const pieChart = new Chart(pieCtx, {
        type: 'pie',
        data: {
            labels: ['區域A', '區域B', '區域C', '區域D'],
            datasets: [{
                data: [35, 25, 20, 20],
                backgroundColor: ['#7986cb', '#4fc3f7', '#ff8a80', '#ffb74d']
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });

    // 比較長條圖
    const compareCtx = document.getElementById('compareChart').getContext('2d');
    const compareChart = new Chart(compareCtx, {
        type: 'bar',
        data: {
            labels: ['AAA', 'BBB', 'CCC', 'EEE', 'DDD', 'FFF', 'GGG'],
            datasets: [
                {
                    label: '類別A',
                    data: [170, 130, 200, 220, 180, 100, 30],
                    backgroundColor: '#7986cb'
                },
                {
                    label: '類別B',
                    data: [150, 80, 120, 200, 250, 180, 80],
                    backgroundColor: '#ff8a80'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: '#e0e0e0'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

// 模擬從API獲取數據
function fetchDataFromAPI() {
    // 這裡可以添加實際的API調用
    console.log('從API獲取數據...');
    // 模擬API延遲
    setTimeout(() => {
        updateCounters();
        console.log('數據更新完成');
    }, 500);
}

// 頁面加載完成後執行
window.addEventListener('load', function() {
    fetchDataFromAPI();
    initCharts();
});

// 模擬導航點擊事件
document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', function() {
        document.querySelector('.active').classList.remove('active');
        this.classList.add('active');
        // 這裡可以添加頁面切換邏輯
        console.log('切換到: ' + this.textContent);
    });
});