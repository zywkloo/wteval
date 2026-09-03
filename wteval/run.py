"""Batch-run configured systems against a labeled dataset."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .baselines import predict_system
from .dataset import load_examples, load_experiment
from .metrics import score_system
from .report import write_report
from .split import select_split


def run_experiment(
    experiment_path: Path,
    dataset_root: Path,
    out_dir: Path,
) -> dict[str, Any]:
    experiment = load_experiment(experiment_path)
    examples = load_examples(dataset_root)
    train, eval_examples = select_split(
        examples,
        split=experiment["split"],
        holdout_fraction=float(experiment.get("holdout_fraction") or 0.2),
    )
    scores = {}
    for system_id in experiment["systems"]:
        predictions = [predict_system(system_id, train, example) for example in eval_examples]
        scores[system_id] = score_system(eval_examples, predictions, experiment["metrics"])
    json_path, md_path = write_report(
        out_dir,
        experiment=experiment,
        scores=scores,
        n_train=len(train),
        n_eval=len(eval_examples),
    )
    return {
        "experiment": experiment,
        "n_train": len(train),
        "n_eval": len(eval_examples),
        "scores": scores,
        "report_json": str(json_path),
        "report_md": str(md_path),
    }
