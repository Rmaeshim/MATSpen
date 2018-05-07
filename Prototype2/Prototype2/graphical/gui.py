import os
import pickle
import asyncio
import numpy as np
from tkinter import *
from atlasbuggy import Node


class TkinterGUI(Node):
    def __init__(self, pickle_file_path):
        super(TkinterGUI, self).__init__()
        self.interval = 1 / 30

        self.root = Tk()
        self.width = 440
        self.height = 800
        self.root.geometry('%sx%s' % (self.width, self.height))
        self.root.protocol("WM_DELETE_WINDOW", self.shutdown_tk)

        self.is_running = True

        self.use_imp = True

        self.kp_slider = Scale(self.root, label="kp", from_=0, to=10.0, resolution=0.01, orient=HORIZONTAL,
                               length=self.width)
        self.ki_slider = Scale(self.root, label="ki", from_=0, to=10.0, resolution=0.01, orient=HORIZONTAL,
                               length=self.width)
        self.kd_slider = Scale(self.root, label="kd", from_=0, to=10.0, resolution=0.01, orient=HORIZONTAL,
                               length=self.width)

        self.imp_enabled = False
        self.feed_forward_enabled = False

        # general buttons
        self.set_pid_button = Button(self.root, text="Set PID", command=self.set_pid)
        self.stop_motor_button = Button(self.root, text="Stop motors", command=self.stop_motors)

        # tremor generator buttons
        self.tremor_set_point_slider = Scale(self.root, label="tremor speed", from_=-6.4, to=6.4, resolution=0.01,
                                             orient=HORIZONTAL, length=self.width)
        self.tremor_set_point_button = Button(self.root, text="Set tremor speed", command=self.set_tremor_motor_speed)

        self.tremor_command_raw_slider = Scale(self.root, label="tremor command", from_=-255, to=255, orient=HORIZONTAL,
                                               length=self.width)
        self.tremor_command_raw_button = Button(self.root, text="Set tremor command",
                                                command=self.tremor_command_raw_speed)

        # pen buttons
        self.pen_set_point_slider = Scale(self.root, label="pen speed", from_=-6.4, to=6.4, resolution=0.01,
                                          orient=HORIZONTAL, length=self.width)
        self.pen_set_point_button = Button(self.root, text="Set pen speed", command=self.set_pen_motor_speed)

        self.pen_command_raw_slider = Scale(self.root, label="pen command", from_=-255, to=255, orient=HORIZONTAL,
                                            length=self.width)
        self.pen_command_raw_button = Button(self.root, text="Set pen command", command=self.pen_command_raw_speed)

        self.chirp_fn_button = Button(self.root, text="Chirp", command=self.send_chirp_fn)
        self.random_fn_button = Button(self.root, text="Random", command=self.send_random_fn)

        # controller parameter
        if self.use_imp:
            self.imp_kp_slider = Scale(self.root, label="IMP Kp", from_=0.01, to=50.0, resolution=0.01,
                                       orient=HORIZONTAL, length=self.width)
            self.enable_imp_button_x = Button(self.root, text="Enable IMP X", command=self.send_imp_x)
            self.enable_imp_button_y = Button(self.root, text="Enable IMP Y", command=self.send_imp_y)
            self.enable_imp_button_z = Button(self.root, text="Enable IMP Z", command=self.send_imp_z)

        else:
            self.feed_forward_kp_slider = Scale(self.root, label="Feed forward Kp", from_=0.01, to=50.0,
                                                resolution=0.01, orient=HORIZONTAL, length=self.width)
            self.enable_feed_forward_button = Button(self.root, text="Enable feed forward",
                                                     command=self.send_feedforward)

        self.kp_slider.pack()
        self.ki_slider.pack()
        self.kd_slider.pack()
        self.set_pid_button.pack()

        self.tremor_set_point_slider.pack()
        self.tremor_set_point_button.pack()
        self.pen_set_point_slider.pack()
        self.pen_set_point_button.pack()

        self.stop_motor_button.pack()

        # self.tremor_command_raw_slider.pack()
        # self.tremor_command_raw_button.pack()
        # self.pen_command_raw_slider.pack()
        # self.pen_command_raw_button.pack()

        # self.chirp_fn_button.pack()
        # self.random_fn_button.pack()

        if self.use_imp:
            self.imp_kp_slider.pack()
            self.enable_imp_button_x.pack()
            self.enable_imp_button_y.pack()
            self.enable_imp_button_z.pack()
        else:
            self.feed_forward_kp_slider.pack()
            self.enable_feed_forward_button.pack()

        self.tb6612_tag = "tb6612"
        self.tb6612_sub = self.define_subscription(
            self.tb6612_tag,
            queue_size=None,
            required_attributes=(
                "set_pid_constants", "command_motor", "command_raw", "command_function", "cancel_commands")
        )
        self.tb6612 = None

        self.bno055_tag = "bno055"
        self.bno055_sub = self.define_subscription(
            self.bno055_tag,
            queue_size=None,
            service="motor",
            required_attributes=(
                "set_pid_constants", "command_motor", "command_raw", "command_function", "cancel_commands")
        )
        self.bno055 = None

        self.pickle_file_path = pickle_file_path
        self.kp = 1.0
        self.ki = 0.0
        self.kd = 0.0

        self.load_constants()

    def take(self):
        self.tb6612 = self.tb6612_sub.get_producer()
        self.bno055 = self.bno055_sub.get_producer()

    def load_constants(self):
        if os.path.isfile(self.pickle_file_path):
            self.kp, self.ki, self.kd = pickle.load(open(self.pickle_file_path, "rb"))

            self.kp_slider.set(self.kp)
            self.ki_slider.set(self.ki)
            self.kd_slider.set(self.kd)

            print("loaded constants:", self.kp, self.ki, self.kd)

    def save_constants(self):
        pickle.dump((self.kp, self.ki, self.kd), open(self.pickle_file_path, "wb"))

        print("saving constants:", self.kp, self.ki, self.kd)

    async def loop(self):
        self.tb6612.set_pid_constants(
            self.kp,
            self.ki,
            self.kd,
        )
        self.bno055.set_pid_constants(
            self.kp,
            self.ki,
            self.kd,
        )

        try:
            while self.is_running:
                self.root.update()

                await asyncio.sleep(self.interval)
        except TclError as e:
            if "application has been destroyed" not in e.args[0]:
                raise

    async def teardown(self):
        self.save_constants()

    def set_pid(self):
        self.tb6612.cancel_commands()
        self.kp = self.kp_slider.get()
        self.ki = self.ki_slider.get()
        self.kd = self.kd_slider.get()

        self.tb6612.set_pid_constants(
            self.kp,
            self.ki,
            self.kd,
        )

        self.bno055.set_pid_constants(
            self.kp,
            self.ki,
            self.kd,
        )

    def stop_motors(self):
        self.tb6612.cancel_commands()
        self.tb6612.command_motor(0)

        self.bno055.cancel_commands()
        self.bno055.command_motor(0)

    def set_tremor_motor_speed(self):
        print("setting tremor motor from slider")
        self.tb6612.command_motor(self.tremor_set_point_slider.get())

    def set_pen_motor_speed(self):
        print("setting pen motor from slider")
        self.bno055.command_motor(self.pen_set_point_slider.get())

    def tremor_command_raw_speed(self):
        self.tb6612.cancel_commands()
        motor_command = self.tremor_command_raw_slider.get()
        print("sent '%s' to tremor motor" % motor_command)
        self.tb6612.command_raw(motor_command)

    def pen_command_raw_speed(self):
        self.bno055.cancel_commands()
        motor_command = self.pen_command_raw_slider.get()
        print("sent '%s' to pen motor" % motor_command)
        self.bno055.command_raw(motor_command)

    def send_chirp_fn(self):
        # t = np.linspace(0, 10.0, 501).tolist()
        t = 10.0
        amp = []
        for _ in range(3):
            amp += np.linspace(3.0, 6.4, 500).tolist()
        amp += [0.0]

        self.tb6612.command_function(t, amp)

    def send_random_fn(self):
        # t = np.linspace(0, 10.0, 501).tolist()
        t = 60.0
        lower_bound = 3.0
        upper_bound = 6.4
        amp = (np.random.random(60) * (upper_bound - lower_bound) + lower_bound).tolist()
        amp += [0.0]

        self.tb6612.command_function(t, amp)

    def send_imp_x(self):
        kp = self.imp_kp_slider.get()
        self.bno055.cancel_commands()

        if self.imp_enabled:
            self.bno055.command_disable_controllers()
            self.enable_imp_button_x["text"] = "Enable IMP X"
        else:
            self.bno055.command_enable_imp("x", kp)
            self.enable_imp_button_x["text"] = "Disable IMP"
        self.imp_enabled = not self.imp_enabled

    def send_imp_y(self):
        kp = self.imp_kp_slider.get()
        self.bno055.cancel_commands()

        if self.imp_enabled:
            self.bno055.command_disable_controllers()
            self.enable_imp_button_y["text"] = "Enable IMP Y"
        else:
            self.bno055.command_enable_imp("y", kp)
            self.enable_imp_button_y["text"] = "Disable IMP"
        self.imp_enabled = not self.imp_enabled

    def send_imp_z(self):
        kp = self.imp_kp_slider.get()
        self.bno055.cancel_commands()

        if self.imp_enabled:
            self.bno055.command_disable_controllers()
            self.enable_imp_button_z["text"] = "Enable IMP Z"
        else:
            self.bno055.command_enable_imp("z", kp)
            self.enable_imp_button_z["text"] = "Disable IMP"
        self.imp_enabled = not self.imp_enabled

    def send_feedforward(self):
        kp = self.feed_forward_kp_slider.get()
        self.bno055.cancel_commands()

        if self.feed_forward_enabled:
            self.bno055.command_disable_controllers()
            self.enable_feed_forward_button["text"] = "Enable feed forward"
        else:
            self.bno055.command_enable_feedforward("y", kp)
            self.enable_feed_forward_button["text"] = "Disable feed forward"
        self.feed_forward_enabled = not self.feed_forward_enabled

    def shutdown_tk(self):
        self.is_running = False
