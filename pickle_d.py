import pickle
import pandas as pd
import matplotlib.pyplot as plt
pad = pickle.load(open('/Users/swiss/projects/myo-raw/swiss_fist_12_emg_accu.p','rb'))
new_emg = []
for sample in pad:
    emg = sample[0]
    new_emg.append(emg)
df_emg = pd.DataFrame(new_emg, columns=range(1,9))
df_emg
print(df_emg)
fig, (ax0, ax1, ax2, ax3, ax4, ax5, ax6, ax7) = plt.subplots(nrows=8)
ax0.plot(df_emg[1])
ax1.plot(df_emg[2])
ax2.plot(df_emg[3])
ax3.plot(df_emg[4])
ax4.plot(df_emg[5])
ax5.plot(df_emg[6])
ax6.plot(df_emg[7])
ax7.plot(df_emg[8])
# ax0.set_ylim(0, 1000)
# ax1.set_ylim(0, 1000)
# ax2.set_ylim(0, 1000)
# ax3.set_ylim(0, 1000)
# ax4.set_ylim(0, 1000)
# ax5.set_ylim(0, 1000)
# ax6.set_ylim(0, 1000)
# ax7.set_ylim(0, 1000)

plt.show()