# -*- coding: utf-8 -*-

import h5py
import numpy as np
import tensorflow_probability as tfp
from scipy.spatial import distance

from anomalyModelBase import AnomalyModelBase
import feature_extractor.utils as utils

class AnomalyModelSVG(AnomalyModelBase):
    """
    Anomaly model formed by a Single Variate Gaussian (SVG) with model parameters Θ_SVG = (μ,σ²)
    Reference: https://www.mdpi.com/1424-8220/16/11/1904/htm
    """
    def __init__(self):
        AnomalyModelBase.__init__(self)
        self.name = "SVG"
        self.var        = None # Variance σ²
        self.mean       = None # Mean μ
        self.threshold  = None # Threshold for classification

    
    def classify(self, feature_vector, threshold=None):
        """
        The anomaly measure is defined as the Mahalanobis distance between a feature sample
        and the single variate Gaussian distribution along each dimension.
        """
        if threshold is None:
            threshold = self.threshold
        return self.mahalanobis_distance(feature_vector) > threshold
    
    def mahalanobis_distance(self, feature_vector):
        """
        Calculate the Mahalanobis distance between the input and the model
        """
        assert not self.var is None and not self.mean is None, \
            "You need to load a model before computing a Mahalanobis distance"
        assert feature_vector.shape == self.var.shape == self.mean.shape, \
            "Shapes don't match (x: %s, μ: %s, σ²: %s)" % (feature_vector.shape, self.mean.shape, self.var.shape)
        
        return np.sqrt(np.sum((feature_vector - self.mean) **2 / self.var))
        
        ### scipy implementation is way slower
        # if self.varI is None:
        #     self.varI = np.linalg.inv(np.diag(self.var))
        # return distance.mahalanobis(feature_vector, self.mean, self.varI)

    def load_model_from_file(self, model_file):
        """ Load a SVG model from file """
        print("Reading model parameters from: %s" % model_file)
        with h5py.File(model_file, "r") as hf:
            self.var  = np.array(hf["var"])
            self.mean = np.array(hf["mean"])
        assert len(self.var) == len(self.mean), "Dimensions of variance and mean do not match!"
        print("Successfully loaded model parameters of dimension %i" % len(self.var))
    
    def generate_model(self, locations, features):
        # Reduce features to simple list
        features_flat = self.reduce_feature_array(features)

        print("Generating a Single Variate Gaussian (SVG) from %i feature vectors of length %i" % (features_flat.shape[0], features_flat.shape[1]))

        # Get the variance
        print("Calculating the variance")
        # self.var = tfp.stats.variance(features_flat)
        self.var = np.var(features_flat, axis=0, dtype=np.float64)
        # --> one variance per feature vector entry

        # Get the mean
        print("Calculating the mean")
        self.mean = np.mean(features_flat, axis=0, dtype=np.float64)
        # --> one mean per feature vector entry

        # Get maximum mahalanobis distance as threshold
        print("Calculating the threshold")
        dists = np.array(list(map(self.mahalanobis_distance, features_flat)))
        self.threshold = np.amax(dists)

    def save_model_to_file(self, output_file = ""):
        """ Save the model to disk """
        print("Writing model parameters to: %s" % output_file)
        with h5py.File(output_file, "w") as hf:
            hf.create_dataset("var", data=self.var, dtype=np.float64)
            hf.create_dataset("mean", data=self.mean, dtype=np.float64)
            hf.create_dataset("threshold", data=self.threshold, dtype=np.float64)
        print("Successfully written model parameters to: %s" % output_file)

# Only for tests
if __name__ == "__main__":
    model = AnomalyModelSVG()
    model.generate_model_from_file("/home/ludwig/ros/src/ROS-kate_bag/bags/autonomous_realsense-TFRecord/FeaturesMobileNetV2.h5")

    locations, features = utils.read_hdf5("/home/ludwig/ros/src/ROS-kate_bag/bags/autonomous_realsense-TFRecord/FeaturesMobileNetV2.h5")

    # model.generate_model(locations, features)
    # model.load_model_from_file("/home/ludwig/ros/src/ROS-kate_bag/bags/autonomous_realsense-TFRecord/FeaturesMobileNetV2AnomalyModelSVG.h5")
    
    features_flat = model.reduce_feature_array(features)

    dists = np.array(list(map(model.mahalanobis_distance, features_flat)))

    print np.amax(dists)