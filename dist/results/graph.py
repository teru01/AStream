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
        RuntimeError("specify <dir> <barkind>")
    # current_dir = os.path.dirname(os.path.abspath(__file__))
    folder = sys.argv[1]
    graphkind = sys.argv[2]
    results = sorted(glob.glob(folder + "/result_*.txt"))
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
    print('rel len: ', len(result_df.query('reliability == "reliable"')))
    print('unrel len: ', len(result_df.query('reliability == "unreliable"')))
    result_df = clip_data(result_df)
    print('reliable len after clip: ', len(result_df.query('reliability == "reliable"')))
    print('unreliable len after clip: ', len(result_df.query('reliability == "unreliable"')))
    sns.factorplot(x='loss', y='bufratio', data=result_df, hue='reliability', col='bw', row='delay', kind=graphkind, ci=68)
    plt.savefig(folder + "_bufratio_{}.png".format(graphkind))
    sns.factorplot(x='loss', y='average ssim', data=result_df, hue='reliability', col='bw', row='delay')
    plt.savefig(folder + "_ssim.png")
    

def clip_data(df):
    rate = 0.95
    reliable = df.query('reliability == "reliable"')
    unreliable = df.query('reliability == "unreliable"')
    reliable = reliable.nlargest(math.ceil(len(reliable) * rate), columns='bufratio')
    reliable = reliable.nsmallest(math.floor(len(reliable) * (1 - (1-rate)/rate)), columns='bufratio')
    unreliable = unreliable.nlargest(math.ceil(len(unreliable) * rate), columns='bufratio')
    unreliable = unreliable.nsmallest(math.floor(len(unreliable) * (1 - (1-rate)/rate)), columns='bufratio')
    return pd.concat([reliable, unreliable])

if __name__ == "__main__":
    main()
