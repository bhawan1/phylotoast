#!/usr/bin/env python
import argparse
import sys
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.lda import LDA
from phylotoast import util


def merge_dicts(*dict_args):
    """
    Given any number of dicts, shallow copy and merge into a new dict,
    precedence goes to key value pairs in latter dicts.
    """
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result


def plot_LDA(X_lda, y_lda, class_colors, out_fp="", dpi=150, title=""):
    cats = class_colors.keys()
    group_lda = {c: [] for c in cats}

    for i, target_name in zip(range(len(cats)), cats):
        cat_x = X_lda[:,0][y_lda == target_name]
        if X_lda.shape[1] == 1:
          cat_y = np.ones((cat_x.shape[0],1)) + i
        else:
          cat_y = X_lda[:,1][y_lda == target_name]
        group_lda[target_name].append(cat_x)
        group_lda[target_name].append(cat_y)
        plt.scatter(x=cat_x, y=cat_y, label=target_name, 
                    color=class_colors[target_name], alpha=1, s=80)

    if X_lda.shape[1] == 1:
        plt.ylim((0.5, 2.5))
    plt.xlabel('LD1')
    plt.ylabel('LD2')
    plt.legend(loc='best')
    plt.title('LDA')

    # save or display result
    if out_fp:
        plt.savefig(out_fp, facecolor='white',
                    edgecolor='none', dpi=dpi,
                    bbox_inches='tight', pad_inches=0.2)
    else:
        plt.show()

def run_LDA(df):
    # Prep variables for sklearn LDA
    X = df[range(2, df.shape[1])].values     # read all numbers from each row into an array
    y = df['Condition'].values         # read categories for each sample

    # Calculate LDA
    sklearn_lda = LDA(n_components=2)
    X_lda_sklearn = sklearn_lda.fit_transform(X, y)

    # Quality Test - can be ignored
    print len(X_lda_sklearn)
    # print sklearn_lda.predict_proba(X)
    print(sklearn_lda.score(X, y))

    return X_lda_sklearn, y


def handle_program_options():
    parser = argparse.ArgumentParser(description="Create an LDA plot from\
                                     sample-grouped OTU data. It is necessary\
                                     to remove the header cell '#OTU ID'\
                                     before running this program.")
    parser.add_argument('-i', '--biom_tsv', required=True,
                        help="Sample-OTU abundance table in TSV format with the\
                        arcsin sqrt transform already applied. [REQUIRED]")
    parser.add_argument('-m', '--map_fp', required=True,
                        help="Metadata mapping file. [REQUIRED]")
    parser.add_argument('-g', '--group_by', required=True, nargs='+',
                        help="Any mapping categories, such as treatment type, \
                              that will be used to group the data in the \
                              output iTol table. For example, one category \
                              with three types will result in three data \
                              columns in the final output. Two categories with\
                              three types each will result in six data \
                              columns. Default is no categories and all the \
                              data will be treated as a single group.")
    parser.add_argument('-c', '--color_by', required=True,
                        help="A column name in the mapping file containing\
                              hexadecimal (#FF0000) color values that will\
                              be used to color the groups. Each sample ID must\
                              have a color entry.")
    parser.add_argument('--dpi', default=200, type=int,
                        help="Set plot quality in Dots Per Inch (DPI). Larger\
                              DPI will result in larger file size.")
    parser.add_argument('-o', '--out_fp', default="",
                        help="The path and file name to save the plot under.\
                              If specified, the figure will be saved directly\
                              instead of opening a window in which the plot can\
                              be viewed before saving")

    return parser.parse_args()

def main():
    args = handle_program_options()    

    map_header, imap = util.parse_map_file(args.map_fp)

    df = pd.read_csv(args.biom_tsv, sep='\t', index_col=0).T
    # exclude Sample IDs not in the mapping file
    df = df.loc[imap.keys()]

    cat_gather = util.gather_categories(imap, map_header, args.group_by)
    if len(cat_gather) < 2:
      sys.stderr.write("ERROR: Only one category value found. Linear Discriminant Analysis requires at least two categories to compare.")
      return

    color_gather = util.gather_categories(imap, map_header, [args.color_by])
    
    class_map = merge_dicts(*[{sid: cat for sid in cat_gather[cat].sids} for cat in cat_gather])
    class_colors = merge_dicts(*[{class_map[sid]: color for sid in color_gather[color].sids} for color in color_gather])

    df.insert(0, "Condition", [class_map[entry] for entry in df.index])

    X_lda, y_lda = run_LDA(df)

    plot_LDA(X_lda, y_lda, class_colors, out_fp=args.out_fp, dpi=args.dpi)


if __name__ == "__main__":
    main()