import numpy as np
import pandas as pd
from excmdstanpy import *
from setup import *
vprint.excluded_tags = ['cache', 'resample']#, 'intermediate_refinement']
cmdstan_paths = [
    '/home/niko/cmdstan'
]
cmdstanpy.set_cmdstan_path(cmdstan_paths[-1])
float_formatter = "{:.4g}".format
np.set_printoptions(formatter={'float_kind':float_formatter})

pd.set_option(
    'display.max_rows', None,
    'display.max_columns', None,
    'display.max_colwidth', None,
    'display.expand_frame_repr', False
)

class Model(StanModel):
    def visualize(self, fit, path, bins):
        fig, axes = fit.fig(len(self.params) + 1, col_width=16)
        for i, col in enumerate(self.params):
            ax = axes[i,0]
            ax.set(xlim=[0, bins[i][-1]])
            fit.plot_hist(ax=ax, col=col, bins=bins[i])
        ax = axes[-1, 0]
        fit.plot_fan(ax=ax, col='y_predicted')
        fig.savefig(path)
        plt.close()



class HeatEQ(Model):

    params = ['K', 'sigma']
    refinement_parameters = {
        'Nx_fit': 'Nx_sim',
        'Nt_fit': 'Nt_sim'
    }
    slice_variables = {}

class SIR(Model):
    params = ['beta', 'gamma', 'phi']
    refinement_parameters = {
        'prec_fit': 'prec_sim'
    }
    slice_variables = {
        'N': ['t_data', 'y_observed']
    }


heat_data = dict(
    N_meas=5,
    T_meas=1.,
    x_meas=np.linspace(0,1,7)[1:-1],
    y_observed=np.ones(5),
    likelihood=0,
    Nx_fit=1,
    Nt_fit=1,
    Nx_sim=100,
    Nt_sim=100
)

sir_data = dict(
    N=16,
    t_data=1+np.arange(16),
    y_observed=np.ones(16, dtype=int),
    max_num_steps=int(1e8),
    likelihood=0,
    prec_fit=3,
    prec_sim=12,
)

heat_model = HeatEQ(stan_file='stan/heat.stan')
heat_fit = heat_model.sample(heat_data, **sample_kwargs)

sir_model = SIR(stan_file='stan/sir.stan')
sir_fit = sir_model.sample(sir_data, **sample_kwargs)


for idx in range(100):
    for fit in [sir_fit, heat_fit]:
        model = fit.sample_model
        bins = None
        for goal in [np.inf, .99]:
            model.final_refinement_goal = goal
            fit_data = fit.sbc_data(idx)
            if model.name == 'sir':
                fit_data['y_observed'] = fit_data['y_observed'].astype(int)
            afit = model.asample(fit_data, **sample_kwargs).solenoidal
            if bins is None:
                bins = [np.linspace(0, afit.lw_df[col].max(), 20) for col in model.params]
            afit.animate(f'figs/{model.name}_{idx}_{goal}', model.visualize, bins=bins)
