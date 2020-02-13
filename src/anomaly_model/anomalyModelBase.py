import os
import logging
import h5py
import cv2

import feature_extractor.utils as utils

class AnomalyModelBase(object):
    
    def __init__(self):
        self.NAME = ""          # Should be set by the implementing class
    
    def generate_model(self, metadata, features):
        """Generate a model based on the features and metadata
        
        Args:
            metadata (list): Array of metadata for the features
            features (list): Array of features as extracted by a FeatureExtractor
        """
        raise NotImplementedError
        
    def classify(self, feature_vector):
        """ Classify a single feature vector based on the loaded model """
        raise NotImplementedError
    
    def load_model_from_file(self, model_file):
        """ Load a model from file """
        raise NotImplementedError

    def save_model_to_file(self, output_file):
        """Save the model to output_file
        
        Args:
            output_file (str): Output path for the model file
        """
        raise NotImplementedError

    ########################
    # Common functionality #
    ########################

    def generate_model_from_file(self, features_file, output_file = ""):
        """Generate a model based on the features in features_file and save it to output_file
        
        Args:
            features_file (str) : HDF5 or TFRecord file containing metadata and features (see feature_extractor for details)
            output_file (str): Output path for the model file (same path as features_file if not specified)
        """
        # Check parameters
        if features_file == "" or not os.path.exists(features_file) or not os.path.isfile(features_file):
            raise ValueError("Specified model file does not exist (%s)" % features_file)
        
        if output_file == "":
            output_file = os.path.abspath(features_file.replace(".h5", "")) + "." + self.NAME + ".h5"
            logging.info("Output file set to %s" % output_file)
        
        # Read file
        metadata, features = utils.read_features_file(features_file)

        # Only take feature vectors of images labeled as anomaly free (label == 1)
        features = features[[m["label"] == 1 for m in metadata]]
        metadata = metadata[[m["label"] == 1 for m in metadata]]
        
        # Generate model
        if self.generate_model(metadata, features) == False:
            logging.info("Could not generate model.")
            return False

        # Save model
        self.save_model_to_file(output_file)
        
        return True

    def reduce_feature_array(self, features_vector_array):
        """Reduce an array of feature vectors of shape to a simple list
        
        Args:
            features_vector_array (object[]): feature vectors array
        """
        # Create an array of only the feature vectors, eg. (25000, 1280)
        return features_vector_array.reshape(-1, features_vector_array.shape[-1])

    def visualize(self, metadata, features, feature_to_color_func, feature_to_text_func=None, pause_func=None):
        total, width, height, depth = features.shape

        font                   = cv2.FONT_HERSHEY_SIMPLEX
        fontScale              = 0.3
        thickness              = 1

        tfrecord = None
        tfrecordCounter = 0

        pause = False

        for i, feature_3d in enumerate(features):
            meta = metadata[i]
            
            if tfrecord != meta["tfrecord"]:
                tfrecord = meta["tfrecord"]
                tfrecordCounter = 0
                image_dataset = utils.load_dataset(meta["tfrecord"]).as_numpy_iterator()
            else:
                tfrecordCounter += 1

            image, example = next(image_dataset)
            # if meta["label"] == 1:
            #     continue

            overlay = image.copy()

            # if example["metadata/time"] != meta["time"]:
            #     logging.error("Times somehow don't match (%f)" % (example["metadata/time"]- meta["time"]))

            patch_size = (image.shape[1] / width, image.shape[0] / height)

            for x in range(width):
                for y in range(height):
                    feature = feature_3d[y,x,:]
                    p1 = (x * patch_size[0], y * patch_size[1])
                    p2 = (p1[0] + patch_size[0], p1[1] + patch_size[1])
                    cv2.rectangle(overlay, p1, p2, feature_to_color_func(feature), -1)

                    if feature_to_text_func is not None:
                        cv2.putText(overlay, str(feature_to_text_func(feature)),
                            (p1[0] + 2, p1[1] + patch_size[1] - 2),
                            font,
                            fontScale,
                            (0, 0, 255),
                            thickness)
                    
                    if pause_func is not None and pause_func(feature):
                        pause = True

            alpha = 0.4  # Transparency factor.

            # Following line overlays transparent overlay over the image
            image_new = cv2.addWeighted(overlay, alpha, image, 1 - alpha, 0)
            
            utils.image_write_label(image_new, meta["label"])

            cv2.imshow("", image_new)
            key = cv2.waitKey(0 if pause else 1)
            if key == 27:   # [esc] => Quit
                return None
            elif key != -1:
                pause = not pause