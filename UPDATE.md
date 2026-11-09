# 更新手冊（美國各州／選區／郡儀表板）

觸發：Titus 說「更新美國儀表板」。目標：資料推進到最新可得月份／年份，三個 HTML 重建並上線，回報變動。

## 0. 前置
- 專案路徑：`…/Admin_Docs_since_0716_2024/us-states-china-exposure/`；`.env` 內有 `CENSUS_API_KEY`、`BEA_API_KEY`。
- Census 貿易 API 月資料延遲約 5 週；`scripts/01_fetch_census.py` 與 `07_fetch_naics_cbp.py` 的 `LATEST`（`'2026-09'`）要改成最新可得月份（先用 HS2 小查詢探測 `time=YYYY-MM` 是否回 200）。年底時把前一年的 `-12` 加進 `YEARS`，`LATEST` 改成新年度的最新月。

## 1. 月更（貿易與曝險）
1. 探測最新月份 → 改 `LATEST`；刪除 `data/raw/census/*_<舊LATEST>.json` 與 `data/raw/naics/*_<舊LATEST>.json`（其餘快取保留）。
2. `python3.12 scripts/01_fetch_census.py`（中國＋台灣＋世界；大檔會 524，腳本自動重試；背景跑約 1–2 小時）。
3. `python3.12 scripts/07_fetch_naics_cbp.py`（全國 NAICS4；CBP／BEA 郡 GDP 已快取則跳過）。
4. `03_build_panel.py` → `04_exposure.py` → `06_validate.py` → `12_shift_share_v2.py` → `05_build_dashboard.py` → `11_build_district_dashboard.py`。
5. 本機 `python3.12 -m http.server` 開 `dashboard/index.html`、`districts.html` 檢查：地圖有色、趨勢圖最後一根為新 YTD、console 無錯誤。
6. README：更新 §1 期間、§3 核對表（從 `validation_results.md` 貼）、§4–5b 排名表若基準年改變；`data/raw/MANIFEST.md` 的日期。
7. `git add -A && git commit && git push`；等 Pages 回 200；回報。

## 2. 年更（有新版才做）
| 來源 | 檢查處 | 動作 |
|---|---|---|
| BEA SAGDP 州 GDP | https://apps.bea.gov/regional/zip/SAGDP.zip | 重下載 → `02_clean_bea_gdp.py` |
| BEA 郡 GDP、CBP、QCEW、ZBP | 年份參數在 `07_fetch_naics_cbp.py`（CBP 2023）、`12_shift_share_v2.py`（QCEW 2024、ZBP 2023）、`common.py` | 改年份、重抓、重跑 |
| USCBC State Export Report | https://www.uschina.org/articles/us-exports-to-china-<年>/ （網站擋 curl，用瀏覽器讀連結，PDF 直連可下載） | 有選區頁才跑 `08_parse_uscbc_districts.py`；州頁用 `02_clean_uscbc.py` 更新前 10 表 |
| USDA AFIDA 年報 | https://www.fsa.usda.gov/… AFIDA annual report | 下載 PDF → `pdftotext -layout` Report 11 頁 → `02_clean_afida.py`（頁碼參數） |
| Census 邊界（選區重劃後） | www2.census.gov/geo/tiger/GENZ<年>/shp/ | `10_geo.py` |

## 3. 回報格式
最新月份、各州對中／對台出口進口的主要變動、核對表差異是否仍在容忍範圍、哪些年度來源沒有新版。

## 4. 國會層（月更可選）
刪除 `data/raw/congress/bills_list_119.json` 與 `data/raw/crec/search_*_<今年>.json`（其餘快取保留）→ `13_fetch_congress_bills.py`（新法案細節會自動補抓；既有法案的共同提案人若要更新，刪 `bills/119-*_cos*.json`）→ `14_fetch_crec.py` → `15_build_congress.py` → `16_build_congress_dashboard.py`。議員名冊每屆換屆時重新下載 YAML。
