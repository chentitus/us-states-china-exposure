# 美國各州對中國／台灣貿易依賴與曝險（2020–2026）

**線上儀表板（GitHub Pages）**：https://chentitus.github.io/us-states-china-exposure/dashboard/index.html
原始碼與資料：https://github.com/chentitus/us-states-china-exposure ｜ 姊妹專案（國家層級）：https://github.com/chentitus/china-exposure-dashboard

沿用 `china-exposure-dashboard`（國家層級）的方法：把金額換成依賴比率 → 概念分組 → 百分位平均子分數 → 總分；單檔儀表板 `dashboard/index.html`（雙擊開啟，Plotly CDN）。建置日期 2026-11-08。

```
us-states-china-exposure/
  .env                 CENSUS_API_KEY、BEA_API_KEY（不進 repo）
  data/raw/            census/（API JSON 快取，70 檔）、bea/SAGDP.zip、uscbc/（2025 報告 PDF＋文字）、afida/（2024 年報 PDF＋Report 11 文字）；MANIFEST.md
  data/clean/          census_state_trade_raw.parquet、panel_state_year.csv、top_products_state_year.csv、summary_state.csv、bea_state_gdp.csv、afida_china_land_by_state_2024.csv、uscbc_state_tables.csv、validation_results.md
  scripts/             01_fetch_census → 02_clean_{afida,uscbc,bea_gdp} → 03_build_panel → 04_exposure → 05_build_dashboard → 06_validate
  dashboard/index.html
```

## 1. 資料來源
| 來源 | 內容 | 期間 | 備註 |
|---|---|---|---|
| U.S. Census Bureau International Trade API `timeseries/intltrade/{exports,imports}/statehs` | 各州對中國（CTY_CODE 5700）、台灣（5830）與全世界（CTY_CODE `-`）商品貿易；出口 = Origin of Movement（起運州），進口 = state of destination（目的州）；HS2／HS4／HS6（中國）；年值取 `time=YYYY-12` 的年累計欄 | 2020–2025；2026 = 1–9 月累計（YTD） | 需 API key；API 在大檔（HS6、世界 HS4）常回 524，腳本有快取與重試；世界 HS4 未抓（不需要） |
| BEA Regional SAGDP1 | 各州 GDP（current dollars） | 2018–2025 | 2026 YTD 指標以 2025 GDP 為分母 |
| USCBC, *US Exports to China 2025* | 對中服務出口前 10 州（2023）、受中國產品別報復關稅出口前 10 州（2025-04）、商品出口前 10 州（2024） | 2023–2025 | 全州服務出口只有地圖圖像，無法取得 |
| USDA FSA AFIDA Annual Report 2024, Report 11 | 中國投資者持有農地按州×郡（pdftotext -layout 解析州小計） | 2024-12-31 | 申報制、按主要投資者，為下限；29 州合計 247,661 英畝（USDA 公布 247,659） |

未納入：中資在美 FDI 按州（BEA API 州級表只列加法德日荷瑞英七國，中國併入「其他」；Rhodium US-China Investment Hub 只到 2020 年）；各州服務出口全表（USCBC 僅前 10）；USDA 州別農產出口（不分目的國）。

## 2. 指標與分數
- **出口依賴**（州經濟靠中國／台灣市場）：`exports_{china,taiwan}_pct_gdp`、`exports_{china,taiwan}_share`；可選 `services_exp_china_pct_gdp_2023`（僅前 10 州）。
- **脆弱性**（曝險集中在少數可被針對的產品／公司，2026-11-08 自出口依賴拆出）：`top1_hs4_share`（對中出口最大 HS4 商品占比）、`hhi_hs4`；可選 `tariff_exposed_share_2025`（僅前 10 州）。例：新墨西哥 94% 對中出口是 Intel 處理器（HS 854231），北卡 57% 是單一藥廠生物製劑。
- **進口依賴**（州經濟靠中國供應）：`imports_china_pct_gdp`、`imports_china_share`。
- **資產與其他**（預設不計入）：`afida_china_acres_2024`。
- 子分數 = 該組勾選指標在所有州中的百分位平均；總分 = 子分數平均（出口依賴／進口依賴／脆弱性三個概念等權，不對單一指標加權）。基準年可切換（2020–2026）；「貿易對象」可改以對台指標計算。
- 另存 `hhi_hs4`、`top3_hs4_share`、2020–2025 合計口徑 `*_pct_gdp_2020_2025`。

## 3. 核對結果
| 項目 | 我算的 | 官方／全國合計 | 差異 | 備註 |
|---|---|---|---|---|
| exports China 2020 | 123.8 | 124.6 | -0.6% | 未知州/其他 0.8 |
| exports China 2021 | 150.5 | 151.4 | -0.6% | 未知州/其他 0.9 |
| exports China 2022 | 152.7 | 154.0 | -0.8% | 未知州/其他 1.3 |
| exports China 2023 | 146.0 | 147.6 | -1.1% | 未知州/其他 1.6 |
| exports China 2024 | 141.7 | 143.3 | -1.1% | 未知州/其他 1.6 |
| exports China 2025 | 104.6 | 106.0 | -1.3% | 未知州/其他 1.4 |
| exports China 2026 | 82.3 | 83.5 | -1.4% | 未知州/其他 1.2 |
| exports Taiwan 2020 | 29.9 | 30.2 | -1.2% | 未知州/其他 0.4 |
| exports Taiwan 2021 | 36.4 | 36.8 | -1.2% | 未知州/其他 0.4 |
| exports Taiwan 2022 | 43.3 | 43.9 | -1.5% | 未知州/其他 0.7 |
| exports Taiwan 2023 | 39.2 | 40.0 | -1.9% | 未知州/其他 0.8 |
| exports Taiwan 2024 | 41.7 | 42.5 | -1.8% | 未知州/其他 0.8 |
| exports Taiwan 2025 | 53.8 | 54.8 | -1.7% | 未知州/其他 0.9 |
| exports Taiwan 2026 | 43.4 | 44.2 | -1.8% | 未知州/其他 0.8 |
| exports World 2020 | 1384.0 | 1430.0 | -3.2% | 未知州/其他 46.0 |
| exports World 2021 | 1702.7 | 1757.7 | -3.1% | 未知州/其他 55.0 |
| exports World 2022 | 2006.8 | 2072.6 | -3.2% | 未知州/其他 65.9 |
| exports World 2023 | 1953.0 | 2021.9 | -3.4% | 未知州/其他 68.9 |
| exports World 2024 | 1989.4 | 2063.0 | -3.6% | 未知州/其他 73.6 |
| exports World 2025 | 2095.1 | 2179.9 | -3.9% | 未知州/其他 84.8 |
| exports World 2026 | 1773.5 | 1847.5 | -4.0% | 未知州/其他 74.0 |
| imports China 2020 | 428.7 | 432.5 | -0.9% | 未知州/其他 3.8 |
| imports China 2021 | 499.8 | 504.2 | -0.9% | 未知州/其他 4.4 |
| imports China 2022 | 531.6 | 536.3 | -0.9% | 未知州/其他 4.6 |
| imports China 2023 | 422.5 | 427.2 | -1.1% | 未知州/其他 4.7 |
| imports China 2024 | 435.2 | 440.3 | -1.2% | 未知州/其他 5.1 |
| imports China 2025 | 299.9 | 308.7 | -2.8% | 未知州/其他 8.7 |
| imports China 2026 | 206.0 | 215.0 | -4.2% | 未知州/其他 9.0 |
| imports Taiwan 2020 | 59.8 | 60.4 | -1.0% | 未知州/其他 0.6 |
| imports Taiwan 2021 | 76.4 | 77.0 | -0.8% | 未知州/其他 0.6 |
| imports Taiwan 2022 | 90.9 | 91.7 | -0.9% | 未知州/其他 0.8 |
| imports Taiwan 2023 | 86.9 | 87.8 | -1.0% | 未知州/其他 0.9 |
| imports Taiwan 2024 | 115.4 | 116.3 | -0.8% | 未知州/其他 0.9 |
| imports Taiwan 2025 | 200.3 | 201.4 | -0.5% | 未知州/其他 1.1 |
| imports Taiwan 2026 | 214.0 | 215.3 | -0.6% | 未知州/其他 1.3 |
| imports World 2020 | 2313.7 | 2331.5 | -0.8% | 未知州/其他 17.8 |
| imports World 2021 | 2808.4 | 2828.5 | -0.7% | 未知州/其他 20.1 |
| imports World 2022 | 3217.6 | 3239.7 | -0.7% | 未知州/其他 22.2 |
| imports World 2023 | 3052.9 | 3076.6 | -0.8% | 未知州/其他 23.6 |
| imports World 2024 | 3239.3 | 3263.9 | -0.8% | 未知州/其他 24.6 |
| imports World 2025 | 3384.2 | 3414.5 | -0.9% | 未知州/其他 30.3 |
| imports World 2026 | 2740.2 | 2768.9 | -1.0% | 未知州/其他 28.7 |
| USCBC 2024 goods exports TX | 22.5 | 21.5 | +4.8% | USCBC 用同一 Census 起運州資料 |
| USCBC 2024 goods exports CA | 15.0 | 14.8 | +1.5% | USCBC 用同一 Census 起運州資料 |
| USCBC 2024 goods exports WA | 11.9 | 6.6 | +79.9% | USCBC 用同一 Census 起運州資料 |
| USCBC 2024 goods exports IN | 5.1 | 6.1 | -17.1% | USCBC 用同一 Census 起運州資料 |
| USCBC 2024 goods exports NC | 5.9 | 6.1 | -2.9% | USCBC 用同一 Census 起運州資料 |
| USCBC 2024 goods exports OR | 5.8 | 5.7 | +2.3% | USCBC 用同一 Census 起運州資料 |
| USCBC 2024 goods exports IL | 4.7 | 5.6 | -15.9% | USCBC 用同一 Census 起運州資料 |
| USCBC 2024 goods exports KY | 4.3 | 4.7 | -8.2% | USCBC 用同一 Census 起運州資料 |
| USCBC 2024 goods exports AL | 4.3 | 4.2 | +1.2% | USCBC 用同一 Census 起運州資料 |
| USCBC 2024 goods exports LA | 10.1 | 4.1 | +145.5% | USCBC 用同一 Census 起運州資料 |
| AFIDA China acres 2024 | 247661 | 247659 | +0.001% | USDA 公布 247,659 |

說明：各州加總低於全國合計 1–4%，差額是 Census 標為「未知州／其他」的紀錄（出口尤其是世界合計，因為有部分無法歸屬起運州）。USCBC 的州別商品出口與 Census 起運州原始值在德州、加州、奧勒岡、阿拉巴馬一致（±5%），但路易斯安那（4.1 vs 10.1 十億）與華盛頓（6.6 vs 11.9）差很大，顯示 USCBC 對港口州的轉運貨物（黃豆、飛機）做了產地調整；本專案保留 Census 原始起運州值，解讀時要注意。

## 4. 2025 年曝險分數前 20（預設指標；詳見儀表板，可改基準年與指標）
| state   | state_name_zh   |   score |   s_export |   s_import |   exp_china_pct_gdp_2025 |   exp_china_share_2025 |   imp_china_pct_gdp_2025 |   imp_china_share_2025 |   top_hs4_2024 | top_hs4_desc_2024                        |   top_hs4_share_2024 |
|:--------|:----------------|--------:|-----------:|-----------:|-------------------------:|-----------------------:|-------------------------:|-----------------------:|---------------:|:-----------------------------------------|---------------------:|
| NM      | 新墨西哥        |   0.937 |      1     |      0.874 |                    2.033 |                  0.203 |                    1.213 |                  0.151 |           8542 | ELECTRONIC INTEGRATED CIRCUITS & MICROAS |                0.82  |
| WA      | 華盛頓州        |   0.832 |      0.955 |      0.709 |                    1.141 |                  0.156 |                    0.708 |                  0.114 |           8800 | CIVILIAN AIRCRAFT, ENGINES, AND PARTS    |                0.393 |
| TN      | 田納西          |   0.819 |      0.742 |      0.896 |                    0.44  |                  0.068 |                    2.221 |                  0.109 |           9018 | MEDICAL, SURGICAL, DENTAL OR VET INST, N |                0.215 |
| KY      | 肯塔基          |   0.767 |      0.923 |      0.611 |                    1.498 |                  0.091 |                    1.476 |                  0.048 |           8800 | CIVILIAN AIRCRAFT, ENGINES, AND PARTS    |                0.606 |
| AL      | 阿拉巴馬        |   0.761 |      0.897 |      0.626 |                    0.59  |                  0.085 |                    0.842 |                  0.082 |           8703 | MOTOR CARS & VEHICLES FOR TRANSPORTING P |                0.696 |
| MN      | 明尼蘇達        |   0.742 |      0.6   |      0.883 |                    0.299 |                  0.065 |                    1.145 |                  0.158 |           9018 | MEDICAL, SURGICAL, DENTAL OR VET INST, N |                0.133 |
| MS      | 密西西比        |   0.731 |      0.652 |      0.809 |                    0.346 |                  0.04  |                    1.398 |                  0.099 |           9018 | MEDICAL, SURGICAL, DENTAL OR VET INST, N |                0.279 |
| SC      | 南卡羅來納      |   0.718 |      0.512 |      0.924 |                    0.498 |                  0.049 |                    1.978 |                  0.133 |           8703 | MOTOR CARS & VEHICLES FOR TRANSPORTING P |                0.276 |
| CA      | 加州            |   0.689 |      0.426 |      0.952 |                    0.239 |                  0.055 |                    1.77  |                  0.156 |           9031 | MACHINES, NESOI IN CHAPTER 90; PROFILE P |                0.089 |
| NC      | 北卡羅來納      |   0.688 |      0.903 |      0.473 |                    0.741 |                  0.151 |                    0.598 |                  0.053 |           3002 | HUMAN BLOOD; ANIMAL BLOOD; ANTISERA, VAC |                0.57  |
| IN      | 印第安納        |   0.676 |      0.666 |      0.687 |                    0.586 |                  0.046 |                    1.76  |                  0.062 |           3002 | HUMAN BLOOD; ANIMAL BLOOD; ANTISERA, VAC |                0.355 |
| OH      | 俄亥俄          |   0.674 |      0.684 |      0.663 |                    0.31  |                  0.054 |                    0.824 |                  0.093 |           8800 | CIVILIAN AIRCRAFT, ENGINES, AND PARTS    |                0.234 |
| GA      | 喬治亞          |   0.672 |      0.601 |      0.742 |                    0.32  |                  0.05  |                    1.381 |                  0.086 |           8800 | CIVILIAN AIRCRAFT, ENGINES, AND PARTS    |                0.131 |
| OR      | 奧勒岡          |   0.664 |      0.981 |      0.347 |                    1.585 |                  0.195 |                    0.424 |                  0.047 |           8542 | ELECTRONIC INTEGRATED CIRCUITS & MICROAS |                0.688 |
| NV      | 內華達          |   0.622 |      0.425 |      0.818 |                    0.185 |                  0.041 |                    1.394 |                  0.109 |           2603 | COPPER ORES AND CONCENTRATES             |                0.409 |
| SD      | 南達科他        |   0.61  |      0.63  |      0.589 |                    0.135 |                  0.06  |                    0.291 |                  0.155 |           0206 | ED OFFAL, BOVINE, SWINE, SHEEP, GOAT, HO |                0.306 |
| IL      | 伊利諾          |   0.592 |      0.298 |      0.886 |                    0.236 |                  0.037 |                    1.881 |                  0.111 |           1201 | SOYBEANS, WHETHER OR NOT BROKEN          |                0.308 |
| WI      | 威斯康辛        |   0.579 |      0.323 |      0.835 |                    0.212 |                  0.037 |                    1.092 |                  0.143 |           9022 | X-RAYS,ALPHA,BETA,GAMMA ETC; PARTS AND A |                0.065 |
| TX      | 德州            |   0.565 |      0.531 |      0.598 |                    0.505 |                  0.033 |                    0.944 |                  0.067 |           2711 | PETROLEUM GASES & OTHER GASEOUS HYDROCAR |                0.219 |
| MA      | 麻薩諸塞        |   0.555 |      0.755 |      0.355 |                    0.347 |                  0.073 |                    0.323 |                  0.061 |           8486 | MACH,APP MANUF SEMICON BOULES ETC;C84 NT |                0.402 |

## 5. 2024 年對中出口前 20 州與最大宗出口商品（HS4，起運州口徑）
| state   | state_name_zh   |   exports_china_usd_mn |   exports_china_share |   exports_china_pct_gdp |   top_hs4_2024 | top_hs4_desc_2024                                  |   top_hs4_share_2024 |
|:--------|:----------------|-----------------------:|----------------------:|------------------------:|---------------:|:---------------------------------------------------|---------------------:|
| TX      | 德州            |               22533.6  |                 0.049 |                   0.803 |           2711 | PETROLEUM GASES & OTHER GASEOUS HYDROCARBONS       |                0.219 |
| CA      | 加州            |               15025.6  |                 0.082 |                   0.371 |           9031 | MACHINES, NESOI IN CHAPTER 90; PROFILE PROJECT, PT |                0.089 |
| WA      | 華盛頓州        |               11874.4  |                 0.205 |                   1.403 |           8800 | CIVILIAN AIRCRAFT, ENGINES, AND PARTS              |                0.393 |
| LA      | 路易斯安那      |               10065.1  |                 0.117 |                   3.046 |           1201 | SOYBEANS, WHETHER OR NOT BROKEN                    |                0.583 |
| NC      | 北卡羅來納      |                5920.19 |                 0.137 |                   0.692 |           3002 | HUMAN BLOOD; ANIMAL BLOOD; ANTISERA, VACCINES ETC  |                0.57  |
| OR      | 奧勒岡          |                5829    |                 0.172 |                   1.769 |           8542 | ELECTRONIC INTEGRATED CIRCUITS & MICROASSEMBL, PTS |                0.688 |
| IN      | 印第安納        |                5058.22 |                 0.084 |                   0.971 |           3002 | HUMAN BLOOD; ANIMAL BLOOD; ANTISERA, VACCINES ETC  |                0.355 |
| IL      | 伊利諾          |                4710.35 |                 0.057 |                   0.401 |           1201 | SOYBEANS, WHETHER OR NOT BROKEN                    |                0.308 |
| KY      | 肯塔基          |                4315.51 |                 0.09  |                   1.454 |           8800 | CIVILIAN AIRCRAFT, ENGINES, AND PARTS              |                0.606 |
| AL      | 阿拉巴馬        |                4251.63 |                 0.157 |                   1.315 |           8703 | MOTOR CARS & VEHICLES FOR TRANSPORTING PERSONS     |                0.696 |
| MA      | 麻薩諸塞        |                3890.35 |                 0.111 |                   0.498 |           8486 | MACH,APP MANUF SEMICON BOULES ETC;C84 NT 11(C);PT  |                0.402 |
| TN      | 田納西          |                3457.31 |                 0.088 |                   0.619 |           9018 | MEDICAL, SURGICAL, DENTAL OR VET INST, NO ELEC, PT |                0.215 |
| PA      | 賓夕法尼亞      |                3448.51 |                 0.064 |                   0.342 |           2701 | COAL; BRIQUETTES, OVOIDS ETC. MFR FROM COAL        |                0.126 |
| SC      | 南卡羅來納      |                3418.16 |                 0.09  |                   0.959 |           8703 | MOTOR CARS & VEHICLES FOR TRANSPORTING PERSONS     |                0.276 |
| GA      | 喬治亞          |                3054.63 |                 0.057 |                   0.345 |           8800 | CIVILIAN AIRCRAFT, ENGINES, AND PARTS              |                0.131 |
| OH      | 俄亥俄          |                2989.95 |                 0.052 |                   0.322 |           8800 | CIVILIAN AIRCRAFT, ENGINES, AND PARTS              |                0.234 |
| NY      | 紐約            |                2957.51 |                 0.031 |                   0.127 |           7113 | ARTICLES OF JEWELRY & PTS, OF PREC METAL OR CLAD   |                0.162 |
| NJ      | 紐澤西          |                2166.44 |                 0.05  |                   0.256 |           3304 | BEAUTY, MAKE-UP & SKIN-CARE PREP; MANICURE ETC PRP |                0.111 |
| MI      | 密西根          |                2062.56 |                 0.033 |                   0.294 |           8708 | PARTS & ACCESS FOR MOTOR VEHICLES (HEAD 8701-8705) |                0.199 |
| MN      | 明尼蘇達        |                2005.9  |                 0.075 |                   0.403 |           9018 | MEDICAL, SURGICAL, DENTAL OR VET INST, NO ELEC, PT |                0.133 |

## 5b. 台美貿易與「對中／對台」相對依賴比（2026-11-08 新增）
配色：中國＝紅、台灣＝藍（地圖、散點、表格長條、州詳情序列、雷達圖皆依此；雷達圖多州以深淺與線型區分）。儀表板「貿易對象」可把分數改以對台指標計算；對中與對台的總分與三個子分數同時計算，可在散點圖 X／Y 與地圖變數中並列（預設散點 X = 對中總分、Y = 對台總分，45° 虛線上方表示對台曝險高於對中）；另有 **中／台出口比**（對中出口 ÷ 對台出口）與 **中／台進口比**，>1 表示該州與中國往來大於與台灣（對數尺度）。州詳情頁並列對中／對台的年度金額、占比與相對依賴比走勢，前十大商品可切換對象。

全美（各州加總，十億美元）：
|   year |   exports_china_usd_mn |   exports_taiwan_usd_mn |   imports_china_usd_mn |   imports_taiwan_usd_mn |   ratio_exp |   ratio_imp |
|-------:|-----------------------:|------------------------:|-----------------------:|------------------------:|------------:|------------:|
|   2020 |                  123.8 |                    29.9 |                  428.7 |                    59.8 |         4.1 |         7.2 |
|   2021 |                  150.5 |                    36.4 |                  499.8 |                    76.4 |         4.1 |         6.5 |
|   2022 |                  152.7 |                    43.3 |                  531.6 |                    90.9 |         3.5 |         5.8 |
|   2023 |                  146   |                    39.2 |                  422.5 |                    86.9 |         3.7 |         4.9 |
|   2024 |                  141.7 |                    41.7 |                  435.2 |                   115.4 |         3.4 |         3.8 |
|   2025 |                  104.6 |                    53.8 |                  299.9 |                   200.3 |         1.9 |         1.5 |
|   2026 |                   82.3 |                    43.4 |                  206   |                   214   |         1.9 |         1   |

2024 年對台出口前 20 州（含最大宗商品）：
| state   | state_name_zh   |   exports_taiwan_usd_mn |   exports_taiwan_share |   exports_taiwan_pct_gdp |   imports_taiwan_usd_mn |   ratio_exp |   ratio_imp |   top_hs4_tw | top_hs4_tw_desc                          |   top_hs4_tw_share |
|:--------|:----------------|------------------------:|-----------------------:|-------------------------:|------------------------:|------------:|------------:|-------------:|:-----------------------------------------|-------------------:|
| TX      | 德州            |               11553.5   |                  0.025 |                    0.412 |               14198.4   |       1.95  |       2.546 |         2709 | CRUDE OIL FROM PETROLEUM AND BITUMINOUS  |              0.555 |
| CA      | 加州            |                9558.67  |                  0.052 |                    0.236 |               40467.6   |       1.572 |       3.051 |         8473 | PARTS ETC FOR TYPEWRITERS & OTHER OFFICE |              0.224 |
| WA      | 華盛頓州        |                2070.86  |                  0.036 |                    0.245 |                1572.2   |       5.734 |       7.132 |         8800 | CIVILIAN AIRCRAFT, ENGINES, AND PARTS    |              0.367 |
| NY      | 紐約            |                1767.53  |                  0.019 |                    0.076 |                2204.03  |       1.673 |       8.453 |         8542 | ELECTRONIC INTEGRATED CIRCUITS & MICROAS |              0.418 |
| AZ      | 亞利桑那        |                1322.52  |                  0.041 |                    0.233 |                3575.12  |       1.299 |       1.495 |         8542 | ELECTRONIC INTEGRATED CIRCUITS & MICROAS |              0.335 |
| OH      | 俄亥俄          |                1183.02  |                  0.021 |                    0.128 |                1775.04  |       2.527 |       5.758 |         9801 | EXPTS OF REPAIRED IMPTS; IMPTS OF RETURN |              0.524 |
| GA      | 喬治亞          |                 881.678 |                  0.016 |                    0.1   |                2914.66  |       3.465 |       6.158 |         8542 | ELECTRONIC INTEGRATED CIRCUITS & MICROAS |              0.189 |
| OR      | 奧勒岡          |                 833.722 |                  0.025 |                    0.253 |                4504.11  |       6.992 |       0.595 |         8486 | MACH,APP MANUF SEMICON BOULES ETC;C84 NT |              0.497 |
| NJ      | 紐澤西          |                 824.759 |                  0.019 |                    0.097 |                2586.03  |       2.627 |       5.516 |         9803 | EXPORTS MILITARY APPAREL & MILITARY EQUI |              0.145 |
| IL      | 伊利諾          |                 807.286 |                  0.01  |                    0.069 |                4386.19  |       5.835 |       9.574 |         1201 | SOYBEANS, WHETHER OR NOT BROKEN          |              0.237 |
| MA      | 麻薩諸塞        |                 751.373 |                  0.021 |                    0.096 |                 581.396 |       5.178 |       5.872 |         8486 | MACH,APP MANUF SEMICON BOULES ETC;C84 NT |              0.243 |
| LA      | 路易斯安那      |                 730.741 |                  0.008 |                    0.221 |                 252.813 |      13.774 |       4.684 |         2711 | PETROLEUM GASES & OTHER GASEOUS HYDROCAR |              0.504 |
| WI      | 威斯康辛        |                 661.181 |                  0.024 |                    0.143 |                1213.38  |       2.349 |       5.252 |         8471 | AUTOMATIC DATA PROCESS MACHINES; MAGN RE |              0.231 |
| VA      | 維吉尼亞        |                 656.958 |                  0.03  |                    0.085 |                 871.572 |       2.094 |       6.555 |         8542 | ELECTRONIC INTEGRATED CIRCUITS & MICROAS |              0.45  |
| MN      | 明尼蘇達        |                 641.514 |                  0.024 |                    0.129 |                 847.824 |       3.127 |       7.912 |         9031 | MACHINES, NESOI IN CHAPTER 90; PROFILE P |              0.384 |
| PA      | 賓夕法尼亞      |                 494.046 |                  0.009 |                    0.049 |                1170.02  |       6.98  |      14.143 |         3004 | MEDICAMENTS NESOI, MIXED OR NOT, IN DOSA |              0.147 |
| ID      | 愛達荷          |                 474.616 |                  0.11  |                    0.366 |                 701.666 |       0.377 |       0.433 |         8541 | SEMICON DEV;PHOTOSENS;LED;MOUNT PIEZOELE |              0.597 |
| TN      | 田納西          |                 414.577 |                  0.011 |                    0.074 |                7343.03  |       8.339 |       2.852 |         8471 | AUTOMATIC DATA PROCESS MACHINES; MAGN RE |              0.304 |
| NC      | 北卡羅來納      |                 403.471 |                  0.009 |                    0.047 |                1293.99  |      14.673 |       5.456 |         3304 | BEAUTY, MAKE-UP & SKIN-CARE PREP; MANICU |              0.13  |
| SC      | 南卡羅來納      |                 391.704 |                  0.01  |                    0.11  |                1023.06  |       8.726 |       8.955 |         8703 | MOTOR CARS & VEHICLES FOR TRANSPORTING P |              0.361 |

中／台出口比最低（台灣相對重要）前 10 州，2024，州總出口 > 50 億：
| state   | state_name_zh   |   exports_china_usd_mn |   exports_taiwan_usd_mn |   ratio_exp |   imports_china_usd_mn |   imports_taiwan_usd_mn |   ratio_imp |
|:--------|:----------------|-----------------------:|------------------------:|------------:|-----------------------:|------------------------:|------------:|
| AZ      | 亞利桑那        |                1717.91 |                 1322.52 |        1.3  |                5343.7  |                 3575.12 |        1.49 |
| ND      | 北達科他        |                  35.6  |                   27.32 |        1.3  |                 153.06 |                   14.11 |       10.85 |
| CA      | 加州            |               15025.6  |                 9558.67 |        1.57 |              123477    |                40467.6  |        3.05 |
| NY      | 紐約            |                2957.51 |                 1767.52 |        1.67 |               18629.6  |                 2204.04 |        8.45 |
| TX      | 德州            |               22533.6  |                11553.5  |        1.95 |               36146.4  |                14198.4  |        2.55 |
| VA      | 維吉尼亞        |                1375.79 |                  656.96 |        2.09 |                5713.2  |                  871.57 |        6.56 |
| WI      | 威斯康辛        |                1553.43 |                  661.18 |        2.35 |                6372.23 |                 1213.38 |        5.25 |
| AR      | 阿肯色          |                 226.01 |                   93.73 |        2.41 |                1036.55 |                  127.94 |        8.1  |
| OH      | 俄亥俄          |                2989.95 |                 1183.02 |        2.53 |               10219.8  |                 1775.03 |        5.76 |
| NE      | 內布拉斯加      |                 652.68 |                  255.04 |        2.56 |                 752.88 |                  116.76 |        6.45 |

中／台出口比最高前 10 州，2024：
| state   | state_name_zh   |   exports_china_usd_mn |   exports_taiwan_usd_mn |   ratio_exp |   imports_china_usd_mn |   imports_taiwan_usd_mn |   ratio_imp |
|:--------|:----------------|-----------------------:|------------------------:|------------:|-----------------------:|------------------------:|------------:|
| IN      | 印第安納        |                5058.22 |                  262.94 |       19.24 |                9277.47 |                 1170.62 |        7.93 |
| AK      | 阿拉斯加        |                1513.49 |                   90.63 |       16.7  |                  92.1  |                   70.43 |        1.31 |
| NC      | 北卡羅來納      |                5920.19 |                  403.47 |       14.67 |                7060.2  |                 1293.99 |        5.46 |
| LA      | 路易斯安那      |               10065.1  |                  730.74 |       13.77 |                1184.19 |                  252.81 |        4.68 |
| KY      | 肯塔基          |                4315.51 |                  327.88 |       13.16 |                6730.14 |                 7952.09 |        0.85 |
| AL      | 阿拉巴馬        |                4251.63 |                  370.72 |       11.47 |                3995.61 |                  302.25 |       13.22 |
| SC      | 南卡羅來納      |                3418.16 |                  391.7  |        8.73 |                9161.54 |                 1023.06 |        8.96 |
| TN      | 田納西          |                3457.31 |                  414.58 |        8.34 |               20940.9  |                 7343.03 |        2.85 |
| NH      | 新罕布夏        |                 368.93 |                   44.49 |        8.29 |                 533.11 |                  226.54 |        2.35 |
| MI      | 密西根          |                2062.56 |                  257.36 |        8.01 |                8922.88 |                 1407.12 |        6.34 |

觀察：(1) 2025 年起對中出口與進口雙雙下跌，而對台出口（原油、LNG、半導體設備）與自台進口（AI 伺服器、晶片）暴增，全美中／台進口比從 2020 年 7.2 倍降到 2026 年 1–9 月 1.0 倍；(2) 台灣相對重要的州集中在半導體與能源：亞利桑那（積體電路）、加州、紐約、德州（原油）；(3) 中國相對重要的州是農業與生技／航太：印第安納、北卡、路易斯安那、肯塔基、阿拉巴馬。

## 6. 重跑
`cd scripts && python3.12 01_fetch_census.py && python3.12 02_clean_afida.py && python3.12 02_clean_uscbc.py && python3.12 02_clean_bea_gdp.py && python3.12 03_build_panel.py && python3.12 04_exposure.py && python3.12 06_validate.py && python3.12 05_build_dashboard.py`
（Census 快取在 `data/raw/census/`，刪除對應 JSON 即重抓；更新 2026 YTD 月份改 `01_fetch_census.py` 的 `LATEST`。）

## 7. 授權與引用
本 repo 的程式碼與衍生資料以 MIT 授權釋出；API 金鑰（`.env`）與原始下載檔不隨 repo 發布（見 `data/raw/MANIFEST.md`）。資料來源條款與引用：

| 來源 | 條款 | 引用 |
|---|---|---|
| U.S. Census Bureau, USA Trade Online / International Trade API | 美國政府公開資料（public domain） | U.S. Census Bureau. *U.S. International Trade in Goods: State Exports (Origin of Movement) and Imports (State of Destination)*. https://api.census.gov/data/timeseries/intltrade |
| BEA Regional Accounts (SAGDP) | 美國政府公開資料 | U.S. Bureau of Economic Analysis. *GDP by State*. https://apps.bea.gov/regional |
| USDA FSA, AFIDA Annual Report 2024 | 美國政府公開資料 | USDA Farm Service Agency. 2026. *Foreign Holdings of U.S. Agricultural Land through December 31, 2024*. |
| US-China Business Council, *US Exports to China 2025* | 報告公開發布；本 repo 只收錄前 10 州摘錄 | US-China Business Council. 2025. *US Exports to China: Goods and Services Exports to China and the Jobs They Support, by State and Congressional District*. |

## 8. 設計決策與變更紀錄（2026-11-07／08）

**動機**：延伸國家層級的「對中依賴與曝險」方法到美國各州，量化各州對中國貿易與投資的依賴，並找出各州對中最大宗出口商品；時間範圍 2020–2026。

### 8.1 資料取得
- Census 貿易 API 現在強制要 key（無 key 直接導到 missing_key）；第一次貼的 key 少一個字元（39/40），第二次正確。BEA API key 也已申請，但 BEA MNE 州級表只列加、法、德、日、荷、瑞、英七國，中國併入「其他」，所以**中資在美 FDI 按州未納入**；Rhodium US-China Investment Hub 只到 2020 年。
- Census API 對大檔（HS6、世界 HS4）常回 Cloudflare 524，腳本改為 8 次重試＋快取；世界 HS4 不需要，放棄。
- USCBC 網站 403 但 PDF 直連可取；全州服務出口只有地圖圖像，僅前 10 州有數值。USDA AFIDA 2024 年報頁面改版，PDF 直連可取，Report 11 用 pdftotext -layout 解析州小計（總數 247,661 ≈ USDA 公布 247,659）。
- 台灣（CTY_CODE 5830）於 11-08 加入同一套抓取。

### 8.2 口徑決策
- 出口 = Census「起運州」(Origin of Movement)，進口 = 「目的州」。起運州不等於生產州：路易斯安那黃豆、華盛頓飛機與 USCBC 的產地調整值差一倍以上，保留 Census 原值並在 README／說明頁標註。
- 各州加總低於全國 1–4%（未歸屬州紀錄），列於核對表。
- 年值用 `time=YYYY-12` 的年累計欄；2026 用 1–9 月累計（YTD），GDP 分母用 2025。

### 8.3 曝險分數的演變
1. 初版兩概念：出口依賴（出口占 GDP、占州總出口、最大商品集中度）＋進口依賴。
2. 新墨西哥以 0.94 排第一，追查後發現 82–94% 對中出口是單一 HS6（854231 處理器，Intel Rio Rancho 廠）。結論：集中度是脆弱性不是依賴。
3. 改為三概念：**出口依賴**（占 GDP、占州總出口）／**進口依賴**／**脆弱性**（最大 HS4 商品占比、HHI；可選報復關稅曝險）。HHI = Σ sᵢ²（HS4 占比平方和）。加州因此從 0.69 降到 0.54（量大但分散）。
4. 「貿易對象」切換（中國／台灣）；對中與對台的總分與子分數同時計算並可在散點圖 X／Y 並列（預設對中總分 × 對台總分，45° 線）；另有中／台出口比與進口比（對數尺度）。

### 8.4 視覺
- 配色：中國＝紅、台灣＝藍（地圖色階、散點、表格長條、州詳情序列、雷達圖）；雷達圖多州以深淺＋線型區分，中位數基準線灰色。
- 雷達圖軸 = 各指標百分位；州詳情頁含對中／對台年度金額、占比、相對依賴比走勢與前十大商品（HS2／HS4／HS6、對象可切換）。

### 8.5 主要發現（2024 結構年；2025 起受關稅戰影響）
- 對中出口前五州：德州 225 億（LNG／石油氣）、加州 150 億、華盛頓 119 億（飛機）、路易斯安那 101 億（黃豆 58%）、北卡 59 億（生物製劑 57%）。
- 對台相對重要的州（中／台出口比最低）：亞利桑那 1.3×、加州 1.6×、紐約 1.7×、德州 2.0×；對中相對重要：印第安納 19×、阿拉斯加 17×、北卡 15×、路易斯安那 14×、肯塔基 13×。
- 全美自台進口 2025 年 2,003 億、2026 年 1–9 月 2,140 億，已超過自中進口（2,060 億）；中／台進口比由 2020 年 7.2× 降到 1.0×。
- 政治解讀的保留：州不做外交；對中依賴高的農業與製造州在 2023–2025 多通過限制中資農地或友台決議，經濟依賴只表現為對關稅的遊說，不會表現為疏遠台灣；對台依賴高的半導體／能源州正是政治上最挺台的州。

### 8.6 發布
- 2026-11-08 發布至 https://github.com/chentitus/us-states-china-exposure 與 GitHub Pages；`.env` 與原始下載檔不上傳。姊妹專案：https://github.com/chentitus/china-exposure-dashboard
