# data/raw/MANIFEST.md（抓取日期 2026-11-07／08）

| 來源 | 檔案 | URL | 備註 |
|---|---|---|---|
| Census International Trade API | `census/*.json`（70 檔，exports/imports × China/World × HS2/HS4/HS6 × 2020-12…2025-12, 2026-09） | `https://api.census.gov/data/timeseries/intltrade/{exports,imports}/statehs?get=STATE,CTY_CODE,CTY_NAME,{E,I}_COMMODITY,…,{ALL,GEN}_VAL_YR&COMM_LVL=…&CTY_CODE=5700|-&time=…&key=…` | `_fetch_log.txt` 為抓取紀錄；世界 HS4 因 API 524 放棄 |
| BEA Regional | `bea/SAGDP.zip`（SAGDP1__ALL_AREAS_1997_2025.csv） | https://apps.bea.gov/regional/zip/SAGDP.zip | 10,381,511 B |
| USCBC | `uscbc/USCBC_2025_Export_Report.pdf`（2,032,427 B）＋ `_text.txt` | https://www.uschina.org/wp-content/uploads/2025/05/2025-Export-Report.pdf | 網站主頁 403，PDF 直連可取 |
| USDA FSA AFIDA | `afida/AFIDA_2024_Report.pdf`（13,448,016 B）＋ `AFIDA_2024_Report_p256-290_layout.txt` | https://www.fsa.usda.gov/sites/default/files/2026-01/AFIDAYR2024ReportWithPageNumbers.pdf | Report 11 = 中國投資者按州×郡 |
| BEA API（MNE, DirectionOfInvestment=state） | 未使用 | — | 州級表只列七國，中國併入 Other |
| Rhodium US-China Investment Hub | 未使用 | https://www.us-china-investment.org/fdi-data | 資料止於 2020-12 |
| USCBC 2025 州＋選區一頁式 PDF | `uscbc2025_states/*.pdf`（51 檔，各州頁＋各選區頁） | https://www.uschina.org/articles/us-exports-to-china-2025/ 列出的 `wp-content/uploads/2025/{04,07}/…` 連結 | 網站 403，PDF 直連可取 |
| USCBC 2026 州一頁式 PDF＋報告 | `uscbc2026/*.pdf`（51 檔） | https://www.uschina.org/articles/us-exports-to-china-2026/ | 2025 年商品；無選區 |
| USCBC 舊版選區報告 | `uscbc_district/2021_district_exports_report.pdf`、`uscbc_2020_district_export_report.pdf` | uschina.org/sites/default/files/… | 未使用 |
| Census statenaics（STATE='-'） | `naics/*.json`（42 檔） | `timeseries/intltrade/{exports,imports}/statenaics?...COMM_LVL=NA4&CTY_CODE=5700|5830|-&STATE=-` | 全國 NAICS4 對中／台／世界貿易 |
| Census CBP 2023 | `cbp/cbp2023_us.json`、`cbp2023_county_XX.json`、`cbp2023_cd_XX.json` | `https://api.census.gov/data/2023/cbp` | 郡＝NAICS 2–6 位；選區只有 2 位 |
| BEA Regional CAGDP2 | `bea/cagdp2_{2020..2024}.json` | BEA API Regional dataset | 郡 GDP |
| Census 邊界與關係檔 | `geo/cb_2024_us_cd119_5m.zip`、`cb_2024_us_county_20m.zip`、`geo/rel/tab20_cd11920_county20_natl.txt` | www2.census.gov/geo/… | 119 屆選區、郡；選區—郡土地面積關係 |
| Congress.gov API | `congress/bills_list_{116..119}.json`、`congress/bills/*.json`（法案細節、共同提案人、主題） | https://api.congress.gov/v3/bill/... | 需 api.data.gov key；2026-11-09 抓取 |
| GovInfo API | `crec/search_{china,taiwan}_{2020..2026}.json`、`crec/mods/*.xml`（1,218 日）、`crec/htm/*.htm`（9,801 段） | https://api.govinfo.gov/search 、/packages/{id}/mods 、/granules/{id}/htm | 同上 key |
| unitedstates/congress-legislators | `congress/legislators-{current,historical}.yaml` | https://github.com/unitedstates/congress-legislators | 公共領域 |
