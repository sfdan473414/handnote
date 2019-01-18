
#%%
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
%matplotlib inline

way="D:/ml-data/regression/diabetes.csv"

#%% 
# load data
df= pd.read_csv(way)
print(df.head())

#%%
# split data
X_df= df.drop('Outcome',axis=1)
Y_df= df["Outcome"]

from sklearn.model_selection import train_test_split

X_train,X_test,y_train,y_test= train_test_split(X_df,Y_df,test_size=0.33,random_state=1)
print('train size is %i'%y_train.shape[0])
print('test size is %i'%y_test.shape[0])

#%% data analyse

names= df.columns.values

zeros=[]
for i in range(len(names)):
    zeros.append(np.count_nonzero(df[names[i]]==0))
count_zeros= pd.DataFrame({"names":names,"zeros:":zeros})
print(count_zeros)

#%%
# convert 0 to -1
for j in range(1,len(names)-1):
    for i in range(len(df)):
        if(df.iloc[i,j]==0):
            df.iloc[i,j]=-1

#%%
corr= X_df.corr()
plt.matshow(corr)

y_label= X_df.columns.values
y_pos=np.arange(len(y_label))
x_label=y_label.copy()
for i in range(len(x_label)):
    x_label[i]=y_label[i][:4]
x_pos=np.arange(len(x_label))

plt.xticks(x_pos,x_label)
plt.yticks(y_pos,y_label)
plt.colorbar()
plt.title('Covariance Matrix')
plt.show()

#%%
# Histogrammes 
plt.figure(2)
plt.hist(df['Pregnancies'],color='g',bins=range(0,20),align='left')
plt.title('Histogramme Pregnancies')
plt.show()

plt.figure(3)
plt.hist(df['Age'],color='y',bins=range(20,90,2),align='left')
plt.title('Histogramme Age')
plt.show()

plt.figure(4)
plt.hist2d(df['Age'],df['Pregnancies'],bins=[range(21,80,2),range(0,20)])
plt.xlabel('Age')
plt.ylabel('Pregnancies')
plt.title('Histogramme 2D Pregnancies/Age')
plt.show()

#%%
# build model
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import PolynomialFeatures
from sklearn.impute import SimpleImputer

from sklearn.model_selection import GridSearchCV

from sklearn import metrics
from sklearn.metrics import roc_curve
from sklearn.metrics import roc_auc_score
from sklearn.metrics import r2_score


#%%
svm = SVC(probability=True)
reglog=LogisticRegression(solver='liblinear')

# preprocess
scale_pipe= StandardScaler()
ploy= PolynomialFeatures(degree=2)
imput= SimpleImputer(missing_values=-1,strategy='mean')

## grid parameters
param_svm=dict(clf__C=[0.001,0.1,1,10],clf__kernel=['rbf','linear','sigmoid'])
param_reglog=dict(clf__C=[0.001,0.1,1,10])

## declaration
clf_name=['SVM','RegLog']
clf=[svm,reglog]
param_grid=[param_svm,param_reglog]

auc_all=[]
fpr_all=[]
tpr_all=[]

train_size_all=[]
train_score_all=[]
cv_score_all=[]

for i in [0,1]:
    pipe= Pipeline([
        ('imput',imput),
        ('ploy',ploy),
        ('scale',scale_pipe),
        ('clf',clf[i])])
    
    grid= GridSearchCV(pipe,param_grid=param_grid[i],cv=4,scoring='accuracy')
    g=grid.fit(X_train,y_train)

    result= grid.cv_results_

    bp=grid.best_params_
    print('Best parameters for %s:'%clf_name[i])
    print(bp)

    be=grid.best_estimator_
    predict=be.predict(X_test)

## scores

    report=metrics.classification_report(y_test,predict)

    conf_mat=metrics.confusion_matrix(y_test,predict)

    print('Reporting for %s:'%clf_name[i])
    print(report)

    print('Confusion matrix for %s:'%clf_name[i])
    print(conf_mat)

### learning curve ###

    from sklearn.model_selection import learning_curve
    from sklearn.model_selection import ShuffleSplit

    cv=ShuffleSplit(n_splits=10,test_size=0.2,train_size=None,random_state=1)


    train_size,train_score,cv_score=learning_curve(be,X_df,
                                                 Y_df,
                                                 cv=cv,scoring='accuracy')
    
    train_size_all.append(train_size)
    train_score_all.append(train_score)
    cv_score_all.append(cv_score)

### ROC curve ###

    clf_proba=be.predict_proba(X_test)

    fpr,tpr,thresolds=roc_curve(y_test,clf_proba[:,1])
    
    auc=roc_auc_score(y_test,clf_proba[:,1])
    
    fpr_all.append(fpr)
    tpr_all.append(tpr)
    auc_all.append(auc)


# %% markdown
> Note： 首先，你应该导入numpy包，`import numpy as np`  
如果还未安装请使用`pip install numpy`或者`conda install numpy`进行安装.  