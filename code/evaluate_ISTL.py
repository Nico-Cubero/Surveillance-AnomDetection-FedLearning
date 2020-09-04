# -*- coding: utf-8 -*-
"""

@author: Nicolás Cubero Torres
@description: Evaluate the prediction of an ISTL model for a given test dataset.

@usage: evaluate_ISTL.py -m <Pretrained model's h5 file>
					-t <Path folder containing the test video>
"""
# Modules imported
import sys
import json
import argparse
import numpy as np
from cv2 import imread, imwrite, resize, cvtColor, COLOR_BGR2GRAY
import tensorflow
from tensorflow.keras.models import load_model
from models import istl

if tensorflow.__version__.startswith('1'):
	from tensorflow import ConfigProto, Session

	config = ConfigProto()
	config.gpu_options.allow_growth = True
	sess = Session(config=config)
else:
	from tensorflow import config

	physical_devices = config.experimental.list_physical_devices('GPU')
	config.experimental.set_memory_growth(physical_devices[0], True)
#from tensorflow.keras import backend as K

# Constants
CUBOIDS_LENGTH = 8
CUBOIDS_WIDTH = 224
CUBOIDS_HEIGHT = 224

# Image resize function
resize_fn = lambda img: np.expand_dims(resize(cvtColor(img, COLOR_BGR2GRAY),
						(CUBOIDS_WIDTH, CUBOIDS_HEIGHT))/255, axis=2)

### Input Arguments
parser = argparse.ArgumentParser(description='Test an Incremental Spatio'\
							' Temporal Learner model for a given test dataset')
parser.add_argument('-m', '--model', help='A pretrained model stored on a'\
					' h5 file', type=str)
parser.add_argument('-c', '--train_folder', help='Path to folder'\
					' containing the train dataset', type=str)
parser.add_argument('-d', '--data_folder', help='Path to folder'\
					' containing the test dataset', type=str)
parser.add_argument('-l', '--labels', help='Path to file containing the test'\
					' labels', type=str)
parser.add_argument('-a', '--anom_threshold',
					help='Anomaly threshold values to test', type=float,
					nargs='+')
parser.add_argument('-t', '--temp_threshold',
					help='Temporal threshold values to test', type=int,
					nargs='+')
parser.add_argument('-o', '--output', help='Output file in which the results'\
					' will be located', type=str)

args = parser.parse_args()

model_fn = args.model
train_video_dir = args.train_folder
test_video_dir = args.data_folder
labels_path = args.labels
anom_threshold = args.anom_threshold
temp_threshold = args.temp_threshold
output = args.output

dot_pos = output.rfind('.')
if dot_pos != -1:
	results_fn = output[:dot_pos] + '.json'
else:
	results_fn = output + '.json'


### Loads model
try:
	model = load_model(model_fn)
except Exception as e:
	print('Cannot load the model: ', str(e), file=sys.stderr)
	exit(-1)


### Load the video test dataset
try:
	data_train = istl.generators.CuboidsGeneratorFromImgs(
									source=train_video_dir,
									cub_frames=CUBOIDS_LENGTH,
									prep_fn=resize_fn)
except Exception as e:
	print('Cannot load {}: '.format(train_video_dir), str(e), file=sys.stderr)
	exit(-1)

try:
	data_test = istl.generators.CuboidsGeneratorFromImgs(source=test_video_dir,
									cub_frames=CUBOIDS_LENGTH,
									prep_fn=resize_fn)
	data_test = istl.generators.ConsecutiveCuboidsGen(data_test)
except Exception as e:
	print('Cannot load {}: '.format(test_video_dir), str(e), file=sys.stderr)
	exit(-1)

try:
	test_labels = np.loadtxt(labels_path, dtype='int8')
except Exception as e:
	print('Cannot load {}: '.format(labels_path), str(e), file=sys.stderr)
	exit(-1)

### Testing for each pair of anomaly and temporal values combinations
print('Performing evaluation with all anomaly and temporal '\
		'thesholds combinations')
evaluator = istl.EvaluatorISTL(model=model,
									cub_frames=CUBOIDS_LENGTH,
									# It's required to put any value
									anom_thresh=0.1,
									temp_thresh=1)
sc_train = evaluator.fit(data_train)

try:
	all_meas = evaluator.evaluate_cuboids_range_params(data_test,
											test_labels,
											anom_threshold,
											temp_threshold)
except Exception as e:
	print(str(e))
	exit(-1)

all_meas['training_rec_error'] = {
								'mean': sc_train.mean(),
								'std': sc_train.std(),
								'min': sc_train.min(),
								'max': sc_train.max()
								}

# Save the results
with open(results_fn, 'w') as f:
	json.dump(all_meas, f, indent=4)
