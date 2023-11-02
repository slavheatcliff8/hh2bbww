# coding: utf-8

"""
Column production method
"""

import functools

from columnflow.production import Producer, producer
from columnflow.selection import SelectionResult
from columnflow.util import maybe_import
from columnflow.columnar_util import set_ak_column, EMPTY_FLOAT
from columnflow.production.util import attach_coffea_behavior

ak = maybe_import("awkward")
coffea = maybe_import("coffea")
np = maybe_import("numpy")
maybe_import("coffea.nanoevents.methods.nanoaod")

set_ak_column_f32 = functools.partial(set_ak_column, value_type=np.float32)

@producer(
    uses=(
        {
            "Lightjet.pt", "Lightjet.eta", "Lightjet.phi", "Lightjet.mass",
            "MET.pt","MET.mass", "MET.phi","Lepton.pt",
            "Lepton.mass","Lepton.eta","Lepton.phi","Bjet.mass","Bjet.pt","Bjet.eta","Bjet.phi"
        }
    )
)
def resonant_features(self: Producer, events: ak.Array,**kwargs) -> ak.Array:

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

    if "Whadron" not in events.fields:
        events = set_ak_column(events, "Whadron", events.Lightjet[:, 0] + events.Lightjet[:, 1])
    if "Wlepton" not in events.fields:
        events = set_ak_column(events, "Wlepton", events.Lepton[:, 0] + events.MET[:])
    if "Higgs_WW" not in events.fields:
        events = set_ak_column(events, "Higgs_WW", events.Whadron[:] + events.Wlepton[:])
    if "Higgs_bb" not in events.fields:
        events = set_ak_column(events, "Higgs_bb", events.Bjet[:,0] + events.Bjet[:, 1])
    if "Heavy_Higgs" not in events.fields:
        events = set_ak_column (events, "Heavy_Higgs", events.Higgs_WW[:] + events.Higgs_bb[:])
    # variables of objects (don't forget to describe them in variables.py and features.py in produces)
    # Wlepton  
    events = set_ak_column_f32(events, "pt_Wlepton", events.Wlepton.pt)
    events = set_ak_column_f32(events, "pt_Wlepton", ak.fill_none(events["pt_Wlepton"], EMPTY_FLOAT))
    events = set_ak_column_f32(events, "m_Wlepton", events.Wlepton.mass)
    events = set_ak_column_f32(events, "m_Wlepton", ak.fill_none(events["m_Wlepton"], EMPTY_FLOAT))
    events = set_ak_column_f32(events, "phi_Wlepton", events.Wlepton.phi)
    events = set_ak_column_f32(events, "phi_Wlepton", ak.fill_none(events["phi_Wlepton"], EMPTY_FLOAT))
    events = set_ak_column_f32(events, "eta_Wlepton", events.Wlepton.eta)
    events = set_ak_column_f32(events, "eta_Wlepton", ak.fill_none(events["eta_Wlepton"], EMPTY_FLOAT))
    # Whadron
    events = set_ak_column_f32(events, "pt_Whadron", events.Whadron.pt)
    events = set_ak_column_f32(events, "pt_Whadron", ak.fill_none(events["pt_Whadron"], EMPTY_FLOAT))
    events = set_ak_column_f32(events, "m_Whadron", events.Whadron.mass)
    events = set_ak_column_f32(events, "m_Whadron", ak.fill_none(events["m_Whadron"], EMPTY_FLOAT))
    events = set_ak_column_f32(events, "phi_Whadron", events.Whadron.phi)
    events = set_ak_column_f32(events, "phi_Whadron", ak.fill_none(events["phi_Whadron"], EMPTY_FLOAT))
    events = set_ak_column_f32(events, "eta_Whadron", events.Whadron.eta)
    events = set_ak_column_f32(events, "eta_Whadron", ak.fill_none(events["eta_Whadron"], EMPTY_FLOAT))
    # Higgs_WW 
    events = set_ak_column_f32(events, "pt_Higgs_WW", events.Higgs_WW.pt)
    events = set_ak_column_f32(events, "pt_Higgs_WW", ak.fill_none(events["pt_Higgs_WW"], EMPTY_FLOAT))
    events = set_ak_column_f32(events, "m_Higgs_WW", events.Higgs_WW.mass)
    events = set_ak_column_f32(events, "m_Higgs_WW", ak.fill_none(events["m_Higgs_WW"], EMPTY_FLOAT))
    events = set_ak_column_f32(events, "eta_Higgs_WW", events.Higgs_WW.eta)
    events = set_ak_column_f32(events, "eta_Higgs_WW", ak.fill_none(events["eta_Higgs_WW"], EMPTY_FLOAT))
    events = set_ak_column_f32(events, "phi_Higgs_WW", events.Higgs_WW.phi)
    events = set_ak_column_f32(events, "phi_Higgs_WW", ak.fill_none(events["phi_Higgs_WW"], EMPTY_FLOAT))
    # Higgs_bb
    events = set_ak_column_f32(events, "pt_Higgs_bb", events.Higgs_bb.pt)
    events = set_ak_column_f32(events, "pt_Higgs_bb", ak.fill_none(events["pt_Higgs_bb"], EMPTY_FLOAT))
    events = set_ak_column_f32(events, "m_Higgs_bb", events.Higgs_bb.mass)
    events = set_ak_column_f32(events, "m_Higgs_bb", ak.fill_none(events["m_Higgs_bb"], EMPTY_FLOAT))
    events = set_ak_column_f32(events, "eta_Higgs_bb", events.Higgs_bb.eta)
    events = set_ak_column_f32(events, "eta_Higgs_bb", ak.fill_none(events["eta_Higgs_bb"], EMPTY_FLOAT))
    events = set_ak_column_f32(events, "phi_Higgs_bb", events.Higgs_bb.phi)
    events = set_ak_column_f32(events, "phi_Higgs_bb", ak.fill_none(events["phi_Higgs_bb"], EMPTY_FLOAT))
    # Heavy_Higgs
    events = set_ak_column_f32(events, "pt_Heavy_Higgs", events.Heavy_Higgs.pt)
    events = set_ak_column_f32(events, "pt_Heavy_Higgs", ak.fill_none(events["pt_Heavy_Higgs"], EMPTY_FLOAT))
    events = set_ak_column_f32(events, "m_Heavy_Higgs", events.Heavy_Higgs.mass)
    events = set_ak_column_f32(events, "m_Heavy_Higgs", ak.fill_none(events["m_Heavy_Higgs"], EMPTY_FLOAT))
    events = set_ak_column_f32(events, "eta_Heavy_Higgs", events.Heavy_Higgs.eta)
    events = set_ak_column_f32(events, "eta_Heavy_Higgs", ak.fill_none(events["eta_Heavy_Higgs"], EMPTY_FLOAT))
    events = set_ak_column_f32(events, "phi_Heavy_Higgs", events.Heavy_Higgs.phi)
    events = set_ak_column_f32(events, "phi_Heavy_Higgs", ak.fill_none(events["phi_Heavy_Higgs"], EMPTY_FLOAT))
    
    return events

