#! /bin/bash

#==========
set -exu
set -o pipefail
#==========

#==========preprocess  & its subsets
# python utils/preprocess_ind_data.py --task WN18RR_v1
# python utils/preprocess_ind_data.py --task WN18RR_v1_ind
# python utils/build_RSG.py --task WN18RR_v1
# python utils/negative_sampling_text_sim.py --task WN18RR_v1
# python utils/negative_sampling_text_sim.py --task WN18RR_v1_ind

# python utils/preprocess_ind_data.py --task WN18RR_v2
# python utils/preprocess_ind_data.py --task WN18RR_v2_ind
# python utils/build_RSG.py --task WN18RR_v2
# python utils/negative_sampling_text_sim.py --task WN18RR_v2
# python utils/negative_sampling_text_sim.py --task WN18RR_v2_ind

# python utils/preprocess_ind_data.py --task WN18RR_v3
# python utils/preprocess_ind_data.py --task WN18RR_v3_ind
# python utils/build_RSG.py --task WN18RR_v3
# python utils/negative_sampling_text_sim.py --task WN18RR_v3
# python utils/negative_sampling_text_sim.py --task WN18RR_v3_ind

# python utils/preprocess_ind_data.py --task WN18RR_v4
# python utils/preprocess_ind_data.py --task WN18RR_v4_ind
# python utils/build_RSG.py --task WN18RR_v4
# python utils/negative_sampling_text_sim.py --task WN18RR_v4
# python utils/negative_sampling_text_sim.py --task WN18RR_v4_ind

# python utils/preprocess_ind_data.py --task fb237_v1
# python utils/preprocess_ind_data.py --task fb237_v1_ind
# python utils/build_RSG.py --task fb237_v1
# python utils/negative_sampling_text_sim.py --task fb237_v1
# python utils/negative_sampling_text_sim.py --task fb237_v1_ind

# python utils/preprocess_ind_data.py --task fb237_v2
# python utils/preprocess_ind_data.py --task fb237_v2_ind
# python utils/build_RSG.py --task fb237_v2
# python utils/negative_sampling_text_sim.py --task fb237_v2
# python utils/negative_sampling_text_sim.py --task fb237_v2_ind

# python utils/preprocess_ind_data.py --task fb237_v3
# python utils/preprocess_ind_data.py --task fb237_v3_ind
# python utils/build_RSG.py --task fb237_v3
# python utils/negative_sampling_text_sim.py --task fb237_v3
# python utils/negative_sampling_text_sim.py --task fb237_v3_ind

# python utils/preprocess_ind_data.py --task fb237_v4
# python utils/preprocess_ind_data.py --task fb237_v4_ind
# python utils/build_RSG.py --task fb237_v4
# python utils/negative_sampling_random.py --task fb237_v4
# python utils/negative_sampling_random.py --task fb237_v4_ind

#python utils/preprocess_ind_data.py --task drkg
#python utils/preprocess_ind_data.py --task drkg_ind
#pthon utils/build_RSG.py --task drkg
python utils/negative_sampling_random.py --task drkg
python utils/negative_sampling_random.py --task drkg_ind
