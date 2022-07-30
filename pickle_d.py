import pickle
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

pad = pickle.load(open('examples/data/song_fist_1_emg_rec.p','rb'))
print(pad)
new_emg = []
is_recording = []
ticks = []
for sample in pad:
    new_emg.append(sample[0])
    is_recording.append(sample[1])
    ticks.append(sample[2])


max = -10000000000
min = 10000000000
for emg_8_channel in new_emg:
    for each_channel in emg_8_channel:
        if max < each_channel:
            max = each_channel
        if min > each_channel:
            min = each_channel   
            

ticks = [(tick - ticks[0])/1000 for tick in ticks] #normalize ticks and change milisec into sec
c = [0 if a else 1 for a in is_recording]
df_emg = pd.DataFrame(new_emg, columns=range(1,9))

fig, (ax0, ax1, ax2, ax3, ax4, ax5, ax6, ax7) = plt.subplots(nrows=8)

c = ['green' if a else 'black' for a in is_recording]
subplot_list = [ax0, ax1, ax2, ax3, ax4, ax5, ax6, ax7]
channel = 1
for i in subplot_list:
    lines = [((x0,y0), (x1,y1)) for x0, y0, x1, y1 in zip(ticks[:-1], df_emg[channel][:-1], ticks[1:], df_emg[channel][1:])]
    colored_lines = LineCollection(lines, colors=c, linewidths=(2,))
    i.add_collection(colored_lines)
    i.autoscale_view()
    channel += 1

plt.setp((ax0, ax1, ax2, ax3, ax4, ax5, ax6, ax7), ylim=(min,max))

plt.show()