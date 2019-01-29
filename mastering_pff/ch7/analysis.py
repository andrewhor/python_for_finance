import matplotlib.pyplot as plt  

with open('/home/cloudera/stock/part-00000', 'rb') as f:
    x, y = [], []
    for line in f.readlines():
      data = line.split() 		
      x.append(float(data[0].strip('%'))) 		
      y.append(float(data[1]))

    print("Max:", max(x))
    print("Min:", min(x))
    plt.bar(x, y, width=0.1)
    plt.show()