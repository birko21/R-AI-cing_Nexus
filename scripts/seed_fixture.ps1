$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) { throw 'Run pnpm bootstrap before seeding fixtures.' }
& '.venv\Scripts\python.exe' scripts/generate_synthetic_fixtures.py --check
if ($LASTEXITCODE -ne 0) { throw "Synthetic fixture validation failed with exit code $LASTEXITCODE" }
& '.venv\Scripts\python.exe' scripts/generate_b0_forecast_manifest.py
if ($LASTEXITCODE -ne 0) { throw "B0 forecast manifest validation failed with exit code $LASTEXITCODE" }
& '.venv\Scripts\python.exe' scripts/generate_b1_forecast_manifest.py
if ($LASTEXITCODE -ne 0) { throw "B1 forecast manifest validation failed with exit code $LASTEXITCODE" }
& '.venv\Scripts\python.exe' scripts/generate_forecast_archive.py
if ($LASTEXITCODE -ne 0) { throw "Forecast archive validation failed with exit code $LASTEXITCODE" }
& '.venv\Scripts\python.exe' scripts/generate_feature_manifest.py
if ($LASTEXITCODE -ne 0) { throw "Feature manifest validation failed with exit code $LASTEXITCODE" }
& '.venv\Scripts\python.exe' scripts/generate_split_manifest.py
if ($LASTEXITCODE -ne 0) { throw "Split manifest validation failed with exit code $LASTEXITCODE" }
& '.venv\Scripts\python.exe' scripts/generate_metric_report.py
if ($LASTEXITCODE -ne 0) { throw "Metric report validation failed with exit code $LASTEXITCODE" }
& '.venv\Scripts\python.exe' scripts/generate_diagnostics_fixture.py
if ($LASTEXITCODE -ne 0) { throw "Diagnostics fixture validation failed with exit code $LASTEXITCODE" }
& '.venv\Scripts\python.exe' scripts/generate_registry_fixture.py
if ($LASTEXITCODE -ne 0) { throw "Registry fixture validation failed with exit code $LASTEXITCODE" }
& '.venv\Scripts\python.exe' scripts/generate_scraping_policy_fixture.py
if ($LASTEXITCODE -ne 0) { throw "Scraping policy fixture validation failed with exit code $LASTEXITCODE" }
& '.venv\Scripts\python.exe' scripts/generate_provider_capability_fixture.py
if ($LASTEXITCODE -ne 0) { throw "Provider capability fixture validation failed with exit code $LASTEXITCODE" }
& '.venv\Scripts\python.exe' scripts/generate_scraped_provenance_fixture.py
if ($LASTEXITCODE -ne 0) { throw "Scraped provenance fixture validation failed with exit code $LASTEXITCODE" }
& '.venv\Scripts\python.exe' scripts/generate_source_checkpoint_fixture.py
if ($LASTEXITCODE -ne 0) { throw "Source checkpoint fixture validation failed with exit code $LASTEXITCODE" }
& '.venv\Scripts\python.exe' scripts/generate_source_health_fixture.py
if ($LASTEXITCODE -ne 0) { throw "Source health fixture validation failed with exit code $LASTEXITCODE" }
& '.venv\Scripts\python.exe' scripts/generate_market_quote_fixture.py
if ($LASTEXITCODE -ne 0) { throw "Market quote fixture validation failed with exit code $LASTEXITCODE" }
& '.venv\Scripts\python.exe' scripts/generate_market_history_fixture.py
if ($LASTEXITCODE -ne 0) { throw "Market history fixture validation failed with exit code $LASTEXITCODE" }
& '.venv\Scripts\python.exe' scripts/generate_market_math_fixture.py
if ($LASTEXITCODE -ne 0) { throw "Market math fixture validation failed with exit code $LASTEXITCODE" }
& '.venv\Scripts\python.exe' scripts/generate_paper_settlement_fixture.py
if ($LASTEXITCODE -ne 0) { throw "Paper settlement fixture validation failed with exit code $LASTEXITCODE" }
& '.venv\Scripts\python.exe' scripts/generate_result_reconciliation_fixture.py
if ($LASTEXITCODE -ne 0) { throw "Result reconciliation fixture validation failed with exit code $LASTEXITCODE" }
& '.venv\Scripts\python.exe' scripts/generate_watchlist_fixture.py
if ($LASTEXITCODE -ne 0) { throw "Watchlist fixture validation failed with exit code $LASTEXITCODE" }
& '.venv\Scripts\python.exe' scripts/generate_alert_fixture.py
if ($LASTEXITCODE -ne 0) { throw "Alert fixture validation failed with exit code $LASTEXITCODE" }
& '.venv\Scripts\python.exe' scripts/generate_responsible_controls_fixture.py
if ($LASTEXITCODE -ne 0) { throw "Responsible controls fixture validation failed with exit code $LASTEXITCODE" }
& '.venv\Scripts\python.exe' scripts/generate_research_tool_fixture.py
if ($LASTEXITCODE -ne 0) { throw "Research tool fixture validation failed with exit code $LASTEXITCODE" }
& '.venv\Scripts\python.exe' scripts/generate_evidence_fixture.py
if ($LASTEXITCODE -ne 0) { throw "Evidence fixture validation failed with exit code $LASTEXITCODE" }
& '.venv\Scripts\python.exe' scripts/generate_egress_fixture.py
if ($LASTEXITCODE -ne 0) { throw "Egress fixture validation failed with exit code $LASTEXITCODE" }
& '.venv\Scripts\python.exe' scripts/generate_assistant_eval_fixture.py
if ($LASTEXITCODE -ne 0) { throw "Assistant evaluation fixture validation failed with exit code $LASTEXITCODE" }
& '.venv\Scripts\python.exe' scripts/generate_thoroughbred_feature_fixture.py
if ($LASTEXITCODE -ne 0) { throw "Thoroughbred feature fixture validation failed with exit code $LASTEXITCODE" }
& '.venv\Scripts\python.exe' scripts/generate_harness_scenario_fixture.py
if ($LASTEXITCODE -ne 0) { throw "Harness scenario fixture validation failed with exit code $LASTEXITCODE" }
& '.venv\Scripts\python.exe' scripts/generate_greyhound_feature_fixture.py
if ($LASTEXITCODE -ne 0) { throw "Greyhound feature fixture validation failed with exit code $LASTEXITCODE" }
& '.venv\Scripts\python.exe' scripts/generate_scenario_fixture.py
if ($LASTEXITCODE -ne 0) { throw "Scenario fixture validation failed with exit code $LASTEXITCODE" }
& '.venv\Scripts\python.exe' scripts/generate_challenger_study_fixture.py
if ($LASTEXITCODE -ne 0) { throw "Challenger study fixture validation failed with exit code $LASTEXITCODE" }
& '.venv\Scripts\python.exe' scripts/generate_sbom.py --write
if ($LASTEXITCODE -ne 0) { throw "SBOM generation failed with exit code $LASTEXITCODE" }
& '.venv\Scripts\python.exe' scripts/security_audit.py --write-report
if ($LASTEXITCODE -ne 0) { throw "Security audit failed with exit code $LASTEXITCODE" }
& '.venv\Scripts\python.exe' scripts/generate_operations_fixture.py
if ($LASTEXITCODE -ne 0) { throw "Operations fixture validation failed with exit code $LASTEXITCODE" }
& '.venv\Scripts\python.exe' scripts/generate_backup_fixture.py
if ($LASTEXITCODE -ne 0) { throw "Backup fixture validation failed with exit code $LASTEXITCODE" }
