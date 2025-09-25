#
# project: CSV Validator
#
# Outlier detector
#
# georgios mountzouris 2025 (gmountzouris@efka.gov.gr)
#

import numpy as np
from sklearn.ensemble import IsolationForest


class OutlierDetector():
    def __init__(self, data):
        self.data = data
        self.n_samples = len(data)

    def detect_outliers_iqr(self, k=1.5, return_thresholds=False):
        q25, q75 = np.percentile(self.data, [25, 75])
        iqr = q75 - q25
        cutoff = iqr * k
        lower_bound, upper_bound = q25 - cutoff, q75 + cutoff
        if return_thresholds:
            return lower_bound, upper_bound
        else:
            result = np.logical_or(self.data < lower_bound, self.data > upper_bound)
            return result
    
    def detect_outliers_iso_forest(self, n_estimators=100, contamination=0.01, sample_size=256):
        if sample_size > self.n_samples:
            sample_size = self.n_samples
        dataset = self.data.to_numpy(dtype=np.float32).reshape(-1, 1)
        iso_forest = IsolationForest(n_estimators=n_estimators,
                                contamination=contamination,
                                max_samples=sample_size,
                                random_state=42)
        iso_forest.fit(dataset)
        #anomaly_score = iso_forest.decision_function(data)
        anomalies = iso_forest.predict(dataset)
        result = np.where(anomalies > 0, False, True)
        return result
    
    def detect_outliers_ensemble_model(self):
        outliers = self.detect_outliers_iqr()
        anomalies = self.detect_outliers_iso_forest()
        outliers_and_anomalies = np.logical_and(outliers, anomalies)
        outliers_and_anomalies = np.invert(outliers_and_anomalies).tolist()
        return outliers_and_anomalies
