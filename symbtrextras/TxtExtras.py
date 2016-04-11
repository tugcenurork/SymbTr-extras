# -*- coding: utf-8 -*-
from musicxmlconverter.symbtr2musicxml import SymbTrScore
from ScoreExtras import ScoreExtras
import pandas as pd
import os
import warnings


class TxtExtras:
    symbtr_cols = ['Sira', 'Kod', 'Nota53', 'NotaAE', 'Koma53', 'KomaAE',
                   'Pay', 'Payda', 'Ms', 'LNS', 'Bas', 'Soz1', 'Offset']

    def __init__(self):
        pass

    @staticmethod
    def check_usul_row(txt_file):
        mu2_usul_dict, inv_mu2_usul_dict = ScoreExtras.parse_usul_dict()

        df = pd.read_csv(txt_file, sep='\t', encoding='utf-8')

        symbtr_name = os.path.splitext(txt_file)[0]

        for index, row in df.iterrows():
            # change null to empty string
            row_changed = TxtExtras._change_null_element_to_empty_str(row)

            if row['Kod'] == 51:
                usul_id = row['LNS']
                usul_name = row['Soz1']
                if usul_name:  # name given
                    TxtExtras._chk_usul_by_name(index, mu2_usul_dict, row,
                                                symbtr_name, usul_id,
                                                usul_name)
                elif usul_id:
                    row_changed = TxtExtras._chk_usul_by_id(
                        index, inv_mu2_usul_dict, row,
                        symbtr_name, usul_id, usul_name, row_changed)
                else:
                    warnings.warn("Unexpected operation")

            # reassign
            if row_changed:
                df.iloc[index] = row

        return df.to_csv(None, sep='\t', index=False, encoding='utf-8')

    @staticmethod
    def _chk_usul_by_name(index, mu2_usul_dict, row, symbtr_name, usul_id,
                          usul_name):
        # check if the usul pair matches with the mu2dict
        if mu2_usul_dict[usul_name]['id'] == usul_id:
            TxtExtras._chk_usul_attr(
                row, mu2_usul_dict[usul_name], 'zaman',
                symbtr_name, index, usul_name)
            TxtExtras._chk_usul_attr(
                row, mu2_usul_dict[usul_name], 'mertebe',
                symbtr_name, index, usul_name)
        else:
            warnings.warn(
                '{0:s}, line {1:s}: {2:s} and {3:s} does not '
                'match.'.format(symbtr_name, str(index),
                                usul_name, str(usul_id)))

    @staticmethod
    def _chk_usul_by_id(index, inv_mu2_usul_dict, row, symbtr_name, usul_id,
                        usul_name, row_changed):
        if usul_id == -1:
            warnings.warn(
                '{0:s}, line {1:s}: Missing usul info'.format(
                    symbtr_name, str(index)))
        else:
            warnings.warn(
                '{0:s}, line {1:s}: Filling missing {2:s}'.format(
                    symbtr_name, str(index),
                    inv_mu2_usul_dict[usul_id]['mu2_name']))
            row['Soz1'] = inv_mu2_usul_dict[usul_id]['mu2_name']

            TxtExtras._chk_usul_attr(
                row, inv_mu2_usul_dict[usul_id], 'zaman',
                symbtr_name, index, usul_name)
            TxtExtras._chk_usul_attr(
                row, inv_mu2_usul_dict[usul_id], 'mertebe',
                symbtr_name, index, usul_name)
            row_changed = True
        return row_changed

    @staticmethod
    def _change_null_element_to_empty_str(row):
        row_changed = False
        for key, val in row.iteritems():
            if pd.isnull(val):
                row[key] = ''
                row_changed = True
        return row_changed

    @staticmethod
    def _chk_usul_attr(row, usul, attr_str, symbtr_name, index, usul_name):
        if attr_str == 'Payda':
            row_str = 'mertebe'
        elif attr_str == 'Pay':
            row_str = 'zaman'
        else:
            raise ValueError('Unexpected usul attribute: %s' % (attr_str))
        if not usul[attr_str] == row[row_str]:
            warnings.warn('{0:s}, line {1:s}: {2:s} and {3:s} does not match.'.
                          format(symbtr_name, str(index), usul_name), attr_str)

    @classmethod
    def add_usul_to_first_row(cls, txt_file, mu2_file):
        # extract symbtr data
        data = ScoreExtras.get_symbtr_data(txt_file, mu2_file)

        # get usul variant
        variant = cls._get_usul_variant(data)  # read the txt score
        df = pd.read_csv(txt_file, sep='\t')

        # create the usul row
        # 1    51            0    0    zaman    mertebe    0    usul_symbtr_internal_id    0    usul_mu2_name    0
        # 1    51            0    0    6    4    0    90    0    Yürüksemâî (6/4)    0
        usul_row = pd.DataFrame(
            {'Sira': 1, 'Kod': 51, 'Nota53': '', 'NotaAE': '', 'Koma53': 0,
             'KomaAE': 0, 'Pay': int(variant['num_pulses']),
             'Payda': int(variant['mertebe']), 'Ms': 0, 'Offset': 0,
             'LNS': variant['symbtr_internal_id'], 'Bas': 0,
             'Soz1': variant['mu2_name']}, index=[0])

        if not df.iloc[0]['Kod'] == 51:
            for index, row in df.iterrows():
                cls._change_null_to_empty_str(row)

                # make sure that "Sira" column continues consecutively
                row['Sira'] = index + 2  # 2 instead of 1, since we also add
                # the usul row to the start

                # reassign
                df.iloc[index] = row

            df_usul = pd.concat(
                [usul_row, df], ignore_index=True)[cls.symbtr_cols]
        else:
            if not df.iloc[0]["LNS"] == usul_row.iloc[0]["LNS"]:
                print(data['symbtr'] + " starts with a different usul row. "
                                       "Correcting...")
                df_usul = pd.concat(
                    [usul_row, df.ix[1:]], ignore_index=True)[cls.symbtr_cols]
            else:
                print(data['symbtr'] + " starts with the usul row. "
                                       "Skipping...")
                df_usul = df

        return df_usul.to_csv(None, sep='\t', index=False, encoding='utf-8')

    @classmethod
    def correct_offset_gracenote(cls, txt_file, mu2_file):
        # extract symbtr data
        data = ScoreExtras.get_symbtr_data(txt_file, mu2_file)

        # get zaman and mertebe from usul variant
        mertebe, zaman = cls._get_zaman_mertebe(data)

        # correct the offsets and the gracenote durations
        df = pd.read_csv(txt_file, sep='\t')
        row = dict()
        for index, row in df.iterrows():
            # recompute the erroneous gracenotes with non-zero duration
            if row['Kod'] == 8 and row['Ms'] > 0:
                row['Pay'] = 0
                row['Payda'] = 0
                row['Ms'] = 0

            # recompute zaman and mertebe, if we hit kod 51
            if row['Kod'] == 51:
                zaman = row['Pay']
                mertebe = row['Payda']
                offset_incr = 0
            else:
                # compute offset
                offset_incr = 0 if row['Payda'] == 0 else \
                    float(row['Pay']) / row['Payda'] * mertebe / zaman

            if index == 0:
                row['Offset'] = offset_incr
            else:
                prev_row = df.iloc[index - 1]
                row['Offset'] = offset_incr + prev_row['Offset']

            # change null to empty string
            cls._change_null_to_empty_str(row)

            # make sure that "Sira" column continues consecutively
            row['Sira'] = index + 1

            # reassign
            df.iloc[index] = row

        cls._check_premature_ending(row)

        return df.to_csv(None, sep='\t', index=False, encoding='utf-8')

    @classmethod
    def _check_premature_ending(cls, row):
        # warn if the last measure end prematurely, i.e. the last note does not
        # have an integer offset
        if not (round(row['Offset'] * 10000) * 0.0001).is_integer():
            warnings.warn("Ends prematurely!")

    @classmethod
    def _get_usul_variant(cls, data):
        usul_dict = ScoreExtras.get_usul_dict()
        vrts = usul_dict[data['usul']['symbtr_slug']]['variants']
        for v in vrts:
            if v['mu2_name'] == data['usul']['mu2_name']:
                return v

        assert False, u'The usul variant {0:s} is not found'.format(
            data['usul']['mu2_name'])

    @classmethod
    def _get_zaman_mertebe(cls, data):
        usul_dict = ScoreExtras.get_usul_dict()
        for usul in usul_dict.values():
            for uv in usul['variants']:
                if uv['mu2_name'] == data['usul']['mu2_name']:
                    return uv['mertebe'], uv['num_pulses']

        assert False, u'Zaman and mertebe for the usul variant {0:s} is not ' \
                      u'available'.format(data['usul']['mu2_name'])

    @staticmethod
    def to_musicxml(symbtr_name, txt_file, mu2_file):
        mbids = ScoreExtras.get_mbids(symbtr_name)

        # MusicXML conversion
        piece = SymbTrScore(txt_file, mu2_file, symbtrname=symbtr_name,
                            mbid_url=mbids)
        return piece.convertsymbtr2xml(verbose=False)

    @staticmethod
    def _change_null_to_empty_str(row):
        # change null to empty string
        for key, val in row.iteritems():
            if pd.isnull(val):
                row[key] = ''
