import sklearn.datasets, sklearn.metrics
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier
import sigopt

X, y = sklearn.datasets.load_iris(return_X_y=True)
Xtrain, Xtest, ytrain, ytest = train_test_split(X, y, test_size=0.33)
sigopt.log_dataset("iris 2/3 training, full test")
sigopt.params.setdefault("n_estimators", 100)
sigopt.log_model("xgboost")
model = XGBClassifier(
  n_estimators=sigopt.params.n_estimators,
  use_label_encoder=False,
  eval_metric="logloss",
)
model.fit(Xtrain, ytrain)
pred = model.predict(Xtest)
sigopt.log_metric("accuracy", sklearn.metrics.accuracy_score(pred, ytest))
