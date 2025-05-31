import pandas as pd
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import GradientBoostingRegressor
import joblib

# Данные
data = [
    [636, 19608, 276, 0.0013],
    [644, 1113, 277, 0.001],
    [652, 1116, 299, 0.001],
    [336, 8073, 140, 0.0025],
    [755, 13037, 292, 0.0012],
    [279, 2163, 116, 0.0028],
    [310, 595, 111, 0.0022],
    [229, 401, 129, 0.0022],
    [207, 273, 87, 0.0025],
    [167, 1955, 72, 0.004],
    [212, 2537, 89, 0.003],
    [1462, 95788, 648, 0.0006],
    [941, 63049, 400, 0.001],
    [2395, 10946, 1031, 0.0005],
    [1993, 10344, 749, 0.0005],
    [1406, 42794, 606, 0.0007],
    [3717, 580190, 1617, 0.0007],
    [2711, 518506, 1162, 0.0007],
    [8196, 32706, 3161, 0.00012],
    [5622, 31047, 2381, 0.00015],
    [1733, 96655, 768, 0.00045],
    [1554, 107762, 693, 0.00045],
    [1092, 52959, 21, 0.00100]

]

df = pd.DataFrame(data, columns=["len", "area", "count", "epsilon"])
df["density"] = df["len"] / df["count"]
X = df[["len", "area", "count", "density"]]
y = np.log1p(df["epsilon"])  # лог-цель

pipeline = Pipeline([
    ("scaler", StandardScaler()),
    ("model", GradientBoostingRegressor(n_estimators=300, max_depth=4, random_state=42))
])

pipeline.fit(X, y)

y_pred_log = pipeline.predict(X)
y_pred = np.expm1(y_pred_log)  # Обратно из лог-пространства

df["predicted_epsilon"] = y_pred
df["error"] = ((y_pred - df["epsilon"]) / df["epsilon"]) * 100

print(df[["len", "area", "count","density", "epsilon", "predicted_epsilon", "error"]].sort_values(by="error", key=np.abs))

joblib.dump(pipeline, "epsilon_model3.joblib")