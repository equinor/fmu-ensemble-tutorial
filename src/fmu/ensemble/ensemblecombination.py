# -*- coding: utf-8 -*-
"""Module for parsing an ensemble from FMU. This class represents an
ensemble, which is nothing but a collection of realizations.

The typical task of this class is book-keeping of each realization,
and abilities to aggregate any information that each realization can
provide.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from fmu.config import etc


xfmu = etc.Interaction()
logger = xfmu.functionlogger(__name__)


class EnsembleCombination(object):
    """
    The class is used to perform airithmetic operations on Ensembles.
    Currently only simulation summary vectors are supported; howvever,
    functionality will be added to perform operations on any data type.
    """
    def __init__(self, ref, adds=None, subs=None):
        """
        The Operations object is used to substract or add Ensembles.

        Args:
            ref (obj): Name identifier for the ensemble ref case.
            ior (obj): Name identifier for the ensemble ior case.
        """

        self.ref = ref
        self.adds = []
        self.subs = []
        if adds:
            self.adds.append(adds)
        if subs:
            self.subs.append(subs)
        self.combined = self.find_combined()

    def find_combined(self):
        """
        The function finds the corresponding realizations
        which have completed successfully in the all ensembles.
        """
        ref_ok = set(self.ref.get_ok().query('OK == True')['REAL'].tolist())
        operations = self.subs + self.adds
        for operator in operations:
            ior_ok = set(operator.get_ok().query('OK == True')['REAL'].tolist()) # noqa
            ref_ok = list(ref_ok & ior_ok)
        return ref_ok

    def from_smry(self, column_keys=None):
        """
        This function performs airthmetic operations on the
        ensembles and return the corresponding dataframe with the
        requested simulation summary keys.
        """
        time_index = self.ref.get_smry_dates(freq='daily')
        ref = self.ref.from_smry(time_index=time_index,
                                 column_keys=column_keys,
                                 stacked=True)
        ref = ref[ref['REAL'].isin(self.combined)]
        dates = ref['DATE']
        real = ref['REAL']
        ref.drop(columns=['DATE'], inplace=True)
        if self.subs:
            for sub in self.subs:
                ior = sub.from_smry(time_index=time_index,
                                    column_keys=column_keys,
                                    stacked=True)
                ior.drop(columns=['DATE'], inplace=True)
                ior = ior[ior['REAL'].isin(self.combined)]
                ref = ior - ref
        if self.adds:
            for add in self.adds:
                ior = add.from_smry(time_index=time_index,
                                    column_keys=column_keys,
                                    stacked=True)
                ior.drop(columns=['DATE'], inplace=True)
                ior = ior[ior['REAL'].isin(self.combined)]
                ref = ior + ref
        ref.insert(0, 'DATE', dates)
        ref['REAL'] = real

        return ref

    def __sub__(self, other):
        self.subs.append(other)
        return self

    def __add__(self, other):
        self.adds.append(other)
        return self