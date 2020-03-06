import numpy as np

class Feature(np.ndarray):
    """A Feature is the output of a Feature Extractor (values) with metadata as attributes"""

    def __new__(cls, input_array, metadata, x, y, w, h):
        # Input array is an already formed ndarray instance
        # We first cast to be our class type
        obj = np.asarray(input_array).view(cls)
        
        obj.metadata = metadata
        obj.x = x
        obj.y = y
        obj.w = w
        obj.h = h

        # Finally, we must return the newly created object:
        return obj

    def __array_finalize__(self, obj):
        if obj is None: return
        
        self.metadata = getattr(obj, "metadata", None)

        # Patch position
        self.x = getattr(obj, "x", None)
        self.y = getattr(obj, "y", None)

        # Patches per image
        self.w = getattr(obj, "w", None)
        self.h = getattr(obj, "h", None)

        # Will eventually be array [x, y]
        # (call FeatureArray.calculate_locations)
        self.location = None

        self.__bins__ = {}
    
    def __get_property__(key):
        return lambda self: None if self.metadata is None or not key in self.metadata.keys() else self.metadata[key]

    time              = property(__get_property__("time"))
    label             = property(__get_property__("label"))
    rosbag            = property(__get_property__("rosbag"))
    tfrecord          = property(__get_property__("tfrecord"))
    feature_extractor = property(__get_property__("feature_extractor"))

    camera_position   = property(lambda self: None if self.metadata is None else
                                                np.array([self.metadata["location/translation/x"],
                                                          self.metadata["location/translation/y"]]))
    camera_rotation   = property(__get_property__("location/rotation/z"))

    def get_bin(self, cell_size, extent=None):
        """Gets the indices for the bin the given feature belongs to

        Args:
            cell_size (float): Round to cell size (increases bounds to fit next cell size)
        
        Returns:
            Tuple containing the bin indices (u, v)
        """
        assert self.location is not None, "Feature locations need to be computed before computing bins"

        if cell_size in self.__bins__.keys():
            return self.__bins__[cell_size]
        else:
            if extent is None:
                raise ValueError("Extent needs to be specified for calculating the bin.")
            x_min, y_min, x_max, y_max = extent 
            self.__bins__[cell_size] = (int((self.location[0] - x_min) / cell_size),
                                        int((self.location[1] - y_min) / cell_size))
            return self.__bins__[cell_size]

    def cast(self, dtype):
        return np.array(self, dtype=dtype)

if __name__ == "__main__":
    meta = {"time": 232, "test": 24}
    f = Feature(np.array([2,3,4]), meta, 0, 0, 10, 10)
    print f.w
    print f.metadata
    print f.time