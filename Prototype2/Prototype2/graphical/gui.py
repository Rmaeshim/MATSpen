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
        self.width = 400
        self.height = 440
        self.root.geometry('%sx%s' % (self.width, self.height))
        self.root.protocol("WM_DELETE_WINDOW", self.shutdown_tk)

        self.is_running = True

        self.kp_slider = Scale(self.root, label="kp", from_=0, to=10.0, resolution=0.01, orient=HORIZONTAL, length=self.width)
        self.ki_slider = Scale(self.root, label="ki", from_=0, to=10.0, resolution=0.01, orient=HORIZONTAL, length=self.width)
        self.kd_slider = Scale(self.root, label="kd", from_=0, to=10.0, resolution=0.01, orient=HORIZONTAL, length=self.width)

        self.kp_slider.pack()
        self.ki_slider.pack()
        self.kd_slider.pack()

        self.set_pid_button = Button(self.root, text="Set PID", command=self.set_pid)
        self.set_pid_button.pack()

        self.set_point_slider = Scale(self.root, label="speed", from_=-6.4, to=6.4, resolution=0.01, orient=HORIZONTAL, length=self.width)
        self.set_point_button = Button(self.root, text="Set speed", command=self.set_motor_speed)
        self.stop_motor_button = Button(self.root, text="Stop motor", command=self.stop_motor)

        self.command_raw_slider = Scale(self.root, label="command", from_=-255, to=255, orient=HORIZONTAL, length=self.width)
        self.command_raw_button = Button(self.root, text="Set command", command=self.command_raw_speed)

        self.chirp_fn_button = Button(self.root, text="Chirp", command=self.send_chirp_fn)

        self.set_point_slider.pack()
        self.set_point_button.pack()
        self.stop_motor_button.pack()

        self.command_raw_button.pack()
        self.command_raw_slider.pack()

        self.chirp_fn_button.pack()

        self.tb6612_tag = "tb6612"
        self.tb6612_sub = self.define_subscription(
            self.tb6612_tag,
            queue_size=None,
            required_attributes=("set_pid_constants", "command_motor", "command_raw", "command_function", "cancel_commands")
        )
        self.tb6612 = None

        self.pickle_file_path = pickle_file_path
        self.kp = 1.0
        self.ki = 0.0
        self.kd = 0.0

        self.load_constants()

    def take(self):
        self.tb6612 = self.tb6612_sub.get_producer()

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

    def stop_motor(self):
        self.tb6612.cancel_commands()
        self.tb6612.command_motor(0)

    def set_motor_speed(self):
        print("setting motor from slider")
        self.tb6612.command_motor(self.set_point_slider.get())

    def command_raw_speed(self):
        self.tb6612.cancel_commands()
        motor_command = self.command_raw_slider.get()
        print("sent:", motor_command)
        self.tb6612.command_raw(motor_command)

    def send_chirp_fn(self):
        # t = np.linspace(0, 10.0, 501).tolist()
        t = 10.0
        amp = []
        for _ in range(3):
            amp += np.linspace(3.0, 6.4, 500).tolist()
        amp += [0.0]

        self.tb6612.command_function(t, amp)

    def shutdown_tk(self):
        self.is_running = False
