
"""
"""

from copy import copy
import numpy as np
import pymc
import wfpt

from kabuki.hierarchical import Knode
from kabuki.utils import stochastic_from_dist
from hddm.models import HDDM
from wfpt import wiener_like_rlddm

class HDDMrl(HDDM):
    """HDDM model that can be used for two-armed bandit tasks.

    """
    def __init__(self, *args, **kwargs):
        self.alpha = kwargs.pop('alpha', True)
        #self.dual_alpha = kwargs.pop('dual_alpha', True)
        self.wfpt_rl_class = WienerRL

        super(HDDMrl, self).__init__(*args, **kwargs)

    def _create_stochastic_knodes(self, include):
        knodes = super(HDDMrl, self)._create_stochastic_knodes(include)
        if self.alpha:
            # Add learning rate parameter
            knodes.update(self._create_family_normal('alpha',
                                                                    value=0,
                                                                    g_mu=0.2,
                                                                    g_tau=3**-2,
                                                                    std_lower=1e-10,
                                                                    std_upper=10, 
                                                                    std_value=.1))
            
        #if 'dual_alpha' in include:
        #    # Add second learning rate parameter
         #   knodes.update(self._create_family_normal('dual_alpha',
         #                                                           value=0,
         #                                                           g_mu=0.2,
         #                                                           g_tau=3**-2,
          #                                                          std_lower=1e-10,
         #                                                           std_upper=10, 
         #                                                           std_value=.1))
            #tried including here, didn't seem to work
            #knodes['dual_alpha'] = knodes['dual_alpha_bottom'] 
        return knodes

    def _create_wfpt_parents_dict(self, knodes):
        wfpt_parents = super(HDDMrl, self)._create_wfpt_parents_dict(knodes)

        wfpt_parents['alpha'] = knodes['alpha_bottom']
        #fails if dual_alpha is not in include
        #wfpt_parents['dual_alpha'] = knodes['dual_alpha_bottom'] if 'dual_alpha' in self.include else self.default_intervars['dual_alpha']
        
        return wfpt_parents

    #use own wfpt_class, defined in the init
    def _create_wfpt_knode(self, knodes):
        wfpt_parents = self._create_wfpt_parents_dict(knodes)
        return Knode(self.wfpt_rl_class, 'wfpt',
                                   observed=True, col_name=['split_by','rew_up', 'rew_low', 'response', 'rt','trial','exp_up','exp_low'],
                                   **wfpt_parents)

def wienerRL_like(x, v, alpha,dual_alpha, sv, a, z, sz, t, st, p_outlier=0.1):
    wiener_params = {'n_st':2,
                     'n_sz':2,
                     'use_adaptive':1,
                     'simps_err':1e-3,
                     'w_outlier': 0.1}
    
    #print("v = %.2f alpha = %.2f a = %.2f x = %.2f" % (v,alpha,a,x['rt'].values))
    sum_logp = 0
    wp = wiener_params

    #x.sort_values(['split_by','trial'],inplace=True)
    #change = (x.split_by.ne(x.split_by.shift())).astype(int)
    #split_positions = np.flatnonzero(change == 1)
    split_positions = np.array([   0,  10,  12])
    response = x['response'].values
    exp_up = x['exp_up'].values
    exp_low = x['exp_low'].values
    rew_up = x['rew_up'].values
    rew_low = x['rew_low'].values
    return wiener_like_rlddm(x['rt'].values, response,rew_up,rew_low,exp_up,exp_low,split_positions,alpha,dual_alpha,v,sv, a, z, sz, t, st, p_outlier, **wp)
WienerRL = stochastic_from_dist('wienerRL', wienerRL_like)
