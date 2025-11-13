
sorterPrefix = '{recording}/processed/ms4'

rule sort_spikes:
    input:
        recording_to_sort = '{recording}',
    output:
        recording_info = '{recording}/processed/recording_info.pkl'
    log:
        '{recording}/processed/snakemake.log'
    script:
        '../scripts/error.py'
