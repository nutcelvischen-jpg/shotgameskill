# 音樂、音效、搞笑配音

## 1. 電子配樂：程式合成，不用音檔
Web Audio 排程器（lookahead 0.12s、每 25ms 檢查一次），每一拍放：大鼓、Hi-hat（濾波噪音）、拍手、鋸齒波 Bass，強度高時加方波琶音。
**緊張感 = 參數跟著遊戲狀態走**：
```js
function mood(){
  const left = stock/total;                       // 剩越少越緊張
  return { bpm: 112 + li*6 + (left<.3?10:0) + (power>.85?6:0),
           int: .3 + .45*(1-left) + (ev?.3:0) + li*.05 };   // int 控制濾波開度、疊幾層
}
```
- 一定要在使用者第一次點擊時才 `new AudioContext()`（瀏覽器自動播放限制），並且 `resume()`。
- 給靜音鈕（🔊/🔇），全部聲音接同一個 master gain。

## 2. 音效：也用合成
| 音效 | 做法 |
|---|---|
| 噗通 | sine 700Hz → 110Hz 指數下滑 0.16s |
| 啪（掉地上） | 白噪音 → lowpass 600Hz，0.12s |
| 叩叩叩 | 140Hz→60Hz 短促 ×3 |
| 狗叫 | 方波 1100→520Hz 0.07s ＋ bandpass |
| 嘶～（蛇） | 白噪音 highpass 5kHz，淡入淡出 |
| 嚇人 | 鋸齒波 300→1800Hz 上滑＋噪音 |
| 得分 | 三音琶音 660/880/1320 |

## 3. TTS 配音（Gemini TTS via OpenRouter）
腳本：`scripts/tts_openrouter.py 台詞.json 輸出資料夾`，台詞檔範例 `example/voice_lines.json`。
- 只回傳 PCM 24kHz s16le → 腳本自動轉 mp3＋剪頭尾靜音
- 金鑰用環境變數 `OPENROUTER_API_KEY`，**不要放進網頁**；遊戲只載入預錄好的 mp3
- 遊戲端：`fetch → decodeAudioData`，缺檔就安靜略過；同一時間只播一句（新的打斷舊的）＋冷卻時間

### 怎麼寫出「好笑」的配音 prompt
格式：`[英文語氣標籤, 用逗號分隔] 中文台詞`
1. **固定加 `comedic, cartoonish`**：讓聲音誇張、卡通化，而不是寫實。
2. **再加一個情緒＋一個角色比喻**，比喻最有效：
   - `like a sports announcer`（運動主播）→ 進球、全破
   - `heroic battle cry`（戰吼）→ 用力、衝刺
   - `dramatically disappointed`（浮誇失望）→ 失誤
   - `stern boss, slow, comedic deadpan`（面無表情的老闆）→ 被抓到
   - `whispering, eerie, slow, breathy`（陰森耳語）→ 阿飄
   - `very cute, excited, high-pitched, fast`（超可愛高音）→ 小狗、小動物
3. **台詞要短**：2~10 個字最好笑，也最不會被打斷。標點會影響節奏：`！！` 會更大聲，`……` 會拖長停頓。
4. **用台詞取代聲音**：✗「嗯～～～」「啊 啊 啊」「呼……呼……」這種用力、喘氣的聲音，TTS 念出來很容易變得**很猥褻**。✓ 改成有字的喊聲：「嘿咻！」「加油！加油！」「衝啊——！」「好險好險……」「任務完成！」。
5. **同一個角色固定同一個聲音**，玩家才認得出是誰在講話。
6. **全破台詞要能截圖分享**：「我很會大便！！讚！」「我是辦公室投籃王！！讚！」。

### 聲音挑選（Gemini TTS voice）
| voice | 適合 |
|---|---|
| Puck | 主角、搞笑男聲（預設） |
| Kore | 女聲、耳語、旁白 |
| Charon | 低沉、老闆、嚴肅反差 |
| Enceladus | 氣音、陰森，適合鬼 |
| Zephyr | 明亮、可愛；再加 `"pitch": 1.12` 變成小動物 |

### 台詞清單建議（每個遊戲都準備）
開始、小中大三段用力、成功、完美、失誤、每個事件的預告＋成功＋失敗、結算過關、結算失敗、全破。
