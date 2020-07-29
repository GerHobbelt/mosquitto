import argparse
import numpy as np
import time, random, string, signal, sys
from multiprocessing import Process, Value, Lock
from camera import *

def time_ms():
    return time.time()*1000

def rand_color():
    r = lambda: random.randint(0,255)
    return "#%02X%02X%02X" % (r(),r(),r())

# root mean squared deviation
def rmsd(arr):
    avg = np.mean(arr)
    diffs_sq = np.square(np.array(arr) - avg)
    rmsd = np.mean(diffs_sq)
    return rmsd

class GracefulKiller:
    def __init__(self):
        self.kill_now = Value('i', 0)
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        self.kill_now.value = 1

class Benchmark(object):
    def __init__(self, name, num_cams, timeout, broker, port, scene):
        self.name = name
        self.num_cams = num_cams
        self.broker = broker
        self.port = port
        self.scene = scene
        self.tot_lat = Value('d', 0.0)
        self.cnt = Value('i', 0)
        self.avg_lats = []
        self.times = []
        self.cams = []
        self.killer = GracefulKiller()
        self.timeout = timeout

    def start(self):
        ps = [Process(target=self.move_cam, args=()) for _ in range(self.num_cams)]

        for p in ps:
            p.start()

        print(f"Started! Scene is {self.scene}")
        self.collect()

        for p in ps:
            p.join()

    def collect(self):
        iters = 0
        start_t = time_ms()
        while True:
            now = time_ms()
            if int(now - start_t) % 100 == 0: # 10 Hz
                if self.cnt.value != 0:
                    self.avg_lats += [self.tot_lat.value / self.cnt.value]
                    self.times += [int(now - start_t) / 1000]

            if iters % 5000 == 0:
                sys.stdout.write(".")
                sys.stdout.flush()

            if int(now - start_t) > self.timeout:
                self.killer.kill_now.value = 1
                print("Timeout reached, exiting...")
                break

            # if len(self.avg_lats) > 100 and rmsd(self.avg_lats[-100:]) < 0.00005:
            #     self.killer.kill_now.value = 1
            #     print("RMSD threshold crossed, exiting...")
            #     break

            if self.killer.kill_now.value:
                if input("Terminate [y/n]? ") == "y":
                    break
                self.killer.kill_now.value = 0

            iters += 1
            time.sleep(0.001)

    def get_avg_lats(self):
        return self.avg_lats[-100:]

    def save(self):
        np.save(f"data/time_vs_lat_{self.name}", np.array([self.times, self.avg_lats]))

    def create_cam(self):
        cam = Camera(f"cam{rand_num(5)}", self.scene, rand_color())
        cam.connect(self.broker, self.port)
        return cam

    def move_cam(self):
        cam = self.create_cam()

        start_t = time_ms()
        while True:
            now = time_ms()
            if int(now - start_t) % 100 == 0: # 10 Hz
                cam.move()
                if cam.lat > 0:
                    self.tot_lat.value += cam.lat
                    self.cnt.value += 1

            if self.killer.kill_now.value:
                break
            time.sleep(0.001)

        cam.disconnect()

def main(num_cams, timeout, broker, port, identifier):
    s = lambda: "benchmark_"+rand_str(4)
    test = Benchmark(identifier, num_cams, timeout*60000, broker, port, s())
    test.start()
    test.save()
    print(np.mean(test.get_avg_lats()), "ms")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=("ARENA MQTT broker benchmarking"))

    parser.add_argument("-c", "--num_cams", type=int, help="Number of clients to spawn",
                        default=1)
    parser.add_argument("-b", "--broker", type=str, help="Broker to connect to",
                        default="oz.andrew.cmu.edu")
    parser.add_argument("-p", "--port", type=int, help="Port to connect to",
                        default=9001)
    parser.add_argument("-i", "--identifier", type=str, help="Optional id for saved plot",
                        default="")
    parser.add_argument("-t", "--timeout", type=int, help="Amount of mins to wait before ending data collection",
                        default=5) # default is 5 mins

    args = parser.parse_args()

    main(**vars(args))