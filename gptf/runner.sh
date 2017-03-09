DATASETS_DIR_1="/Users/IzmailovPavel/Documents/Education/Programming/DataSets/"
DATASETS_DIR_2="/Users/IzmailovPavel/Documents/Education/Projects/GPtf/data/"

# Synthetic Data (300, 2)
# Initial Values [0.3, 0.8, 0.3]
#DATA_DIR=$DATASETS_DIR_2"synthetic(300,2)/"
#python3 train.py --lr=.1 --batch_size=100 --n_inputs=7 --n_epoch=100 \
#                 --refresh_stats=True --mu_ranks=5 --load_mu_sigma=False \
#                 --datadir=$DATA_DIR --datatype="numpy"
#python3 train.py --lr=.05 --batch_size=100 --n_inputs=7 --n_epoch=100 \
#                 --refresh_stats=True --mu_ranks=5 --load_mu_sigma=True \
#                 --datadir=$DATA_DIR --datatype="numpy"
# Achieves 0.92.

# Synthetic Data (1000, 3)
# Initial Values [0.7, 0.2, 0.2]
# DATA_DIR=$DATASETS_DIR_2"synthetic(1000,3)/"
#python3 train.py --lr=.1 --batch_size=100 --n_inputs=7 --n_epoch=25 \
#                 --refresh_stats=True --mu_ranks=5 --load_mu_sigma=False \
#                 --datadir=$DATA_DIR --datatype="numpy"
#python3 train.py --lr=.01 --batch_size=100 --n_inputs=7 --n_epoch=10 \
#                 --refresh_stats=True --mu_ranks=5 --load_mu_sigma=True \
#                 --datadir=$DATA_DIR --datatype="numpy"
# Achieves 0.97. The second part of the training isn't really required.

# Synthetic Data (3000, 3). Harder dataset, it is generated from a fast varying
# GP in 3D space. Normal methods don't really work on it.
# Initial Values [0.7, 0.2, 0.2]
# DATA_DIR=$DATASETS_DIR_2"synthetic_hard(3000,3)/"
#python3 train.py --lr=.1 --batch_size=100 --n_inputs=7 --n_epoch=25 \
#                 --refresh_stats=True --mu_ranks=7 --load_mu_sigma=False \
#                 --datadir=$DATA_DIR --datatype="numpy"
#python3 train.py --lr=.01 --batch_size=100 --n_inputs=7 --n_epoch=10 \
#                 --refresh_stats=True --mu_ranks=7 --load_mu_sigma=True \
#                 --datadir=$DATA_DIR --datatype="numpy"
# Achieves 0.78.# tt-ranks 5 -> 0.6; tt-ranks 7 -> 0.78

# mg data (1385, 6). This dataset is easy for standard methods.
# Initial Values [0.7, 0.2, 0.2]
#DATA_DIR=$DATASETS_DIR_1"Regression/mg(1385, 6).txt"
#python3 train.py --lr=.05 --batch_size=100 --n_inputs=10 --n_epoch=200 \
#                 --refresh_stats=True --mu_ranks=3 --load_mu_sigma=False \
#                 --datadir="$DATA_DIR" --datatype="svmlight"
#python3 train.py --lr=.01 --batch_size=100 --n_inputs=10 --n_epoch=200 \
#                 --refresh_stats=True --mu_ranks=3 --load_mu_sigma=True \
#                 --datadir="$DATA_DIR" --datatype="svmlight"
# Achieves NA. tt-ranks 3 -> 0.68.
