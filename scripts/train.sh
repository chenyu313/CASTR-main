#! /bin/bash

#==========
set -exu
set -o pipefail
#==========

#python model/run.py --task WN18RR_v1 --cuda_id 0
#python model/run.py --task WN18RR_v2 --cuda_id 0
#python model/run.py --task WN18RR_v3 --cuda_id 0
#python model/run.py --task WN18RR_v4 --cuda_id 1

#python model/run.py --task fb237_v1 --cuda_id 0
python model/run.py --task fb237_v2 --cuda_id 0
#python model/run.py --task fb237_v3 --cuda_id 0
#python model/run.py --task fb237_v4 --cuda_id 1

#python model/run_noise.py --task WN18RR_v1 --cuda_id 1
#python model/run_noise.py --task WN18RR_v2 --cuda_id 1
#python model/run_noise.py --task WN18RR_v3 --cuda_id 1
#python model/run_noise.py --task WN18RR_v4 --cuda_id 1

#python model/run_noise.py --task fb237_v1 --cuda_id 1
#python model/run_noise.py --task fb237_v2 --cuda_id 1
#python model/run_noise.py --task fb237_v3 --cuda_id 1
#python model/run_noise.py --task fb237_v4 --cuda_id 1

#python model/run_noise.py --task drkg --cuda_id 1