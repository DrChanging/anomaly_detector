from featureExtractorBase import FeatureExtractorBase

class FeatureExtractorEfficientNetB6_Block10(FeatureExtractorBase):
    """Feature extractor based on EfficientNetB6 (trained on ImageNet).
    Output layer: block_10
    Generates 14x14x112 feature vectors per image
    """

    def __init__(self):
        FeatureExtractorBase.__init__(self)

        self.IMG_SIZE = 528 # All images will be resized to 224x224

        # Create the base model from the pre-trained model
        self.model = self.load_model("https://tfhub.dev/google/efficientnet/b6/feature-vector/1",
                                     output_key="block_10")
    
    def extract_batch(self, batch):
        return self.model(batch)

# Only for tests
if __name__ == "__main__":
    extractor = FeatureExtractorEfficientNetB6_Block10()
    extractor.plot_model(extractor.model, 600)
    extractor.extract_files("/home/ludwig/ros/src/ROS-kate_bag/bags/real/TFRecord/*.tfrecord")