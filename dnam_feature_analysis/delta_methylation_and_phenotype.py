#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Produce the delta methylation and delta phenotype files.
Vegreville minus Lethbridge.

"""

from . import timeit, df, pd
from .helpers import remove_trailing_slash, print_program_runtime


# lethbridge_methylation_file_path = sys.argv[1]
# vegreville_methylation_file_path = sys.argv[2]
# lethbridge_phenotype_file_path = sys.argv[3]
# vegreville_phenotype_file_path = sys.argv[4]
# output_dir_path = sys.argv[5]

def delta(
        lethbridge_methylation_file_path: str,
        vegreville_methylation_file_path: str,
        lethbridge_phenotype_file_path: str, vegreville_phenotype_file_path: str,
        output_dir_path: str
    ) -> None:
    """
    """
    start_time = timeit.default_timer()
    lethbridge_methylation_file_path, vegreville_methylation_file_path, \
        lethbridge_phenotype_file_path, vegreville_phenotype_file_path, \
        output_dir_path = \
            remove_trailing_slash((
                lethbridge_methylation_file_path,
                vegreville_methylation_file_path,
                lethbridge_phenotype_file_path, vegreville_phenotype_file_path,
                output_dir_path
            ))

    print("Reading files...")
    lethbridge_methylation = pd.read_table(lethbridge_methylation_file_path)
    vegreville_methylation = pd.read_table(vegreville_methylation_file_path)
    lethbridge_phenotype = pd.read_table(lethbridge_phenotype_file_path)
    vegreville_phenotype = pd.read_table(vegreville_phenotype_file_path)

    print("Concatentating...")
    methylation_output_df = pd.concat(
        [
            lethbridge_methylation.iloc[:, 0:2],
            vegreville_methylation.iloc[:, 2:] - \
                lethbridge_methylation.iloc[:, 2:]
        ], axis = 1
    )
    phenotype_output_df = vegreville_phenotype - lethbridge_phenotype

    print("Writing...")
    methylation_output_df.to_csv(
        "delta_methylation_v_minus_l.tsv", output_dir_path, sep = '\t',
        index = False
    )
    phenotype_output_df.to_csv(
        "delta_phenotype_v_minus_l.tsv", output_dir_path, sep = '\t')

    print("Done!")
    print_program_runtime("Delta methylation and phenotype", start_time)
