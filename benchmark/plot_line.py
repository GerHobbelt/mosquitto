import numpy as np
import argparse

import matplotlib.pyplot as plt
plt.style.use('seaborn-whitegrid')

def main(filename):
    num_cams = 0
    num_threads = 0
    times = []
    avgs = []

    with open(filename, "r") as f:
        contents = f.readlines()

        info = contents[0].split(",")
        num_cams = int(info[0])
        num_threads = int(info[1])

        times = [float(n) for n in contents[1].split(",")[:-1]]
        avgs = [float(n) for n in contents[2].split(",")[:-1]]

    filename = filename.split(".")[:-1][0].split("/")[-1]

    plt.plot(times, avgs, "--b.")
    plt.title(f"Time vs Response Time - {num_cams} client(s), {num_threads} thread(s)")
    plt.xlabel("Time (s)")
    plt.ylabel("Response Time (ms)")
    plt.savefig(f"plots/{filename}.png")
    # plt.show()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=("ARENA MQTT broker benchmarking"))

    parser.add_argument("-f", "--filename", type=str, help="txt file to",
                        default="")

    args = parser.parse_args()

    main(**vars(args))
