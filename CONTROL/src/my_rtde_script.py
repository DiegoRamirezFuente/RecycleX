import rtde_control
rtde_c = rtde_control.RTDEControlInterface("169.254.12.28")

velocity = 0.5
acceleration = 0.5
blend_1 = 0.0
blend_2 = 0.02
blend_3 = 0.0
path_pose1 = [-0.143, -0.435, 0.20, -0.001, 3.12, 0.04, velocity, acceleration, blend_1]
path_pose2 = [-0.143, -0.51, 0.21, -0.001, 3.12, 0.04, velocity, acceleration, blend_2]
path_pose3 = [-0.32, -0.61, 0.31, -0.001, 3.12, 0.04, velocity, acceleration, blend_3]
path = [path_pose1, path_pose2, path_pose3]

# Send a linear path with blending in between - (currently uses separate script)
rtde_c.moveL(path)
rtde_c.stopScript()

#rtde_c.moveL([1.6328052282333374, -1.609624525109762, 0.09630042711366826, -1.6356679401793421, -0.0695274511920374, 1.146], 0.1, 0.1)
#rtde_c.moveL([0.8419468311620646, -1.0281734623498595, 0.013788101090755204, -0.5665338751973594, -1.5671311353657087, 1.2356931104119853], 0.5, 0.3)


#import rtde_receive
#rtde_r = rtde_receive.RTDEReceiveInterface("169.254.12.28")
#actual_q = rtde_r.getActualQ()
#print(actual_q)