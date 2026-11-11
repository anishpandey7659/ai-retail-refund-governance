import numpy as np
from catboost import CatBoostClassifier
from pathlib import Path

""" In this basis model will predict the behavior risk:
features = [
    "return_rate_pct",
    "customer_support_contacts",
    "refund_to_order_ratio",
    "previous_dispute_count",
    "item_returned_opened",
    "multiple_accounts_flag",
    "refund_to_different_account",
    "refund_amount_requested_usd",
    "return_reason",
    "address_change_before_delivery",
]
"""


MODEL_PATH = Path("ml/behaviour_risk_model.cbm")

CLASS_NAMES = {
    0: "legitimate",
    1: "policy_abuser",
    2: "fraudulent_return",
    3: "wardrobing",
}


def load_model() -> CatBoostClassifier:
    model = CatBoostClassifier()
    model.load_model(str(MODEL_PATH))
    return model


def risk_probability(model: CatBoostClassifier, X):

    if model.classes_ is None:
        raise ValueError("Model has not been fitted or classes are unavailable.")

    probabilities = model.predict_proba(X)

    results = []

    for probability in probabilities:
        class_probabilities = {
            CLASS_NAMES[int(cls)]: float(prob)
            for cls, prob in zip(model.classes_, probability)
        }

        predicted_index = np.argmax(probability)
        predicted_class = model.classes_[predicted_index]

        results.append({
            "predicted_class": CLASS_NAMES[int(predicted_class)],
            "class_probabilities": class_probabilities
        })

    return results



if __name__ == "__main__":
    # Load model once
    model = load_model()
    X=[]

    # Make predictions
    result = risk_probability(model=model,X=X)

    # print(result["predictions"])
    # print(result["probabilities"])

