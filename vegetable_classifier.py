"""
vegetable_classifier.py
------------------------
Wraps BOTH trained VegiVision models:
  - vegivision_final_model.keras   -> single dominant vegetable (softmax)
  - multilabel_vegivision.keras    -> every vegetable present (sigmoid)

app.py can call whichever mode fits the UI: classify_vegetable() for the
"identify the one vegetable in this photo" flow, or
classify_vegetables_multi() for "list everything in this photo".
"""

import json
from pathlib import Path

import streamlit as st
import tensorflow as tf
from PIL import Image

MODEL_DIR = Path(__file__).parent / "ml_model"


@st.cache_resource
def _load_single_label_classifier():
    model = tf.keras.models.load_model(MODEL_DIR / "vegivision_final_model.keras")
    with open(MODEL_DIR / "class_mapping.json") as f:
        mapping = json.load(f)
    idx_to_class = {int(k): v for k, v in mapping["idx_to_class"].items()}
    with open(MODEL_DIR / "preprocessing_config.json") as f:
        config = json.load(f)
    return model, idx_to_class, config


@st.cache_resource
def _load_multilabel_classifier():
    model = tf.keras.models.load_model(MODEL_DIR / "multilabel_vegivision.keras")
    with open(MODEL_DIR / "multilabel_config.json") as f:
        config = json.load(f)
    return model, config


def _preprocess(image: Image.Image, image_size, preprocess_fn_name):
    img = image.convert("RGB").resize(tuple(image_size))
    arr = tf.keras.preprocessing.image.img_to_array(img)
    arr = tf.expand_dims(arr, 0)

    if preprocess_fn_name == "divide_by_255":
        arr = arr / 255.0
    elif "mobilenet_v3" in preprocess_fn_name:
        arr = tf.keras.applications.mobilenet_v3.preprocess_input(arr)
    elif "resnet50" in preprocess_fn_name:
        arr = tf.keras.applications.resnet50.preprocess_input(arr)
    return arr


def classify_vegetable(image: Image.Image, top_k: int = 3) -> dict:
    """Single dominant vegetable. Returns:
        {"predicted_vegetable": str, "confidence": float, "top_k": [...]}
    """
    model, idx_to_class, config = _load_single_label_classifier()
    arr = _preprocess(image, config["image_size"], config["preprocess_fn"])

    probs = model.predict(arr, verbose=0)[0]
    top_indices = probs.argsort()[::-1][:top_k]
    top_predictions = [
        {"vegetable": idx_to_class[int(i)], "confidence": float(probs[i])}
        for i in top_indices
    ]
    return {
        "predicted_vegetable": top_predictions[0]["vegetable"],
        "confidence": top_predictions[0]["confidence"],
        "top_k": top_predictions,
    }


def classify_vegetables_multi(image: Image.Image, threshold: float = None, top_n: int = None) -> dict:
    """Every vegetable present. Returns:
        {"detected_vegetables": [str, ...], "detections": [{"vegetable", "confidence"}, ...]}

    If `top_n` is given, the threshold is ignored and the top `top_n` most
    confident classes are returned regardless of score -- useful when the
    model's confidence scores run low overall but you still want its best
    guesses at everything in the photo, rather than only whatever happens
    to clear a fixed cutoff.
    """
    model, config = _load_multilabel_classifier()
    arr = _preprocess(image, config["image_size"], config["preprocess_fn"])

    probs = model.predict(arr, verbose=0)[0]
    class_names = config["class_names"]

    if top_n is not None:
        ranked = sorted(
            ({"vegetable": class_names[i], "confidence": float(p)} for i, p in enumerate(probs)),
            key=lambda d: -d["confidence"],
        )
        detections = ranked[:top_n]
    else:
        thr = threshold if threshold is not None else config.get("threshold", 0.5)
        detections = [
            {"vegetable": class_names[i], "confidence": float(p)}
            for i, p in enumerate(probs) if p >= thr
        ]
        detections.sort(key=lambda d: -d["confidence"])

    return {
        "detected_vegetables": [d["vegetable"] for d in detections],
        "detections": detections,
    }
