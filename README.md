# Network Programming HW3 - Game Store System
本作業實作遊戲大廳 (Lobby) 與 遊戲商城 (Store) 的多人連線平台。目標是打造一個完整、可多人操作的遊戲平台，連結「遊戲開發者」與「玩家」兩端。
系統採用 Client-Server 架構，並透過標準化的遊戲規格，讓不同類型的遊戲（CLI / GUI / 多人對戰）皆能在此平台上順利發布與執行。

## 核心功能:
### Developer Platform
提供開發者管理遊戲的工具，支援統一的介面標準：
* 遊戲上架：支援上傳雙人 CLI、雙人 GUI 及多人小遊戲。
* 版本管理：可隨時更新遊戲版本或下架遊戲。
* 標準化規格：透過統一的檔案結構與啟動方式，確保遊戲能被平台正確管理與啟動。

### Player Platform
提供玩家流暢的遊玩體驗：
* 遊戲商城：瀏覽上架遊戲、檢視詳細資訊（作者、版本、簡介），並支援評分與評論功能。
* 遊戲大廳：即時查看線上玩家、現有房間列表與遊戲狀態。
* 多人連線：支援建立房間、加入房間，連線啟動遊戲。


## File Structure
```
GameStore/
├── Makefile                
├── README.md                
├── common/
│   ├── __init__.py
│   └── protocol.py          
├── server/
│   └── server.py

├── client_dev/
│   └── dev_client.py
├── client_player/
│   └── player_client.py
└── games/                   
    ├── tictactoe.py
    ├── bingo.py
    ├── guessgame.py
    └── game_template.py
```

## How to start

### 1. 環境需求
* Python 3.8+
* Tkinter 
    * Linux install:
    ```
    sudo apt-get install python3-tk
    ```
### 2. 連線設定 
Server 預設跑在交大資工系計中工作站，若欲更改設定請將每份檔案中的
```
HOST = 'linux2.cs.nycu.edu.tw'
PORT = 12131
```


Developer
----------------------
如果你想上架遊戲供大家遊玩，請依照以下步驟操作。
### 1\. 啟動與登入
```bash
cd NP_hw3
make dev
# or python3 client_dev/dev_client.py
```
-   首次使用請點擊 **REGISTER** 註冊帳號。
-   註冊後請點擊 **LOGIN** 登入。
    
### 2\. 上架新遊戲 (Upload)
1.  點擊左側選單的 **Upload New Game**。
2.  填寫遊戲資訊：
    -   **Game Name**: 遊戲名稱 (例如: `TicTacToe`)。
    -   **Description**: 簡單介紹玩法。
    -   **Type**: 選擇 `GUI` (視窗介面) 或 `CLI` (純文字介面)。
3.  點擊 **Choose File**，選擇你的遊戲原始碼 (`.py` 檔)。
    -   _注意：遊戲程式碼需符合平台的 Game Template 規範。_
4.  點擊 **Publish to Store** 完成上架。
    
### 3\. 管理與更新遊戲
點擊左側選單的 **My Games**：
-   **更新遊戲 (Update)**：選取遊戲 -> 點擊 **Update Version** -> 上傳新的 `.py` 檔。版本號會自動更新。
-   **查看評論 (Reviews)**：選取遊戲 -> 點擊 **View Reviews**，查看玩家的評分與留言。
-   **下架遊戲 (Delete)**：選取遊戲 -> 點擊 **Delete Game**。注意：這會將遊戲從所有玩家的電腦中移除。
---

Player
----------------
如果你想下載遊戲並與朋友連線對戰，請依照以下步驟。
### 1\. 啟動與登入
```bash
make player
# or python3 client_player/player_client.py
```
-   首次使用請點擊 **REGISTER** 註冊帳號。 
-   註冊後請點擊 **LOGIN** 登入。
### 2\. 瀏覽與下載 (Store)
1.  進入 **Store** 頁面。
2.  你可以看到目前所有上架的遊戲、類型與平均評分。
3.  點擊卡片上的 **Details / Download**。
4.  在彈出視窗中點擊 **Download**，遊戲會下載至你的 `My Library`。
    

### 3\. 建立房間 (Host Game)
1.  進入 **Library** 頁面。
2.  找到你想玩的遊戲，點擊 **Create Room**。
    -   _若按鈕顯示 `Update Now`，代表有新版本，請先更新。_
3.  系統會開啟一個「等待室 (Waiting Room)」，並顯示你的 **Room ID**。
4.  等待朋友加入房間。
    

### 4\. 加入房間 (Join Game)
1.  進入 **Lobby** 頁面，點擊 **Refresh** 刷新列表。
2.  雙擊你想加入的房間。
    -   _若你尚未下載該遊戲，系統會提示並協助你自動下載。_
3.  進入等待室後，等待房主開始遊戲。

### 5\. 開始遊戲與評分
1.  當房間人數足夠 (通常為 2 人以上) 時，房主的 **Start Game** 按鈕會亮起。
2.  房主按下 Start 後，所有玩家的遊戲視窗會自動彈出並連線。 
3.  **遊戲結束後**，你可以回到遊戲詳情頁面，給予 **1-5 星評分** 並留下評論。
