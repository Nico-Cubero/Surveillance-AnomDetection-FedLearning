# -*- coding: utf-8 -*-
###############################################################################
# Author: Nicolás Cubero Torres
# Description: Agregattion methods implementation for federated learning
#				architectures..
###############################################################################

# Imported modules
from tf.keras import Model

def fedAvg(models: list, samp_per_models: list, output_model: Model):

	# Check input parameters
	if (not isinstance(models, list) or
							any(not isinstance(x, Model) for x in models)):
		raise ValueError('"models" should be a list of keras models')

	if (not isinstance(samp_per_models, list) or
				any(not isinstance(x, int) for x in samp_per_models) or
				len(models) != len(samp_per_models)):
		raise ValueError('"samp_per_models" should be a list of int with'\
						' the same length as "models"')

	if any(x < 0 for x in samp_per_models):
		raise ValueError('"samp_per_models" values must be greater than 0')

	if not isinstance(output_model, Model):
		raise ValueError('"output_model" must be a Model')

	# Processing
	total_samples = float(sum(samp_per_models))

	# Agregates weights of first client
	for l in range(len(output_model.layers)):
		output_model.get_layer(l).set_weights(
							models[0].get_layer(l).get_weights()*
							(samp_per_models[0]/total_samples))

	# Agregates weights of the rest clients
	for c in range(1, len(models)):

		for l in range(len(output_model.layers)):
			output_model.get_layer(l).set_weights(
								output_model.get_layer(l).get_weights()+
								models[c].get_layer(l).get_weights()*
								(samp_per_models[c]/total_samples))

