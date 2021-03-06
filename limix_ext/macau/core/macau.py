import logging
import os
import subprocess
import tempfile

import numpy as np
import pandas as pd
from pandas import DataFrame


def _run_scan(y_fp, ntrials_fp, K_fp, predictor_fp):
    outfolder = tempfile.mkdtemp()
    here = os.path.abspath(os.path.dirname(__file__))
    cmd = [
        os.path.join(here, 'macau'), '-g', y_fp, '-t', ntrials_fp, '-p',
        predictor_fp, '-k', K_fp, '-o', outfolder
    ]

    os.makedirs(os.path.join(outfolder, 'output', 'tmp'))
    logger = logging.getLogger(__name__)
    msg = "Running shell list %s.", str(cmd)
    logger.debug(msg)
    p = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=outfolder)
    out, err = p.communicate()
    logger.debug(out)
    if len(err) > 0:
        logger.warn(err)

    assoc_file = os.path.join(outfolder, 'output', 'tmp',
                              os.path.basename(outfolder) + '.assoc.txt')
    df = pd.read_csv(assoc_file, sep='\t', index_col=0)

    return df


def _run_heritability(y_fp, ntrials_fp, K_fp, predictor_fp, NP):
    outfolder = tempfile.mkdtemp()
    here = os.path.abspath(os.path.dirname(__file__))
    cmd = [
        os.path.join(here, 'macau'),
        '-g',
        y_fp,
        '-t',
        ntrials_fp,
        '-p',
        predictor_fp,
        '-k',
        K_fp,
        '-h',
        '0.01',
        '0.99',
        str(NP)
    ]

    logger = logging.getLogger(__name__)
    msg = "Running shell list %s.", str(cmd)
    logger.debug(msg)
    p = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=outfolder)
    out, err = p.communicate()
    logger.debug(out)
    if len(err) > 0:
        logger.warn(err)

    assoc_file = os.path.join(outfolder, 'output', 'result.assoc.txt')
    df = pd.read_csv(assoc_file, sep='\t', index_col=0)
    return df['h'].item()


def run_scan(y, ntrials, K, X):
    outfolder = tempfile.mkdtemp()

    np.savetxt(os.path.join(outfolder, 'K.txt'), K, fmt='%.10f')

    y_df = DataFrame()

    ntrials_df = DataFrame()

    for i in range(K.shape[0]):
        y_df['sample_%d' % i] = [int(y[i])]
        ntrials_df['sample_%d' % i] = [int(ntrials[i])]

    y_df.index = ['site1']
    y_df.index.name = 'site'

    ntrials_df.index = ['site1']
    ntrials_df.index.name = 'site'

    y_df.to_csv(os.path.join(outfolder, 'y.txt'), sep=" ")
    ntrials_df.to_csv(os.path.join(outfolder, 'ntrials.txt'), sep=" ")

    dfs = DataFrame()
    for i in range(X.shape[1]):
        np.savetxt(
            os.path.join(outfolder, 'predictor.txt'), X[:, i], fmt='%.2f')

        df = _run_scan(
            os.path.join(outfolder, 'y.txt'),
            os.path.join(outfolder, 'ntrials.txt'),
            os.path.join(outfolder, 'K.txt'),
            os.path.join(outfolder, 'predictor.txt'))
        df.index = [i]
        dfs = dfs.append(df)

    dfs.index.name = 'snp'
    return np.asarray(dfs['pvalue'])


def run_heritability(y, ntrials, K, NP=10):
    outfolder = tempfile.mkdtemp()
    X = np.random.randn(K.shape[0], 1)

    np.savetxt(os.path.join(outfolder, 'K.txt'), K, fmt='%.10f')

    y_df = DataFrame()

    ntrials_df = DataFrame()

    for i in range(K.shape[0]):
        y_df['sample_%d' % i] = [int(y[i])]
        ntrials_df['sample_%d' % i] = [int(ntrials[i])]

    y_df.index = ['site1']
    y_df.index.name = 'site'

    ntrials_df.index = ['site1']
    ntrials_df.index.name = 'site'

    y_df.to_csv(os.path.join(outfolder, 'y.txt'), sep=" ")
    ntrials_df.to_csv(os.path.join(outfolder, 'ntrials.txt'), sep=" ")

    np.savetxt(os.path.join(outfolder, 'predictor.txt'), X[:, 0], fmt='%.2f')

    return _run_heritability(
        os.path.join(outfolder, 'y.txt'), os.path.join(outfolder,
                                                       'ntrials.txt'),
        os.path.join(outfolder, 'K.txt'),
        os.path.join(outfolder, 'predictor.txt'), NP=NP)
