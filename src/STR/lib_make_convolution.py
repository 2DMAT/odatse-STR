import numpy as np

def calc(data, omega):
    """
    Calculate the convolution of the input data with a Gaussian function.

    Parameters:
    data (numpy.ndarray): Input data array where the first column is x values and the remaining columns are y values.
    omega (float): Parameter to determine the width of the Gaussian function.

    Returns:
    numpy.ndarray: Convolved data array with the same shape as the input data.
    """
    sigma = 0.5 * omega / (np.sqrt(2.0 * np.log(2.0)))

    def gaussian(x):
        """
        Gaussian function.

        Parameters:
        x (numpy.ndarray): Input array.

        Returns:
        numpy.ndarray: Gaussian function values for the input array.
        """
        gaussian = (1.0 / (sigma * np.sqrt(2.0 * np.pi))) * np.exp(-0.5 * x**2 / sigma**2)
        return gaussian

    conv = np.zeros(data.shape)

    xs = np.array(data[:,0])
    vs = data[:,1:]

    dxs = np.roll(xs,-1) - xs
    dxs[-1] = dxs[-2]

    ys = np.zeros(vs.shape)

    for idx in range(xs.shape[0]):
        ys[idx] = np.einsum('ik,i,i->k', vs, gaussian(xs-xs[idx]), dxs)

    conv[:,0] = xs
    conv[:,1:] = ys

    # if verbose_mode:
    #     print("conv =\n", conv)

    return conv

