 // sir.stan

 functions {
   // SIR system right-hand side
   real[] stan_sir(real t, real[] y, real[] theta, real[] x_r, int[] x_i) {
     real S = y[1];
     real I = y[2];
     real R = y[3];
     real M = x_i[1];
     real beta = theta[1];
     real gamma = theta[2];
     real dS_dt = -beta * I * S / M;
     real dI_dt =  beta * I * S / M - gamma * I;
     real dR_dt =  gamma * I;
     return { dS_dt, dI_dt, dR_dt };
   }

   // Solve the SIR system
   vector stan_solve_sir(data real[] ts, real[] theta,
       data real[] x_r,
       data real rtol, data real atol, data int max_num_steps) {
     int N = num_elements(ts);
     int M = 1000; // population size
     int I0 = 20; // number of infected on day 0
     int x_i[1] = { M }; // population size
     real y0[3] = { M - I0, I0, 0.0 }; // S, I, R on day 0
     real f[N, 3] = integrate_ode_bdf(stan_sir, y0, 0.0, ts, theta,
       x_r, x_i, rtol, atol, max_num_steps);
     return(to_vector(f[, 2]));
   }
 }

 data {
   int<lower=1> N;         // Number of observations
   real t_data[N];         // Observation times
   int y_observed[N];          // Counts of infected people
   int<lower=1> max_num_steps;

   real likelihood;
   real prec_fit;
   real prec_sim;
 }

 transformed data {
   real x_r[0];
   real rtol_fit = pow(10, -prec_fit);
   real atol_fit = pow(10, -prec_fit-8);
   real rtol_sim = pow(10, -prec_sim);
   real atol_sim = pow(10, -prec_sim-8);
 }

 parameters {
   real<lower=0> beta;
   real<lower=0> gamma;
   real<lower=0> phi;
 }

 transformed parameters{
   vector[N] y_true;
   if(likelihood){
    y_true = stan_solve_sir(
      t_data, { beta, gamma },
      x_r, rtol_fit, atol_fit, max_num_steps
     );
   }
 }

 model {
   beta ~ normal(2, 1);
   gamma ~ normal(0.4, 0.5);
   phi ~ lognormal(1, 1);

   // Add small positive number to solution to avoid negative numbers
   if(likelihood){
     y_observed ~ neg_binomial_2(y_true + 2.0 * atol_fit, phi);
   }
 }
generated quantities {
  int y_predicted[N] = neg_binomial_2_rng(
    stan_solve_sir(
      t_data, { beta, gamma },
      x_r, rtol_sim, atol_sim, max_num_steps
    )  + 2.0 * atol_sim,
     phi
    );
}
