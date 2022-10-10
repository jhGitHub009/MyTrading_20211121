#################################################################################################################
import ray
@ray.remote
def f(arg):
    return arg
ray.init(_memory=True)
a = ray.put(None)
b = f.remote(None)
print()
#################################################################################################################
import ray
import numpy as np

a = ray.put(np.zeros(1))
b = ray.get(a)
del a
print()
#################################################################################################################
import ray
@ray.remote
def f(arg):
    while True:
        pass

a = ray.put(None)
b = f.remote(a)
#################################################################################################################
import ray
a = ray.put(None)
b = ray.put([a])
del a
#################################################################################################################
import ray
@ray.remote(memory=500 * 1024 * 1024)
def some_function(x):
    pass

# reserve 2.5GiB of available memory to place this actor
@ray.remote(memory=2500 * 1024 * 1024)
class SomeActor(object):
    def __init__(self, a, b):
        pass
# override the memory quota to 100MiB when submitting the task
some_function.options(memory=100 * 1024 * 1024).remote(x=1)

# override the memory quota to 1GiB when creating the actor
SomeActor.options(memory=1000 * 1024 * 1024).remote(a=1, b=2)
#################################################################################################################

# import ray
# import datetime
# import time
#
# print(ray.__version__)
# # 1.0.1.post1
# def print_current_datetime():
#     time.sleep(0.3)
#     current_datetime = datetime.datetime.now()
#     print(current_datetime)
#     return current_datetime
#
# print_current_datetime()
#
# # ray.init(address='127.0.0.1')
# ray.init()
# # Ray Task
# @ray.remote
# def print_current_datetime():
#     time.sleep(0.3)
#     current_datetime = datetime.datetime.now()
#     print(current_datetime)
#     return current_datetime


futures = [print_current_datetime.remote() for i in range(4)]

print(futures)

ray.get(futures)