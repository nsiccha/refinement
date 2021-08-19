no_samples = 6*8*100
no_chains = 6
sample_kwargs = dict(
    chains=no_chains,
    parallel_chains=6,
    seed=3,
    show_progress=True, refresh=1,
    iter_sampling=no_samples//no_chains,
    cache_dir='out',
    warmup=dict(
        resample=dict(min_mul=-2),
    )
)
