import numpy as np

from testing_helpers import expect, run_local_tests

def create_const(x):
  return [x,x,x,x]

def test_create_const():
  expect(create_const, [1],  np.array([1,1,1,1]))
  expect(create_const, [1.0], np.array([1.0, 1.0, 1.0, 1.0]))
  expect(create_const, [True], np.array([True, True, True, True]))

shape_1d = 40
ints_1d = np.arange(shape_1d)
floats_1d = np.arange(shape_1d, dtype='float')
bools_1d = ints_1d % 2

vecs = [ints_1d, floats_1d, bools_1d]

def index_1d(x, i):
  return x[i]

def test_index_1d():
  for vec in vecs:
    expect(index_1d, [vec, 20], vec[20])

shape_2d = (4,10)
matrices = [np.reshape(vec, shape_2d) for vec in vecs]

def index_2d(x, i, j):
  return x[i, j]

def test_index_2d():
  for mat in matrices:
    expect(index_2d, [mat, 2, 5], mat[2,5])

def index_3d(x, i, j, k):
  return x[i, j, k]

shape_3d = (4,5,2)
tensors = [np.reshape(mat, shape_3d) for mat in matrices]

def test_index_3d():
  for x in tensors:
    expect(index_3d, [x, 2, 2, 1], x[2,2,1])

def set_idx_1d(arr,i,val):
  arr[i] = val
  return arr

def test_set_idx_1d():
  idx = 10
  for vec in vecs:
    vec1, vec2 = vec.copy(), vec.copy()
    val = -vec[idx]
    vec2[idx] = val
    expect(set_idx_1d, [vec1, idx, val], vec2)

def set_idx_2d(arr,i,j,val):
  arr[i, j] = val
  return arr

def test_set_idx_2d():
  i = 2
  j = 2
  for mat in matrices:
    mat1, mat2 = mat.copy(), mat.copy()
    val = -mat[i,j]
    mat2[i,j] = val
    expect(set_idx_2d, [mat1, i, j, val], mat2)

def set_idx_3d(arr, i, j, k, val):
  arr[i, j, k] = val
  return arr

def test_set_idx_3d():
  i = 2
  j = 3
  k = 1
  for x in tensors:
    x1, x2 = x.copy(), x.copy()
    val = -x[i, j, k]
    x2[i, j, k] = val
    expect(set_idx_3d, [x1, i, j, k, val], x2)

if __name__ == '__main__':
  run_local_tests()
