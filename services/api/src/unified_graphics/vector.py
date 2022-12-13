import numpy as np


def direction(u, v):
    direction = (90 - np.degrees(np.arctan2(-v, -u))) % 360

    # Anywhere the magnitude of the vector is 0
    calm = (np.abs(u) == 0) & (np.abs(v) == 0)

    # numpy.arctan2 treats 0.0 and -0.0 differently. Whenever the second
    # argument to the function is -0.0, it return pi or -pi depending on the
    # sign of the first argument. Whenever the second argument is 0.0, it will
    # return 0.0 or -0.0 depending on the sign of the first argument. We
    # normalize all calm vectors (magnitude 0) to have a direction of 0.0, per
    # the NCAR Command Language docs.
    # http://ncl.ucar.edu/Document/Functions/Contributed/wind_direction.shtml
    direction[calm] = 0.0

    return direction


def magnitude(u, v):
    return np.sqrt(u**2 + v**2)
