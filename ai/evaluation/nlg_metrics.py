"""
BERTScore F1, BLEU, ROUGE (F1), comparando migración generada vs gold.
"""
import logging

logger = logging.getLogger(__name__)


def compute_nlg_metrics(generations: list[str], references: list[str]) -> dict:
    """
    Requiere:
      pip install bert-score sacrebleu rouge-score
    """
    out = {}
    try:
        from bert_score import score as bscore
        P, R, F1 = bscore(generations, references, lang="en", verbose=False)
        out["BERTScore_F1"] = round(float(F1.mean()), 4)
    except Exception as e:
        logger.warning("BERTScore no disponible: %s", e)
        out["BERTScore_F1"] = None

    try:
        from sacrebleu.metrics import BLEU
        bleu = BLEU()
        out["BLEU"] = round(bleu.corpus_score(generations, [references]).score / 100, 4)
    except Exception as e:
        logger.warning("BLEU no disponible: %s", e)
        out["BLEU"] = None

    try:
        from rouge_score import rouge_scorer
        scorer = rouge_scorer.RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=True)
        r1, r2, rl = [], [], []
        for g, r in zip(generations, references):
            s = scorer.score(r, g)
            r1.append(s["rouge1"].fmeasure)
            r2.append(s["rouge2"].fmeasure)
            rl.append(s["rougeL"].fmeasure)
        n = len(generations) or 1
        out["ROUGE-1_F1"] = round(sum(r1) / n, 4)
        out["ROUGE-2_F1"] = round(sum(r2) / n, 4)
        out["ROUGE-L_F1"] = round(sum(rl) / n, 4)
    except Exception as e:
        logger.warning("ROUGE no disponible: %s", e)
        out["ROUGE-1_F1"] = out["ROUGE-2_F1"] = out["ROUGE-L_F1"] = None

    return out