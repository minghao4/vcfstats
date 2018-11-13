#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Methods for calculating DNAm sequence divergence (Pi)

The original formula for nucleotide diversity can be found here:
https://en.wikipedia.org/wiki/Nucleotide_diversity

This tool implements a slightly different formula. As we are working with
methylation sites, we are looking at the number of sites deviating from
normal methylation status per methylation site (within a pre-defined bin size).

The input parameters required are as follows:
* Bin size
* Sorted variation frequency TSV as per the output from the VCF Parser.
    - Scaffold_Position
    - Variation_Frequency

* Sorted scaffold sizes file.
* Output directory path.
"""

from .__init__ import timeit, Tuple, df, math, np, pd
from . import helpers

# import sys


# TODO: move this to user interface.
start_time = timeit.default_timer()
# bin_width = int(sys.argv[1])
# alleles = int(sys.argv[2])
# variation_file_path = sys.argv[3]
# scaffold_sizes_file_path = sys.argv[4]
# output_dir_path = sys.argv[5]
output_df_header = ("#Distance", "Pi")


class PiCalculator:
    def __init__(self):
        self.bin_size = 0
        self.alleles = 0
        self.variation_df = None
        self.scaffold_sizes_df = None
        self.current_output_df = None


    # Sets input dataframes.
    def __set_input_dfs(
            self, bin_width: int, alleles: int, variation_file_path: str,
            scaffold_sizes_file_path: str
        ) -> None:
        """
        Sets bin width and cultivars/alleles; reads input files and sets as
        pandas dataframes.
        """
        self.bin_size = bin_width
        self.alleles = alleles

        # Only read scaffold_position and variation frequency information from
        # variation file.
        self.variation_df = pd.read_table(
            variation_file_path,
            usecols = ["#Scaffold_Position", "Variation_Frequency"]
        )

        # Split scaffold and position into separate columns.
        scaffold_position = self.variation_df.columns[0]
        self.variation_df[["Scaffold", "Position"]] = \
            self.variation_df[scaffold_position].str.split('_', expand = True)
        self.variation_df["Position"] = \
            pd.to_numeric(self.variation_df["Position"])

        # Reordering the columns.
        self.variation_df = self.variation_df.drop(scaffold_position, axis = 1)
        cols = self.variation_df.columns.tolist()
        cols = cols[1:] + [cols[0]]
        self.variation_df = self.variation_df[cols]

        # Read scaffold sizes file.
        self.scaffold_sizes_df = pd.read_table(scaffold_sizes_file_path)


    # Final part of the pi calculation.
    def __final_pi_calculation(self, sites: int) -> None:
        """
        Divides the pi value by the number of sites.
        """
        divide = sites
        if sites == 0:
            divide = 1

        # divide = self.bin_size
        self.current_output_df.iloc[:, 1] = \
            self.current_output_df.iloc[:, 1] * 2 / divide


    # Final part of pi calculation and writing to output.
    def __final_calculation_and_write(
            self, scaffold_name: str, sites: int, output_dir_path: str
        ) -> None:
        """
        Combined final pi calculation and output writing.
        """
        print()
        print("Final pi calculations...")
        self.__final_pi_calculation(sites)
        output_file_name = helpers.string_builder((
            scaffold_name, "_pi_dnam.tsv" # "_pi_dna.tsv"
        ))

        helpers.write_output(
            self.current_output_df, output_file_name, output_dir_path
        )


    # Loops through list of variants, calculates pi, and accumulates number of
    # sites. Writes the output for a scaffold upon hitting a variant on a
    # different scaffold. Returns a bookmark index and the final number of
    # methylation sites on this scaffold.
    def __read_variation_df(
            self, variation_df_bookmark: int, current_scaffold: str,
            num_bins: int, output_dir_path: str
        ) -> Tuple[int, bool]:
        """
        Processes the variation dataframe.
        """
        sites = 0
        for idx in range(variation_df_bookmark, self.variation_df.shape[0]):
            variant = self.variation_df.loc[idx]
            variant_scaffold = variant[0]
            variant_position = variant[1]
            variant_frequency = variant[2]

            if variant_scaffold == current_scaffold:
                sites += 1
                variation_df_bookmark += 1
                bin_idx = int(variant_position / self.bin_size)

                if bin_idx < num_bins:
                    pi_part = float(
                        variant_frequency * (1 - variant_frequency) * \
                            self.alleles / (self.alleles - 1)
                    )
                    self.current_output_df.iloc[bin_idx, 1] += pi_part

            else:
                self.__final_calculation_and_write(
                    current_scaffold, sites, output_dir_path
                )
                break

        return (variation_df_bookmark, sites)


    # Sets the output pi matrix.
    def __set_pi_matrix(
            self, num_bins: int, header: Tuple[str], final_bin_label: float
        ) -> None:
        """
        Defines and returns the output pandas dataframe for a scaffold.
        """
        self.current_output_df = \
            ((np.arange(num_bins * 2).reshape(num_bins, 2) + 1) * \
            (self.bin_size / 2)).astype(float)

        self.current_output_df[:, 1] *= 0
        self.current_output_df = df(self.current_output_df, columns = header)

        num_rows = self.current_output_df.shape[0]
        if num_rows > 1 and final_bin_label != 0:
            self.current_output_df.loc[num_rows - 1][0] = final_bin_label


    # Loops through list of scaffolds, sets bins, calculates pi, and
    # accumulates number of sites. Writes the output for a scaffold upon
    # hitting a variant on a different scaffold. Returns a bookmark index and the
    # final number of methylation sites on this scaffold.
    def __read_scaffold_df(
            self, output_df_header: Tuple[str], output_dir_path: str
        ) -> None:
        """
        Processes the scaffold list dataframe.
        """
        variation_df_bookmark = 0
        for idx in range(self.scaffold_sizes_df.shape[0]):
            scaffold = self.scaffold_sizes_df.iloc[idx]
            scaffold_name = scaffold[0]
            print(
                helpers.string_builder((
                    '\n', "Currently reading: ", scaffold_name
                ))
            )

            scaffold_size = int(scaffold[1])
            num_bins = math.ceil(scaffold_size / self.bin_size)
            final_bin_label = int((scaffold_size % self.bin_size) / 2)
            if final_bin_label != 0:
                final_bin_label += self.bin_size * (num_bins - 1)
            elif scaffold_size % self.bin_size == 1:
                final_bin_label == scaffold_size

            self.__set_pi_matrix(num_bins, output_df_header, final_bin_label)
            variation_df_bookmark_and_sites = self.__read_variation_df(
                variation_df_bookmark, scaffold_name, num_bins, output_dir_path
            )

            variation_df_bookmark = variation_df_bookmark_and_sites[0]
            sites = variation_df_bookmark_and_sites[1]
            if variation_df_bookmark == self.variation_df.shape[0]:
                self.__final_calculation_and_write(
                    scaffold_name, sites, output_dir_path
                )


    # Main method.
    def calculate_pi_all_scaffolds(
            self, bin_width: int, alleles: int, variation_file_path: str,
            scaffold_sizes_file_path: str, output_df_header: Tuple[str],
            output_dir_path: str,
        ) -> None:
        """
        Main method.
        """
        print(helpers.string_builder(('\n', "Start.")))
        helpers.remove_trailing_slash([
            variation_file_path, scaffold_sizes_file_path, output_dir_path
        ])

        print(helpers.string_builder(('\n', "Setting variant dataframe...")))
        self.__set_input_dfs(
            bin_width, alleles, variation_file_path, scaffold_sizes_file_path
        )

        print(helpers.string_builder(('\n', "Reading scaffold dataframe...")))
        self.__read_scaffold_df(output_df_header, output_dir_path)

        # Runtime.
        # TODO: move this to user interface as well.
        helpers.print_program_runtime(
            "Sequence divergence (pi) calculations", start_time
        )


# pc = PiCalculator()
# pc.calculate_pi_all_scaffolds(
#     bin_width, alleles, variation_file_path, scaffold_sizes_file_path,
#     output_df_header, output_dir_path
# )