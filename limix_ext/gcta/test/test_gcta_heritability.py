import numpy as np
import pytest

from limix_ext.gcta.heritability import estimate
from limix_ext.util import platform


@pytest.mark.skipif(platform() != "linux", reason="requires linux")
def test_bernoulli():
    random = np.random.RandomState(981)
    n = 500
    p = n + 4

    M = np.ones((n, 1)) * 0.4
    G = random.randint(3, size=(n, p))
    Gi = G.copy()
    G = np.asarray(G, dtype=float)
    G -= G.mean(axis=0)
    G /= G.std(axis=0)
    G /= np.sqrt(p)

    K = np.dot(G, G.T)
    Kg = K / K.diagonal().mean()
    K = 0.5 * Kg + 0.5 * np.eye(n)
    K = K / K.diagonal().mean()

    z = random.multivariate_normal(M.ravel(), K)
    y = np.zeros_like(z)
    y[z > 0] = 1.
    prevalence = 0.5
    h2 = estimate(Gi, y, prevalence)
    np.testing.assert_allclose(h2, 0.329104, rtol=1e-4)
