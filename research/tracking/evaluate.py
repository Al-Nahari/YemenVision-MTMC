"""Invoke official TrackEval for MOTChallenge-formatted ground truth/predictions."""
from __future__ import annotations
import argparse
def main():
    p=argparse.ArgumentParser(); p.add_argument("--gt-folder",required=True); p.add_argument("--trackers-folder",required=True); p.add_argument("--tracker",required=True); p.add_argument("--output",default="reports/tracking_evaluation")
    a=p.parse_args()
    try: import trackeval
    except ImportError as e: raise SystemExit("Install requirements-phase04.txt; TrackEval is required for official HOTA/IDF1/MOTA.") from e
    eval_config=trackeval.Evaluator.get_default_eval_config(); eval_config.update({'OUTPUT_FOLDER':a.output})
    dataset_config=trackeval.datasets.MotChallenge2DBox.get_default_dataset_config(); dataset_config.update({'GT_FOLDER':a.gt_folder,'TRACKERS_FOLDER':a.trackers_folder,'TRACKERS_TO_EVAL':[a.tracker],'BENCHMARK':'MOT17','SPLIT_TO_EVAL':'train'})
    evaluator=trackeval.Evaluator(eval_config); dataset=trackeval.datasets.MotChallenge2DBox(dataset_config)
    evaluator.evaluate([dataset],[trackeval.metrics.HOTA(),trackeval.metrics.CLEAR(),trackeval.metrics.Identity()])
if __name__=='__main__': main()
