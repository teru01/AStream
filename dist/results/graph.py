import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import glob
import sys
import os
from argparse import ArgumentParser

# def get_option():
#     argparser = ArgumentParser()
#     argparser.add_argument('-b', '--begin', type=str)
#     argparser.add_argument('-e', '--end', type=str)
#     return argparser.parse_args()

def main():
    if len(sys.argv) != 2:
        RuntimeError("specify <dir>")
    # current_dir = os.path.dirname(os.path.abspath(__file__))
    folder = sys.argv[1]
    results = sorted(glob.glob(folder + "/result_*.txt"))
    print(results)
    res_dict = {'proto': [], 'reliability': [], 'loss': [], 'bufratio': [], 'average ssim': [], 'delay': [], 'algor': []}
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
    sns.factorplot(x='loss', y='bufratio', data=result_df, hue='reliability', col='delay', kind='box')
    plt.savefig(folder + "_bufratio.png")
    sns.factorplot(x='loss', y='average ssim', data=result_df, hue='reliability', col='delay')
    plt.savefig(folder + "_ssim.png")
    

if __name__ == "__main__":
    main()
