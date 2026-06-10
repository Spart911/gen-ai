# Подсчёт одинаковых значений, идущих подряд, в Pandas

- doc_id: doc_09_ru_pandas_consecutive_values
- Источник: ru.stackoverflow.com через Stack Exchange API
- Тредов внутри документа: 1
- Дата выгрузки: 2026-06-10
- Лицензия исходного контента: CC BY-SA 4.0

## Тред: Как посчитать количество одинаковых значений вектора идущих в ряд?

- question_id: 1198455
- URL: https://ru.stackoverflow.com/questions/1198455/%d0%9a%d0%b0%d0%ba-%d0%bf%d0%be%d1%81%d1%87%d0%b8%d1%82%d0%b0%d1%82%d1%8c-%d0%ba%d0%be%d0%bb%d0%b8%d1%87%d0%b5%d1%81%d1%82%d0%b2%d0%be-%d0%be%d0%b4%d0%b8%d0%bd%d0%b0%d0%ba%d0%be%d0%b2%d1%8b%d1%85-%d0%b7%d0%bd%d0%b0%d1%87%d0%b5%d0%bd%d0%b8%d0%b9-%d0%b2%d0%b5%d0%ba%d1%82%d0%be%d1%80%d0%b0-%d0%b8%d0%b4%d1%83%d1%89%d0%b8%d1%85-%d0%b2-%d1%80%d1%8f%d0%b4
- Теги: python, pandas, оптимизация, numpy, обработка-данных
- Автор вопроса: nick (https://ru.stackoverflow.com/users/406984/nick)
- Рейтинг вопроса: 8
- Ответов в исходном треде: 5
- Лицензия: CC BY-SA 4.0

### Вопрос

Надо средствами numpy/pandas, без циклов. Производительность имеет значение.

Блок кода:

a = np.array([1, 1, 1, 1, 1, -1, -1, -1, -1, -1, -1, 1, 1, 1, 1, 1, 1])

 Ожидаемый результат:

Блок кода:

[1, 2, 3, 4, 5, 1, 2, 3, 4, 5, 6, 1, 2, 3, 4, 5, 6]

 Пример решения с циклом:

Блок кода:

res = np.full_like(a, np.nan)
counter = 1

for i in range(len(a)):
 if i > 0:
 if a[i] == a[i - 1]:
 counter += 1
 else:
 counter = 1

 res[i] = counter

print(res)

 Update: замер скорости с timeit

 В моем python окружении пример с pandas работает быстрее всего. Медленнее всего пример с numba.

 Пример с циклом

Блок кода:

import numpy as np
import timeit

a = np.array([1, 1, 1, 1, 1, -1, -1, -1, -1, -1, -1, 1, 1, 1, 1, 1, 1])
a = np.concatenate([a] * 10 ** 4)

def count_sequential(a):
 res = np.full_like(a, np.nan)
 counter = 1
 for i in range(len(a)):
 if i > 0:
 if a[i] == a[i - 1]:
 counter += 1
 else:
 counter = 1

 res[i] = counter
 return res

starttime = timeit.default_timer()
count_sequential(a)
print("Execution time:", timeit.default_timer() - starttime)

# Execution time: 0.086103173

 Пример с pandas

Блок кода:

import numpy as np
import pandas as pd
import timeit

a = np.array([1, 1, 1, 1, 1, -1, -1, -1, -1, -1, -1, 1, 1, 1, 1, 1, 1])
a = np.concatenate([a] * 10 ** 4)

starttime = timeit.default_timer()
s = pd.Series(a)
res = s.groupby(s.diff().fillna(0).ne(0).cumsum()).cumcount().add(1)
res.to_numpy()
print("Execution time:", timeit.default_timer() - starttime)

# Execution time: 0.015625225999999992

 Пример с numba

Блок кода:

import numpy as np
from numba import prange, njit, jit
import timeit

a = np.array([1, 1, 1, 1, 1, -1, -1, -1, -1, -1, -1, 1, 1, 1, 1, 1, 1])

a = np.concatenate([a] * 10 ** 4)

@njit # (['int64[:](int64[:])'])
def count_sequential_numba(a):
 res = np.full_like(a, np.nan)
 counter = 1
 for i in prange(len(a)):
 if i > 0:
 if a[i] == a[i - 1]:
 counter += 1
 else:
 counter = 1
 res[i] = counter
 return res

starttime = timeit.default_timer()
count_sequential_numba(a)
print("Execution time:", timeit.default_timer() - starttime)

# Execution time: 0.23011980099999996

 Пример с groupby

Блок кода:

import numpy as np
from itertools import groupby
import timeit

a = np.array([1, 1, 1, 1, 1, -1, -1, -1, -1, -1, -1, 1, 1, 1, 1, 1, 1])
a = np.concatenate([a] * 10 ** 4)

starttime = timeit.default_timer()
ans = []
for elem, count in groupby(a):
 c, d = elem, sum(1 for i in count)
 ans.extend(list(range(1, d + 1)))
print("Execution time:", timeit.default_timer() - starttime)

# Execution time: 0.05182988100000002

### Ответ 1198459

- Автор ответа: MaxU - stand with Ukraine (https://ru.stackoverflow.com/users/211923/maxu-stand-with-ukraine)
- Рейтинг ответа: 7
- Принят: да
- URL ответа: https://ru.stackoverflow.com/a/1198459
- Лицензия: CC BY-SA 4.0

Вариант векторизированного решения с использованием `Pandas`:

Блок кода:

s = pd.Series(a)
res = s.groupby(s.diff().fillna(0).ne(0).cumsum()).cumcount().add(1)

 результат:

Блок кода:

In [14]: res.to_numpy()
Out[14]: array([1, 2, 3, 4, 5, 1, 2, 3, 4, 5, 6, 1, 2, 3, 4, 5, 6])

### Ответ 1199243

- Автор ответа: Владислав Харламов (https://ru.stackoverflow.com/users/224217/%d0%92%d0%bb%d0%b0%d0%b4%d0%b8%d1%81%d0%bb%d0%b0%d0%b2-%d0%a5%d0%b0%d1%80%d0%bb%d0%b0%d0%bc%d0%be%d0%b2)
- Рейтинг ответа: 5
- Принят: нет
- URL ответа: https://ru.stackoverflow.com/a/1199243
- Лицензия: CC BY-SA 4.0

Метод, который быстрее чем через `pandas` от @MaxU (https://ru.stackoverflow.com/users/211923/maxu) в 200~ раз на коротких массивах.

Блок кода:

%%timeit
s = pd.Series(a)
res = s.groupby(s.diff().fillna(0).ne(0).cumsum()).cumcount().add(1)
# 2.25 ms ± 188 µs per loop (mean ± std. dev. of 7 runs, 100 loops each)

%%timeit
from itertools import groupby
ans = []
for elem, count in groupby(a):
 c, d = elem, sum(1 for i in count)
 ans.extend(list(range(1, d + 1)))
# 11.4 µs ± 163 ns per loop (mean ± std. dev. of 7 runs, 100000 loops each)

### Ответ 1199335

- Автор ответа: MaxU - stand with Ukraine (https://ru.stackoverflow.com/users/211923/maxu-stand-with-ukraine)
- Рейтинг ответа: 4
- Принят: нет
- URL ответа: https://ru.stackoverflow.com/a/1199335
- Лицензия: CC BY-SA 4.0

Сравнение скорости выполнения решений для массива, состоящего из 17.000 элементов:

Блок кода:

In [24]: a = np.concatenate([a] * 1000)

In [25]: len(a)
Out[25]: 17000

In [26]: %%timeit
 ...: s = pd.Series(a)
 ...: res = s.groupby(s.diff().fillna(0).ne(0).cumsum()).cumcount().add(1)
 ...: 
 ...: 
1.66 ms ± 59.7 µs per loop (mean ± std. dev. of 7 runs, 1000 loops each)

In [27]: %%timeit
 ...: ans = []
 ...: for elem, count in groupby(a):
 ...: c, d = elem, sum(1 for i in count)
 ...: ans.extend(list(range(1, d + 1)))
 ...: 
3.92 ms ± 46.2 µs per loop (mean ± std. dev. of 7 runs, 100 loops each)

 PS для более честного сравнения я убрал импорт из блока `%%timeit`...

### Ответ 1199780

- Автор ответа: MaxU - stand with Ukraine (https://ru.stackoverflow.com/users/211923/maxu-stand-with-ukraine)
- Рейтинг ответа: 4
- Принят: нет
- URL ответа: https://ru.stackoverflow.com/a/1199780
- Лицензия: CC BY-SA 4.0

Продолжаем оптимизировать... :)

 На этот раз воспользуемся Numba.njit (https://numba.pydata.org/numba-doc/latest/user/5minguide.html) (`Just In Time compiler`) - он идеально подходит для оптимизации простых циклов:

Блок кода:

from numba import prange, njit, jit

@njit #(['int64[:](int64[:])'])
def count_sequential_numba(a):
 res = np.full_like(a, np.nan)
 counter = 1
 for i in prange(len(a)):
 if i > 0:
 if a[i] == a[i - 1]:
 counter += 1
 else:
 counter = 1
 res[i] = counter
 return res

 Заметьте функция состоит из оригинального кода из вопроса - я добавил только декоратор.

 тест:

Блок кода:

In [39]: a = np.array([1, 1, 1, 1, 1, -1, -1, -1, -1, -1, -1, 1, 1, 1, 1, 1, 1])

In [40]: count_sequential_numba(a)
Out[40]: array([1, 2, 3, 4, 5, 1, 2, 3, 4, 5, 6, 1, 2, 3, 4, 5, 6])

 
 Сравнение производительности для массива, состоящего из 170.000 элементов:

Блок кода:

In [41]: a = np.concatenate([a] * 10**4)

In [42]: a.shape
Out[42]: (170000,)

In [44]: %%timeit
 ...: ans = []
 ...: for elem, count in groupby(a):
 ...: c, d = elem, sum(1 for i in count)
 ...: ans.extend(list(range(1, d + 1)))
 ...:
73.9 ms ± 626 µs per loop (mean ± std. dev. of 7 runs, 10 loops each)

In [45]: %%timeit
 ...: s = pd.Series(a)
 ...: res = s.groupby(s.diff().fillna(0).ne(0).cumsum()).cumcount().add(1)
 ...:
23.1 ms ± 1.57 ms per loop (mean ± std. dev. of 7 runs, 10 loops each)

In [46]: %%timeit
 ...: res = count_sequential_numba(a)
 ...:
207 µs ± 115 ns per loop (mean ± std. dev. of 7 runs, 1000 loops each)

 Выигрыш - в 357 раз по сравнению с `itertools.groupby` (https://ru.stackoverflow.com/a/1199243/211923) и в 112 раз посравнению с `Pandas` (https://ru.stackoverflow.com/a/1198459/211923):

Блок кода:

In [47]: 73.9 * 1000 / 207
Out[47]: 357.0048309178744

In [48]: 23.1 * 1000 / 207
Out[48]: 111.59420289855072

### Ответ 1202319

- Автор ответа: Danis (https://ru.stackoverflow.com/users/400096/danis)
- Рейтинг ответа: 1
- Принят: нет
- URL ответа: https://ru.stackoverflow.com/a/1202319
- Лицензия: CC BY-SA 4.0

Вариант для обычных массивов и с использованием строк

Блок кода:

a = [1, 1, 1, 1, 1, -1, -1, -1, -1, -1, -1, 1, 1, 1, 1, 1, 1]

a = str(a)[1:-1]
a = a.replace("-1", "0")
a = a.replace(", ", "")
a = a.replace("10", "1 0").replace("01", "0 1")
n = map(lambda x: list(range(1, len(x) + 2)), a.split())

print(sum(n, start = []))
