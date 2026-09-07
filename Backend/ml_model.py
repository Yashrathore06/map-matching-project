import os
import joblib


MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    "ml",
    "models",
    "random_forest_model.pkl"
)


model_data = joblib.load(
    MODEL_PATH
)

model = model_data["model"]

features = model_data["features"]


def predict_road_type(
    road_length,
    lanes,
    max_speed,
    road_width,
    curvature
):

    input_data = [[
        road_length,
        lanes,
        max_speed,
        road_width,
        curvature
    ]]

    prediction = model.predict(
        input_data
    )[0]

    probabilities = model.predict_proba(
        input_data
    )[0]

    confidence = float(
        max(probabilities)
    )

    return {
        "road_type": prediction,
        "confidence": confidence
    }