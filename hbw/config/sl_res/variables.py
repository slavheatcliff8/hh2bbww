# coding: utf-8

"""
Definition of variables.
"""

import order as od

from columnflow.util import maybe_import

np = maybe_import("numpy")
ak = maybe_import("awkward")

from columnflow.columnar_util import EMPTY_FLOAT  # noqa


    #object of resonans 2Higgs analysis 
#
#                           _    b 
#                    Higgs_bb  /
#                  - - - - - - 
#                /             \ _
#               /                b 
#  Heavy_Higgs /                          l
# - - - - - - -                 Wlepton  /
#              \                ---------
#               \              /         \ 
#                \  Higgs_WW  /           nu
#                  - - - - - -            
#                             \              q
#                              \  Whadron   /
#                               ------------
#                                           \ 
#                                            q'
#           

def add_sl_res_variables(config: od.Config) -> None:

    #Whadron 
    config.add_variable(
        name="pt_Whadron",
        binning=(40, 0., 1500.),
        unit="GeV",
        x_title=r"$pt_{qq'}$",
    )
    config.add_variable(
        name="m_Whadron",
        binning=(40, 0., 1500.),
        unit="GeV",
        x_title=r"$m_{qq'}$",
    )
    config.add_variable(
        name="eta_Whadron",
        binning=(50, -2.5, 2.5),
        x_title=r"$eta_{qq'}$",
    )
    config.add_variable(
        name="phi_Whadron",
        binning=(40, -3.2, 3.2),
        x_title=r"$phi_{qq'}$",
    )
    #Wlepton
    config.add_variable(
        name="pt_Wlepton",
        binning=(40, 0., 1500.),
        unit="GeV",
        x_title=r"$pt_{leptnu'}$",
    )
    config.add_variable(
        name="m_Wlepton",
        binning=(40, 0., 1500.),
        unit="GeV",
        x_title=r"$m_{leptnu}$",
    )
    config.add_variable(
        name="eta_Wlepton",
        binning=(50, -2.5, 2.5),
        x_title=r"$eta_{leptnu}$",
    )
    config.add_variable(
        name="phi_Wlepton",
        binning=(40, -3.2, 3.2),
        x_title=r"$phi_{leptnu}$",
    )
    #Higgs_WW
    config.add_variable(
        name="pt_Higgs_WW",
        binning=(40, 0., 600.),
        unit="GeV",
        x_title=r"$pt_{Leptnu+qq'}$",
    )
    config.add_variable(
        name="m_Higgs_WW",
        binning=(40, 0., 1500.),
        unit="GeV",
        x_title=r"$m_{Leptnu+qq'}$",
    )
    config.add_variable(
        name="eta_Higgs_WW",
        binning=(50, -2.5, 2.5),
        x_title=r"$eta_{Leptnu+qq'}$",
    )
    config.add_variable(
        name="phi_Higgs_WW",
        binning=(40, -3.2, 3.2),
        x_title=r"$phi_{Leptnu+qq'}$",
    )
    #Higgs_bb
    config.add_variable(
        name="pt_Higgs_bb",
        binning=(40, 0., 600.),
        unit="GeV",
        x_title=r"$pt_{bb}$",
    )
    config.add_variable(
        name="m_Higgs_bb",
        binning=(40, 0., 400.),
        unit="GeV",
        x_title=r"$m_{bb}$",
    )
    config.add_variable(
        name="eta_Higgs_bb",
        binning=(50, -2.5, 2.5),
        x_title=r"$eta_{bb}$",
    )
    config.add_variable(
        name="phi_Higgs_bb",
        binning=(40, -3.2, 3.2),
        x_title=r"$phi_{bb}$",
    )
    #Heavy_Higgs
    config.add_variable(
        name="pt_Heavy_Higgs",
        binning=(40, 0., 600.),
        unit="GeV",
        x_title=r"$pt_{Leptnu+bb+qq'}$",
    )
    config.add_variable(
        name="m_Heavy_Higgs",
        binning=(40, 0., 1500.),
        unit="GeV",
        x_title=r"$m_{Leptnu+bb+qq'}$",
    )
    config.add_variable(
        name="eta_Heavy_Higgs",
        binning=(50, -2.5, 2.5),
        x_title=r"$eta_{Leptnu+bb+qq'}$",
    )
    config.add_variable(
        name="phi_Heavy_Higgs",
        binning=(40, -3.2, 3.2),
        x_title=r"$phi_{Leptnu+bb+qq'}$",
    )
