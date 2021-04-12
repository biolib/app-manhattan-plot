import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import argparse
import base64

# utility function to parse csv
def format_data(buffer, sep ='\t', chromosome ='chr', p_value ='p_wald'):
    data = pd.read_table(buffer, sep = sep)
    data['-log10(p_value)'] = -np.log10(data[p_value])
    data[chromosome] = data[chromosome].astype('category')
    data['ind'] = range(len(data))
    data_grouped = data.groupby((chromosome))
    return data, data_grouped

# utility function to generate plot
def generate_manhattan(pyhattan_object, significance = 0.05, colors = ['#40AEA0', '#0B405C'], ref_snp = False, significant_genes=[]):
    data = pyhattan_object[0]
    data_grouped = pyhattan_object[1]
    fig = plt.figure()
    ax = fig.add_subplot(111)
    significance_log = -np.log10(significance)

    x_labels = []
    x_labels_pos = []
    for num, (name, group) in enumerate(data_grouped):
        group.plot(kind='scatter', x='ind', y='-log10(p_value)', color=colors[num % len(colors)], ax=ax, s= 10000/len(data))
        x_labels.append(name)
        x_labels_pos.append((group['ind'].iloc[-1] - (group['ind'].iloc[-1] - group['ind'].iloc[0]) / 2))

    ax.set_xticks(x_labels_pos)
    ax.set_xticklabels(x_labels)
    ax.set_xlim([0, len(data)])
    ax.set_ylim([0, data['-log10(p_value)'].max() + 1])
    ax.set_xlabel('Chromosome')
    plt.axhline(y=significance_log, color='gray', linestyle='-', linewidth = 0.5)
    plt.xticks(fontsize=8, rotation=60)
    plt.yticks(fontsize=8)

    if ref_snp:
        for index, row in data.iterrows():
            if row['-log10(p_value)'] >= significance_log:
                ax.annotate(str(row[ref_snp]), xy = (index, row['-log10(p_value)']))
                significant_genes.append(str(row[ref_snp]))

    plt.savefig("plot.png")

# Input parameters
parser = argparse.ArgumentParser()
parser.add_argument('--in', help = 'Input file', dest = 'file')
parser.add_argument('--sig', help = 'Significance', dest='significance')
args = parser.parse_args()

# define some variables
title = 'Title'
description = 'RefSNPs with p-value < '+args.significance+' translate to strong associated loci.'
ncbi_url = "https://www.ncbi.nlm.nih.gov/snp/?term="
# datetime object containing current date and time.
now = datetime. now()
date = now.strftime("%d/%m/%Y %H:%M:%S")

# load input data
data = format_data(args.file, sep=',', chromosome='chromosome', p_value='p_value')

# generate plot
significant_genes = []
generate_manhattan(data, significance=float(args.significance), ref_snp='refSNP', significant_genes=significant_genes)

# Produce Markdown
file_data = open("plot.png", "rb").read()
md_data = base64.b64encode(file_data).decode('ascii')
markdown_of_plot = '![picture](data:{};base64,{})'.format('image/png', md_data)

# generate info message
if len(significant_genes) == 0:
    result_text= f'WARNING: No SNPs had any significant p values < {args.significance} !'

# generate list of significant IDs
significant_IDs = f"\n".join(f"ID\t{i}\t NCBI SNP entry: {ncbi_url}{i}" for i in significant_genes)

# generate final markdown report
report = f"```\nGWA STUDY\nDATE\t{date}\nDS\t{description}\n\n{significant_IDs}\n\\\ \n```\n{markdown_of_plot}"

# print and return the report (last line is returned)
print(report)

