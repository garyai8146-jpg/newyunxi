# 📦 雲熙驗單打包助手 (Yunxi Weight Calculator) - 重構優化版

## 🎯 專案背景與開發動機
本專案開發初衷是為了解決原廠「雲熙軟體」在生產線作業中的功能缺失與停止維護問題。在實際的木工廠與板材生產現場，作業員面臨 XML 格式相容性差、重量計算不精確以及缺乏實時作業反饋等痛點。

本系統透過 **Python 3.14** 重新構建，不僅 100% 還原並優化了原有的驗單邏輯，更導入了 **MVC (Model-View-Controller)** 軟體架構，確保系統在工業環境下的高穩定性與可擴展性。

---

## 🛠️ 技術核心亮點

### 1. 智慧分包演算法 (Bin Packing Logic)
* **自動分包決策**:實作貪婪演算法（Greedy Algorithm），根據使用者設定的「單包限重 (kg)」自動計算板件分配。
* **動態重整機制**:當作業中途調整限重參數時，系統會立即觸發重新裝箱邏輯，即時重整所有已掃描件的分包狀態，無需重新作業。

### 2. 多維度材質重量計算引擎 (Dynamic Density Engine)
* **高精確度換算**:針對不同材質（如防水發泡板、塑合板等）實作長寬高與密度的物理換算。
* **厚度對照表 (Thickness Mapping)**:支援針對特定厚度（如 9mm, 18mm, 25mm）設定獨立密度參數，解決板材發泡率不均導致的重量誤差。

### 3. 工業級非同步語音作業反饋 (Async TTS)
* **非阻塞式 UX 設計**:利用 `threading` 結合 `pyttsx3` 實作非同步語音播報。
* **現場作業優化**:作業員無需時刻盯著螢幕，透過聲音即可確認「已掃描」、「重複掃描」或「條碼錯誤」，大幅提升掃描槍作業效率。

### 4. 數據韌性與高相容性解析 (Legacy XML Support)
* **強大容錯能力**:相容原廠 XML 中常見的 `LitsPack` (拼寫錯誤) 與不同編碼（GB18030 / UTF-8）格式。
* **進度保存機制**:支援將掃描狀態、分包結果與系統配置完整封裝回 XML，達成跨平台、跨時段的作業銜接。

---

## 🏗️ 軟體架構 (MVC Design)
本專案採用專業的模組化設計，將商業邏輯與介面徹底解耦:

* **`main.py` (View/Controller)**:負責 Tkinter 高性能 UI 渲染、事件監聽與非同步執行緒調度。
* **`calculator.py` (Model)**:核心大腦，負責所有重量換算與分包演算法。
* **`data_manager.py` (Model/IO)**:處理系統設定儲存 (JSON)、XML 序列化與 PyInstaller 資源路徑優化。

---

## ⚙️ 技術棧 (Tech Stack)
* **Language**: Python 3.14+
* **GUI**: Tkinter (Standard Library)
* **Hardware Interfacing**: USB 條碼掃描槍 (HID Mode)
* **Audio**: pyttsx3 (SAPI5/NSSpeechSynthesizer)
* **Packaging**: PyInstaller (支援單一執行檔封裝)

---

## 🚀 部署與打包
專案已針對 Windows 環境進行優化，支援打包成獨立 `.exe` 檔案:

```bash
# 安裝依賴
pip install pyttsx3

# 打包指令 (自動處理相對路徑問題)
pyinstaller --onefile --windowed --name "雲熙打包助手_v2" main.py