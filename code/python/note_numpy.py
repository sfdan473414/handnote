
#%%
import numpy as np

x=np.ones((3,3))
a=np.array([1,2,3])
print(x+a)

#%%
import numpy as np

a = np.arange(3)
b = np.arange(3)[:, np.newaxis]
a+b

#%%
import numpy as np
x = np.array([1, 2, 3, 4, 5])
print(x<3)
print(x>3)
print(x<=3)
print(x>=3)
print(x!=3)
print(x==3)

#%%
import numpy as np
rng = np.random.RandomState(0)
x=rng.randint(10,size=(3,4))
print(x)
x<6

print( np.count_nonzero(x<6))
print( np.sum(x<6))

