import logging

import numpy as np
import scipy.stats as stats

from .eigd import eigenDecompose


def calcLiabThreholds(U, S, keepArr, phe, numRemovePCs, prev):

    #Run logistic regression
    G = U[:, -numRemovePCs:] * np.sqrt(S[-numRemovePCs:])
    import sklearn.linear_model
    Logreg = sklearn.linear_model.LogisticRegression(
        penalty='l2', C=500000, fit_intercept=True)
    Logreg.fit(G[keepArr, :numRemovePCs], phe[keepArr])

    #Compute individual thresholds
    Pi = Logreg.predict_proba(G)[:, 1]

    #Compute thresholds and save to files
    P = np.sum(phe == 1) / float(phe.shape[0])
    K = prev
    Ki = K * (1 - P) / (P * (1 - K)) * Pi / (1 + K * (1 - P) /
                                             (P * (1 - K)) * Pi - Pi)
    thresholds = stats.norm(0, 1).isf(Ki)
    thresholds[Ki >= 1.] = -999999999
    thresholds[Ki <= 0.] = 999999999

    return Pi, thresholds


def calcH2Continuous_twotails(XXT, phe, keepArr, prev, h2coeff):
    logger = logging.getLogger(__name__)
    logger.debug('computing h2 for a two-tails ascertained study.')

    XXT = XXT[np.ix_(keepArr, keepArr)]
    phe = phe[keepArr]

    t1 = stats.norm(0, 1).ppf(prev)
    t2 = stats.norm(0, 1).isf(prev)
    phit1 = stats.norm(0, 1).pdf(t1)
    phit2 = stats.norm(0, 1).pdf(t2)

    K1 = prev
    K2 = prev

    xCoeff = ((phit2 * t2 - phit1 * t1 + K1 + K2)**2 * (K1 + K2)**2 -
              (phit2 - phit1)**4) / (K1 + K2)**4
    intersect = ((phit2 - phit1) / (K1 + K2))**2

    pheMean = 0
    pheVar = 1

    x = (xCoeff * h2coeff) * XXT
    y = np.outer((phe - pheMean) / np.sqrt(pheVar),
                 (phe - pheMean) / np.sqrt(pheVar))
    y -= intersect

    y = y[np.triu_indices(y.shape[0], 1)]
    x = x[np.triu_indices(x.shape[0], 1)]

    slope, _, _, _, _ = stats.linregress(x, y)
    return slope


def calcH2Continuous(XXT, phe, keepArr, prev, h2coeff):
    t = stats.norm(0, 1).isf(prev)
    phit = stats.norm(0, 1).pdf(t)

    K1 = 1 - prev
    K2 = 1 - K1
    P = np.sum(phe < t) / float(phe.shape[0])
    P2 = 1.0
    P1 = K2 * P2 * P / (K1 * (1 - P))
    R = P2 / P1

    XXT = XXT[np.ix_(keepArr, keepArr)]
    phe = phe[keepArr]

    xCoeff = (((R - 1) * phit * t + K1 + R * K2)**2 * (K1 + R * K2)**2 -
              ((R - 1) * phit)**4) / (K1 + R * K2)**4
    x = (xCoeff * h2coeff) * XXT
    pheMean = 0
    pheVar = 1
    y = np.outer((phe - pheMean) / np.sqrt(pheVar),
                 (phe - pheMean) / np.sqrt(pheVar))
    y -= ((R - 1) * phit / (K1 + R * K2))**2

    y = y[np.triu_indices(y.shape[0], 1)]
    x = x[np.triu_indices(x.shape[0], 1)]

    slope, _, _, _, _ = stats.linregress(x, y)
    return slope


def calcH2Binary(XXT, phe, probs, thresholds, keepArr, prev, h2coeff):
    K = prev
    P = np.sum(phe > 0) / float(phe.shape[0])

    XXT = XXT[np.ix_(keepArr, keepArr)]
    phe = phe[keepArr]

    if (thresholds is None):
        t = stats.norm(0, 1).isf(K)
        phit = stats.norm(0, 1).pdf(t)
        xCoeff = P * (1 - P) / (K**2 * (1 - K)**2) * phit**2 * h2coeff
        y = np.outer((phe - P) / np.sqrt(P * (1 - P)),
                     (phe - P) / np.sqrt(P * (1 - P)))
        x = xCoeff * XXT

    else:
        probs = probs[keepArr]
        thresholds = thresholds[keepArr]
        Ki = K * (1 - P) / (P * (1 - K)) * probs / (1 + K * (1 - P) /
                                                    (P *
                                                     (1 - K)) * probs - probs)
        phit = stats.norm(0, 1).pdf(thresholds)
        probsInvOuter = np.outer(probs * (1 - probs), probs * (1 - probs))
        y = np.outer(phe - probs, phe - probs) / np.sqrt(probsInvOuter)
        sumProbs = np.tile(np.column_stack(probs).T,
                           (1, probs.shape[0])) + np.tile(
                               probs, (probs.shape[0], 1))
        Atag0 = np.outer(phit, phit) * (
            1 - (sumProbs) * (P - K) / (P * (1 - K)) + np.outer(probs, probs) *
            (((P - K) / (P * (1 - K)))**2)) / np.sqrt(probsInvOuter)
        B0 = np.outer(Ki + (1 - Ki) * (K * (1 - P)) / (P * (1 - K)),
                      Ki + (1 - Ki) * (K * (1 - P)) / (P * (1 - K)))
        x = (Atag0 / B0 * h2coeff) * XXT

    y = y[np.triu_indices(y.shape[0], 1)]
    x = x[np.triu_indices(x.shape[0], 1)]

    slope, _, _, _, _ = stats.linregress(x, y)
    return slope


def calc_h2(pheno, prev, eigen, keepArr, numRemovePCs, h2coeff, lowtail):
    logger = logging.getLogger(__name__)
    # pheno = leapUtils._fixup_pheno(pheno)

    #Extract phenotype
    if isinstance(pheno, dict): phe = pheno['vals']
    else: phe = pheno
    if (len(phe.shape) == 2):
        if (phe.shape[1] == 1): phe = phe[:, 0]
        else: raise Exception('More than one phenotype found')
    if (keepArr is None): keepArr = np.ones(phe.shape[0], dtype=np.bool)

    #Compute kinship matrix
    XXT = eigen['XXT']

    #Remove top PCs from kinship matrix
    if (numRemovePCs > 0):
        if (eigen is None):
            S, U = leapUtils.eigenDecompose(XXT)
        else:
            S, U = eigen['arr_1'], eigen['arr_0']
        logger.info('Removing the top %d PCs from the kinship matrix',
                    numRemovePCs)
        XXT -= (U[:, -numRemovePCs:] *
                S[-numRemovePCs:]).dot(U[:, -numRemovePCs:].T)

    #Determine if this is a case-control study
    pheUnique = np.unique(phe)
    if (pheUnique.shape[0] < 2):
        raise Exception('Less than two different phenotypes observed')
    isCaseControl = (pheUnique.shape[0] == 2)

    if isCaseControl:
        logger.debug('Computing h2 for a binary phenotype')
        pheMean = phe.mean()
        phe[phe <= pheMean] = 0
        phe[phe > pheMean] = 1
        if (numRemovePCs > 0):
            probs, thresholds = calcLiabThreholds(U, S, keepArr, phe,
                                                  numRemovePCs, prev)
            h2 = calcH2Binary(XXT, phe, probs, thresholds, keepArr, prev,
                              h2coeff)
        else:
            h2 = calcH2Binary(XXT, phe, None, None, keepArr, prev, h2coeff)
    else:
        logger.debug('Computing h2 for a continuous phenotype')
        if (not lowtail):
            h2 = calcH2Continuous(XXT, phe, keepArr, prev, h2coeff)
        else:
            h2 = calcH2Continuous_twotails(XXT, phe, keepArr, prev, h2coeff)

    if (h2 <= 0):
        h2 = 0.01
        print("Negative heritability found. Exitting...")
        # raise Exception("Negative heritability found. Exitting...")
    if (np.isnan(h2)):
        h2 = 0.01
        print("Invalid heritability estimate. " +
              "Please double-check your input for any errors.")
        # raise Exception("Invalid heritability estimate. "+
        #                 "Please double-check your input for any errors.")

    logger.debug('h2: %0.6f', h2)
    return h2
