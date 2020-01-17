import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import glob
import sys
import os
from argparse import ArgumentParser
import math

# def get_option():
#     argparser = ArgumentParser()
#     argparser.add_argument('-b', '--begin', type=str)
#     argparser.add_argument('-e', '--end', type=str)
#     return argparser.parse_args()

def main():
    if len(sys.argv) != 3:
        RuntimeError("specify <barkind> <dir...>")
    # current_dir = os.path.dirname(os.path.abspath(__file__))
    folders = sys.argv[2:]
    graphkind = sys.argv[1]
    results = []
    for f in folders:
        results.extend(sorted(glob.glob(f + "/result_*.txt")))
    print(results)
    res_dict = {'proto': [], 'reliability': [], 'loss': [], 'bufratio': [], 'average ssim': [], 'delay': [], 'algor': [], 'bw': []}
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
    sns.factorplot(x='loss', y='bufratio', data=result_df, hue='proto', col='bw', row='delay', ci=68, kind=graphkind, hue_order=['h2 reliable', 'h3 reliable', 'h3 unreliable ver1', 'h3 unreliable ver2'])
    plt.savefig(folders[-1][:-1] + "_bufratio_{}.png".format(graphkind))

    for loss, _ in result_df.groupby('loss'):
        result_df = result_df.append(pd.DataFrame.from_dict({'reliability': ['reliable'], 'bufratio': [0], 'delay': [None], 'algor': [None], 'bw': [None], 'loss': [loss], 'average ssim': [0.95283], 'proto': ['L0 only']}))
    sns.factorplot(x='loss', y='average ssim', data=result_df, hue='proto')
    plt.savefig(folders[-1][:-1] + "_ssim.png")
    
def change_protocol(df):
    df.loc[(df['proto'] == 'h3') & (df['reliability'] == 'reliable'), 'proto'] = 'h3 reliable'
    df.loc[(df['proto'] == 'h3') & (df['reliability'] == 'unreliable'), 'proto'] = 'h3 unreliable ver1'
    # df.loc[(df['proto'] == 'h3') & (df['reliability'] == 'unreliable'), 'proto'] = 'h3 unreliable ver2'
    df.loc[(df['proto'] == 'h2') & (df['reliability'] == 'reliable'), 'proto'] = 'h2 reliable'
    return df


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
