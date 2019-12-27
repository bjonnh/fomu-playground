from migen import log2_int


def get_sdram_phy_init_sequence(phy_settings, timing_settings):
    # init sequence
    cmds = {
        "PRECHARGE_ALL": "DFII_COMMAND_RAS|DFII_COMMAND_WE|DFII_COMMAND_CS",
        "MODE_REGISTER": "DFII_COMMAND_RAS|DFII_COMMAND_CAS|DFII_COMMAND_WE|DFII_COMMAND_CS",
        "AUTO_REFRESH":  "DFII_COMMAND_RAS|DFII_COMMAND_CAS|DFII_COMMAND_CS",
        "UNRESET":       "DFII_CONTROL_ODT|DFII_CONTROL_RESET_N",
        "CKE":           "DFII_CONTROL_CKE|DFII_CONTROL_ODT|DFII_CONTROL_RESET_N"
    }

    cl = phy_settings.cl
    mr1 = None

    if phy_settings.memtype == "SDR":
        bl = 1
        mr = log2_int(bl) + (cl << 4)
        reset_dll = 1 << 8

        init_sequence = [
            ("Bring CKE high", 0x0000, 0, cmds["CKE"], 20000),
            ("Precharge All",  0x0400, 0, cmds["PRECHARGE_ALL"], 0),
            ("Load Mode Register / Reset DLL, CL={0:d}, BL={1:d}".format(cl, bl), mr + reset_dll, 0, cmds["MODE_REGISTER"], 200),
            ("Precharge All", 0x0400, 0, cmds["PRECHARGE_ALL"], 0),
            ("Auto Refresh", 0x0, 0, cmds["AUTO_REFRESH"], 4),
            ("Auto Refresh", 0x0, 0, cmds["AUTO_REFRESH"], 4),
            ("Load Mode Register / CL={0:d}, BL={1:d}".format(cl, bl), mr, 0, cmds["MODE_REGISTER"], 200)
        ]

    elif phy_settings.memtype == "DDR":
        bl = 4
        mr  = log2_int(bl) + (cl << 4)
        emr = 0
        reset_dll = 1 << 8

        init_sequence = [
            ("Bring CKE high", 0x0000, 0, cmds["CKE"], 20000),
            ("Precharge All",  0x0400, 0, cmds["PRECHARGE_ALL"], 0),
            ("Load Extended Mode Register", emr, 1, cmds["MODE_REGISTER"], 0),
            ("Load Mode Register / Reset DLL, CL={0:d}, BL={1:d}".format(cl, bl), mr + reset_dll, 0, cmds["MODE_REGISTER"], 200),
            ("Precharge All", 0x0400, 0, cmds["PRECHARGE_ALL"], 0),
            ("Auto Refresh", 0x0, 0, cmds["AUTO_REFRESH"], 4),
            ("Auto Refresh", 0x0, 0, cmds["AUTO_REFRESH"], 4),
            ("Load Mode Register / CL={0:d}, BL={1:d}".format(cl, bl), mr, 0, cmds["MODE_REGISTER"], 200)
        ]

    elif phy_settings.memtype == "LPDDR":
        bl = 4
        mr  = log2_int(bl) + (cl << 4)
        emr = 0
        reset_dll = 1 << 8

        init_sequence = [
            ("Bring CKE high", 0x0000, 0, cmds["CKE"], 20000),
            ("Precharge All",  0x0400, 0, cmds["PRECHARGE_ALL"], 0),
            ("Load Extended Mode Register", emr, 2, cmds["MODE_REGISTER"], 0),
            ("Load Mode Register / Reset DLL, CL={0:d}, BL={1:d}".format(cl, bl), mr + reset_dll, 0, cmds["MODE_REGISTER"], 200),
            ("Precharge All", 0x0400, 0, cmds["PRECHARGE_ALL"], 0),
            ("Auto Refresh", 0x0, 0, cmds["AUTO_REFRESH"], 4),
            ("Auto Refresh", 0x0, 0, cmds["AUTO_REFRESH"], 4),
            ("Load Mode Register / CL={0:d}, BL={1:d}".format(cl, bl), mr, 0, cmds["MODE_REGISTER"], 200)
        ]

    elif phy_settings.memtype == "DDR2":
        bl = 4
        wr = 2
        mr = log2_int(bl) + (cl << 4) + (wr << 9)
        emr = 0
        emr2 = 0
        emr3 = 0
        reset_dll = 1 << 8
        ocd = 7 << 7

        init_sequence = [
            ("Bring CKE high", 0x0000, 0, cmds["CKE"], 20000),
            ("Precharge All",  0x0400, 0, cmds["PRECHARGE_ALL"], 0),
            ("Load Extended Mode Register 3", emr3, 3, cmds["MODE_REGISTER"], 0),
            ("Load Extended Mode Register 2", emr2, 2, cmds["MODE_REGISTER"], 0),
            ("Load Extended Mode Register", emr, 1, cmds["MODE_REGISTER"], 0),
            ("Load Mode Register / Reset DLL, CL={0:d}, BL={1:d}".format(cl, bl), mr + reset_dll, 0, cmds["MODE_REGISTER"], 200),
            ("Precharge All", 0x0400, 0, cmds["PRECHARGE_ALL"], 0),
            ("Auto Refresh", 0x0, 0, cmds["AUTO_REFRESH"], 4),
            ("Auto Refresh", 0x0, 0, cmds["AUTO_REFRESH"], 4),
            ("Load Mode Register / CL={0:d}, BL={1:d}".format(cl, bl), mr, 0, cmds["MODE_REGISTER"], 200),
            ("Load Extended Mode Register / OCD Default", emr+ocd, 1, cmds["MODE_REGISTER"], 0),
            ("Load Extended Mode Register / OCD Exit", emr, 1, cmds["MODE_REGISTER"], 0),
        ]
    elif phy_settings.memtype == "DDR3":
        bl = 8
        cwl = phy_settings.cwl

        def format_mr0(bl, cl, wr, dll_reset):
            bl_to_mr0 = {
                4: 0b10,
                8: 0b00
            }
            cl_to_mr0 = {
                 5: 0b0010,
                 6: 0b0100,
                 7: 0b0110,
                 8: 0b1000,
                 9: 0b1010,
                10: 0b1100,
                11: 0b1110,
                12: 0b0001,
                13: 0b0011,
                14: 0b0101
            }
            wr_to_mr0 = {
                16: 0b000,
                 5: 0b001,
                 6: 0b010,
                 7: 0b011,
                 8: 0b100,
                10: 0b101,
                12: 0b110,
                14: 0b111
            }
            mr0 = bl_to_mr0[bl]
            mr0 |= (cl_to_mr0[cl] & 1) << 2
            mr0 |= ((cl_to_mr0[cl] >> 1) & 0b111) << 4
            mr0 |= dll_reset << 8
            mr0 |= wr_to_mr0[wr] << 9
            return mr0

        def format_mr1(ron, rtt_nom):
            mr1 = ((ron >> 0) & 1) << 1
            mr1 |= ((ron >> 1) & 1) << 5
            mr1 |= ((rtt_nom >> 0) & 1) << 2
            mr1 |= ((rtt_nom >> 1) & 1) << 6
            mr1 |= ((rtt_nom >> 2) & 1) << 9
            return mr1

        def format_mr2(cwl, rtt_wr):
            mr2 = (cwl-5) << 3
            mr2 |= rtt_wr << 9
            return mr2

        z_to_rtt_nom = {
            "disabled" : 0,
            "60ohm"    : 1,
            "120ohm"   : 2,
            "40ohm"    : 3,
            "20ohm"    : 4,
            "30ohm"    : 5
        }

        z_to_rtt_wr = {
            "disabled" : 0,
            "60ohm"    : 1,
            "120ohm"   : 2,
        }

        z_to_ron = {
            "40ohm" : 0,
            "34ohm" : 1,
        }

        # default electrical settings (point to point)
        rtt_nom = "60ohm"
        rtt_wr = "60ohm"
        ron = "34ohm"

        # override electrical settings if specified
        if hasattr(phy_settings, "rtt_nom"):
            rtt_nom = phy_settings.rtt_nom
        if hasattr(phy_settings, "rtt_wr"):
            rtt_wr = phy_settings.rtt_wr
        if hasattr(phy_settings, "ron"):
            ron = phy_settings.ron

        wr = max(timing_settings.tWTR*phy_settings.nphases, 5) # >= ceiling(tWR/tCK)
        mr0 = format_mr0(bl, cl, wr, 1)
        mr1 = format_mr1(z_to_ron[ron], z_to_rtt_nom[rtt_nom])
        mr2 = format_mr2(cwl, z_to_rtt_wr[rtt_wr])
        mr3 = 0

        init_sequence = [
            ("Release reset", 0x0000, 0, cmds["UNRESET"], 50000),
            ("Bring CKE high", 0x0000, 0, cmds["CKE"], 10000),
            ("Load Mode Register 2, CWL={0:d}".format(cwl), mr2, 2, cmds["MODE_REGISTER"], 0),
            ("Load Mode Register 3", mr3, 3, cmds["MODE_REGISTER"], 0),
            ("Load Mode Register 1", mr1, 1, cmds["MODE_REGISTER"], 0),
            ("Load Mode Register 0, CL={0:d}, BL={1:d}".format(cl, bl), mr0, 0, cmds["MODE_REGISTER"], 200),
            ("ZQ Calibration", 0x0400, 0, "DFII_COMMAND_WE|DFII_COMMAND_CS", 200),
        ]
    elif phy_settings.memtype == "DDR4":
        bl = 8
        cwl = phy_settings.cwl

        def format_mr0(bl, cl, wr, dll_reset):
            bl_to_mr0 = {
                4: 0b10,
                8: 0b00
            }
            cl_to_mr0 = {
                 9: 0b00000,
                10: 0b00001,
                11: 0b00010,
                12: 0b00011,
                13: 0b00100,
                14: 0b00101,
                15: 0b00110,
                16: 0b00111,
                18: 0b01000,
                20: 0b01001,
                22: 0b01010,
                24: 0b01011,
                23: 0b01100,
                17: 0b01101,
                19: 0b01110,
                21: 0b01111,
                25: 0b10000,
                26: 0b10001,
                27: 0b10010,
                28: 0b10011,
                29: 0b10100,
                30: 0b10101,
                31: 0b10110,
                32: 0b10111,
            }
            wr_to_mr0 = {
                10: 0b0000,
                12: 0b0001,
                14: 0b0010,
                16: 0b0011,
                18: 0b0100,
                20: 0b0101,
                24: 0b0110,
                22: 0b0111,
                26: 0b1000,
                28: 0b1001,
            }
            mr0 = bl_to_mr0[bl]
            mr0 |= (cl_to_mr0[cl] & 0b1) << 2
            mr0 |= ((cl_to_mr0[cl] >> 1) & 0b111) << 4
            mr0 |= ((cl_to_mr0[cl] >> 4) & 0b1) << 12
            mr0 |= dll_reset << 8
            mr0 |= (wr_to_mr0[wr] & 0b111) << 9
            mr0 |= (wr_to_mr0[wr] >> 3) << 13
            return mr0

        def format_mr1(dll_enable, ron, rtt_nom):
            mr1 = dll_enable
            mr1 |= ((ron >> 0) & 0b1) << 1
            mr1 |= ((ron >> 1) & 0b1) << 2
            mr1 |= ((rtt_nom >> 0) & 0b1) << 8
            mr1 |= ((rtt_nom >> 1) & 0b1) << 9
            mr1 |= ((rtt_nom >> 2) & 0b1) << 10
            return mr1

        def format_mr2(cwl, rtt_wr):
            cwl_to_mr2 = {
                 9: 0b000,
                10: 0b001,
                11: 0b010,
                12: 0b011,
                14: 0b100,
                16: 0b101,
                18: 0b110,
                20: 0b111
            }
            mr2 = cwl_to_mr2[cwl] << 3
            mr2 |= rtt_wr << 9
            return mr2

        def format_mr6(tccd):
            tccd_to_mr6 = {
                4: 0b000,
                5: 0b001,
                6: 0b010,
                7: 0b011,
                8: 0b100
            }
            mr6 = tccd_to_mr6[tccd] << 10
            return mr6

        z_to_rtt_nom = {
            "disabled" : 0b000,
            "60ohm"    : 0b001,
            "120ohm"   : 0b010,
            "40ohm"    : 0b011,
            "240ohm"   : 0b100,
            "48ohm"    : 0b101,
            "80ohm"    : 0b110,
            "34ohm"    : 0b111
        }

        z_to_rtt_wr = {
            "disabled" : 0b000,
            "120ohm"   : 0b001,
            "240ohm"   : 0b010,
            "high-z"   : 0b011,
            "80ohm"    : 0b100,
        }

        z_to_ron = {
            "34ohm" : 0b00,
            "48ohm" : 0b01,
        }

         # default electrical settings (point to point)
        rtt_nom = "40ohm"
        rtt_wr = "120ohm"
        ron = "34ohm"

        # override electrical settings if specified
        if hasattr(phy_settings, "rtt_nom"):
            rtt_nom = phy_settings.rtt_nom
        if hasattr(phy_settings, "rtt_wr"):
            rtt_wr = phy_settings.rtt_wr
        if hasattr(phy_settings, "ron"):
            ron = phy_settings.ron

        wr = max(timing_settings.tWTR*phy_settings.nphases, 10) # >= ceiling(tWR/tCK)
        mr0 = format_mr0(bl, cl, wr, 1)
        mr1 = format_mr1(1, z_to_ron[ron], z_to_rtt_nom[rtt_nom])
        mr2 = format_mr2(cwl, z_to_rtt_wr[rtt_wr])
        mr3 = 0
        mr4 = 0
        mr5 = 0
        mr6 = format_mr6(4) # FIXME: tCCD

        init_sequence = [
            ("Release reset", 0x0000, 0, cmds["UNRESET"], 50000),
            ("Bring CKE high", 0x0000, 0, cmds["CKE"], 10000),
            ("Load Mode Register 3", mr3, 3, cmds["MODE_REGISTER"], 0),
            ("Load Mode Register 6", mr6, 6, cmds["MODE_REGISTER"], 0),
            ("Load Mode Register 5", mr5, 5, cmds["MODE_REGISTER"], 0),
            ("Load Mode Register 4", mr4, 4, cmds["MODE_REGISTER"], 0),
            ("Load Mode Register 2, CWL={0:d}".format(cwl), mr2, 2, cmds["MODE_REGISTER"], 0),
            ("Load Mode Register 1", mr1, 1, cmds["MODE_REGISTER"], 0),
            ("Load Mode Register 0, CL={0:d}, BL={1:d}".format(cl, bl), mr0, 0, cmds["MODE_REGISTER"], 200),
            ("ZQ Calibration", 0x0400, 0, "DFII_COMMAND_WE|DFII_COMMAND_CS", 200),
        ]
    else:
        raise NotImplementedError("Unsupported memory type: " + phy_settings.memtype)


    return init_sequence, mr1


def get_sdram_phy_c_header(phy_settings, timing_settings):
    r = "#ifndef __GENERATED_SDRAM_PHY_H\n#define __GENERATED_SDRAM_PHY_H\n"
    r += "#include <hw/common.h>\n#include <generated/csr.h>\n#include <hw/flags.h>\n\n"

    nphases = phy_settings.nphases
    r += "#define DFII_NPHASES "+str(nphases)+"\n\n"

    r += "static void cdelay(int i);\n"

    # commands_px functions
    for n in range(nphases):
        r += """
__attribute__((unused)) static void command_p{n}(int cmd)
{{
    sdram_dfii_pi{n}_command_write(cmd);
    sdram_dfii_pi{n}_command_issue_write(1);
}}""".format(n=str(n))
    r += "\n\n"

    # rd/wr access macros
    r += """
#define sdram_dfii_pird_address_write(X) sdram_dfii_pi{rdphase}_address_write(X)
#define sdram_dfii_piwr_address_write(X) sdram_dfii_pi{wrphase}_address_write(X)
#define sdram_dfii_pird_baddress_write(X) sdram_dfii_pi{rdphase}_baddress_write(X)
#define sdram_dfii_piwr_baddress_write(X) sdram_dfii_pi{wrphase}_baddress_write(X)
#define command_prd(X) command_p{rdphase}(X)
#define command_pwr(X) command_p{wrphase}(X)
""".format(rdphase=str(phy_settings.rdphase), wrphase=str(phy_settings.wrphase))
    r += "\n"

    #
    # sdrrd/sdrwr functions utilities
    #
    r += "#define DFII_PIX_DATA_SIZE CSR_SDRAM_DFII_PI0_WRDATA_SIZE\n"
    sdram_dfii_pix_wrdata_addr = []
    for n in range(nphases):
        sdram_dfii_pix_wrdata_addr.append("CSR_SDRAM_DFII_PI{n}_WRDATA_ADDR".format(n=n))
    r += """
const unsigned long sdram_dfii_pix_wrdata_addr[{n}] = {{
    {sdram_dfii_pix_wrdata_addr}
}};
""".format(n=nphases, sdram_dfii_pix_wrdata_addr=",\n\t".join(sdram_dfii_pix_wrdata_addr))

    sdram_dfii_pix_rddata_addr = []
    for n in range(nphases):
        sdram_dfii_pix_rddata_addr.append("CSR_SDRAM_DFII_PI{n}_RDDATA_ADDR".format(n=n))
    r += """
const unsigned long sdram_dfii_pix_rddata_addr[{n}] = {{
    {sdram_dfii_pix_rddata_addr}
}};
""".format(n=nphases, sdram_dfii_pix_rddata_addr=",\n\t".join(sdram_dfii_pix_rddata_addr))
    r += "\n"

    init_sequence, mr1 = get_sdram_phy_init_sequence(phy_settings, timing_settings)

    if phy_settings.memtype in ["DDR3", "DDR4"]:
        # the value of MR1 needs to be modified during write leveling
        r += "#define DDRX_MR1 {}\n\n".format(mr1)

    r += "static void init_sequence(void)\n{\n"
    for comment, a, ba, cmd, delay in init_sequence:
        r += "\t/* {0} */\n".format(comment)
        r += "\tsdram_dfii_pi0_address_write({0:#x});\n".format(a)
        r += "\tsdram_dfii_pi0_baddress_write({0:d});\n".format(ba)
        if cmd[:12] == "DFII_CONTROL":
            r += "\tsdram_dfii_control_write({0});\n".format(cmd)
        else:
            r += "\tcommand_p0({0});\n".format(cmd)
        if delay:
            r += "\tcdelay({0:d});\n".format(delay)
        r += "\n"
    r += "}\n"

    r += "#endif\n"

    return r

def get_sdram_phy_py_header(phy_settings, timing_settings):
    r = ""
    r += "dfii_control_sel     = 0x01\n"
    r += "dfii_control_cke     = 0x02\n"
    r += "dfii_control_odt     = 0x04\n"
    r += "dfii_control_reset_n = 0x08\n"
    r += "\n"
    r += "dfii_command_cs     = 0x01\n"
    r += "dfii_command_we     = 0x02\n"
    r += "dfii_command_cas    = 0x04\n"
    r += "dfii_command_ras    = 0x08\n"
    r += "dfii_command_wrdata = 0x10\n"
    r += "dfii_command_rddata = 0x20\n"
    r += "\n"

    init_sequence, mr1 = get_sdram_phy_init_sequence(phy_settings, timing_settings)

    if mr1 is not None:
        r += "ddrx_mr1 = 0x{:x}\n".format(mr1)
        r += "\n"

    r += "init_sequence = [\n"
    for comment, a, ba, cmd, delay in init_sequence:
        r += "    "
        r += "(\"" + comment + "\", "
        r += str(a) + ", "
        r += str(ba) + ", "
        r += cmd.lower() + ", "
        r += str(delay) + "),"
        r += "\n"
    r += "]\n"
    return r
