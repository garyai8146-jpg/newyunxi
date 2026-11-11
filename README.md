# 雲熙驗單打包助手｜讓掃碼、算重、分包在同一個畫面完成

工廠出貨時，要先確認訂單裡有哪些板件、掃描它們的條碼，再看怎麼分包比較合適。問題是這幾件事通常分開做：訂單在 XML、重量要算、包裝上限會變，現場還要一直確認有沒有掃錯或重複掃描。

我做了這個 Windows 桌面工具，讓現場人員不用一直切換資料和計算方式。

**[回到面試作品集](https://github.com/garyai8146-jpg/Yihop_LineBOT/blob/main/PORTFOLIO.md)**

## 可以做什麼

- 匯入既有雲熙格式的 XML 訂單，整理板件與條碼資料。
- 根據長、寬、厚度與板材密度估算重量，也支援特定厚度的密度設定。
- 按單包重量上限依序分包；修改上限後可以重新分配。
- 配合 USB 條碼掃描槍（鍵盤輸入模式）核對板件與進度。
- 在支援的 Windows 環境用語音提醒掃碼結果，並保存作業狀態。

## 程式怎麼分工

`main.py` 管畫面與掃碼操作，`calculator.py` 負責重量及分包規則，`data_manager.py` 處理 XML 與設定檔。把核心計算從介面分開，未來要調整包裝規則就比較容易測試。

使用 Python、Tkinter、XML、threading，以及選用的 pyttsx3 語音功能。

## Windows 執行

```powershell
python -m pip install -r requirements.txt
python main.py
```

如果只想先確認核心演算法，不需要掃描槍或真實訂單，可執行離線單元測試：

```powershell
python -m unittest discover -s tests -v
```

## 我最想分享的地方

這個專案不是把一個新的流程硬套進工廠，而是讓程式配合**已經在使用的訂單格式和掃碼設備**。重量估算需要處理單位、密度和厚度設定；分包採用速度較快、容易解釋的貪婪策略，不保證找到全域最少包數。

GitHub Actions 會檢查 Python 語法、重量計算、分包與樣本 XML 解析。實際掃描槍、語音驅動與不同來源的 XML 仍需在對應 Windows 環境驗證；工具不取代實體包材承重或出貨安全檢查。
