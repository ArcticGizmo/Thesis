import csv
import re

__object_name__ = "Achernar"
__file_name__ = "/home/jon/.stellarium/" + __object_name__ + "-path.txt"
#__file_name__ = "CZ-path.txt"
__output__ = "trajectory.csv"

delimiters = 'T| |\n|\r'

if __name__ == "__main__":
    with open(__file_name__) as fin:
        with open(__output__, 'wb') as fout:
            writer = csv.writer(fout, delimiter=',')
            writer.writerow(["Date", "Time", "Az", "Alt"])
            for line in fin:
                mline = re.split(delimiters, line)
                print mline
                writer.writerow(mline)