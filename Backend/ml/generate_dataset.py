import os
import pandas as pd
import osmnx as ox

OUTPUT = "ml/data/training_dataset.csv"

os.makedirs("ml/data", exist_ok=True)

print("Downloading OpenStreetMap road data for Indore...")

G = ox.graph_from_place(
    "Indore, Madhya Pradesh, India",
    network_type="drive",
    simplify=True
)

edges = ox.graph_to_gdfs(
    G,
    nodes=False,
    edges=True
)

rows = []

for _, road in edges.iterrows():

    highway = road.get("highway")

    # Some OSM roads have multiple highway types
    if isinstance(highway, list):
        highway = highway[0]

    highway = str(highway)

    # Ignore non-road paths
    if highway in [
        "footway",
        "path",
        "cycleway",
        "steps",
        "pedestrian"
    ]:
        continue

    # -----------------------------
    # ROAD FEATURES
    # -----------------------------

    length = float(road.get("length", 0))

    # Lanes
    lanes = road.get("lanes", 1)

    try:
        lanes = float(str(lanes).split(";")[0])
    except:
        lanes = 1.0

    # Maximum speed
    maxspeed = road.get("maxspeed", 50)

    try:
        maxspeed = float(
            str(maxspeed).replace(" km/h", "").split(";")[0]
        )
    except:
        maxspeed = 50.0

    # -----------------------------
    # TARGET LABEL
    # -----------------------------

    if highway in [
        "motorway",
        "motorway_link",
        "trunk",
        "trunk_link"
    ]:
        label = "highway"

    elif highway in [
        "service",
        "living_street"
    ]:
        label = "service_road"

    else:
        # We don't need local roads for this model
        continue

    # -----------------------------
    # DERIVED FEATURES
    # -----------------------------

    road_width = lanes * 3.5

    curvature = 1 / length if length > 0 else 0

    rows.append({
        "road_length": length,
        "lanes": lanes,
        "max_speed": maxspeed,
        "road_width": road_width,
        "curvature": curvature,
        "highway_class": highway,
        "label": label
    })


# -----------------------------
# CREATE DATAFRAME
# -----------------------------

df = pd.DataFrame(rows)

# Safety check
if df.empty:
    raise ValueError(
        "No highway/service-road data was found from OpenStreetMap."
    )

# Remove invalid rows
df = df[
    (df["road_length"] > 5) &
    (df["lanes"] > 0)
].reset_index(drop=True)


# -----------------------------
# CHECK CLASS DISTRIBUTION
# -----------------------------

print("\nBefore balancing:")
print(df["label"].value_counts())


# Make sure both classes exist
classes = df["label"].unique()

if len(classes) < 2:
    raise ValueError(
        "Only one class was found. "
        "Need both highway and service_road roads."
    )


# -----------------------------
# BALANCE DATASET
# -----------------------------

min_count = df["label"].value_counts().min()

balanced_parts = []

for label in ["highway", "service_road"]:

    class_data = df[df["label"] == label]

    sampled = class_data.sample(
        n=min_count,
        random_state=42
    )

    balanced_parts.append(sampled)


df = pd.concat(
    balanced_parts,
    ignore_index=True
)


# Shuffle dataset
df = df.sample(
    frac=1,
    random_state=42
).reset_index(drop=True)


# -----------------------------
# SAVE DATASET
# -----------------------------

df.to_csv(
    OUTPUT,
    index=False
)


# -----------------------------
# FINAL INFORMATION
# -----------------------------

print("\nDataset created successfully!")

print("Total rows:", len(df))

print("\nClass distribution:")
print(df["label"].value_counts())

print("\nSaved at:")
print(OUTPUT)