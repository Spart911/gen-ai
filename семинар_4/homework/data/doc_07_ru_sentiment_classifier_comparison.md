# Сравнение классификаторов для тональной оценки комментариев

- doc_id: doc_07_ru_sentiment_classifier_comparison
- Источник: ru.stackoverflow.com через Stack Exchange API
- Тредов внутри документа: 1
- Дата выгрузки: 2026-06-10
- Лицензия исходного контента: CC BY-SA 4.0

## Тред: Сравнение производительности классификаторов для эмоциональной (тональной) оценки комментариев/твитов

- question_id: 792931
- URL: https://ru.stackoverflow.com/questions/792931/%d0%a1%d1%80%d0%b0%d0%b2%d0%bd%d0%b5%d0%bd%d0%b8%d0%b5-%d0%bf%d1%80%d0%be%d0%b8%d0%b7%d0%b2%d0%be%d0%b4%d0%b8%d1%82%d0%b5%d0%bb%d1%8c%d0%bd%d0%be%d1%81%d1%82%d0%b8-%d0%ba%d0%bb%d0%b0%d1%81%d1%81%d0%b8%d1%84%d0%b8%d0%ba%d0%b0%d1%82%d0%be%d1%80%d0%be%d0%b2-%d0%b4%d0%bb%d1%8f-%d1%8d%d0%bc%d0%be%d1%86%d0%b8%d0%be%d0%bd%d0%b0%d0%bb%d1%8c%d0%bd%d0%be%d0%b9-%d1%82%d0%be%d0%bd%d0%b0%d0%bb%d1%8c%d0%bd%d0%be%d0%b9-%d0%be%d1%86%d0%b5%d0%bd%d0%ba
- Теги: python, нейронные-сети, машинное-обучение, классификация, естественный-язык
- Автор вопроса: MaxU - stand with Ukraine (https://ru.stackoverflow.com/users/211923/maxu-stand-with-ukraine)
- Рейтинг вопроса: 9
- Ответов в исходном треде: 1
- Лицензия: CC BY-SA 3.0

### Вопрос

Отвечая на данный вопрос (https://ru.stackoverflow.com/questions/790609/naivebaies-%D0%BD%D0%B5-%D1%85%D0%BE%D1%87%D0%B5%D1%82-%D0%BE%D0%B1%D1%80%D0%B0%D0%B1%D0%B0%D1%82%D1%8B%D0%B2%D0%B0%D1%82%D1%8C-%D1%80%D1%83%D1%81%D1%81%D0%BA%D0%B8%D0%B9-%D1%82%D0%B5%D0%BA%D1%81%D1%82), захотелось сравнить эффективность разных классификаторов для эмоциональной(тональной) оценки комментариев/твитов.

 Не уверен, что этот вопрос полностью соответствует правилам StackOverflow, но уверен, что это может пригодиться людям интересующимся проблемами классификации натуральных текстов.

 PS свою попытку решения я оформил в виде ответа (https://ru.stackoverflow.com/a/792932/211923).

### Ответ 792932

- Автор ответа: MaxU - stand with Ukraine (https://ru.stackoverflow.com/users/211923/maxu-stand-with-ukraine)
- Рейтинг ответа: 6
- Принят: да
- URL ответа: https://ru.stackoverflow.com/a/792932
- Лицензия: CC BY-SA 3.0

В этом ответе я сравниваю производительность (точность предсказания) следующих классификаторов:

 
- SGDClassifier ( S tochastic G radient D escent) (http://scikit-learn.org/stable/modules/generated/sklearn.linear_model.SGDClassifier.html)

- MultinomialNB (Multinomial N aive B ayes) (http://scikit-learn.org/stable/modules/generated/sklearn.naive_bayes.MultinomialNB.html)

- KNeighborsClassifier ( K - N earest N eighbors Vote) (http://scikit-learn.org/stable/modules/generated/sklearn.neighbors.KNeighborsClassifier.html)

- SVC(kernel='linear') ( S upport V ector Machine C lassification; kernel: `linear`) (http://scikit-learn.org/stable/modules/generated/sklearn.svm.SVC.html)

- SVC(kernel='rbf') ( S upport V ector Machine C lassification; kernel: `Radial-Basis Function`) (http://scikit-learn.org/stable/modules/generated/sklearn.svm.SVC.html)

- MLPClassifier ( M ulti- L ayer P erceptron) (http://scikit-learn.org/stable/modules/generated/sklearn.neural_network.MLPClassifier.html)

 Я также тестировал:

 
- LogisticRegression (http://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html) - `SGDClassifier` более продвинутая версия

- DecisionTreeClassifier (http://scikit-learn.org/stable/modules/generated/sklearn.tree.DecisionTreeClassifier.html)

- RandomForestClassifier (http://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html)

 `DecisionTreeClassifier` и `RandomForestClassifier` давали плохие результаты (точность предсказания) как для корпуса так и для новых (собственноручно написанных комментариев), поэтому я решил от них отказаться.

 Все модели тренировались на 5% данных от всего корпуса, т.е. оставшиеся 95% корпуса классификаторы никогда не видели перед предсказанием.

 Результат предсказания для всего (100%) корпуса:

Блок кода:

In [11]: df.drop('ttext',1)
Out[11]:
 ttype pred_SGD pred_MultinomialNB pred_SVC_linear pred_SVC_rbf pred_MLP_NN
30221 1 1 1 1 1 1
88858 1 1 1 1 1 1
220076 -1 -1 -1 -1 -1 -1
201195 -1 -1 -1 -1 -1 -1
78267 1 1 1 1 1 1
71817 1 1 1 1 1 1
207275 -1 -1 -1 -1 -1 -1
226007 -1 -1 -1 -1 -1 -1
140091 -1 -1 -1 -1 -1 -1
2433 1 1 1 1 1 1
... ... ... ... ... ... ...
199205 -1 -1 -1 -1 -1 -1
178062 -1 -1 -1 -1 -1 -1
54428 1 1 1 1 1 1
176046 -1 -1 -1 -1 -1 -1
171906 -1 -1 -1 -1 -1 -1
53821 1 1 1 1 1 1
113037 1 1 1 1 1 1
87279 1 1 1 1 1 1
6561 1 1 1 1 1 1
30793 1 1 1 1 1 1

[226834 rows x 6 columns]

 Точность:

Блок кода:

r = (df.filter(regex='pred_')
 .rename(columns=lambda c: c.replace('pred_', ''))
 .eq(df['ttype'], axis=0).mean()
 .to_frame('Accuracy'))

In [55]: r
Out[55]:
 Accuracy
SGD 0.998554
MultinomialNB 0.991165
SVC_linear 0.998611
SVC_rbf 0.958441
MLP_NN 0.998492

 График:

Блок кода:

ax = r.plot.barh(alpha=0.55, title='Classifier Comparison', figsize=(12,8))
plt.tight_layout()

for rect in ax.patches:
 width = rect.get_width()
 ax.text(0.5, rect.get_bbox().get_points()[:, 1].mean(),
 '{:.2%}'.format(width), ha='center', va='center')

 (https://i.sstatic.net/turIb.png)

 Проверяем модели на собственноручно написанных комментариях:

Блок кода:

test = get_test_data()

In [85]: test
Out[85]:
 ttext ttype
0 Погода сегодня полная фигня, но настроение все равно отличное 1
1 Ну сходил я на этот фильм. Отзывы были нормальные, а оказалось - отстой! -1
2 StackOverflow рулит 1
3 все очень плохо -1
4 бывало и получше -1
5 да вы задолбали -1
6 ненавижу вас :))) 1
7 ненавижу вас -1

test = test_unseen_dataset(grid, test, 'ttext')

In [112]: test.drop('ttext',1)
Out[112]:
 ttype pred_SGD pred_MultinomialNB pred_KNN pred_SVC_linear pred_SVC_rbf pred_MLP_NN
0 1 1 1 1 1 1 1
1 -1 -1 -1 -1 -1 -1 -1
2 1 1 1 -1 1 -1 1
3 -1 1 -1 -1 1 -1 -1
4 -1 -1 -1 -1 -1 -1 -1
5 -1 1 -1 -1 1 -1 -1
6 1 1 1 -1 1 1 1
7 -1 -1 -1 -1 -1 -1 -1

 Считаем точность:

Блок кода:

r2 = (test.filter(regex='pred_')
 .rename(columns=lambda c: c.replace('pred_', ''))
 .eq(test['ttype'], axis=0).mean()
 .to_frame('Accuracy'))

In [114]: r2
Out[114]:
 Accuracy
SGD 0.750
MultinomialNB 1.000
KNN 0.750
SVC_linear 0.750
SVC_rbf 0.875
MLP_NN 1.000

 (https://i.sstatic.net/D4CyI.png)

 Код программы для тренировки моделей:

Блок кода:

# (с) https://ru.stackoverflow.com/users/211923/maxu?tab=profile

# Corpus download: http://study.mokoron.com/
# Corpus (c)
# positive: https://www.dropbox.com/s/fnpq3z4bcnoktiv/positive.csv?dl=0
# negative: https://www.dropbox.com/s/r6u59ljhhjdg6j0/negative.csv?dl=0
# join them together: type positive.csv negative.csv > pos_neg.csv

#cols = 'id tdate tmane ttext ttype trep tfav tstcount tfol tfrien listcount'.split()

try:
 from pathlib import Path
except ImportError: # Python 2
 from pathlib2 import Path
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.model_selection import GridSearchCV
from sklearn.linear_model import SGDClassifier, LogisticRegression
from sklearn.naive_bayes import MultinomialNB, GaussianNB
from sklearn.neural_network import MLPClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.gaussian_process import GaussianProcessClassifier
from sklearn.gaussian_process.kernels import RBF
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.externals import joblib

def get_train_data(path, frac=0.15, **kwargs):
 df = pd.read_csv(path, sep=';', header=None,
 names=['id','ttext','ttype'],
 usecols=[0,3,4], **kwargs)
 # Speed up: randomly select 15% of data
 # comment it out for better prediction performance
 return df.sample(frac=frac)

def get_test_data(path=None, **kwargs):
 if path:
 return pd.read_csv(path, **kwargs)
 else: # generate a dummy DF
 test = pd.DataFrame({
 'ttext':['Погода сегодня полная фигня, но настроение все равно отличное',
 'Ну сходил я на этот фильм. Отзывы были нормальные, а оказалось - отстой!',
 'StackOverflow рулит', 'все очень плохо', 'бывало и получше', 'да вы задолбали',
 'ненавижу вас :)))', 'ненавижу вас']
 })
 test['ttype'] = [1, -1, 1, -1, -1, -1, 1, -1]
 return test

def fit_all_classifiers_grid(X, y, classifiers, **common_grid_kwargs):
 grids = {}
 for clf in classifiers:
 print('{:-^70}'.format(' [' + clf['name'] + '] '))
 pipe = Pipeline([
 ("vect", CountVectorizer()),
 (clf['name'], clf['clf'])])
 grids[clf['name']] = (GridSearchCV(pipe,
 param_grid=clf['parm_grid'],
 **common_grid_kwargs)
 .fit(X, y))
 # saving single trained model ...
 joblib.dump(grids[clf['name']], './pickle/{}.pkl'.format(clf['name']))
 return grids

classifiers = [
 { 'name': 'SGD',
 'clf': SGDClassifier(),
 'title': "SGDClassifier",
 'parm_grid': {
 'vect__min_df': [1, 2, 3],
 'vect__ngram_range': [(2,5)],
 'vect__analyzer': ['char_wb'],
 'SGD__alpha': [0.0001, 0.001, 0.01, 0.1],
 'SGD__max_iter': [200]
 } 
 },
 #{ 'name': 'LogRegr',
 # 'clf': LogisticRegression(),
 # 'title': "LogisticRegression",
 # 'parm_grid': {
 # 'vect__min_df': [1, 2, 3],
 # 'vect__ngram_range': [(2,5)],
 # 'vect__analyzer': ['char_wb'],
 # 'LogRegr__C': [5, 10],
 # 'LogRegr__max_iter': [100, 200]
 # } 
 #},
 { 'name': 'MultinomialNB',
 'clf': MultinomialNB(),
 'title': "MultinomialNB",
 'parm_grid': {
 'vect__min_df': [1, 2, 5, 7],
 'vect__ngram_range': [(2,5)],
 'vect__analyzer': ['char_wb'],
 'MultinomialNB__alpha': [0.0001, 0.001, 0.01, 0.1]
 } 
 },
 { 'name': 'KNN',
 'clf': KNeighborsClassifier(),
 'title': "K-Neighbors",
 'parm_grid': {
 'vect__min_df': [1, 3, 5, 7],
 'vect__ngram_range': [(2,5)],
 'vect__analyzer': ['char_wb'],
 'KNN__n_neighbors': [3, 4, 5]
 } 
 },
 { 'name': 'SVC_linear',
 'clf': SVC(),
 'title': "SVC (linear)",
 'parm_grid': {
 'vect__min_df': [1, 3, 5],
 'vect__ngram_range': [(2,5)],
 'vect__analyzer': ['char_wb'],
 'SVC_linear__kernel': ['linear'],
 'SVC_linear__C': [0.025, 0.1, 0.5],
 } 
 },
 { 'name': 'SVC_rbf',
 'clf': SVC(),
 'title': "SVC (rbf)",
 'parm_grid': {
 'vect__min_df': [1, 3, 5],
 'vect__ngram_range': [(2,5)],
 'vect__analyzer': ['char_wb'],
 'SVC_rbf__kernel': ['rbf'],
 'SVC_rbf__gamma': ['auto'],
 'SVC_rbf__C': [0.5, 1, 2],
 } 
 },
 #{ 'name': 'DecisionTree',
 # 'clf': DecisionTreeClassifier(),
 # 'title': "DecisionTree",
 # 'parm_grid': {
 # 'vect__min_df': [1, 3, 5],
 # 'vect__ngram_range': [(2,5)],
 # 'vect__analyzer': ['char_wb'],
 # 'DecisionTree__max_depth': [3, 5],
 # } 
 #},
 #{ 'name': 'RandomForest',
 # 'clf': RandomForestClassifier(),
 # 'title': "RandomForest",
 # 'parm_grid': {
 # 'vect__min_df': [1, 3, 5],
 # 'vect__ngram_range': [(2,5)],
 # 'vect__analyzer': ['char_wb'],
 # 'RandomForest__max_depth': [3, 5],
 # 'RandomForest__n_estimators': [10],
 # 'RandomForest__max_features': [1],
 # } 
 #},
 { 'name': 'MLP_NN', # NOTE: very slow, might give poor accuracy on small data sets
 'clf': MLPClassifier(),
 'title': "MLP NN",
 'parm_grid': {
 'vect__min_df': [3, 5, 7],
 'vect__ngram_range': [(2,5)],
 'vect__analyzer': ['char_wb'],
 'MLP_NN__activation': ['relu'],
 'MLP_NN__alpha': [0.0001, 0.001, 0.01, 0.1],
 } 
 },
 #{ 'name': 'AdaBoost', # NOTE: poor accuracy
 # 'clf': AdaBoostClassifier(),
 # 'title': "AdaBoost",
 # 'parm_grid': {
 # 'vect__min_df': [1, 3, 5, 7],
 # 'vect__ngram_range': [(2,5)],
 # 'vect__analyzer': ['char_wb'],
 # 'AdaBoost__n_estimators': [25, 50, 75, 150],
 # } 
 #},
]

def print_grid_results(grids):
 for name, clf in grids.items():
 print('{:-^70}'.format(' [' + name + '] '))
 print('Score:\t\t{:.2%}'.format(clf.best_score_))
 print('Parameters:\t{}'.format(clf.best_params_))
 print('*' * 70)

def print_best_features(grids, clf_name, n=20):
 clf = grids[clf_name]
 if not hasattr(clf.best_estimator_.named_steps[clf_name], 'coef_'):
 print('*' * 70)
 print('Attribute [coef_] not available for [clf_name]')
 print('*' * 70)
 return
 features = clf.best_estimator_.named_steps['vect'].get_feature_names()
 coefs = pd.Series(clf.best_estimator_.named_steps[clf_name].coef_.ravel(), features)
 print('*' * 70)
 print('Top {} POSITIVE features:'.format(n))
 print('*' * 70)
 print(coefs.nlargest(20))
 print('-' * 70)
 print('Top {} NEGATIVE features:'.format(n))
 print('*' * 70)
 print(coefs.nsmallest(20))
 print('-' * 70)
 print('*' * 70)

def test_unseen_dataset(grid, test_df, X_col='ttext'):
 for name, clf in grid.items():
 test_df['pred_{}'.format(name)] = clf.predict(test_df[X_col])
 return test_df

def main(path): 
 p = Path('.')
 pkl_dir = p / 'pickle'
 print(pkl_dir)
 pkl_dir.mkdir(parents=True, exist_ok=True)

 # read data set into DF. Only the following columns: ['id','tdate','ttext','ttype']
 df = get_train_data(path, frac=0.05)

 test = get_test_data()

 # tune up hyperparameters for ALL classifiers
 print('Tuning up hyperparameters for ALL classifiers ...')
 print('NOTE: !!! this might take hours !!!')
 grid = fit_all_classifiers_grid(df['ttext'], df['ttype'],
 classifiers, cv=2,
 verbose=2, n_jobs=-1)

 # persist trained models
 fn = str(pkl_dir / 'ALL_grids.pkl')
 print('Saving tuned [grid] to [{}]'.format(fn))
 joblib.dump(grid, fn)

 # print best scores and best parameters for ALL classifiers
 print_grid_results(grid)

 pd.options.display.expand_frame_repr = False
 test = test_unseen_dataset(grid, test, 'ttext')
 test.to_excel('./test.xlsx', index=False)
 #print(test)
 print(test.iloc[:, 2:].eq(test['ttype'], axis=0).mean())

if __name__ == "__main__":
 p = Path(__file__).parent.resolve()
 main(str(p / 'pos_neg.csv.gz'))

 PS в ответе использовался корпус, подготовленный Юлией Рубцовой (http://study.mokoron.com/)
