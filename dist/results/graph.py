import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import glob
import sys
import os

def main():
    nfile = 1
    if len(sys.argv) != 3:
        RuntimeError("specify file num")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    results = sorted(glob.glob(current_dir + "/result_*.txt"))
    print(results)
    target = results.index(sys.argv[1])
    n = int(sys.argv[2])
    results = results[target: target + n]
    res_dict = {'proto': [], 'loss': [], 'bufratio': [], 'average ssim': [], 'delay': [], 'algor': []}
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
    g = sns.FacetGrid(result_df, col="delay")
    g.map(sns.catplot, x="delay", y="ssim", hue="algor", kind="bar", data=result_df)
    # sns_plot = 
    plt.savefig("out.png")
    

if __name__ == "__main__":
    main()
