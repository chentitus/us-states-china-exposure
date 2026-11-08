# data/raw/MANIFEST.md（抓取日期 2026-11-07／08）

| 來源 | 檔案 | URL | 備註 |
|---|---|---|---|
| Census International Trade API | `census/*.json`（70 檔，exports/imports × China/World × HS2/HS4/HS6 × 2020-12…2025-12, 2026-09） | `https://api.census.gov/data/timeseries/intltrade/{exports,imports}/statehs?get=STATE,CTY_CODE,CTY_NAME,{E,I}_COMMODITY,…,{ALL,GEN}_VAL_YR&COMM_LVL=…&CTY_CODE=5700|-&time=…&key=…` | `_fetch_log.txt` 為抓取紀錄；世界 HS4 因 API 524 放棄 |
| BEA Regional | `bea/SAGDP.zip`（SAGDP1__ALL_AREAS_1997_2025.csv） | https://apps.bea.gov/regional/zip/SAGDP.zip | 10,381,511 B |
| USCBC | `uscbc/USCBC_2025_Export_Report.pdf`（2,032,427 B）＋ `_text.txt` | https://www.uschina.org/wp-content/uploads/2025/05/2025-Export-Report.pdf | 網站主頁 403，PDF 直連可取 |
| USDA FSA AFIDA | `afida/AFIDA_2024_Report.pdf`（13,448,016 B）＋ `AFIDA_2024_Report_p256-290_layout.txt` | https://www.fsa.usda.gov/sites/default/files/2026-01/AFIDAYR2024ReportWithPageNumbers.pdf | Report 11 = 中國投資者按州×郡 |
| BEA API（MNE, DirectionOfInvestment=state） | 未使用 | — | 州級表只列七國，中國併入 Other |
| Rhodium US-China Investment Hub | 未使用 | https://www.us-china-investment.org/fdi-data | 資料止於 2020-12 |
