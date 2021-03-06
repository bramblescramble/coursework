from imblearn.over_sampling import SMOTE
import numpy as np
import pandas as pd
import pickle
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, make_scorer
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.svm import SVC
import time

# categorial feats
# job(12), marital(4), education(8), default(3), housing(3), loan(3), contact(2), month(12), day_of_week(5), poutcome(3)


cat_features = [
	('job', ['admin.','blue-collar','entrepreneur','housemaid','management','retired','self-employed','services','student','technician','unemployed','unknown']),
	('marital', ['divorced','married','single','unknown']),
	('education', ['basic.4y','basic.6y','basic.9y','high.school','illiterate','professional.course','university.degree','unknown']),
	('default', ['no','yes','unknown']),
	('housing', ['no','yes','unknown']),
	('loan', ['no','yes','unknown']),
	('contact', ['cellular','telephone']),
	('day_of_week', [1,2,3,4,5]),
	('poutcome', ['failure','nonexistent','success']),
	('month', [1,2,3,4,5,6,7,8,9,10,11,12])
]


# receives a csv file and return features and labels np arrays
def pre_process_data(filename, labeled=False):
	print('\npre-processing ', filename)

	features = pd.read_csv(filename)
	print('shape: ', features.shape)
	dim_orig = features.shape[1]

	features['age'] = np.round(features['age']/10)

	# do one-hot encoding for categorical features
	# done by hand to assert dimension of each hot-encoded feat
	for feat in cat_features:
		# print('one-hot encoding ', feat[0])
		one_hot = pd.get_dummies(features[feat[0]], prefix=feat[0])
		one_hot = one_hot.T.reindex(
			map(lambda x: '{}_{}'.format(feat[0], x), feat[1]),
			fill_value=0).T
		# print(one_hot.columns)
		features = features.drop(feat[0], axis=1)
		dim0 = features.shape[1]
		features = features.join(one_hot)
		dim1 = features.shape[1]
		assert dim1 - dim0 == len(feat[1])

	# feature_list = list(features.columns)

	dim_final = features.shape[1]
	assert dim_final == dim_orig + 45

	print('shape after one-hot encoding: ', features.shape)

	if labeled:
		# retrieve labels from features
		labels = np.array(features['y'])
		features = features.drop('y', axis=1)

		# oversample to avoid imbalance
		sm = SMOTE(random_state=42)
		features, labels = sm.fit_sample(features, labels)
		unique, counts = np.unique(labels, return_counts=True)
		assert counts[0] == counts[1]
		print('shape after oversampling: ', features.shape)
	else:
		labels = None

	return np.array(features), labels


# trains model using k-fold stratified cross validation
def train_model(model, k, X, y):
	kfolds = StratifiedKFold(k)
	scores = []
	for train_idx, test_idx in kfolds.split(X, y):
		X_train, y_train = X[train_idx], y[train_idx]
		X_test, y_test = X[test_idx], y[test_idx]
		model = model.fit(X_train, y_train)
		y_hat = model.predict(X_test)
		scores.append(f1_score(y_test, y_hat, average='weighted'))
	print('f1 scores: ', scores, '; mean: ', np.mean(scores))
	

# evaluates models using cross_val_score
def eval_model(model, X, y):
	# f1_weighted = make_scorer(f1_score, average='weighted')
	t = time.process_time()
	scores = cross_val_score(model, X, y, scoring='f1', n_jobs=-1)
	print('elapsed time: ', time.process_time() - t)
	print('k-fold f1 scores: ', scores, '; mean: ', scores.mean())


# predicts responses to X using model, and saves them in a csv file
def predict(model, X):
	y_hat = model.predict(X)
	
	output = np.zeros((X.shape[0], 2))
	output[:,0] = X[:,0]
	output[:,1] = y_hat
	df = pd.DataFrame(output, columns=['id','y'], dtype='int')
	df.to_csv('submission_{}.csv'.format(time.time()), index=False)


if __name__ == "__main__":

	# read data

	X_train, y_train = pre_process_data('train.csv', labeled=True)

	#### dataset is unbalanced!!!
	## y=1 -> 12% of points

	# initialize models

	rf = RandomForestClassifier(n_estimators=200, random_state = 42, class_weight={0:1, 1:100})
	# hyperparams = {
	# 	'class_weight': [{0:1, 1:100}, {0:1, 1:200}, {0:1, 1:400}, {0:1, 1:1000}],
	# 	'n_estimators': [200, 500, 1000]
	# 	}
	lr = LogisticRegression(class_weight={0:1, 1:100})
	# svm = SVC()

	# evaluate models

	# print('\nrandom forests')
	# eval_model(rf, X_train, y_train)
	# print('\nlogistic regression')
	# eval_model(lr, X_train, y_train)
	# print('\nsvm')
	# eval_model(svm, X_train, y_train)

	# train best model with cross-validation

	k = 7
	print('\nrandom forests')
	train_model(rf, k, X_train, y_train)

	# save model (it may be used afterwards when necessary)

	pickle.dump(rf, open('rf.sav', 'wb'))


	# predict

	X_test, _ = pre_process_data('test.csv')
	predict(rf, X_test)
