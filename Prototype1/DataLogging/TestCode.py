
from mpl_toolkits.mplot3d import axes3d
import matplotlib.pyplot as plt

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

# load some test data for demonstration and plot a wireframe
X, Y, Z = axes3d.get_test_data(0.1)
print X,Y,Z
ax.plot_wireframe(X, Y, Z, rstride=5, cstride=5)
plt.title('Prototype1 Euler Angle Data')
plt.xlabel('EulerX (deg)')
plt.ylabel('EulerY (deg)')
#plt.plot(eulerX, 'r--', label='X', eulerY, 'bs', label='Y',eulerZ, 'g^', label='Z')
#plt.plot(eulerX, 'r--', label='X')
plt.legend(loc='upper left')

# rotate the axes and update
for angle in range(0, 360):
    ax.view_init(30, angle)
    plt.draw()
    plt.pause(.001)
