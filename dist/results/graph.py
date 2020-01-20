import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import glob
import sys
import os
from argparse import ArgumentParser
import math

def get_option():
    argparser = ArgumentParser()
    argparser.add_argument('folders', type=str, nargs='+')
    argparser.add_argument('-f', '--outfilename', type=str)
    argparser.add_argument('-g', '--graphkind', type=str, default='bar')
    return argparser.parse_args()

def main():
    args = get_option()
    graphkind = args.graphkind
    folders = args.folders
    results = []
    for f in folders:
        results.extend(sorted(glob.glob(f + "/result_*.txt")))
    print(results)
    res_dict = {'proto': [], 'reliability': [], 'loss': [], 'bufratio': [], 'average ssim': [], 'delay': [], 'algor': [], 'bw': [], 'assim': []}
    # print(results)
    for file in results:
        with open(file) as f:
            for line in f:
                for header in res_dict:
                    if header in line:
                        v = line.split()[-1]
                        try:
                            v = round(float(v), 5)
                        except ValueError:
                            pass
                        res_dict[header].append(v)
    
    result_df = pd.DataFrame.from_dict(res_dict)
    print(result_df)
    result_df = change_protocol(result_df)
    for name, group in result_df.groupby('proto'):
        print(name, len(group))
    result_df = clip_data(result_df)
    for name, group in result_df.groupby('proto'):
        print(name, len(group))

    result_df = cut_loss(result_df, [0, 1, 3, 4, 4.5, 5])

    result_df = result_df.rename(columns={'proto': 'method', 'loss': 'packet loss rate(%)'})
    ax = sns.factorplot(x='packet loss rate(%)', y='bufratio', data=result_df, hue='method', ci=68, kind=graphkind, hue_order=['normal', 'proposed'])
    # handles, labels = ax.get_legend_handles_labels()
    # ax.legend(handles=handles[1:], labels=labels[1:])
    # lg = ax.fig
    # print(lg)
    # lg.texts[1]
    img_name = folders[-1][:-1]
    if args.outfilename != None:
        img_name = args.outfilename
    plt.savefig(img_name + "_bufratio_{}.png".format(graphkind))

    for loss, _ in result_df.groupby('packet loss rate(%)'):
        result_df = result_df.append(pd.DataFrame.from_dict({'reliability': ['reliable'], 'bufratio': [0], 'delay': [None], 'algor': [None], 'bw': [None], 'packet loss rate(%)': [loss], 'average ssim': [0.95283], 'method': ['L0 only']}))
    sns.factorplot(x='packet loss rate(%)', y='average ssim', data=result_df, hue='method')
    plt.savefig(img_name + "_ssim.png")

    # sns.factorplot(x='packet loss rate(%)', y='assim', data=result_df, hue='method')
    # plt.savefig(img_name + "_assim.png")

    
def change_protocol(df):
    df.loc[(df['proto'] == 'h3') & (df['reliability'] == 'reliable'), 'proto'] = 'normal'
    df.loc[(df['proto'] == 'h3') & (df['reliability'] == 'unreliable') & (df['algor'] == 'svc-naive-variableBW'), 'proto'] = 'proposed'
    df.loc[(df['proto'] == 'h3') & (df['reliability'] == 'unreliable') & (df['algor'] == 'svc-naive-variableBW-reliable-layer'), 'proto'] = 'h3 unreliable ver2'
    df.loc[(df['proto'] == 'h2') & (df['reliability'] == 'reliable'), 'proto'] = 'h2 reliable'
    return df

def cut_loss(df, loss_set):
    ret_df = []
    for loss, loss_g in df.groupby('loss'):
        if loss in loss_set:
            ret_df.append(loss_g)
    return pd.concat(ret_df)

def clip_data(df):
    rate = 1.5
    ret_df = []
    for protoname, group in df.groupby('proto'):
        for loss, loss_g in group.groupby('loss'):
            col = loss_g['bufratio']
            q1 = col.describe()['25%']
            q3 = col.describe()['75%']
            iqr = q3 - q1
            outlier_min = q1 - iqr * rate
            outlier_max = q3 + iqr * rate
            col[col < outlier_min] = None
            col[col > outlier_max] = None
            ret_df.append(loss_g)
            # group = group.nlargest(math.ceil(len(group) * rate), columns='bufratio')
            # group = group.nsmallest(math.floor(len(group) * (1 - (1-rate)/rate)), columns='bufratio')
            # ret_df.append(group)

    return pd.concat(ret_df)

if __name__ == "__main__":
    main()
