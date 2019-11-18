import configparser
import glob
import os
import shutil
import struct
import time
import pickle

def timed_folder_name():
    name = time.asctime()
    for x in range(3): name = name.replace('  ', ' ')
    name = name.replace(' ', '_')
    name = name.replace(':', '_')
    return name


def copy_files(target, extension='.py'):
    files = glob.glob('*' + extension)
    for f in files:
        # print(f, '>'),
        src = os.path.join(os.getcwd(), f)
        tgt = target + '/' + f
        # print src, '>', tgt
        shutil.copy(src, tgt)


def copy_folder(src, target):
    try:
        shutil.rmtree(target)
    except shutil.Error as e:
        print(('Directory not copied. Error: %s' % e))
    try:
        shutil.copytree(src, target)
    except shutil.Error as e:
        print(('Directory not copied. Error: %s' % e))
    except OSError as e:
        print(('Directory not copied. Error: %s' % e))


def copy_library(target, src='library'):
    try:
        shutil.copytree(src, target)
    # Directories are the same
    except shutil.Error as e:
        print(('Directory not copied. Error: %s' % e))
    # Any error saying that the directory doesn't exist
    except OSError as e:
        print(('Directory not copied. Error: %s' % e))


def find_nearest(array, value):
    array = numpy.asarray(array)
    idx = (numpy.abs(array - value)).argmin()
    return array[idx]


def mat2array(matrix):
    array = numpy.array(matrix, dtype='f')
    array = numpy.squeeze(array)
    if array.shape == (): array = numpy.reshape(array, (1,))
    return array


def normalize_vector(vector):
    norm = numpy.linalg.norm(vector)
    if norm == 0: return vector
    x = vector / norm
    return x


def angle_between(v1, v2):
    v1 = numpy.reshape(v1, (1, -1))
    v2 = numpy.reshape(v2, (-1, 1))
    v1_u = normalize_vector(v1)
    v2_u = normalize_vector(v2)
    angle = numpy.arccos(numpy.clip(numpy.dot(v1_u, v2_u), -1.0, 1.0))
    angle = float(angle)
    angle = numpy.rad2deg(angle)
    if numpy.isnan(angle): return 90
    return angle


def signed_vector_angle(p1, p2):
    ang1 = numpy.arctan2(*p1[::-1])
    ang2 = numpy.arctan2(*p2[::-1])
    return numpy.rad2deg((ang1 - ang2) % (2 * numpy.pi))


def append2csv(data, path, sep=","):
    import os
    if not os.path.isfile(path):
        data.to_csv(path, mode='a', index=False, sep=sep)
    else:
        data.to_csv(path, mode='a', index=False, sep=sep, header=False)


def scale_ranges(a, b, zoom_out=1.25):
    rng_a = numpy.ptp(a)
    rng_b = numpy.ptp(b)
    mean_a = numpy.mean(a)
    mean_b = numpy.mean(b)
    if rng_b > rng_a: a = (b - mean_b) + mean_a
    if rng_a > rng_b: b = (a - mean_a) + mean_b
    mean_a = numpy.mean(a)
    mean_b = numpy.mean(b)
    a = ((a - mean_a) * zoom_out) + mean_a
    b = ((b - mean_b) * zoom_out) + mean_b
    return a, b


def minmax(array):
    mn = numpy.nanmin(array)
    mx = numpy.nanmax(array)
    rng = numpy.array((mn, mx), dtype='f')
    return rng


def unwrap(angles):
    radians = numpy.deg2rad(angles)
    radians = numpy.unwrap(radians)
    angels = numpy.rad2deg(radians)
    return angels


def iterable(x):
    if isinstance(x, str): return False
    try:
        for t in x:
            break
        return True
    except:
        return False


def isstr(x):
    return isinstance(x, str)


def nan_array(shape):
    return numpy.full(shape, numpy.nan)


def rand_range(min_value, max_value, shape):
    y = numpy.random.random(shape)
    y = y * (max_value - min_value)
    y = y + min_value
    return y


def unit_vector(norm=1):
    return numpy.array([[0], [0], [1]], dtype='f') * norm


def closest(array, value):
    idx = (numpy.abs(array - value)).argmin()
    return array[idx], idx


def angle_arrays(az_range=180, el_range=90, step=2.5, grid=True):
    az_range = abs(az_range)
    el_range = abs(el_range)
    az = numpy.arange(-az_range, az_range + 0.001, step)
    az = numpy.transpose(az)
    el = numpy.arange(-el_range, el_range + 0.001, step)
    if not grid: return az, el
    az, el = numpy.meshgrid(az, el)
    return az, el


def random_cds(n, min_value, max_value, y_zero=True):
    points = numpy.random.rand(n, 3)
    r = max_value - min_value
    points = (points * r) + min_value
    x = points[:, 0]
    y = points[:, 1]
    z = points[:, 2]
    if y_zero: y = numpy.zeros(x.shape)
    return x, y, z


def corr2cov(sigma, corr):
    sigma = numpy.array(sigma, dtype='f')
    corr = numpy.array(corr, dtype='f')
    cov = corr * (numpy.transpose(sigma) * sigma)
    return cov


def almost_equal(a, b, threshold):
    diff = abs(a - b)
    if diff <= threshold: return True
    return False


def sign(x):
    if x < 0: return -1
    if x > 0: return 1
    if x == 0: return 0


def lst2command(lst):
    command = ''
    for x in lst: command += str(x) + ','
    command = command.rstrip(',')
    command += '*'
    return command


def lst2str(lst):
    if isinstance(lst, str): return lst
    text = ''
    for x in lst: text += str(x) + ' '
    text = text.rstrip(' ')
    return text


def contains(text, lst):
    for x in lst:
        if x in text: return True
    return False

