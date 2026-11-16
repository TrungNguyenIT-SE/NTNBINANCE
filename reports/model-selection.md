# Stage O model-selection report

- Date: 16/11/2026 (Asia/Saigon)
- Run ID: `36f8fca940ef7e7b`
- Champion candidate: **`NONE`**
- FINAL_HOLDOUT opened: **false**
- Result: **NO-GO**

## Validation and resource comparison

| Candidate | Family | Accuracy | Macro F1 | Brier | ECE | Net return | Latency ms/sample | Peak MiB | Artifact bytes | Resource gate |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `numeric_logistic` | numeric | 0.2308 | 0.1865 | 1.2124 | 0.6084 | -0.024002 | 0.0110 | 0.08 | 2043 | PASS |
| `numeric_xgboost` | numeric | 0.3846 | 0.3847 | 0.7664 | 0.2269 | -0.038422 | 0.0087 | 0.01 | 140523 | PASS |
| `image_logistic` | image | 0.2692 | 0.1975 | 1.3897 | 0.6992 | -0.050187 | 0.0248 | 1.06 | 66691 | PASS |
| `fusion_logistic` | fusion | 0.4615 | 0.3537 | 1.0581 | 0.5296 | -0.017208 | 0.0792 | 1.11 | 69439 | PASS |
| `fusion_xgboost` | fusion | 0.2308 | 0.2241 | 0.7001 | 0.2604 | -0.045772 | 0.0101 | 0.02 | 140743 | PASS |
| `numeric_v1_svc_c0.1_scale` | numeric | 0.5000 | 0.2222 | 0.6271 | 0.0354 | -0.017355 | 0.0530 | 0.09 | 13691 | PASS |
| `numeric_v1_svc_c0.1_auto` | numeric | 0.5000 | 0.2222 | 0.6271 | 0.0354 | -0.017355 | 0.0530 | 0.08 | 13680 | PASS |
| `numeric_v1_svc_c1_scale` | numeric | 0.3462 | 0.3667 | 0.7095 | 0.2667 | -0.049876 | 0.0522 | 0.08 | 13319 | PASS |
| `numeric_v1_svc_c1_auto` | numeric | 0.3462 | 0.3667 | 0.7096 | 0.2667 | -0.049876 | 0.0564 | 0.08 | 13308 | PASS |
| `numeric_v1_svc_c10_scale` | numeric | 0.3462 | 0.3714 | 0.7408 | 0.2867 | -0.051691 | 0.0668 | 0.08 | 12327 | PASS |
| `numeric_v1_svc_c10_auto` | numeric | 0.3462 | 0.3714 | 0.7540 | 0.2939 | -0.051691 | 0.0489 | 0.08 | 12316 | PASS |
| `numeric_v1_svc_c100_scale` | numeric | 0.3462 | 0.3714 | 0.7528 | 0.2946 | -0.051691 | 0.0726 | 0.08 | 12327 | PASS |
| `numeric_v1_svc_c100_auto` | numeric | 0.3462 | 0.3714 | 0.7667 | 0.3020 | -0.051691 | 0.0511 | 0.08 | 12316 | PASS |
| `numeric_v1_random_forest_d2_leaf1` | numeric | 0.3462 | 0.3222 | 0.7027 | 0.1431 | -0.027514 | 0.5397 | 0.31 | 176731 | PASS |
| `numeric_v1_extra_trees_d2_leaf1` | numeric | 0.4231 | 0.4199 | 0.6691 | 0.0466 | -0.020418 | 0.5537 | 0.31 | 178312 | PASS |
| `numeric_v1_random_forest_d2_leaf3` | numeric | 0.2692 | 0.2605 | 0.7048 | 0.1617 | -0.040222 | 0.5169 | 0.31 | 175499 | PASS |
| `numeric_v1_extra_trees_d2_leaf3` | numeric | 0.4231 | 0.4199 | 0.6684 | 0.0464 | -0.020418 | 0.5354 | 0.30 | 176728 | PASS |
| `numeric_v1_random_forest_d2_leaf5` | numeric | 0.2692 | 0.2628 | 0.7077 | 0.1873 | -0.043297 | 0.5283 | 0.31 | 172331 | PASS |
| `numeric_v1_extra_trees_d2_leaf5` | numeric | 0.4231 | 0.4238 | 0.6704 | 0.0435 | -0.025956 | 0.5459 | 0.30 | 169864 | PASS |
| `numeric_v1_random_forest_d4_leaf1` | numeric | 0.3462 | 0.3500 | 0.7223 | 0.2177 | -0.038028 | 0.4724 | 0.31 | 403631 | PASS |
| `numeric_v1_extra_trees_d4_leaf1` | numeric | 0.3077 | 0.3183 | 0.6938 | 0.2076 | -0.048736 | 0.4480 | 0.30 | 461717 | PASS |
| `numeric_v1_random_forest_d4_leaf3` | numeric | 0.2692 | 0.2836 | 0.7484 | 0.3279 | -0.053155 | 0.4650 | 0.31 | 365254 | PASS |
| `numeric_v1_extra_trees_d4_leaf3` | numeric | 0.1923 | 0.1908 | 0.6916 | 0.2332 | -0.068017 | 0.5717 | 0.30 | 389363 | PASS |
| `numeric_v1_random_forest_d4_leaf5` | numeric | 0.1923 | 0.1940 | 0.7382 | 0.2717 | -0.054870 | 0.4529 | 0.31 | 305053 | PASS |
| `numeric_v1_extra_trees_d4_leaf5` | numeric | 0.2692 | 0.2506 | 0.6895 | 0.1444 | -0.053695 | 0.4485 | 0.30 | 320890 | PASS |
| `numeric_v1_random_forest_d8_leaf1` | numeric | 0.3846 | 0.3896 | 0.7417 | 0.1424 | -0.033184 | 0.5355 | 0.31 | 725571 | PASS |
| `numeric_v1_extra_trees_d8_leaf1` | numeric | 0.3846 | 0.3959 | 0.7191 | 0.1900 | -0.042780 | 0.4903 | 0.30 | 1426147 | PASS |
| `numeric_v1_random_forest_d8_leaf3` | numeric | 0.3077 | 0.3146 | 0.7459 | 0.2997 | -0.042514 | 0.5159 | 0.31 | 504136 | PASS |
| `numeric_v1_extra_trees_d8_leaf3` | numeric | 0.3462 | 0.3610 | 0.7084 | 0.2128 | -0.047955 | 0.4879 | 0.30 | 681744 | PASS |
| `numeric_v1_random_forest_d8_leaf5` | numeric | 0.1923 | 0.1913 | 0.7434 | 0.2814 | -0.049422 | 0.4574 | 0.31 | 346598 | PASS |
| `numeric_v1_extra_trees_d8_leaf5` | numeric | 0.3462 | 0.3474 | 0.6895 | 0.0749 | -0.040505 | 0.5472 | 0.31 | 396764 | PASS |
| `numeric_v2_svc_c0.1_scale` | numeric | 0.5000 | 0.2222 | 0.6468 | 0.0814 | -0.017355 | 0.0506 | 0.09 | 17099 | PASS |
| `numeric_v2_svc_c0.1_auto` | numeric | 0.5000 | 0.2222 | 0.6468 | 0.0813 | -0.017355 | 0.0703 | 0.09 | 17088 | PASS |
| `numeric_v2_svc_c1_scale` | numeric | 0.3462 | 0.2619 | 0.6718 | 0.1739 | -0.037400 | 0.0483 | 0.09 | 16919 | PASS |
| `numeric_v2_svc_c1_auto` | numeric | 0.3077 | 0.2402 | 0.6775 | 0.1569 | -0.038717 | 0.0484 | 0.09 | 16908 | PASS |
| `numeric_v2_svc_c10_scale` | numeric | 0.2692 | 0.2078 | 0.7114 | 0.2385 | -0.050728 | 0.0606 | 0.09 | 16199 | PASS |
| `numeric_v2_svc_c10_auto` | numeric | 0.2692 | 0.2078 | 0.6989 | 0.2348 | -0.050728 | 0.0573 | 0.09 | 16188 | PASS |
| `numeric_v2_svc_c100_scale` | numeric | 0.2692 | 0.2078 | 0.7225 | 0.2386 | -0.050728 | 0.0702 | 0.09 | 16019 | PASS |
| `numeric_v2_svc_c100_auto` | numeric | 0.2692 | 0.2078 | 0.7092 | 0.2346 | -0.050728 | 0.0663 | 0.09 | 16008 | PASS |
| `numeric_v2_random_forest_d2_leaf1` | numeric | 0.3462 | 0.3340 | 0.7234 | 0.2212 | -0.027804 | 0.5285 | 0.30 | 175243 | PASS |
| `numeric_v2_extra_trees_d2_leaf1` | numeric | 0.1923 | 0.1442 | 0.6877 | 0.1920 | -0.047573 | 0.4778 | 0.30 | 177000 | PASS |
| `numeric_v2_random_forest_d2_leaf3` | numeric | 0.3077 | 0.2848 | 0.7294 | 0.1511 | -0.029203 | 0.4901 | 0.31 | 174539 | PASS |
| `numeric_v2_extra_trees_d2_leaf3` | numeric | 0.1923 | 0.1369 | 0.6868 | 0.1931 | -0.059173 | 0.5151 | 0.31 | 174712 | PASS |
| `numeric_v2_random_forest_d2_leaf5` | numeric | 0.3077 | 0.2848 | 0.7384 | 0.1563 | -0.029203 | 0.5459 | 0.31 | 167499 | PASS |
| `numeric_v2_extra_trees_d2_leaf5` | numeric | 0.1538 | 0.1185 | 0.6951 | 0.2361 | -0.053142 | 0.5146 | 0.31 | 173480 | PASS |
| `numeric_v2_random_forest_d4_leaf1` | numeric | 0.3077 | 0.3021 | 0.7917 | 0.2889 | -0.027009 | 0.5219 | 0.31 | 384358 | PASS |
| `numeric_v2_extra_trees_d4_leaf1` | numeric | 0.2308 | 0.1807 | 0.7092 | 0.2110 | -0.044260 | 0.4967 | 0.30 | 438044 | PASS |
| `numeric_v2_random_forest_d4_leaf3` | numeric | 0.3077 | 0.2848 | 0.7892 | 0.2397 | -0.029203 | 0.5149 | 0.31 | 344406 | PASS |
| `numeric_v2_extra_trees_d4_leaf3` | numeric | 0.1923 | 0.1902 | 0.7189 | 0.2305 | -0.046814 | 0.5155 | 0.30 | 388227 | PASS |
| `numeric_v2_random_forest_d4_leaf5` | numeric | 0.3077 | 0.3021 | 0.7889 | 0.2437 | -0.031420 | 0.4592 | 0.31 | 281037 | PASS |
| `numeric_v2_extra_trees_d4_leaf5` | numeric | 0.1923 | 0.1404 | 0.7198 | 0.2310 | -0.054283 | 0.5110 | 0.30 | 323450 | PASS |
| `numeric_v2_random_forest_d8_leaf1` | numeric | 0.3462 | 0.3340 | 0.7942 | 0.2771 | -0.027804 | 0.5436 | 0.31 | 632906 | PASS |
| `numeric_v2_extra_trees_d8_leaf1` | numeric | 0.2308 | 0.1807 | 0.7281 | 0.3097 | -0.044260 | 0.5415 | 0.31 | 1197407 | PASS |
| `numeric_v2_random_forest_d8_leaf3` | numeric | 0.3077 | 0.2848 | 0.7995 | 0.2673 | -0.029203 | 0.4604 | 0.31 | 438047 | PASS |
| `numeric_v2_extra_trees_d8_leaf3` | numeric | 0.1923 | 0.1541 | 0.7389 | 0.2562 | -0.053379 | 0.4798 | 0.30 | 671984 | PASS |
| `numeric_v2_random_forest_d8_leaf5` | numeric | 0.2692 | 0.2562 | 0.7923 | 0.2323 | -0.032820 | 0.5241 | 0.31 | 305853 | PASS |
| `numeric_v2_extra_trees_d8_leaf5` | numeric | 0.1923 | 0.1404 | 0.7297 | 0.2408 | -0.054283 | 0.5014 | 0.30 | 398796 | PASS |
| `numeric_v1_xgboost_cv` | numeric | 0.3846 | 0.3367 | 0.8254 | 0.1864 | -0.018834 | 0.0080 | 0.01 | 237576 | PASS |
| `numeric_v2_xgboost_cv` | numeric | 0.3462 | 0.3497 | 0.8751 | 0.2770 | -0.032375 | 0.0086 | 0.01 | 141065 | PASS |
| `numeric_v1_xgboost_validation` | numeric | 0.4615 | 0.4586 | 0.7982 | 0.2839 | -0.022814 | 0.0082 | 0.01 | 162849 | PASS |
| `numeric_v2_xgboost_validation` | numeric | 0.3846 | 0.3942 | 0.7781 | 0.2956 | -0.038708 | 0.0064 | 0.01 | 75294 | PASS |

## Selection decision

Locked Stage I baseline macro F1: `0.4607`.
Locked exit threshold (baseline + minimum gain): `0.4707`.
Best resource-eligible candidate: `numeric_v1_xgboost_validation` with macro F1 `0.4586`.
Delta versus baseline: `-0.0021`; delta versus exit threshold: `-0.0121`.
Selection reason: best resource-eligible candidate numeric_v1_xgboost_validation macro-F1=0.4586; locked requirement=0.4707.
No candidate is promoted to Stage P; Stage O remains incomplete.
Every evaluated candidate had negative cost-aware net return on validation.
It is not a production/live model. Every directional candidate remains subject to cost-aware validation and NO_TRADE policy.

## Experiment rounds and interpretation

1. Evaluated the locked numeric-v2, image-only and fusion candidates.
2. Tuned XGBoost with purged chronological TRAIN cross-validation.
3. Ran a bounded validation sensitivity analysis across XGBoost, calibrated SVC, Random Forest and Extra Trees families.
4. Stopped after the bounded family analysis failed the locked exit threshold.

The validation-tuned metrics are selection-biased and are retained as diagnostics, not as unbiased performance estimates. More searching on the same 26 validation samples would increase overfitting risk. The legitimate next step is more independent historical training/validation evidence and a versioned real-chart corpus, followed by a new Stage O run. Stage P must not begin from this NO-GO result.

## Image benchmark boundary

Image-only and fusion inputs are point-in-time synthetic 1H+15m charts.
Header/OCR text and axes are cropped; quality metrics are appended.
There is no versioned real-chart corpus. This measures pipeline contribution only.
It cannot establish generalization to screenshots supplied by users.

## Reproducibility

- Config hash: `3292fc9f8d67cb86fe3394263e2c3d5e07f06a98f161e9f1079ce06ec0211723`
- Split SHA-256: `2d7a0a201d371418d2282db85c82dfa28ebb52e9a21e7548560c015e1922a0b2`
- Labels SHA-256: `ca156100916c3d4d32e17711c5f25697317de8aeb900865da8f0d65852666e55`
- Clean manifest SHA-256: `ca988a80e7f4704272e317f35bd6dee1d01695a541d3cebea9a6719684c3b13b`
- Seed: `20261116`
- TRAIN/VALIDATION: `80` / `26`; holdout labels read: `0`.
- TRAIN rows rejected by feature-v2 warm-up: `10`; VALIDATION rejected: `0`.
- Champion artifact: not created because the exit gate failed.

All computation used existing local CPU and open-source dependencies.
New cash cost is **0 VNĐ**.
