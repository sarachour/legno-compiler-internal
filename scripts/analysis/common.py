import matplotlib.pyplot as plt

def simple_plot(entry,path_h,trial,tag,t,x):
  plt.plot(t,x,label=tag)
  plt.legend()
  filename = path_h.plot(entry.bmark,
                         entry.arco_indices,
                         entry.jaunt_index,
                         entry.objective_fun,
                         entry.math_env,
                         entry.hw_env,
                         '%s-%d-%s' % (entry.varname,trial,tag))
  plt.savefig(filename)
  plt.clf()


def mean_std_plot(entry,path_h,trial,tag,t,mean,std):
  UPPER = list(map(lambda a: a[0]+a[1],zip(mean,std)))
  LOWER = list(map(lambda a: a[0]-a[1],zip(mean,std)))
  plt.plot(t,UPPER,label='+std',color='red')
  plt.plot(t,LOWER,label='-std',color='red')
  plt.plot(t,mean,label='mean',color='black')
  plt.legend()
  filename = path_h.plot(entry.bmark,
                         entry.arco_indices,
                         entry.jaunt_index,
                         entry.objective_fun,
                         entry.math_env,
                         entry.hw_env,
                         '%s-%d-%s' % (entry.varname,trial,tag))
  plt.savefig(filename)
  plt.clf()


