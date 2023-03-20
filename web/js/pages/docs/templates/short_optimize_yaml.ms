name: XGBoost Optimization
metrics:
- name: accuracy
  strategy: optimize
  objective: maximize
parameters:
- name: n_estimators
  bounds:
    min: 10
    max: 100
  type: int
budget: 10
