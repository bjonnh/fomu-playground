#!/usr/bin/env python3
LX_DEPENDENCIES = ["icestorm", "yosys", "nextpnr-ice40"]
#LX_CONFIG = "skip-git" # This can be useful for workshops

import os,os.path,shutil,sys,subprocess
sys.path.insert(0, os.path.dirname(__file__))
import lxbuildenv

# Disable pylint's E1101, which breaks completely on migen
#pylint:disable=E1101

from migen import *
from migen.genlib.resetsync import AsyncResetSynchronizer

from litex.soc.integration import SoCCore
from litex.soc.integration.builder import Builder
from litex.soc.interconnect.csr import AutoCSR, CSRStatus, CSRStorage

from litex_boards.partner.targets.fomu import BaseSoC, add_dfu_suffix

from valentyusb.usbcore import io as usbio
from valentyusb.usbcore.cpu import dummyusb

import argparse

class Touch(Module, AutoCSR):
    def __init__(self, touch_pads, led_pads):
        self.output = CSRStorage(3)
        r = Signal()
        g = Signal()
        b = Signal()

        # We invert the signal from the touchpads so LEDs are OFF when
        # nothing is touched.
        self.sync += [
            r.eq(~touch_pads[3]), 
            b.eq(~touch_pads[2]),
            g.eq(~touch_pads[0])
            ]
        
        self.specials += Instance("SB_RGBA_DRV",
            i_CURREN = 0b1, # This means that there is a reference current given
            i_RGBLEDEN = 0b1, # Enable the module
            i_RGB0PWM = r, # Technically these are PWM inputs, but we use them just as ON/OFF
            i_RGB1PWM = g,
            i_RGB2PWM = b,
            o_RGB0 = led_pads.r,
            o_RGB1 = led_pads.g,
            o_RGB2 = led_pads.b,
            p_CURRENT_MODE = "0b1", # Keep that at 1 or you can burn the LEDs!
            p_RGB0_CURRENT = "0b000001", # Means 2mA
            p_RGB1_CURRENT = "0b000011", # Means 4mA
            p_RGB2_CURRENT = "0b011111", # Means 10mA (max for LEDs)
        )
       
                                  
def main():
    parser = argparse.ArgumentParser(
        description="Build Fomu Main Gateware")
    parser.add_argument(
        "--seed", default=0, help="seed to use in nextpnr"
    )
    parser.add_argument(
        "--placer", default="heap", choices=["sa", "heap"], help="which placer to use in nextpnr"
    )
    parser.add_argument(
        "--board", choices=["evt", "pvt", "hacker"], required=True,
        help="build for a particular hardware board"
    )
    args = parser.parse_args()

    soc = BaseSoC(args.board, pnr_seed=args.seed, pnr_placer=args.placer, usb_bridge=True)

    led_pads = soc.platform.request("rgb_led")
    touch_pads = [soc.platform.request("user_touch_n",0),
                  soc.platform.request("user_touch_n",1),
                  soc.platform.request("user_touch_n",2),
                  soc.platform.request("user_touch_n",3)]
    soc.submodules.touch = Touch(touch_pads, led_pads)

    builder = Builder(soc,
                      output_dir="build", csr_csv="build/csr.csv",
                      compile_software=False)
    vns = builder.build()
    soc.do_exit(vns)
    add_dfu_suffix(os.path.join('build', 'gateware', 'top.bin'))


if __name__ == "__main__":
    main()
