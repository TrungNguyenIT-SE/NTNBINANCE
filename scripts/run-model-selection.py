"""Run the locked Stage O model-selection experiment."""

from pathlib import Path

from ntnbinance.model_selection import ModelSelectionPipeline

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    pipeline = ModelSelectionPipeline(
        project_root=ROOT,
        config_path=ROOT / "configs" / "models" / "model-selection-v1.toml",
        labels_path=(
            ROOT
            / "data"
            / "labels"
            / "label_version=1.0.0"
            / "run_id=8780c5a42857c830"
            / "labels.jsonl"
        ),
        clean_root=(
            ROOT / "data" / "clean" / "candles" / "schema_version=1.0.0" / "run_id=13f11d10018f9914"
        ),
        artifact_dir=ROOT / "models" / "candidates",
        report_path=ROOT / "reports" / "model-selection.md",
    )
    result = pipeline.run()
    print(f"run_id={result.run_id}")
    print(f"champion={result.champion}")
    print(f"artifact={result.artifact_path}")
    print(f"report={result.report_path}")
    print(f"sealed_holdout_rows={result.sealed_holdout_rows}")


if __name__ == "__main__":
    main()
