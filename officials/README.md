# 州官員與州議會：建置流程

產出 `../dashboard/officials.html`。涵蓋全部 50 州（見根目錄 README §11）。期間：行政部門新聞稿自 2025-01-01 起；議會為 2025 年起的會期。

## 執行順序（python3.12，於 repo 根目錄執行）
| 腳本 | 內容 | 輸出 |
|---|---|---|
| `01_fetch_governors.py` | 州長新聞稿（CA：WordPress API；TX：官網分頁，可用 `TX-resume <offset>` 續抓） | `data/raw/gov_*.jsonl` |
| `01b_fetch_lg_sos.py` | 副州長、州務卿新聞稿 | `data/raw/{lg,sos}_*.jsonl` |
| `01c_fetch_listing.py <州…>` | 其他觀察州：WordPress API、Squarespace JSON、官網新聞列表 | `data/raw/{gov,lg,sos}_*.jsonl`、`fetch_status_*.json` |
| `01d_fill_from_cdx.py` | 佛州 2025 年補抓（CDX 網址＋官網原文）；日期修補、去重、去除翻譯下載區塊 | 同上 |
| `01e_fetch_archive.py <州…>` | 官網拒絕爬蟲或列表為動態載入：CDX 索引＋官網原文或 Internet Archive 存檔 | 同上 |
| `02_filter_keywords.py` | 涉中／涉台關鍵字篩選 | `releases_*.csv` |
| `03_fetch_legiscan.py` | LegiScan 會期資料與全文搜尋（需 `officials/.env` 的 `LEGISCAN_API_KEY`） | `data/raw/legiscan/` |
| `04_build_bills.py` | 法案、提案人、記名表決、議員 | `bills_china_taiwan.csv` 等 |
| `05_rule_exclusions.py`、`05b_incidental_mentions.py` | 規則排除 | `*_rules.csv` |
| `06_bill_snippets.py` | 法案全文關鍵字上下文 | `bill_snippets.csv` |
| `07_manual_codes_bills.py`、`08_manual_codes_releases.py` | 人工判讀代碼（新聞稿代碼存於 `release_codes_manual.json`） | `bills_coded.csv`、`releases_coded.csv` |
| `09_indicators.py` | 州、議員、議員 × 會期指標；偏離本黨 | `ind_*.csv` |
| `11_district_exposure.py` | 州議會選區對中／對台出口曝險（三種口徑；需 repo 根目錄 `.env` 的 `CENSUS_API_KEY` 與 `data/raw` 的 ZBP、QCEW） | `sld_exposure_2025.csv` |
| `10_build_page.py` | 產生頁面（範本 `page_template.html`） | `../dashboard/officials.html` |

`data/processed/` 隨 repo 提供；`data/raw/`（新聞稿原文、LegiScan 資料、Census 邊界與對照檔，約 1.4 GB）不納入 repo，需依上列腳本重新抓取。各腳本開頭的說明列出公式與資料來源。
