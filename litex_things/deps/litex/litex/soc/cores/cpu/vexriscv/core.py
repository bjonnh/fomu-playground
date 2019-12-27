# This file is Copyright (c) 2018 Dolu1990 <charles.papon.90@gmail.com>
# This file is Copyright (c) 2018-2019 Florent Kermarrec <florent@enjoy-digital.fr>
# This file is Copyright (c) 2018-2019 Sean Cross <sean@xobs.io>
# This file is Copyright (c) 2019 Tim 'mithro' Ansell <me@mith.ro>
# This file is Copyright (c) 2019 David Shah <dave@ds0.me>
# This file is Copyright (c) 2019 Joanna Brozek <jbrozek@antmicro.com>
# This file is Copyright (c) 2019 Kurt Kiefer <kekiefer@gmail.com>
# This file is Copyright (c) 2019 Mateusz Holenko <mholenko@antmicro.com>

# License: BSD

import os

from migen import *

from litex.soc.interconnect import wishbone
from litex.soc.interconnect.csr import *


CPU_VARIANTS = {
    "minimal":          "VexRiscv_Min",
    "minimal+debug":    "VexRiscv_MinDebug",
    "lite":             "VexRiscv_Lite",
    "lite+debug":       "VexRiscv_LiteDebug",
    "standard":         "VexRiscv",
    "standard+debug":   "VexRiscv_Debug",
    "full":             "VexRiscv_Full",
    "full+debug":       "VexRiscv_FullDebug",
    "linux":            "VexRiscv_Linux",
    "linux+debug":      "VexRiscv_LinuxDebug",
    "linux+no-dsp":     "VexRiscv_LinuxNoDspFmax",
}


GCC_FLAGS = {
    #                               /-------- Base ISA
    #                               |/------- Hardware Multiply + Divide
    #                               ||/----- Atomics
    #                               |||/---- Compressed ISA
    #                               ||||/--- Single-Precision Floating-Point
    #                               |||||/-- Double-Precision Floating-Point
    #                               imacfd
    "minimal":          "-march=rv32i      -mabi=ilp32",
    "minimal+debug":    "-march=rv32i      -mabi=ilp32",
    "lite":             "-march=rv32i      -mabi=ilp32",
    "lite+debug":       "-march=rv32i      -mabi=ilp32",
    "standard":         "-march=rv32im     -mabi=ilp32",
    "standard+debug":   "-march=rv32im     -mabi=ilp32",
    "full":             "-march=rv32im     -mabi=ilp32",
    "full+debug":       "-march=rv32im     -mabi=ilp32",
    "linux":            "-march=rv32ima    -mabi=ilp32",
    "linux+debug":      "-march=rv32ima    -mabi=ilp32",
    "linux+no-dsp":     "-march=rv32ima    -mabi=ilp32",
}


class VexRiscvTimer(Module, AutoCSR):
    def __init__(self):
        self._latch = CSR()
        self._time = CSRStatus(64)
        self._time_cmp = CSRStorage(64, reset=2**64-1)
        self.interrupt = Signal()

        # # #

        time = Signal(64)
        self.sync += time.eq(time + 1)
        self.sync += If(self._latch.re, self._time.status.eq(time))

        time_cmp = Signal(64, reset=2**64-1)
        self.sync += If(self._latch.re, time_cmp.eq(self._time_cmp.storage))

        self.comb += self.interrupt.eq(time >= time_cmp)


class VexRiscv(Module, AutoCSR):
    @property
    def name(self):
        return "vexriscv"

    @property
    def endianness(self):
        return "little"

    @property
    def gcc_triple(self):
        return ("riscv64-unknown-elf", "riscv32-unknown-elf", "riscv-none-embed")

    @property
    def gcc_flags(self):
        flags = GCC_FLAGS[self.variant]
        flags += " -D__vexriscv__"
        return flags

    @property
    def linker_output_format(self):
        return "elf32-littleriscv"

    @property
    def reserved_interrupts(self):
        return {}

    def __init__(self, platform, cpu_reset_address, variant="standard"):
        assert variant in CPU_VARIANTS, "Unsupported variant %s" % variant
        self.platform = platform
        self.variant = variant
        self.external_variant = None
        self.reset = Signal()
        self.ibus = ibus = wishbone.Interface()
        self.dbus = dbus = wishbone.Interface()
        self.cpu_reset_address = cpu_reset_address

        self.interrupt = Signal(32)

        self.cpu_params = dict(
                i_clk=ClockSignal(),
                i_reset=ResetSignal() | self.reset,

                i_externalResetVector=self.cpu_reset_address,
                i_externalInterruptArray=self.interrupt,
                i_timerInterrupt=0,
                i_softwareInterrupt=0,

                o_iBusWishbone_ADR=ibus.adr,
                o_iBusWishbone_DAT_MOSI=ibus.dat_w,
                o_iBusWishbone_SEL=ibus.sel,
                o_iBusWishbone_CYC=ibus.cyc,
                o_iBusWishbone_STB=ibus.stb,
                o_iBusWishbone_WE=ibus.we,
                o_iBusWishbone_CTI=ibus.cti,
                o_iBusWishbone_BTE=ibus.bte,
                i_iBusWishbone_DAT_MISO=ibus.dat_r,
                i_iBusWishbone_ACK=ibus.ack,
                i_iBusWishbone_ERR=ibus.err,

                o_dBusWishbone_ADR=dbus.adr,
                o_dBusWishbone_DAT_MOSI=dbus.dat_w,
                o_dBusWishbone_SEL=dbus.sel,
                o_dBusWishbone_CYC=dbus.cyc,
                o_dBusWishbone_STB=dbus.stb,
                o_dBusWishbone_WE=dbus.we,
                o_dBusWishbone_CTI=dbus.cti,
                o_dBusWishbone_BTE=dbus.bte,
                i_dBusWishbone_DAT_MISO=dbus.dat_r,
                i_dBusWishbone_ACK=dbus.ack,
                i_dBusWishbone_ERR=dbus.err)

        if "linux" in variant:
            self.add_timer()

        if "debug" in variant:
            self.add_debug()

    def add_debug(self):
        debug_reset = Signal()

        ibus_err = Signal()
        dbus_err = Signal()

        self.i_cmd_valid = Signal()
        self.i_cmd_payload_wr = Signal()
        self.i_cmd_payload_address = Signal(8)
        self.i_cmd_payload_data = Signal(32)
        self.o_cmd_ready = Signal()
        self.o_rsp_data = Signal(32)
        self.o_resetOut = Signal()

        reset_debug_logic = Signal()

        self.transfer_complete = Signal()
        self.transfer_in_progress = Signal()
        self.transfer_wait_for_ack = Signal()

        self.debug_bus = wishbone.Interface()

        self.sync += [
            self.debug_bus.dat_r.eq(self.o_rsp_data),
            debug_reset.eq(reset_debug_logic | ResetSignal()),
        ]

        self.sync += [
            # CYC is held high for the duration of the transfer.
            # STB is kept high when the transfer finishes (write)
            # or the master is waiting for data (read), and stays
            # there until ACK, ERR, or RTY are asserted.
            If((self.debug_bus.stb & self.debug_bus.cyc)
            & (~self.transfer_in_progress)
            & (~self.transfer_complete)
            & (~self.transfer_wait_for_ack),
                self.i_cmd_payload_data.eq(self.debug_bus.dat_w),
                self.i_cmd_payload_address.eq((self.debug_bus.adr[0:6] << 2) | 0),
                self.i_cmd_payload_wr.eq(self.debug_bus.we),
                self.i_cmd_valid.eq(1),
                self.transfer_in_progress.eq(1),
                self.transfer_complete.eq(0),
                self.debug_bus.ack.eq(0)
            ).Elif(self.transfer_in_progress,
                If(self.o_cmd_ready,
                    self.i_cmd_valid.eq(0),
                    self.i_cmd_payload_wr.eq(0),
                    self.transfer_complete.eq(1),
                    self.transfer_in_progress.eq(0)
                )
            ).Elif(self.transfer_complete,
                self.transfer_complete.eq(0),
                self.debug_bus.ack.eq(1),
                self.transfer_wait_for_ack.eq(1)
            ).Elif(self.transfer_wait_for_ack & ~(self.debug_bus.stb & self.debug_bus.cyc),
                self.transfer_wait_for_ack.eq(0),
                self.debug_bus.ack.eq(0)
            ),
            # Force a Wishbone error if transferring during a reset sequence.
            # Because o_resetOut is multiple cycles and i.stb/d.stb should
            # deassert one cycle after i_err/i_ack/d_err/d_ack are asserted,
            # this will give i_err and o_err enough time to be reset to 0
            # once the reset cycle finishes.
            If(self.o_resetOut,
                If(self.ibus.cyc & self.ibus.stb, ibus_err.eq(1)).Else(ibus_err.eq(0)),
                If(self.dbus.cyc & self.dbus.stb, dbus_err.eq(1)).Else(dbus_err.eq(0)),
                reset_debug_logic.eq(1))
            .Else(
                reset_debug_logic.eq(0)
            )
        ]

        self.cpu_params.update(
            i_reset=ResetSignal() | self.reset | debug_reset,
            i_iBusWishbone_ERR=self.ibus.err | ibus_err,
            i_dBusWishbone_ERR=self.dbus.err | dbus_err,
            i_debugReset=ResetSignal(),
            i_debug_bus_cmd_valid=self.i_cmd_valid,
            i_debug_bus_cmd_payload_wr=self.i_cmd_payload_wr,
            i_debug_bus_cmd_payload_address=self.i_cmd_payload_address,
            i_debug_bus_cmd_payload_data=self.i_cmd_payload_data,
            o_debug_bus_cmd_ready=self.o_cmd_ready,
            o_debug_bus_rsp_data=self.o_rsp_data,
            o_debug_resetOut=self.o_resetOut
        )

    def add_timer(self):
        self.submodules.timer = VexRiscvTimer()
        self.cpu_params.update(i_timerInterrupt=self.timer.interrupt)

    @staticmethod
    def add_sources(platform, variant="standard"):
        cpu_filename = CPU_VARIANTS[variant] + ".v"
        vdir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "verilog")
        platform.add_source(os.path.join(vdir, cpu_filename))

    def use_external_variant(self, variant_filename):
        self.external_variant = True
        self.platform.add_source(variant_filename)

    def do_finalize(self):
        if not self.external_variant:
            self.add_sources(self.platform, self.variant)
        self.specials += Instance("VexRiscv", **self.cpu_params)
