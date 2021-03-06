#sorry for the messy code in advance
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import scipy.stats as stats
from sklearn import linear_model
import time
import kernelml
#Seaborn scatter plot error?
import matplotlib as mpl
mpl.style.use('default')

def generate_MoG_data(num_data, means, covariances, weights):
    """ Creates a list of data points """
    num_clusters = len(weights)
    data = []
    for i in range(num_data):
        k = np.random.choice(len(weights), 1, p=weights)[0]
        x = np.random.multivariate_normal(means[k], covariances[k])
        data.append(x)
    return data

init_means = [
    [5, 0], # mean of cluster 1
    [1, 1], # mean of cluster 2
    [0, 5]  # mean of cluster 3
]

init_covariances = [
    [[.5, 0.], [0, .5]], # covariance of cluster 1
    [[.92, .38], [.38, .91]], # covariance of cluster 2
    [[.5, 0.], [0, .5]]  # covariance of cluster 3
]
init_weights = [1/4., 1/2., 1/4.]  # weights of each cluster

# Generate data
np.random.seed(4)
data = generate_MoG_data(1000, init_means, init_covariances, init_weights)
d = np.vstack(data)
plt.plot(d[:,0], d[:,1],'ko')
plt.rcParams.update({'font.size':16})
plt.tight_layout()
plt.show()

#probably isn't the best way to get the n-d histogram data
vals, indxs = np.histogramdd(d, normed=False,bins=20)
i=0
for indx in reversed(indxs):
    x = np.linspace(np.min(d[:,i]),np.max(d[:,i]),len(vals)) + np.diff(indx)
    if i==0:
        X = pd.DataFrame(x)
        X['i'] = 1
    else:
        newX = pd.DataFrame(x)
        newX['i'] = 1
        X = X.merge(newX,on='i',how='outer')
    i+=1

X.drop('i',inplace=True,axis=1)
vals = vals.flatten()
X = X.values
X = X[np.where(vals>0)]
vals = vals[np.where(vals>0)]
y = vals/np.max(vals)


#multivariate normal sampler
def sampler_custom(best_param,
                                param_by_iter,
                                error_by_iter,
                                parameter_update_history,
                                random_sample_num=100):
    
    best = param_by_iter[np.where(error_by_iter==np.min(error_by_iter))[0]]
    mean = best.flatten()
    pvarience = np.var(parameter_update_history[:,:],axis=1)
    r = [0]*12
    try:
        for i in range(12):
            r[i] = np.random.normal(mean[i], pvarience[i], (random_sample_num)).T
        
        for i in [1,3,5,7,9,11]:
            val = r[i]
            val[np.where(val<=0)] = 0.1
            r[i] = val
        return np.array(r)
    except:
        print(best,np.where(error_by_iter==np.min(error_by_iter)))



def loss_function(x,y,w):

        u11,u21 = w[0],w[2]
        s11,s21 = w[1],w[3]
        
        u12,u22 = w[4],w[6]
        s12,s22 = w[5],w[7]
        
        u13,u23 = w[8],w[10]
        s13,s23 = w[9],w[11]

        dist1 = scipy.stats.norm(u11,s11).pdf(x[:,0:1])
        dist2 = scipy.stats.norm(u21,s21).pdf(x[:,1:2])
        dist3 = scipy.stats.norm(u12,s12).pdf(x[:,0:1])
        dist4 = scipy.stats.norm(u22,s22).pdf(x[:,1:2])
        dist5 = scipy.stats.norm(u13,s13).pdf(x[:,0:1])
        dist6 = scipy.stats.norm(u23,s23).pdf(x[:,1:2])
         
        rv = (dist1+dist2+dist3+dist4+dist5+dist6)/6

        loss = numpy.sum(numpy.abs(y-rv))
        return loss/len(y)


#change the random sampler
#change the prior uniform distribution
#try to make the algorithm converge faster 
#update magnitude should correspond to loss's magnitude
#low the number of parameter update and rely more on the simulation
#analyze more parameters to add variance to the updates
#update parameters in random order
runs = 1
zscore = 2.0
umagnitude = 1
analyzenparam = 50
nupdates = 10
npriorsamples=100
nrandomsamples = 100
tinterations = 10
percentupdated=1
sequpdate = False

kml = kernelml.KernelML(
         prior_sampler_fcn=None,
         sampler_fcn=sampler_custom,
         intermediate_sampler_fcn=None,
         mini_batch_sampler_fcn=None,
         parameter_transform_fcn=None,
         batch_size=None)

kml.use_ipyparallel(dview)
parameter_by_run = kml.optimize(X,y,loss_function=loss_function,
                                num_param=12,
                                args=[],
                                runs=runs,
                                total_iterations=tinterations,
                                analyze_n_parameters=analyzenparam,
                                n_parameter_updates=nupdates,
                                update_magnitude=umagnitude,
                                sequential_update=sequpdate,
                                percent_of_params_updated=percentupdated,
                                init_random_sample_num=npriorsamples,
                                random_sample_num=nrandomsamples,
                                convergence_z_score=zscore,
                                prior_uniform_low=0.1,
                                prior_uniform_high=2.5,
                                plot_feedback=False,
                                print_feedback=False)


def generate_pdfs(x,y,w):
        u11,u21 = w[0],w[2]
        s11,s21 = w[1],w[3]
        
        u12,u22 = w[4],w[6]
        s12,s22 = w[5],w[7]
        
        u13,u23 = w[8],w[10]
        s13,s23 = w[9],w[11]
        rv = [  stats.norm(u11,s11).pdf(x[:,0:1]),stats.norm(u21,s21).pdf(x[:,1:2]),
                stats.norm(u12,s12).pdf(x[:,0:1]),stats.norm(u22,s22).pdf(x[:,1:2]),
                stats.norm(u13,s13).pdf(x[:,0:1]),stats.norm(u23,s23).pdf(x[:,1:2])
             ]
        return rv


w = kml.model.get_best_param().flatten()

df = pd.DataFrame(X)
df[['dist1','dist2','dist3','dist4','dist5','dist6']]=pd.DataFrame(np.squeeze(np.array(generate_pdfs(X,y,w)))).T
df['y'] = vals/np.max(vals)

#normalize the values
tmp = df[['dist1','dist2','dist3','dist4','dist5','dist6']].values
df[['dist1','dist2','dist3','dist4','dist5','dist6']] = tmp/np.linalg.norm(tmp,axis=0)

#combinations of distributions across each dimension
df[['c0','c1']] = pd.DataFrame(np.column_stack(
                        (np.argmax(df[['dist1','dist3','dist5']].values,axis=1),
                         np.argmax(df[['dist2','dist4','dist6']].values,axis=1)))
                         )
#assign category to each cluster
G = df[['c0','c1']].groupby(['c0','c1']).count().reset_index().reset_index()
df = df.merge(G,on=['c0','c1'])

#plot results
plt.figure(figsize=(10,10))
plt.scatter([x[0] for x in d], [y[1] for y in d])
for i in df['index'].unique():
    clust = df[[0,1,'index']][df['index']==i]
    plt.scatter([x[0] for x in clust[[0]].values], [y[0] for y in clust[[1]].values])
plt.show()

