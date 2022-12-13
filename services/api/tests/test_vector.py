import numpy as np
import pytest

from unified_graphics import vector


# Test cases taken from the examples at
# http://ncl.ucar.edu/Document/Functions/Contributed/wind_direction.shtml
@pytest.mark.parametrize(
    "u,v,expected",
    (
        [
            np.array([10, 0, 0, -10, 10, 10, -10, -10]),
            np.array([0, 10, -10, 0, 10, -10, 10, -10]),
            np.array([270, 180, 0, 90, 225, 315, 135, 45]),
        ],
        [
            np.array([0.0, -0.0, 0.0, -0.0]),
            np.array([0.0, 0.0, -0.0, -0.0]),
            np.array([0.0, 0.0, 0.0, 0.0]),
        ],
    ),
)
def test_vector_direction(u, v, expected):
    result = vector.direction(u, v)

    np.testing.assert_array_almost_equal(result, expected, decimal=5)


def test_vector_magnitude():
    u = np.array([1, 0, 1, 0])
    v = np.array([0, 1, 1, 0])

    result = vector.magnitude(u, v)

    np.testing.assert_array_almost_equal(
        result, np.array([1, 1, 1.41421, 0]), decimal=5
    )
