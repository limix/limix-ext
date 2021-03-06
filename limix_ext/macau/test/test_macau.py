from __future__ import division

import sys

import pytest
from numpy import array, asarray, dot, empty, hstack, ones, pi, sqrt, zeros
from numpy.random import RandomState
from numpy.testing import assert_almost_equal, assert_allclose

import limix_ext as lxt


@pytest.mark.skipif('linux' not in sys.platform, reason="requires Linux")
def test_macau():

    random = RandomState(139)
    nsamples = 1000
    nfeatures = 1500

    G = random.randn(nsamples, nfeatures) / sqrt(nfeatures)

    u = random.randn(nfeatures)

    z = 0.1 + 2 * dot(G, u) + random.randn(nsamples)

    ntrials = random.randint(10, 500, size=nsamples)

    y = zeros(nsamples)
    for i in range(len(ntrials)):
        y[i] = sum(
            z[i] + random.logistic(scale=pi / sqrt(3), size=ntrials[i]) > 0)
    M = ones((nsamples, 1))

    K = G.dot(G.T)
    (stats, pvals) = lxt.macau.qtl.binomial_scan(y, ntrials, M, G[:, 0:5], K)

    pvals_expected = array([0.02004, 0.4066, 0.5314, 0.9621, 0.8318])
    stats_expected = array([0, 0, 0, 0, 0])

    pvals = asarray(pvals)
    stats = asarray(stats)

    assert_almost_equal(pvals / 10, pvals_expected / 10, decimal=1)
    assert_almost_equal(stats / 10, stats_expected / 10, decimal=1)


@pytest.mark.skipif('linux' not in sys.platform, reason="requires Linux")
def test_macau_heritability():

    random = RandomState(139)
    # random = RandomState(int(sys.argv[1]))
    nsamples = 100
    # nsamples = int(sys.argv[2])
    nfeatures = 1500

    G = random.randn(nsamples, nfeatures) / sqrt(nfeatures)

    u = random.randn(nfeatures)

    # z = 0.1 + 2 * dot(G, u) + random.randn(nsamples)
    z = 0 * dot(G, u) + random.randn(nsamples)

    ntrials = random.randint(10, 500, size=nsamples)

    y = zeros(nsamples)
    for i in range(len(ntrials)):
        y[i] = sum(
            z[i] + random.logistic(scale=pi / sqrt(3), size=ntrials[i]) > 0)
    M = ones((nsamples, 1))

    K = G.dot(G.T)
    h2 = lxt.macau.heritability.binomial_estimate(y, ntrials, M, K)
    assert_allclose(h2, 0.4196, rtol=1e-1)


if __name__ == '__main__':
    test_macau_heritability()
