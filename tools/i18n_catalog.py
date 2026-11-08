# -*- coding: utf-8 -*-
"""大肥鱼控制台界面文案：简体中文 -> 日本語 / English / 繁體中文。

键是源码里的简体中文原文；{0}、{1} 是占位符，译文里必须原样保留。
"""

CATALOG: dict[str, dict[str, str]] = {
    "打开 SnowLuma 面板 → 左侧「配置」→ 顶部切到「客户端」→ 找到 ws://127.0.0.1:6199/ws 这一行": {
        "ja": "「SnowLuma パネルを開く」→ 左側の「設定」→ 上部の「クライアント」タブ → ws://127.0.0.1:6199/ws の行を探す",
        "en": "Open the SnowLuma panel → 「Config」 on the left → switch to 「Clients」 at the top → find the ws://127.0.0.1:6199/ws row",
        "zh-Hant": "開啟 SnowLuma 面板 → 左側「設定」→ 頂部切到「用戶端」→ 找到 ws://127.0.0.1:6199/ws 這一行",
    },
    "点「一键启动」会依次拉起 AstrBot、SnowLuma（和 QQ）。首次启动 AstrBot 大约要 15–30 秒。": {
        "ja": "「ワンクリック起動」を押すと、AstrBot、SnowLuma（および QQ）が順に起動します。AstrBot の初回起動には 15～30 秒ほどかかります。",
        "en": "「One-click start」 launches AstrBot, SnowLuma (and QQ) in order. The first AstrBot start takes about 15–30 seconds.",
        "zh-Hant": "點「一鍵啟動」會依序拉起 AstrBot、SnowLuma（和 QQ）。首次啟動 AstrBot 大約要 15–30 秒。",
    },
    "在 AstrBot 里加一个 aiocqhttp 适配器，把下面的地址和 SnowLuma 的令牌填进去。": {
        "ja": "AstrBot に aiocqhttp アダプターを追加し、下のアドレスと SnowLuma のトークンを入力します。",
        "en": "Add an aiocqhttp adapter in AstrBot and fill in the address below plus SnowLuma's token.",
        "zh-Hant": "在 AstrBot 裡新增一個 aiocqhttp 適配器，把下面的位址和 SnowLuma 的權杖填進去。",
    },
    "日志里搜「initial credentials」，形如 user=admin password=xxxx": {
        "ja": "ログで「initial credentials」を検索します（user=admin password=xxxx の形式）。",
        "en": "Search the log for 「initial credentials」 — it looks like user=admin password=xxxx",
        "zh-Hant": "日誌裡搜「initial credentials」，形如 user=admin password=xxxx",
    },
    "打开 SnowLuma 目录里的 console.log，搜「initial credentials」。": {
        "ja": "SnowLuma ディレクトリの console.log を開き、「initial credentials」を検索します。",
        "en": "Open console.log in the SnowLuma directory and search for 「initial credentials」.",
        "zh-Hant": "開啟 SnowLuma 目錄裡的 console.log，搜「initial credentials」。",
    },
    "缺哪个就点右边的「安装」，AstrBot / SnowLuma 会自动下载，QQ 会打开官方下载页。": {
        "ja": "足りないものの右側にある「インストール」を押すと、AstrBot / SnowLuma は自動ダウンロード、QQ は公式ダウンロードページが開きます。",
        "en": "Click 「Install」 next to whatever is missing: AstrBot / SnowLuma download automatically, and QQ opens its official download page.",
        "zh-Hant": "缺哪個就點右邊的「安裝」，AstrBot / SnowLuma 會自動下載，QQ 會開啟官方下載頁。",
    },
    "SnowLuma 把 QQ 挂上后转成 OneBot 协议；扫码这一步得你本人来，程序代替不了。": {
        "ja": "SnowLuma は QQ を接続して OneBot プロトコルに変換します。QR コードの読み取りはご本人が行う必要があり、プログラムでは代行できません。",
        "en": "SnowLuma hooks up QQ and exposes it over OneBot; you must do the QR scan yourself — the app cannot do it for you.",
        "zh-Hant": "SnowLuma 把 QQ 掛上後轉成 OneBot 協議；掃碼這一步得你本人來，程式代替不了。",
    },
    "端口：AstrBot 6185 · SnowLuma 5099（都是在后台跑，不用管命令行窗口）": {
        "ja": "ポート：AstrBot 6185 · SnowLuma 5099（どちらもバックグラウンドで動作するので、コマンドライン画面は気にしなくて大丈夫です）",
        "en": "Ports: AstrBot 6185 · SnowLuma 5099 (both run in the background; ignore the console windows)",
        "zh-Hant": "連接埠：AstrBot 6185 · SnowLuma 5099（都是在後台跑，不用管命令列視窗）",
    },
    "首次登录用账号 admin；初始密码在 SnowLuma 的 console.log 里": {
        "ja": "初回ログインはアカウント admin。初期パスワードは SnowLuma の console.log にあります",
        "en": "Log in the first time with account admin; the initial password is in SnowLuma's console.log",
        "zh-Hant": "首次登入用帳號 admin；初始密碼在 SnowLuma 的 console.log 裡",
    },
    "只影响控制台自己的显示，不会修改 AstrBot / SnowLuma 或机器人配置。": {
        "ja": "コンソール自体の表示だけに影響し、AstrBot / SnowLuma やロボットの設定は変更しません。",
        "en": "Affects only how the console displays; it does not modify AstrBot / SnowLuma or bot settings.",
        "zh-Hant": "只影響控制台自己的顯示，不會修改 AstrBot / SnowLuma 或機器人設定。",
    },
    "跟着四步走：装好组件 → 启动服务 → 扫码登录 QQ → 把 AstrBot 接上": {
        "ja": "4 ステップで進めます：コンポーネントを用意 → サービスを起動 → QR で QQ にログイン → AstrBot を接続",
        "en": "Four steps: install components → start services → scan in QQ → connect AstrBot",
        "zh-Hant": "跟著四步走：裝好元件 → 啟動服務 → 掃碼登入 QQ → 把 AstrBot 接上",
    },
    "提示：关掉控制台不会停机器人，AstrBot / SnowLuma 会继续在后台跑。": {
        "ja": "ヒント：コンソールを閉じてもロボットは停止しません。AstrBot / SnowLuma はバックグラウンドで動き続けます。",
        "en": "Tip: closing the console does not stop the bot — AstrBot / SnowLuma keep running in the background.",
        "zh-Hant": "提示：關掉控制台不會停機器人，AstrBot / SnowLuma 會繼續在後台跑。",
    },
    "字号只影响文字大小，不改布局；换台屏幕或改分辨率后会按新的 DPI 自动适配。": {
        "ja": "文字サイズは文字の大きさだけを変え、レイアウトは変えません。別の画面や解像度に変えると、新しい DPI に合わせて自動調整されます。",
        "en": "Font size only changes text size, not layout; on another screen or resolution it adapts to the new DPI automatically.",
        "zh-Hant": "字號只影響文字大小，不改版面；換台螢幕或改解析度後會依新的 DPI 自動調整。",
    },
    "点「打开 SnowLuma 面板」，会自动打开 127.0.0.1:5099": {
        "ja": "「SnowLuma パネルを開く」を押すと、127.0.0.1:5099 が自動で開きます",
        "en": "Click 「Open SnowLuma panel」 to open 127.0.0.1:5099 automatically",
        "zh-Hant": "點「開啟 SnowLuma 面板」，會自動開啟 127.0.0.1:5099",
    },
    "「反向 WS 地址」粘贴上面的 ws://127.0.0.1:6199/ws": {
        "ja": "「リバース WS アドレス」に上の ws://127.0.0.1:6199/ws を貼り付けます",
        "en": "Paste the ws://127.0.0.1:6199/ws above into 「Reverse WS address」",
        "zh-Hant": "「反向 WS 位址」貼上上面的 ws://127.0.0.1:6199/ws",
    },
    "→「令牌」点眼睛显示、点复制复制；改完保存，SnowLuma 会自动热重载": {
        "ja": "→「トークン」は目のアイコンで表示、コピーアイコンでコピー。変更を保存すると SnowLuma が自動でホットリロードします",
        "en": "→ For 「Token」, click the eye to reveal and the copy icon to copy; save your changes and SnowLuma hot-reloads automatically",
        "zh-Hant": "→「權杖」點眼睛顯示、點複製複製；改完儲存，SnowLuma 會自動熱重載",
    },
    "没有发现已登录的机器人；可以稍后在 SnowLuma 里登录，再回来扫描。": {
        "ja": "ログイン済みのロボットが見つかりません。あとで SnowLuma でログインしてから、もう一度スキャンしてください。",
        "en": "No logged-in bots found; log in via SnowLuma later and scan again.",
        "zh-Hant": "沒有發現已登入的機器人；可以稍後在 SnowLuma 裡登入，再回來掃描。",
    },
    "登录页也能选「使用访问令牌」，令牌在 配置 → 服务（远程访问）里生成。": {
        "ja": "ログイン画面でも「アクセストークンを使用」を選べます。トークンは 設定 → サービス（リモートアクセス）で生成します。",
        "en": "The login page also offers 「Use access token」; generate the token under Config → Service (remote access).",
        "zh-Hant": "登入頁也能選「使用存取權杖」，權杖在 設定 → 服務（遠端存取）裡產生。",
    },
    "未配置（在 tools/release.json 里填 repo 即可）": {
        "ja": "未設定（tools/release.json に repo を記入するだけです）",
        "en": "Not configured (just fill in repo in tools/release.json)",
        "zh-Hant": "未設定（在 tools/release.json 裡填 repo 即可）",
    },
    "关掉面板不会停机器人，AstrBot / SnowLuma 会继续运行。": {
        "ja": "パネルを閉じてもロボットは停止しません。AstrBot / SnowLuma は動き続けます。",
        "en": "Closing the panel does not stop the bot; AstrBot / SnowLuma keep running.",
        "zh-Hant": "關掉面板不會停機器人，AstrBot / SnowLuma 會繼續執行。",
    },
    "点「完成配置」回到主界面，以后只需要点「启动」，面板会自己出现在右边。": {
        "ja": "「設定完了」を押すとメイン画面に戻ります。以後は「起動」を押すだけで、パネルが右側に自動で表示されます。",
        "en": "Click 「Finish setup」 to return to the main screen; from then on just click 「Start」 and the panel appears on the right.",
        "zh-Hant": "點「完成設定」回到主介面，以後只需要點「啟動」，面板會自己出現在右邊。",
    },
    "工作日 9:00-12:00 / 14:00-18:00 不自动启动": {
        "ja": "平日 9:00-12:00 / 14:00-18:00 は自動起動しません",
        "en": "No auto-start on weekdays 9:00–12:00 / 14:00–18:00",
        "zh-Hant": "平日 9:00-12:00 / 14:00-18:00 不自動啟動",
    },
    "深色模式适合夜里用，跟随系统会跟着 Windows 的应用主题走。": {
        "ja": "ダークモードは夜間向けです。「システムに従う」は Windows のアプリテーマに合わせます。",
        "en": "Dark mode suits the night; 「Follow system」 tracks the Windows app theme.",
        "zh-Hant": "深色模式適合夜裡用，跟隨系統會跟著 Windows 的應用程式主題走。",
    },
    "面板、主题、插件清单都放在运行目录里，换机器时整个目录拷走即可。": {
        "ja": "パネル、テーマ、プラグイン一覧は実行ディレクトリに保存されます。別の PC に移すときはフォルダごとコピーしてください。",
        "en": "The panel, theme and plugin list live in the run directory — copy the whole folder when switching machines.",
        "zh-Hant": "面板、主題、外掛清單都放在執行目錄裡，換機器時整個目錄拷走即可。",
    },
    "提示：SnowLuma 必须先启动（上一步），这个面板才打得开。": {
        "ja": "ヒント：このパネルを開くには、先に SnowLuma を起動してください（前のステップ）。",
        "en": "Tip: SnowLuma must be running first (previous step) before this panel can open.",
        "zh-Hant": "提示：SnowLuma 必須先啟動（上一步），這個面板才打得開。",
    },
    "「访问令牌」粘贴 SnowLuma 里那串令牌（见下方卡片）": {
        "ja": "「アクセストークン」に SnowLuma のトークンを貼り付けます（下のカード参照）",
        "en": "Paste SnowLuma's token into 「Access token」 (see the card below)",
        "zh-Hant": "「存取權杖」貼上 SnowLuma 裡那串權杖（見下方卡片）",
    },
    "面板打不开：没找到 Edge 或窗口创建失败，8 秒后重试": {
        "ja": "パネルを開けません：Edge が見つからないか、ウィンドウの作成に失敗しました。8 秒後に再試行します",
        "en": "Cannot open the panel: Edge not found or window creation failed; retrying in 8 seconds",
        "zh-Hant": "面板打不開：沒找到 Edge 或視窗建立失敗，8 秒後重試",
    },
    "这些开关只影响控制台本身，不会改 AstrBot 的配置。": {
        "ja": "これらのスイッチはコンソール自体にのみ影響し、AstrBot の設定は変更しません。",
        "en": "These switches affect only the console itself, not AstrBot's config.",
        "zh-Hant": "這些開關只影響控制台本身，不會改 AstrBot 的設定。",
    },
    "保存后平台列表显示「在线」，回 QQ 里 @ 机器人试一句": {
        "ja": "保存後、プラットフォーム一覧に「オンライン」と表示されたら、QQ でロボットを @ して一言送ってみてください",
        "en": "After saving, the platform list shows 「Online」 — go back to QQ, @ the bot and send a message",
        "zh-Hant": "儲存後平台清單顯示「線上」，回 QQ 裡 @ 機器人試一句",
    },
    "之后想再看这份引导：设置 → 关于 → 重新打开新手引导": {
        "ja": "あとでこのガイドを見るには：設定 → バージョン情報 → 初心者ガイドを再度開く",
        "en": "To see this guide again: Settings → About → Reopen the setup guide",
        "zh-Hant": "之後想再看這份引導：設定 → 關於 → 重新開啟新手引導",
    },
    "第四步 · 让 AstrBot 连上 SnowLuma": {
        "ja": "ステップ 4 · AstrBot を SnowLuma に接続",
        "en": "Step 4 · Connect AstrBot to SnowLuma",
        "zh-Hant": "第四步 · 讓 AstrBot 連上 SnowLuma",
    },
    "先选一个界面语言：控制台、新手引导和设置都会用它显示。": {
        "ja": "まず表示言語を選んでください。コンソール、初心者ガイド、設定がこの言語で表示されます。",
        "en": "Pick an interface language first: the console, setup guide and settings will use it.",
        "zh-Hant": "先選一個介面語言：控制台、新手引導和設定都會用它顯示。",
    },
    "两边令牌必须一致；本机连接也可以都留空，但要“都空”。": {
        "ja": "両側のトークンは一致している必要があります。ローカル接続なら両方空欄でも構いませんが、「両方とも空」にしてください。",
        "en": "Tokens on both sides must match; for a local connection both may be empty — but they must both be empty.",
        "zh-Hant": "兩邊權杖必須一致；本機連線也可以都留空，但要「都空」。",
    },
    "就绪 · 改完插件点「热重启 AstrBot」即可生效": {
        "ja": "準備完了 · プラグインを変更したら「AstrBot をホットリスタート」で反映されます",
        "en": "Ready · after changing plugins, click 「Hot restart AstrBot」 to apply",
        "zh-Hant": "就緒 · 改完外掛點「熱重啟 AstrBot」即可生效",
    },
    "窗口再拉宽一点就能在这里直接看 AstrBot 面板": {
        "ja": "ウィンドウをもう少し広げると、ここで AstrBot パネルを直接表示できます",
        "en": "Widen the window a bit to view the AstrBot panel right here",
        "zh-Hant": "視窗再拉寬一點就能在這裡直接看 AstrBot 面板",
    },
    "左侧「平台」→「新增平台」→ 选 aiocqhttp": {
        "ja": "左側の「プラットフォーム」→「プラットフォームを追加」→ aiocqhttp を選択",
        "en": "Left side 「Platforms」 → 「Add platform」 → choose aiocqhttp",
        "zh-Hant": "左側「平台」→「新增平台」→ 選 aiocqhttp",
    },
    "已跳过新手引导，之后可在「设置 → 关于」里重新打开": {
        "ja": "初心者ガイドをスキップしました。あとで「設定 → バージョン情報」から再度開けます",
        "en": "Setup guide skipped; reopen it later under Settings → About",
        "zh-Hant": "已跳過新手引導，之後可在「設定 → 關於」裡重新開啟",
    },
    "选一张图片当面板背景（会自动淡化，不挡住文字）": {
        "ja": "パネルの背景画像を選択（自動で淡くなるので文字は隠れません）",
        "en": "Pick an image as the panel background (it fades automatically so text stays readable)",
        "zh-Hant": "選一張圖片當面板背景（會自動淡化，不擋住文字）",
    },
    "这些记录只保存在控制台里，不会修改机器人文件。": {
        "ja": "この記録はコンソール内に保存されるだけで、ロボットのファイルは変更しません。",
        "en": "These records are stored only in the console; no bot files are modified.",
        "zh-Hant": "這些記錄只儲存在控制台裡，不會修改機器人檔案。",
    },
    "必要插件从 GitHub 检查、修复或一键安装": {
        "ja": "必要なプラグインを GitHub から確認・修復・一括インストール",
        "en": "Check, repair or one-click install required plugins from GitHub",
        "zh-Hant": "必要外掛從 GitHub 檢查、修復或一鍵安裝",
    },
    "看到「已连接 / 在线」后，回来点「下一步」": {
        "ja": "「接続済み / オンライン」が表示されたら、戻って「次へ」を押してください",
        "en": "Once you see 「Connected / Online」, come back and click 「Next」",
        "zh-Hant": "看到「已連線 / 線上」後，回來點「下一步」",
    },
    "用要当机器人的 QQ 扫码登录，手机上点确认": {
        "ja": "ロボットにする QQ で QR コードを読み取り、スマホで確認します",
        "en": "Scan with the QQ account that will be the bot, then confirm on your phone",
        "zh-Hant": "用要當機器人的 QQ 掃碼登入，手機上點確認",
    },
    "ID 随便填（例如 qq），把「启用」打开": {
        "ja": "ID は任意（例：qq）。「有効」をオンにします",
        "en": "Enter any ID (e.g. qq) and turn on 「Enable」",
        "zh-Hant": "ID 隨便填（例如 qq），把「啟用」開啟",
    },
    "把 AstrBot 接到 SnowLuma": {
        "ja": "AstrBot を SnowLuma に接続",
        "en": "Connect AstrBot to SnowLuma",
        "zh-Hant": "把 AstrBot 接到 SnowLuma",
    },
    "第三步 · 登录要挂机器人的 QQ": {
        "ja": "ステップ 3 · ロボットにする QQ にログイン",
        "en": "Step 3 · Log in the QQ account for the bot",
        "zh-Hant": "第三步 · 登入要掛機器人的 QQ",
    },
    "点上面的「启动」，面板会在这里打开": {
        "ja": "上の「起動」を押すと、ここにパネルが開きます",
        "en": "Click 「Start」 above and the panel opens here",
        "zh-Hant": "點上面的「啟動」，面板會在這裡開啟",
    },
    "只影响控制台界面，切换后立即生效": {
        "ja": "コンソールの表示のみに影響し、切り替えるとすぐ反映されます",
        "en": "Only affects the console UI; applies immediately",
        "zh-Hant": "只影響控制台介面，切換後立即生效",
    },
    "在 AstrBot 面板里这样配": {
        "ja": "AstrBot パネルではこのように設定します",
        "en": "Configure it like this in the AstrBot panel",
        "zh-Hant": "在 AstrBot 面板裡這樣設定",
    },
    "SnowLuma 的访问令牌在哪": {
        "ja": "SnowLuma のアクセストークンの場所",
        "en": "Where is SnowLuma's access token?",
        "zh-Hant": "SnowLuma 的存取權杖在哪",
    },
    "正在扫描已登录的 QQ 机器人…": {
        "ja": "ログイン済みの QQ ロボットをスキャン中…",
        "en": "Scanning for logged-in QQ bots…",
        "zh-Hant": "正在掃描已登入的 QQ 機器人…",
    },
    "WebUI 就绪后会自动打开面板": {
        "ja": "WebUI の準備ができ次第、パネルが自動で開きます",
        "en": "The panel opens automatically once the WebUI is ready",
        "zh-Hant": "WebUI 就緒後會自動開啟面板",
    },
    "新手引导已完成，可以点「启动」了": {
        "ja": "初心者ガイドは完了しました。「起動」を押せます",
        "en": "Setup guide complete — you can click 「Start」",
        "zh-Hant": "新手引導已完成，可以點「啟動」了",
    },
    "点「启动」时顺带把 QQ 打开": {
        "ja": "「起動」時に QQ も一緒に開く",
        "en": "Also open QQ when clicking 「Start」",
        "zh-Hant": "點「啟動」時順帶把 QQ 開啟",
    },
    "QQ 协议端，负责登录 QQ": {
        "ja": "QQ プロトコル側。QQ へのログインを担当",
        "en": "QQ protocol side; handles the QQ login",
        "zh-Hant": "QQ 協議端，負責登入 QQ",
    },
    "面板连接断开了，稍后自动重连": {
        "ja": "パネルの接続が切れました。しばらくすると自動で再接続します",
        "en": "Panel connection lost; reconnecting automatically",
        "zh-Hant": "面板連線中斷了，稍後自動重新連線",
    },
    "打开 SnowLuma 目录": {
        "ja": "SnowLuma ディレクトリを開く",
        "en": "Open SnowLuma directory",
        "zh-Hant": "開啟 SnowLuma 目錄",
    },
    "打开 SnowLuma 面板": {
        "ja": "SnowLuma パネルを開く",
        "en": "Open SnowLuma panel",
        "zh-Hant": "開啟 SnowLuma 面板",
    },
    "热重启 AstrBot 生效": {
        "ja": "AstrBot をホットリスタートして反映",
        "en": "Hot restart AstrBot to apply",
        "zh-Hant": "熱重啟 AstrBot 生效",
    },
    "要关掉面板，还是留它在后台？": {
        "ja": "パネルを閉じますか、それともバックグラウンドに残しますか？",
        "en": "Close the panel, or leave it in the background?",
        "zh-Hant": "要關掉面板，還是留它在後台？",
    },
    "打开 AstrBot 面板": {
        "ja": "AstrBot パネルを開く",
        "en": "Open AstrBot panel",
        "zh-Hant": "開啟 AstrBot 面板",
    },
    "分类设置 · 改完立即生效": {
        "ja": "カテゴリ設定 · 変更はすぐ反映",
        "en": "Category settings · changes apply immediately",
        "zh-Hant": "分類設定 · 改完立即生效",
    },
    "AstrBot 正在启动…": {
        "ja": "AstrBot を起動中…",
        "en": "AstrBot is starting…",
        "zh-Hant": "AstrBot 正在啟動…",
    },
    "未配置 GitHub 仓库": {
        "ja": "GitHub リポジトリが未設定",
        "en": "GitHub repo not configured",
        "zh-Hant": "未設定 GitHub 儲存庫",
    },
    "等待启动 AstrBot": {
        "ja": "AstrBot の起動待ち",
        "en": "Waiting for AstrBot",
        "zh-Hant": "等待啟動 AstrBot",
    },
    "面板打不开，稍后自动重试": {
        "ja": "パネルを開けません。しばらくすると自動で再試行します",
        "en": "Cannot open the panel; retrying automatically",
        "zh-Hant": "面板打不開，稍後自動重試",
    },
    "第二步 · 把服务跑起来": {
        "ja": "ステップ 2 · サービスを起動",
        "en": "Step 2 · Get the services running",
        "zh-Hant": "第二步 · 把服務跑起來",
    },
    "界面语言已切换为 {0}": {
        "ja": "表示言語を {0} に切り替えました",
        "en": "Interface language switched to {0}",
        "zh-Hant": "介面語言已切換為 {0}",
    },
    "第一步 · 备齐三样东西": {
        "ja": "ステップ 1 · 3 つを用意",
        "en": "Step 1 · Get the three pieces ready",
        "zh-Hant": "第一步 · 備齊三樣東西",
    },
    "机器人本体，网页控制台": {
        "ja": "ロボット本体、Web コンソール",
        "en": "The bot itself, with a web console",
        "zh-Hant": "機器人本體，網頁控制台",
    },
    "大肥鱼控制台 v{0}": {
        "ja": "大肥魚コンソール v{0}",
        "en": "Dafeiyu Console v{0}",
        "zh-Hant": "大肥魚控制台 v{0}",
    },
    "热重启 AstrBot": {
        "ja": "AstrBot をホットリスタート",
        "en": "Hot restart AstrBot",
        "zh-Hant": "熱重啟 AstrBot",
    },
    "欢迎使用大肥鱼控制台": {
        "ja": "大肥魚コンソールへようこそ",
        "en": "Welcome to Dafeiyu Console",
        "zh-Hant": "歡迎使用大肥魚控制台",
    },
    "AstrBot 面板": {
        "ja": "AstrBot パネル",
        "en": "AstrBot panel",
        "zh-Hant": "AstrBot 面板",
    },
    "所有必要插件都已就位": {
        "ja": "必要なプラグインはすべて揃っています",
        "en": "All required plugins are ready",
        "zh-Hant": "所有必要外掛都已就位",
    },
    "已检测到的机器人实体": {
        "ja": "検出されたロボット",
        "en": "Detected bot accounts",
        "zh-Hant": "已偵測到的機器人實體",
    },
    "首次检查需要几秒钟": {
        "ja": "初回チェックには数秒かかります",
        "en": "The first check takes a few seconds",
        "zh-Hant": "首次檢查需要幾秒鐘",
    },
    "跳过，使用简体中文": {
        "ja": "スキップ（簡体字中国語を使用）",
        "en": "Skip and use Simplified Chinese",
        "zh-Hant": "跳過，使用簡體中文",
    },
    "状态已复制到剪贴板": {
        "ja": "状態をクリップボードにコピーしました",
        "en": "Status copied to clipboard",
        "zh-Hant": "狀態已複製到剪貼簿",
    },
    "没有需要安装的插件": {
        "ja": "インストールが必要なプラグインはありません",
        "en": "No plugins need installing",
        "zh-Hant": "沒有需要安裝的外掛",
    },
    "启动时拉起 QQ": {
        "ja": "起動時に QQ も開く",
        "en": "Open QQ on start",
        "zh-Hant": "啟動時拉起 QQ",
    },
    "关闭大肥鱼控制台": {
        "ja": "大肥魚コンソールを閉じる",
        "en": "Close Dafeiyu Console",
        "zh-Hant": "關閉大肥魚控制台",
    },
    "，点「插件」查看": {
        "ja": "。「プラグイン」で確認",
        "en": "; click 「Plugins」 to view",
        "zh-Hant": "，點「外掛」查看",
    },
    "组件文件不完整：": {
        "ja": "コンポーネントのファイルが不完全です：",
        "en": "Component files are incomplete: ",
        "zh-Hant": "元件檔案不完整：",
    },
    "扫码登录的客户端": {
        "ja": "QR コードでログインするクライアント",
        "en": "Client to log in by QR",
        "zh-Hant": "掃碼登入的用戶端",
    },
    "扫码登录机器人号": {
        "ja": "QR コードでロボット用 QQ にログイン",
        "en": "Scan to log in the bot account",
        "zh-Hant": "掃碼登入機器人號",
    },
    "找不到初始密码？": {
        "ja": "初期パスワードが見つかりませんか？",
        "en": "Can't find the initial password?",
        "zh-Hant": "找不到初始密碼？",
    },
    "已重新检测组件": {
        "ja": "コンポーネントを再チェックしました",
        "en": "Components re-checked",
        "zh-Hant": "已重新偵測元件",
    },
    "选一张背景图片": {
        "ja": "背景画像を選択",
        "en": "Choose a background image",
        "zh-Hant": "選一張背景圖片",
    },
    "已登录的客户端": {
        "ja": "ログイン済みのクライアント",
        "en": "Logged-in clients",
        "zh-Hant": "已登入的用戶端",
    },
    "背景已恢复默认": {
        "ja": "背景を既定に戻しました",
        "en": "Background reset to default",
        "zh-Hant": "背景已恢復預設",
    },
    "让机器人跑起来": {
        "ja": "ロボットを動かす",
        "en": "Get the bot running",
        "zh-Hant": "讓機器人跑起來",
    },
    "正在打开面板…": {
        "ja": "パネルを開いています…",
        "en": "Opening the panel…",
        "zh-Hant": "正在開啟面板…",
    },
    "最小化到后台": {
        "ja": "バックグラウンドに最小化",
        "en": "Minimize to background",
        "zh-Hant": "最小化到背景",
    },
    "最小化到托盘": {
        "ja": "トレイに最小化",
        "en": "Minimize to tray",
        "zh-Hant": "最小化到托盤",
    },
    "一键安装缺失": {
        "ja": "不足分を一括インストール",
        "en": "Install missing components",
        "zh-Hant": "一鍵安裝缺少的元件",
    },
    "复制仓库地址": {
        "ja": "リポジトリの URL をコピー",
        "en": "Copy repo URL",
        "zh-Hant": "複製儲存庫位址",
    },
    "选择界面语言": {
        "ja": "表示言語を選択",
        "en": "Choose interface language",
        "zh-Hant": "選擇介面語言",
    },
    "记住这个选择": {
        "ja": "この選択を記憶する",
        "en": "Remember this choice",
        "zh-Hant": "記住這個選擇",
    },
    "大肥鱼控制台": {
        "ja": "大肥魚コンソール",
        "en": "Dafeiyu Console",
        "zh-Hant": "大肥魚控制台",
    },
    "打开日志目录": {
        "ja": "ログディレクトリを開く",
        "en": "Open log directory",
        "zh-Hant": "開啟日誌目錄",
    },
    "打开插件目录": {
        "ja": "プラグインディレクトリを開く",
        "en": "Open plugin directory",
        "zh-Hant": "開啟外掛目錄",
    },
    "备齐三样东西": {
        "ja": "3 つを用意する",
        "en": "Get the three pieces ready",
        "zh-Hant": "備齊三樣東西",
    },
    "QQ 协议端": {
        "ja": "QQ プロトコル側",
        "en": "QQ protocol side",
        "zh-Hant": "QQ 協議端",
    },
    "版本与路径": {
        "ja": "バージョンとパス",
        "en": "Version & paths",
        "zh-Hant": "版本與路徑",
    },
    "主题与背景": {
        "ja": "テーマと背景",
        "en": "Theme & background",
        "zh-Hant": "主題與背景",
    },
    "正在检查…": {
        "ja": "チェック中…",
        "en": "Checking…",
        "zh-Hant": "正在檢查…",
    },
    "机器人本体": {
        "ja": "ロボット本体",
        "en": "Bot engine",
        "zh-Hant": "機器人本體",
    },
    "自定义背景": {
        "ja": "カスタム背景",
        "en": "Custom background",
        "zh-Hant": "自訂背景",
    },
    "重启协议端": {
        "ja": "プロトコル側を再起動",
        "en": "Restart protocol side",
        "zh-Hant": "重啟協議端",
    },
    "开关与启动": {
        "ja": "スイッチと起動",
        "en": "Switches & startup",
        "zh-Hant": "開關與啟動",
    },
    "连接机器人": {
        "ja": "ロボットを接続",
        "en": "Connect the bot",
        "zh-Hant": "連接機器人",
    },
    "关闭窗口时": {
        "ja": "ウィンドウを閉じるとき",
        "en": "When closing the window",
        "zh-Hant": "關閉視窗時",
    },
    "开始用起来": {
        "ja": "使い始める",
        "en": "Start using it",
        "zh-Hant": "開始用起來",
    },
    "登录 QQ": {
        "ja": "QQ にログイン",
        "en": "Log in to QQ",
        "zh-Hant": "登入 QQ",
    },
    "‹ 上一页": {
        "ja": "‹ 前へ",
        "en": "‹ Previous",
        "zh-Hant": "‹ 上一頁",
    },
    "下一页 ›": {
        "ja": "次へ ›",
        "en": "Next ›",
        "zh-Hant": "下一頁 ›",
    },
    "关闭与退出": {
        "ja": "閉じると終了",
        "en": "Closing & exit",
        "zh-Hant": "關閉與退出",
    },
    "缺仓库地址": {
        "ja": "リポジトリ URL がありません",
        "en": "Missing repo URL",
        "zh-Hant": "缺儲存庫位址",
    },
    "面板已就绪": {
        "ja": "パネルの準備ができました",
        "en": "Panel is ready",
        "zh-Hant": "面板已就緒",
    },
    "还没有日志": {
        "ja": "ログはまだありません",
        "en": "No logs yet",
        "zh-Hant": "還沒有日誌",
    },
    "谷时门禁": {
        "ja": "ピーク時間帯の制限",
        "en": "Peak-hour gate",
        "zh-Hant": "尖峰時段門檻",
    },
    "重新检查": {
        "ja": "再チェック",
        "en": "Check again",
        "zh-Hant": "重新檢查",
    },
    "直接关闭": {
        "ja": "直接閉じる",
        "en": "Close directly",
        "zh-Hant": "直接關閉",
    },
    "新手引导": {
        "ja": "初心者ガイド",
        "en": "Setup guide",
        "zh-Hant": "新手引導",
    },
    "刷新状态": {
        "ja": "状態を更新",
        "en": "Refresh status",
        "zh-Hant": "重新整理狀態",
    },
    "都搞定了": {
        "ja": "すべて完了",
        "en": "All done",
        "zh-Hant": "都搞定了",
    },
    "重新检测": {
        "ja": "再検出",
        "en": "Re-detect",
        "zh-Hant": "重新偵測",
    },
    "跟随系统": {
        "ja": "システムに従う",
        "en": "Follow system",
        "zh-Hant": "跟隨系統",
    },
    "系统默认": {
        "ja": "システム既定",
        "en": "System default",
        "zh-Hant": "系統預設",
    },
    "启动服务": {
        "ja": "サービスを起動",
        "en": "Start services",
        "zh-Hant": "啟動服務",
    },
    "插件目录": {
        "ja": "プラグインディレクトリ",
        "en": "Plugin directory",
        "zh-Hant": "外掛目錄",
    },
    "复制状态": {
        "ja": "状態をコピー",
        "en": "Copy status",
        "zh-Hant": "複製狀態",
    },
    "开源仓库": {
        "ja": "オープンソースリポジトリ",
        "en": "Open-source repo",
        "zh-Hant": "開源儲存庫",
    },
    "显示面板": {
        "ja": "パネルを表示",
        "en": "Show panel",
        "zh-Hant": "顯示面板",
    },
    "每次询问": {
        "ja": "毎回確認",
        "en": "Ask every time",
        "zh-Hant": "每次詢問",
    },
    "全部停止": {
        "ja": "すべて停止",
        "en": "Stop all",
        "zh-Hant": "全部停止",
    },
    "所有文件": {
        "ja": "すべてのファイル",
        "en": "All files",
        "zh-Hant": "所有檔案",
    },
    "重新扫描": {
        "ja": "再スキャン",
        "en": "Rescan",
        "zh-Hant": "重新掃描",
    },
    "打开仓库": {
        "ja": "リポジトリを開く",
        "en": "Open repo",
        "zh-Hant": "開啟儲存庫",
    },
    "完成配置": {
        "ja": "設定を完了",
        "en": "Finish setup",
        "zh-Hant": "完成設定",
    },
    "全部重启": {
        "ja": "すべて再起動",
        "en": "Restart all",
        "zh-Hant": "全部重啟",
    },
    "运行目录": {
        "ja": "実行ディレクトリ",
        "en": "Run directory",
        "zh-Hant": "執行目錄",
    },
    "一键启动": {
        "ja": "ワンクリック起動",
        "en": "One-click start",
        "zh-Hant": "一鍵啟動",
    },
    "开源协议": {
        "ja": "ライセンス",
        "en": "License",
        "zh-Hant": "開源授權",
    },
    "打开目录": {
        "ja": "ディレクトリを開く",
        "en": "Open directory",
        "zh-Hant": "開啟目錄",
    },
    "直接退出": {
        "ja": "直接終了",
        "en": "Quit directly",
        "zh-Hant": "直接退出",
    },
    "检查组件": {
        "ja": "コンポーネントを確認",
        "en": "Check components",
        "zh-Hant": "檢查元件",
    },
    "插件体检": {
        "ja": "プラグイン診断",
        "en": "Plugin checkup",
        "zh-Hant": "外掛健檢",
    },
    "打开面板": {
        "ja": "パネルを開く",
        "en": "Open panel",
        "zh-Hant": "開啟面板",
    },
    "还没启动": {
        "ja": "まだ起動していません",
        "en": "Not started yet",
        "zh-Hant": "還沒啟動",
    },
    "未安装": {
        "ja": "未インストール",
        "en": "Not installed",
        "zh-Hant": "未安裝",
    },
    "看日志": {
        "ja": "ログを見る",
        "en": "View log",
        "zh-Hant": "看日誌",
    },
    "已就绪": {
        "ja": "準備完了",
        "en": "Ready",
        "zh-Hant": "已就緒",
    },
    "缺文件": {
        "ja": "ファイル不足",
        "en": "Missing files",
        "zh-Hant": "缺檔案",
    },
    "上一步": {
        "ja": "前へ",
        "en": "Back",
        "zh-Hant": "上一步",
    },
    "下一步": {
        "ja": "次へ",
        "en": "Next",
        "zh-Hant": "下一步",
    },
    "需修复": {
        "ja": "要修復",
        "en": "Needs repair",
        "zh-Hant": "需修復",
    },
    "已安装": {
        "ja": "インストール済み",
        "en": "Installed",
        "zh-Hant": "已安裝",
    },
    "运行中": {
        "ja": "実行中",
        "en": "Running",
        "zh-Hant": "執行中",
    },
    "未运行": {
        "ja": "停止中",
        "en": "Not running",
        "zh-Hant": "未執行",
    },
    "主题": {
        "ja": "テーマ",
        "en": "Theme",
        "zh-Hant": "主題",
    },
    "返回": {
        "ja": "戻る",
        "en": "Back",
        "zh-Hant": "返回",
    },
    "外观": {
        "ja": "外観",
        "en": "Appearance",
        "zh-Hant": "外觀",
    },
    "退出": {
        "ja": "終了",
        "en": "Quit",
        "zh-Hant": "退出",
    },
    "语言": {
        "ja": "言語",
        "en": "Language",
        "zh-Hant": "語言",
    },
    "特大": {
        "ja": "特大",
        "en": "Extra large",
        "zh-Hant": "特大",
    },
    "继续": {
        "ja": "続行",
        "en": "Continue",
        "zh-Hant": "繼續",
    },
    "下载": {
        "ja": "ダウンロード",
        "en": "Download",
        "zh-Hant": "下載",
    },
    "修复": {
        "ja": "修復",
        "en": "Repair",
        "zh-Hant": "修復",
    },
    "关于": {
        "ja": "バージョン情報",
        "en": "About",
        "zh-Hant": "關於",
    },
    "字体": {
        "ja": "フォント",
        "en": "Font",
        "zh-Hant": "字型",
    },
    "打开": {
        "ja": "開く",
        "en": "Open",
        "zh-Hant": "開啟",
    },
    "设置": {
        "ja": "設定",
        "en": "Settings",
        "zh-Hant": "設定",
    },
    "日志": {
        "ja": "ログ",
        "en": "Log",
        "zh-Hant": "日誌",
    },
    "清除": {
        "ja": "クリア",
        "en": "Clear",
        "zh-Hant": "清除",
    },
    "关闭": {
        "ja": "閉じる",
        "en": "Close",
        "zh-Hant": "關閉",
    },
    "取消": {
        "ja": "キャンセル",
        "en": "Cancel",
        "zh-Hant": "取消",
    },
    "就绪": {
        "ja": "準備完了",
        "en": "Ready",
        "zh-Hant": "就緒",
    },
    "安装": {
        "ja": "インストール",
        "en": "Install",
        "zh-Hant": "安裝",
    },
    "选择": {
        "ja": "選択",
        "en": "Select",
        "zh-Hant": "選擇",
    },
    "跳过": {
        "ja": "スキップ",
        "en": "Skip",
        "zh-Hant": "跳過",
    },
    "启动": {
        "ja": "起動",
        "en": "Start",
        "zh-Hant": "啟動",
    },
    "刷新": {
        "ja": "更新",
        "en": "Refresh",
        "zh-Hant": "重新整理",
    },
    "行为": {
        "ja": "動作",
        "en": "Behavior",
        "zh-Hant": "行為",
    },
    "字号": {
        "ja": "文字サイズ",
        "en": "Font size",
        "zh-Hant": "字號",
    },
    "浅色": {
        "ja": "ライト",
        "en": "Light",
        "zh-Hant": "淺色",
    },
    "常规": {
        "ja": "標準",
        "en": "Regular",
        "zh-Hant": "一般",
    },
    "插件": {
        "ja": "プラグイン",
        "en": "Plugins",
        "zh-Hant": "外掛",
    },
    "版本": {
        "ja": "バージョン",
        "en": "Version",
        "zh-Hant": "版本",
    },
    "标准": {
        "ja": "標準",
        "en": "Standard",
        "zh-Hant": "標準",
    },
    "完成": {
        "ja": "完了",
        "en": "Done",
        "zh-Hant": "完成",
    },
    "复制": {
        "ja": "コピー",
        "en": "Copy",
        "zh-Hant": "複製",
    },
    "图片": {
        "ja": "画像",
        "en": "Image",
        "zh-Hant": "圖片",
    },
    "停止": {
        "ja": "停止",
        "en": "Stop",
        "zh-Hant": "停止",
    },
    "深色": {
        "ja": "ダーク",
        "en": "Dark",
        "zh-Hant": "深色",
    },
    "小": {
        "ja": "小",
        "en": "Small",
        "zh-Hant": "小",
    },
    "大": {
        "ja": "大",
        "en": "Large",
        "zh-Hant": "大",
    },
    "安装结束：成功 {0}/{1}，点「热重启 AstrBot」生效": {
        "ja": "インストール完了：成功 {0}/{1}。「AstrBot をホットリスタート」で反映されます",
        "en": "Install finished: {0}/{1} succeeded. Click 「Hot restart AstrBot」 to apply",
        "zh-Hant": "安裝結束：成功 {0}/{1}，點「熱重啟 AstrBot」生效",
    },
    "有 {0} 个必要插件未安装，点「插件」可一键修复": {
        "ja": "必要なプラグインが {0} 個未インストールです。「プラグイン」から一括修復できます",
        "en": "{0} required plugins are missing; click 「Plugins」 to fix them in one go",
        "zh-Hant": "有 {0} 個必要外掛未安裝，點「外掛」可一鍵修復",
    },
    "{0} 已就位，点「热重启 AstrBot」生效": {
        "ja": "{0} は準備完了。「AstrBot をホットリスタート」で反映されます",
        "en": "{0} is ready; click 「Hot restart AstrBot」 to apply",
        "zh-Hant": "{0} 已就位，點「熱重啟 AstrBot」生效",
    },
    "还有 {0} 个需要处理，装完点热重启生效": {
        "ja": "あと {0} 個の対応が必要です。インストール後にホットリスタートで反映されます",
        "en": "{0} more to handle; hot restart after installing",
        "zh-Hant": "還有 {0} 個需要處理，裝完點熱重啟生效",
    },
    "插件检查：{0}/{1} 已安装{2}": {
        "ja": "プラグイン確認：{0}/{1} インストール済み{2}",
        "en": "Plugin check: {0}/{1} installed{2}",
        "zh-Hant": "外掛檢查：{0}/{1} 已安裝{2}",
    },
    "开始安装 {0} 个插件…": {
        "ja": "{0} 個のプラグインのインストールを開始…",
        "en": "Installing {0} plugins…",
        "zh-Hant": "開始安裝 {0} 個外掛…",
    },
    "{0} / {1} 已安装": {
        "ja": "{0} / {1} インストール済み",
        "en": "{0} / {1} installed",
        "zh-Hant": "{0} / {1} 已安裝",
    },
    "正在取消 {0} 下载…": {
        "ja": "{0} のダウンロードをキャンセル中…",
        "en": "Cancelling download of {0}…",
        "zh-Hant": "正在取消 {0} 下載…",
    },
    "{0} 安装失败：{1}": {
        "ja": "{0} のインストールに失敗：{1}",
        "en": "Failed to install {0}: {1}",
        "zh-Hant": "{0} 安裝失敗：{1}",
    },
    "打不开插件目录：{0}": {
        "ja": "プラグインディレクトリを開けません：{0}",
        "en": "Cannot open plugin directory: {0}",
        "zh-Hant": "打不開外掛目錄：{0}",
    },
    "重绘用时 {0}ms": {
        "ja": "再描画 {0}ms",
        "en": "Redraw took {0}ms",
        "zh-Hant": "重繪用時 {0}ms",
    },
    "插件检查失败：{0}": {
        "ja": "プラグイン確認に失敗：{0}",
        "en": "Plugin check failed: {0}",
        "zh-Hant": "外掛檢查失敗：{0}",
    },
    "开始准备 {0} …": {
        "ja": "{0} の準備を開始 …",
        "en": "Preparing {0} …",
        "zh-Hant": "開始準備 {0} …",
    },
    "{0} 失败：{1}": {
        "ja": "{0} に失敗：{1}",
        "en": "{0} failed: {1}",
        "zh-Hant": "{0} 失敗：{1}",
    },
    " · {0} 构建": {
        "ja": " · {0} ビルド",
        "en": " · {0} build",
        "zh-Hant": " · {0} 建置",
    },
    "，{0} 个待处理": {
        "ja": "、{0} 件待機中",
        "en": ", {0} pending",
        "zh-Hant": "，{0} 個待處理",
    },
    "背景已换成 {0}": {
        "ja": "背景を {0} に変更しました",
        "en": "Background changed to {0}",
        "zh-Hant": "背景已換成 {0}",
    },
    "{0} 下载已取消": {
        "ja": "{0} のダウンロードをキャンセルしました",
        "en": "{0} download cancelled",
        "zh-Hant": "{0} 下載已取消",
    },
    "共 {0} 个": {
        "ja": "全 {0} 個",
        "en": "{0} in total",
        "zh-Hant": "共 {0} 個",
    },
    "已复制：{0}": {
        "ja": "コピーしました：{0}",
        "en": "Copied: {0}",
        "zh-Hant": "已複製：{0}",
    },
    "取消 {0}%": {
        "ja": "キャンセル {0}%",
        "en": "Cancel {0}%",
        "zh-Hant": "取消 {0}%",
    },
    "字体：{0}": {
        "ja": "フォント：{0}",
        "en": "Font: {0}",
        "zh-Hant": "字型：{0}",
    },
    "字号：{0}": {
        "ja": "文字サイズ：{0}",
        "en": "Font size: {0}",
        "zh-Hant": "字號：{0}",
    },
    "{0} 完成": {
        "ja": "{0} 完了",
        "en": "{0} complete",
        "zh-Hant": "{0} 完成",
    },
    "主题：{0}": {
        "ja": "テーマ：{0}",
        "en": "Theme: {0}",
        "zh-Hant": "主題：{0}",
    },
    "← → 选择语言 · Enter 继续": {
        "ja": "← → で言語を選択 · Enter で続行",
        "en": "← → choose language · Enter to continue",
        "zh-Hant": "← → 選擇語言 · Enter 繼續",
    },
    "← → 切换步骤 · Enter 继续": {
        "ja": "← → で手順を切替 · Enter で続行",
        "en": "← → switch steps · Enter to continue",
        "zh-Hant": "← → 切換步驟 · Enter 繼續",
    },
    "↑ ↓ 切换分类 · Esc 返回": {
        "ja": "↑ ↓ で分類切替 · Esc で戻る",
        "en": "↑ ↓ switch category · Esc to go back",
        "zh-Hant": "↑ ↓ 切換分類 · Esc 返回",
    },
}
