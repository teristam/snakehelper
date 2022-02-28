
sorterPrefix = '{recording}/processed/ms4'

rule sort_spikes:
    input:
        recording_to_sort = '{recording}',
    output:
        recording_info = '{recording}/processed/recording_info.pkl'
    run:
        print(wildcards.recording)
