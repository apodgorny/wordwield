import torch
import torch.nn.functional as F
from datetime import datetime

# ============================================================
#  INSERT YOUR MODEL CALLS HERE
# ============================================================

def encode(text: str):
    # YOUR ENCODER:
    # should return a torch.Tensor AP vector
    return encoder(text)

def decode_from_ap(ap):
    # YOUR DECODER:
    # should return text string
    return decoder(ap)

# ============================================================
#  TEST CASES
# ============================================================

TEST_CASES = [
    "Это простой тест. Он проверяет, изменился ли стиль модели после обучения.",
    "The quick brown fox jumps over the lazy dog.",
    "Опиши момент, когда человек впервые понимает, что мысль может изменить его судьбу.",
    "Система AP-векторов позволяет формировать непрерывное пространство смыслов.",
    "— Ты веришь, что у каждой идеи есть свой звук?\n— Иногда кажется, что мысль звучит раньше, чем рождается.",
    "azio0-23990kkk lorem ipsum kz12!! непонятная строка 🤖",
    "Скажи то же самое другими словами: 'Я ищу способ научиться чувствовать собственные мысли.'",
    "Напиши короткое размышление о свободе."
]

# ============================================================
#  Cosine similarity helper
# ============================================================

def embed_text_for_eval(text):
    # re-encode output to get comparable embeddings
    ap = encode(text)
    return ap.float()

def cosine_similarity(a, b):
    a = F.normalize(a, dim=-1)
    b = F.normalize(b, dim=-1)
    return (a * b).sum().item()

# ============================================================
#  Evaluation
# ============================================================

def evaluate_model():
    results = []
    for idx, text in enumerate(TEST_CASES):
        ap = encode(text)
        out = decode_from_ap(ap)
        ap_out = encode(out)

        sim = cosine_similarity(ap, ap_out)

        results.append({
            "id": idx,
            "input": text,
            "output": out,
            "similarity": sim
        })
    return results

# ============================================================
#  REPORT
# ============================================================

def print_report(before, after):
    print("\n=========== TRAINING EFFECTIVENESS REPORT ===========")
    print("Generated:", datetime.now())
    print("=====================================================\n")

    improved = 0

    for b, a in zip(before, after):
        delta = a["similarity"] - b["similarity"]
        print(f"Test {b['id']}: Δ similarity = {delta:+.4f}")
        if delta > 0.02:
            improved += 1

    print("\n-----------------------------------------------------")
    print(f"Improved: {improved}/{len(before)} tests")
    print("-----------------------------------------------------")

    if improved == 0:
        print("\n❌ No visible training effect.\n")
    elif improved < len(before) * 0.3:
        print("\n⚡ Partial effect — training influenced some outputs.\n")
    else:
        print("\n✅ Training clearly succeeded — strong stylistic shift.\n")

# ============================================================
#  MAIN
# ============================================================

if __name__ == "__main__":
    print("\n=== Baseline evaluation (before loading new weights) ===")
    before = evaluate_model()

    # ---- LOAD UPDATED WEIGHTS HERE --------------------------
    # Example:
    # decoder.load_state_dict(torch.load('/kaggle/working/sentence_decoder_epoch3.pt'))
    # ----------------------------------------------------------

    print("\n=== Evaluation AFTER loading updated weights ===")
    after = evaluate_model()

    print_report(before, after)
