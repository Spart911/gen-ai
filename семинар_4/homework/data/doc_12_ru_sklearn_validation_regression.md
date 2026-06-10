# sklearn: train_test_split, отбор признаков и доверительные интервалы регрессии

- doc_id: doc_12_ru_sklearn_validation_regression
- Источник: ru.stackoverflow.com через Stack Exchange API
- Тредов внутри документа: 3
- Дата выгрузки: 2026-06-10
- Лицензия исходного контента: CC BY-SA 4.0

## Тред: "TypeError: Singleton array...cannot be considered a valid collection" и "ValueError: Found input ...inconsistent num...samples" в train_test_split

- question_id: 1108047
- URL: https://ru.stackoverflow.com/questions/1108047/typeerror-singleton-array-cannot-be-considered-a-valid-collection-%d0%b8-valuee
- Теги: python, python-3.x, sklearn
- Автор вопроса: sqrt495 (https://ru.stackoverflow.com/users/341468/sqrt495)
- Рейтинг вопроса: 0
- Ответов в исходном треде: 1
- Лицензия: CC BY-SA 4.0

### Вопрос

Не могу понять что является причиной ошибки на второй итерации в функции ниже:

Блок кода:

# create empty pandas DF:
model_q = pd.DataFrame(columns=['model', 'set', 'threshold','set_size','tn','fp','fn','tp'])

# get seed
cv_seed = random.sample(range(1, 1000), 10) 

def bootstraping_estimator(clf, model_name, X, y, cv_seed=cv_seed):

for i in cv_seed:
 print(i)
 X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, shuffle=True, random_state=i, stratify=y)

 # StandartScaler
 scaler.fit(X_train.values)
 X_train = scaler.transform(X_train)
 X_test = scaler.transform(X_test)

 # compute TEST ############################################################ 
 y_pred_test = clf.predict_proba(X_test)[:, 1]
 fpr, tpr, ths = roc_curve(y_test, y_pred_test)
 roc_auc = auc(fpr, tpr) 
 optimal_ths_idx = np.argmax(tpr - fpr)
 optimal_ths = ths[optimal_ths_idx]

 # round predicts ##########################################################
 for y in y_pred_test:
 y_pred_test_round = [1 if y >= 0.5 else 0 for y in y_pred_test]
 y_pred_test_round_ths = [1 if y >= optimal_ths else 0 for y in y_pred_test]

 # cm with default ths = 0.5 ##################################################
 cm = confusion_matrix(y_test, y_pred_test_round) 
 cm_norm = cm.astype('float') / cm.sum() # normalize cm 
 tn, fp, fn, tp = cm.ravel() # compute estimetor answers

 # cm with ths = optimal_ths
 cm_ths = confusion_matrix(y_test, y_pred_test_round_ths)
 cm_norm_ths = cm_ths.astype('float') / cm_ths.sum() # normalize cm 
 tn_ths, fp_ths, fn_ths, tp_ths = cm_ths.ravel()
 fpr_ths, tpr_ths, _ = roc_curve(y_test, y_pred_test_round_ths) # ... for test with optimal_threshold
 roc_auc_ths = auc(fpr_ths, tpr_ths) 

 # get global var and appned metrics
 global model_q
 model_q = model_q.append({'model': f'{model_name}_{i}',
 'threshold': 0.5,
 'set_size': len(y_test),
 'tn': tn,'fp': fp, 'fn': fn, 'tp': tp,
 'roc_auc': roc_auc},
 ignore_index=True)

 model_q = model_q.append({'model': f'{model_name}_{i}',
 'threshold': optimal_ths,
 'set_size': len(y_test),
 'tn': tn_ths,'fp': fp_ths, 'fn': fn_ths, 'tp': tp_ths,
 'roc_auc': roc_auc_ths},
 ignore_index=True)

 model_q['sensitivity'] = model_q.tp/(model_q.tp+model_q.fn)
 model_q['specificity'] = model_q.tn/(model_q.tn+model_q.fp)
 model_q['accuracy'] = (model_q.tp+model_q.tn)/(model_q.tp+model_q.tn+model_q.fn+model_q.fp)

 model_q.iloc[:,1:] = model_q.iloc[:,1:].apply(pd.to_numeric)

 model_q = model_q.round({'roc_auc':3,
 'threshold':3,
 'sensitivity':3,
 'specificity':3,
 'accuracy':3})

return (model_q.sort_values(by='accuracy', ascending=False)[:10].style.hide_index()\
 .bar(color='#FFA07A', vmin=500, subset=['fp', 'fn'], align='zero')\
 .bar(color='lightgreen', vmin=500, subset=['tp', 'tn'], align='zero')
 .set_caption('Top-10 accuracy'))

 Есть сохранение данных в переменную, второй `train_test_split` падает:

 (https://i.sstatic.net/4nAvT.png)

Блок кода:

TypeError Traceback (most recent call last)
 in 
----> 1 bootstraping_estimator(clf_NB, 'NBGaussian', X, y)

 in bootstraping_estimator(clf, model_name, X, y, cv_seed)
 6 for i in cv_seed:
 7 print(i)
----> 8 X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, shuffle=True, random_state=i, stratify=y)
 9 
 10 # StandartScaler

~\Anaconda3\lib\site-packages\sklearn\model_selection\_split.py in train_test_split(*arrays, **options)
 2182 test_size = 0.25
 2183 
-> 2184 arrays = indexable(*arrays)
 2185 
 2186 if shuffle is False:

~\Anaconda3\lib\site-packages\sklearn\utils\validation.py in indexable(*iterables)
 258 else:
 259 result.append(np.array(X))
--> 260 check_consistent_length(*result)
 261 return result
 262 

~\Anaconda3\lib\site-packages\sklearn\utils\validation.py in check_consistent_length(*arrays)
 229 """
 230 
--> 231 lengths = [_num_samples(X) for X in arrays if X is not None]
 232 uniques = np.unique(lengths)
 233 if len(uniques) > 1:

~\Anaconda3\lib\site-packages\sklearn\utils\validation.py in - (.0)
 229 """
 230 
--> 231 lengths = [_num_samples(X) for X in arrays if X is not None]
 232 uniques = np.unique(lengths)
 233 if len(uniques) > 1:

~\Anaconda3\lib\site-packages\sklearn\utils\validation.py in _num_samples(x)
 140 if len(x.shape) == 0:
 141 raise TypeError("Singleton array %r cannot be considered"
--> 142 " a valid collection." % x)
 143 # Check that shape is returning an integer or default to len
 144 # Dask dataframes may not return numeric shape[0] value

TypeError: Singleton array 6.80836481004117e-07 cannot be considered a valid collection.

### Ответ 1108061

- Автор ответа: CrazyElf (https://ru.stackoverflow.com/users/260769/crazyelf)
- Рейтинг ответа: 1
- Принят: да
- URL ответа: https://ru.stackoverflow.com/a/1108061
- Лицензия: CC BY-SA 4.0

А, всё, я понял. Вы используете `y` как переменную цикла `for y in y_pred_test:`. А потом на второй итерации тот же `y` используете в `train_test_split(X, y, ...)`. Типичная ошибка начинающего питониста - использовать одни и те же названия переменных для разных целей.

 Ну и до кучи вы где-то потеряли `clf.fit(X_train, y_train)`. Если б вы не использовали `scaler` я бы подумал, что так и задумано, но если вы скейлите `X_test` каждый раз заново, вам придётся заново обучать модель на `X_train`, иначе это вообще не пойми что будет в результате.

## Тред: Машинное обучение. Отбор признаков при построении модели

- question_id: 908839
- URL: https://ru.stackoverflow.com/questions/908839/%d0%9c%d0%b0%d1%88%d0%b8%d0%bd%d0%bd%d0%be%d0%b5-%d0%be%d0%b1%d1%83%d1%87%d0%b5%d0%bd%d0%b8%d0%b5-%d0%9e%d1%82%d0%b1%d0%be%d1%80-%d0%bf%d1%80%d0%b8%d0%b7%d0%bd%d0%b0%d0%ba%d0%be%d0%b2-%d0%bf%d1%80%d0%b8-%d0%bf%d0%be%d1%81%d1%82%d1%80%d0%be%d0%b5%d0%bd%d0%b8%d0%b8-%d0%bc%d0%be%d0%b4%d0%b5%d0%bb%d0%b8
- Теги: python, машинное-обучение, scikit-learn
- Автор вопроса: Ste_kd (https://ru.stackoverflow.com/users/310134/ste-kd)
- Рейтинг вопроса: 10
- Ответов в исходном треде: 2
- Лицензия: CC BY-SA 4.0

### Вопрос

Построил 2 модели кредитного скоринга (задача бинарной классификации) на XGBoost и RandomForest. Накидал из БД различных фичей, около 60, загрузил. Построил график значимости признаков.

 1) Стоит ли усекать количество фичей, если по графику видно, что значимости они не несут, если да, то по какой линии? (график прикреплен снизу)

 2) Стоит ли оставлять бинарные фичи, в которых соотношение категорий например 90 на 10% и они не входят, скажем, в первую 10ку самых значимых признаков?

 3) Каким образом может повлиять на модель и конкретно на эффективность модели бустинга и случайного леса, если оставить все эти "маловлиятельные" признаки?

 Или же нужно ориентироваться чисто на какие-либо метрики вроде auc-roc, gini, accuracy? Грубо говоря - убрал\добавил, посмотрел на значение метрики увеличилась\нет и опять заного..

 Подскажите.

 (https://i.sstatic.net/xEys3.png)

 Функция отрисовки графика:

Блок кода:

import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer as Imputer
from sklearn import ensemble
from xgboost import XGBClassifier
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split, StratifiedKFold, GridSearchCV
from scipy.interpolate import interp1d
from scipy.integrate import quad
from sklearn.metrics import roc_auc_score, roc_curve, confusion_matrix, mean_squared_error, classification_report
import itertools
# (присутствуют лишние импорты)

def MY_plotting_feature_priority(X, model, n=3):
 importances = model.feature_importances_
 indices = np.argsort(importances)[::-1]
 feature_names = X.columns
 d_first = X.shape[1]
 plt.figure(figsize=(8, 8))
 plt.title("Значимость признаков")
 plt.bar(range(d_first), importances[indices[:d_first]], align='center')
 plt.xticks(range(d_first), np.array(feature_names)[indices[:d_first]], rotation=90)
 plt.xlim([-1, d_first])
 best_features = indices[:n]
 best_features_names = feature_names[best_features]
 print(f'Первые {n} значимых признаков {list(best_features_names)} из {d_first} ')
 plt.show()

### Ответ 909041

- Автор ответа: passant (https://ru.stackoverflow.com/users/254172/passant)
- Рейтинг ответа: 5
- Принят: нет
- URL ответа: https://ru.stackoverflow.com/a/909041
- Лицензия: CC BY-SA 4.0

Общий ответ на ваш вопрос - все зависит от поставленных целей и стоимости ошибки.
Если вы видите, что добавдение-удаление определенного признака на тестовой выборке не приводит к значимому для вас изменению точности прогноза - данные убираем, если приводят- оставляют. Даже если вы будете основываться на формальных метриках, в каждой из них есть порог, который вы сами вольны задать и по которому потом будете принимать решение.
Я не знаю, насколько значимо, например, для вашего банка уменьшение ложнонегативных прогнозов на 0.0001%. Может это всего несколько тысяч рублей, что для вашего банка ничто. А вот такое же изменение в медицине - это жизнь конкретных людей. А в психологии - вообще точность порядка 10% считается отличной. 
Так что как ни крути, но окончательное решение - всегда за вами и оно вне области формального анализа.

### Ответ 919498

- Автор ответа: passant (https://ru.stackoverflow.com/users/254172/passant)
- Рейтинг ответа: 4
- Принят: нет
- URL ответа: https://ru.stackoverflow.com/a/919498
- Лицензия: CC BY-SA 4.0

Не знаю, насколько еще актуален вопрос, но вот одно из возможных решений задачи выбора признаков именно для задач кредитного скоринга.
http://ai-news.ru/2018/12/open_source_instrument_na_python_dlya_vybora_priznakov_nejroseti.html (http://ai-news.ru/2018/12/open_source_instrument_na_python_dlya_vybora_priznakov_nejroseti.html)

## Тред: Доверительные интервалы для параметров регрессионной модели в Python

- question_id: 1283898
- URL: https://ru.stackoverflow.com/questions/1283898/%d0%94%d0%be%d0%b2%d0%b5%d1%80%d0%b8%d1%82%d0%b5%d0%bb%d1%8c%d0%bd%d1%8b%d0%b5-%d0%b8%d0%bd%d1%82%d0%b5%d1%80%d0%b2%d0%b0%d0%bb%d1%8b-%d0%b4%d0%bb%d1%8f-%d0%bf%d0%b0%d1%80%d0%b0%d0%bc%d0%b5%d1%82%d1%80%d0%be%d0%b2-%d1%80%d0%b5%d0%b3%d1%80%d0%b5%d1%81%d1%81%d0%b8%d0%be%d0%bd%d0%bd%d0%be%d0%b9-%d0%bc%d0%be%d0%b4%d0%b5%d0%bb%d0%b8-%d0%b2-python
- Теги: python, numpy, статистика, статический-анализ, sklearn
- Автор вопроса: Юрий (https://ru.stackoverflow.com/users/284507/%d0%ae%d1%80%d0%b8%d0%b9)
- Рейтинг вопроса: 1
- Ответов в исходном треде: 2
- Лицензия: CC BY-SA 4.0

### Вопрос

Есть 2 выборки X,Y, необходимо построить модель Y=aX+b+eps. Нужно для параметров a,b найти доверительные интервалы .

 Я написал поиск интервалов самостоятельно, основываясь на соответствующих формулах из учениках.
(teta- матрица параметров, 252 - объем выборки, предполагается нормальное распределение, то есть 2 параметра, уровень надежности a=0.05)

Блок кода:

a_left = teta[0]-stats.t.ppf(0.975,250)*math.sqrt(eps2.sum()*C[0,0]/250)
a_right = teta[0]+stats.t.ppf(0.975,250)*math.sqrt(eps2.sum()*C[0,0]/250)
b_left = teta[1]-stats.t.ppf(0.975,250)*math.sqrt(eps2.sum()*C[1,1]/250)
b_right = teta[1]+stats.t.ppf(0.975,250)*math.sqrt(eps2.sum()*C[1,1]/250)

 Однако мне необходимо(не по своей воле) использовать только штатные возможности библиотек(stats, sklearn, numpy, scipy etc...). Есть ли в этих библиотеках такая встроенная функция? 

 На данный момент удалось только найти параметры в модели

Блок кода:

import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn import metrics

model = LinearRegression().fit(x, y)
y_pred = model.predict(x)
print("a,b= ", model.coef_[0], model.intercept_)

### Ответ 1284022

- Автор ответа: Pak Uula (https://ru.stackoverflow.com/users/371023/pak-uula)
- Рейтинг ответа: 4
- Принят: да
- URL ответа: https://ru.stackoverflow.com/a/1284022
- Лицензия: CC BY-SA 4.0

Если к штатным возможностям вы относите `scipy` и `numpy`, то доверительные интервалы для линейной регрессии можно найти несколькими способами.

 Какой бы способ вы ни выбрали, для вычисления доверительного интервала нужно знать сам параметр (например, `a`) и его среднеквадратичное отклонение (пусть будет `a_err`).

 Доверительный интервал с уровнем доверия `alpha` вычисляют по распределению Стьюдента:

Блок кода:

conf_int = scipy.stats.t.interval(1-alpha, df=n-2, loc=a, scale=a_err)

 Если нужно найти только полуширину интервала - ту величину, которая ставится после знака ±, то она вычисляется так:

Блок кода:

plus_minus = abs(sps.t.ppf(alpha/2, n-2))*a_err

 Теперь как найти параметры и их ошибки.

 Средствами linregress

 `scipy.stats.linregress` (https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.linregress.html#scipy.stats.linregress) - специализированный метод вычисления линейной регрессии.

Блок кода:

import scipy.stats as sps

n = len(x)
lin_model = sps.linregress(x, y)
a,b = lin_model.slope, lin_model.intercept
# оценка ср.кв. ошибки для a и b
a_err, b_err = lin_model.stderr, lin_model.intercept_stderr
# Доверительный интервал для alpha=5%
a_conf = sps.t.interval(0.95, df = n-2, loc=a, scale=a_err)
b_conf = sps.t.interval(0.95, df = n-2, loc=b, scale=b_err)

print(f"a = {a:0.4f}, α=5% [{a_conf[0]:0.4f} - {a_conf[1]:0.4f}]")
print(f"b = {b:0.4f}, α=5% [{b_conf[0]:0.4f} - {b_conf[1]:0.4f}]")

 Результат для 100 точек на прямой `y=0.5x+2` со случайной ошибкой `sigma=0.5`:

Блок кода:

a = 0.5291, α=5% [0.4971 - 0.5610]
b = 1.8568, α=5% [1.6718 - 2.0418]

 Универсальный инструмент `curve_fit`

 В `scipy` есть универсальный инструмент приближения набора точек заданной моделью `scipy.optimize.curve_fit` (https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.curve_fit.html). Эта функция ищет наилучший набор параметров методом наименьших квадратов для любого вида моделей, не только линейных. Помимо оптимальных значений параметров функция возвращает ковариационную матрицу, диагональные элементы которой дают оценку дисперсии параметров.

Блок кода:

import numpy as np
import scipy.stats as sps
import scipy.optimize as spo

def linear(x, a,b):
 return a*x+b

((a,b), cov) = spo.curve_fit(linear, xdata=x, ydata=y)
a_err, b_err = np.sqrt(np.diag(cov))
a_conf = sps.t.interval(0.95, df = n-2, loc=a, scale=a_err)
b_conf = sps.t.interval(0.95, df = n-2, loc=b, scale=b_err)

 Результат для того же набора данных:

Блок кода:

a = 0.5291, α=5% [0.4971 - 0.5610]
b = 1.8568, α=5% [1.6718 - 2.0418]

 Как видно, результат тот же, что для специализированного средства.

 Прямое вычисление

 Можно напрямую вычислить параметры линейной регрессии по формулам

Блок кода:

# Вычисление параметров модели
sum_x = x.sum()
sum_y = y.sum()
sum_xy = (x*y).sum()
sum_x_sq = (x*x).sum()
a = (n*sum_xy - sum_x*sum_y)/(n*sum_x_sq - sum_x*sum_x)
b = (sum_y*sum_x_sq - sum_x*sum_xy)/(n*sum_x_sq - sum_x*sum_x)

# вычисление ошибки параметров
u = y - (a*x+b)
u_avg = np.mean(u)
sigma_square = 1.0/(n-2)*np.sum((u - u_avg)**2)
x_mean = np.mean(x)
dx_square = np.sum((x-x_mean)**2)

a_err = np.sqrt(sigma_square/dx_square)
b_err = np.sqrt(sigma_square*(1.0/n + np.mean(x)**2/dx_square))

 Замеры производительности

 Линейная регрессия для 100 точек

 
- Прямое вычисление: 51.6 µs ± 2.47

- `linregress` : 207 µs ± 2.67 µs

- `curve_fit`: 237 µs ± 8.29 µs

 Результат линейной регрессии на графике.

 (https://i.sstatic.net/FrvaC.png)

 Пример

 Пример загружен в github (https://github.com/pakuula/StackOverflow/blob/main/python/1283898/linear_reg.ipynb) как jupyter notebook.

### Ответ 1283970

- Автор ответа: passant (https://ru.stackoverflow.com/users/254172/passant)
- Рейтинг ответа: 0
- Принят: нет
- URL ответа: https://ru.stackoverflow.com/a/1283970
- Лицензия: CC BY-SA 4.0

Странно как-то вы вычисляете доверительный интервал для коэффициентов. Не знаю, на каких учебниках вы основываетесь, но вот посмотрите тут:

 http://mcimeer.narod.ru/data/t5/t5_2.html (http://mcimeer.narod.ru/data/t5/t5_2.html)

 Она отличается от той, которую вы пытаетесь применить и несколько отличается от той, которую (для коэффициента b) привел уважаемый Pak Uula
