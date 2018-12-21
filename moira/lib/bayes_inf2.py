
class BayesianSubModel:
    class Correlation:
        UNCORRELATED = 0

    def __init__(self,lower_bound,upper_bound,n):
        self._lb = lower_bound
        self._ub = upper_bound
        self._n = n


    def to_fv(self,state):
        # indices: [-n/2...-1,0,1,...n/2] (0 means no offset)
        raise Exception("TODO: center around freq to predict")

    def help(self):
        """
        bayesian inference derives the posterior, from the
        likelihood function and the prior.
        the likelihood function is framed as a statistical
        model.
        """
    def prior(self):
        """
        our guess of the distribution of the noise model
        P(noise_model)
        """
        pass

    def marginal_likelihood(self):
        """
        our guess at the probability of the noise data
        P(noise_data)
        """
        pass

    def likelihood(self):
        """
        the probability the data was observed, given noise model
        P(noise_data|noise_model)
        """
        pass

    def posterior(self):
        """
        the probability the noise model is valid, given data
        P(noise_model|noise_data)
        """
        pass

    def _statistical_model_correlated(self):
        # 500,000 for example
        nfreqs = self._fv.num_features()
        freqs = self._fv.freqs()
        # freqs to pull from :FA*freq+FB
        FREQS = self._fv.freqs()
        FA=pm.Uniform('FA',0.0,1.0,shape=(self._n))
        FB=pm.Uniform('FB',0.0,1.0,shape=(self._n))
        TARG = FA*FREQ+FB
        # find index of closest frequency for each index
        indices = tensor.argmax(((FREQS - TARG)**2).sum(axis=1))
        # signal-dependent scaling for mean
        A=pm.Uniform('A',0.0,1.0,shape=(self._n))


    def statistical_model(self,corr=BayesianSubModel.UNCORRELATED):
        F = theano.shared(np.zeros(1))
        # signal independent scaling for mean
        U1=pm.Uniform('U1',-1.0,1.0,shape=(1))
        U2=pm.Uniform('U2',-1.0,1.0,shape=(1))
        # signal independent scaling for variance
        V1=pm.Uniform('V1',-1.0,1.0,shape=(1))
        V2=pm.Uniform('V2',-1.0,1.0,shape=(1))
        if corr == BayesianSubModel.UNCORRELATED:
            mu_model = U1*F + U2
            sigma_model = V1*F + V2
        else:
            raise Exception("unimpl")

        mu_model = signal_mu*A+B
        sigma_model = signal_var*A+C
        obs = pm.Normal('mu_obs',
                        mu=model,
                        sd=error,
                        observed=obs,
                        total_size=(2))

        return obs
