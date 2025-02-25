# coding: utf-8

"""
Column production methods related to higher-level features.
"""

from __future__ import annotations

import functools

from columnflow.production import Producer, producer
from columnflow.util import maybe_import
from columnflow.columnar_util import set_ak_column

from hbw.production.prepare_objects import prepare_objects
from hbw.config.ml_variables import add_ml_variables
from hbw.config.dl.variables import add_dl_ml_variables
from hbw.config.sl_res.variables import add_sl_res_ml_variables
from hbw.util import four_vec
ak = maybe_import("awkward")
np = maybe_import("numpy")

# helper
set_ak_column_f32 = functools.partial(set_ak_column, value_type=np.float32)

ZERO_PADDING_VALUE = -10


@producer(
    uses={
        prepare_objects,
        "HbbJet.msoftdrop",
        "Jet.btagDeepFlavB", "Bjet.btagDeepFlavB", "Lightjet.btagDeepFlavB",
    } | four_vec(
        {"Electron", "Muon", "MET", "Jet", "Bjet", "Lightjet", "HbbJet", "VBFJet"},
    ),
    # produced columns set in the init function
)
def sl_ml_inputs(self: Producer, events: ak.Array, **kwargs) -> ak.Array:
    # add behavior and define new collections (e.g. Lepton)
    events = self[prepare_objects](events, **kwargs)

    # object padding
    events = set_ak_column(events, "Lightjet", ak.pad_none(events.Lightjet, 2))
    events = set_ak_column(events, "Bjet", ak.pad_none(events.Bjet, 2))
    events = set_ak_column(events, "HbbJet", ak.pad_none(events.HbbJet, 1))
    events = set_ak_column(events, "VBFJet", ak.pad_none(events.VBFJet, 2))

    # low-level features
    for var in ["pt", "eta", "btagDeepFlavB"]:
        events = set_ak_column_f32(events, f"mli_b1_{var}", events.Bjet[:, 0][var])
        events = set_ak_column_f32(events, f"mli_b2_{var}", events.Bjet[:, 1][var])
        events = set_ak_column_f32(events, f"mli_j1_{var}", events.Lightjet[:, 0][var])
        events = set_ak_column_f32(events, f"mli_j2_{var}", events.Lightjet[:, 1][var])

    events = set_ak_column_f32(events, "mli_lep_pt", events.Lepton[:, 0].pt)
    events = set_ak_column_f32(events, "mli_lep_eta", events.Lepton[:, 0].eta)
    events = set_ak_column_f32(events, "mli_met_pt", events.MET.pt)

    # H->bb FatJet
    for var in ["pt", "eta", "phi", "mass", "msoftdrop"]:
        events = set_ak_column_f32(events, f"mli_fj_{var}", events.HbbJet[:, 0][var])

    # general
    events = set_ak_column_f32(events, "mli_ht", ak.sum(events.Jet.pt, axis=1))
    events = set_ak_column_f32(events, "mli_lt", ak.sum(events.Lepton.pt, axis=1) + events.MET.pt)
    events = set_ak_column_f32(events, "mli_n_jet", ak.num(events.Jet.pt, axis=1))

    # all possible jet pairs
    jet_pairs = ak.combinations(events.Jet, 2)
    dr = jet_pairs[:, :, "0"].delta_r(jet_pairs[:, :, "1"])
    events = set_ak_column_f32(events, "mli_mindr_jj", ak.min(dr, axis=1))

    # vbf jet pair features
    events = set_ak_column_f32(events, "mli_vbf_deta", abs(events.VBFJet[:, 0].eta - events.VBFJet[:, 1].eta))
    events = set_ak_column_f32(events, "mli_vbf_invmass", (events.VBFJet[:, 0] + events.VBFJet[:, 1]).mass)
    vbf_tag = ak.sum(events.VBFJet.pt > 0, axis=1) >= 2
    events = set_ak_column_f32(events, "mli_vbf_tag", vbf_tag)

    # bjets in general
    # TODO: generalize using selection
    wp_med = self.config_inst.x.btag_working_points.deepjet.medium
    events = set_ak_column_f32(events, "mli_n_deepjet", ak.num(events.Jet[events.Jet.btagDeepFlavB > wp_med], axis=1))
    events = set_ak_column_f32(events, "mli_deepjetsum", ak.sum(events.Jet.btagDeepFlavB, axis=1))
    events = set_ak_column_f32(events, "mli_b_deepjetsum", ak.sum(events.Bjet.btagDeepFlavB, axis=1))
    events = set_ak_column_f32(events, "mli_l_deepjetsum", ak.sum(events.Lightjet.btagDeepFlavB, axis=1))

    # hbb features
    events = set_ak_column_f32(events, "mli_dr_bb", events.Bjet[:, 0].delta_r(events.Bjet[:, 1]))
    events = set_ak_column_f32(events, "mli_dphi_bb", abs(events.Bjet[:, 0].delta_phi(events.Bjet[:, 1])))

    hbb = events.Bjet[:, 0] + events.Bjet[:, 1]
    events = set_ak_column_f32(events, "mli_mbb", hbb.mass)

    # wjj features
    events = set_ak_column_f32(events, "mli_dr_jj", events.Lightjet[:, 0].delta_r(events.Lightjet[:, 1]))
    events = set_ak_column_f32(events, "mli_dphi_jj", abs(events.Lightjet[:, 0].delta_phi(events.Lightjet[:, 1])))

    wjj = events.Lightjet[:, 0] + events.Lightjet[:, 1]
    events = set_ak_column_f32(events, "mli_mjj", wjj.mass)

    # wlnu features
    # NOTE: we might want to consider neutrino reconstruction or transverse masses instead when including MET
    wlnu = events.MET + events.Lepton[:, 0]
    events = set_ak_column_f32(events, "mli_mlnu", wlnu.mass)
    events = set_ak_column_f32(events, "mli_dphi_lnu", abs(events.Lepton[:, 0].delta_phi(events.MET)))
    events = set_ak_column_f32(events, "mli_dphi_wl", abs(wlnu.delta_phi(events.Lepton[:, 0])))

    # angles to lepton
    mindr_lb = ak.min(events.Bjet.delta_r(events.Lepton[:, 0]), axis=-1)
    events = set_ak_column_f32(events, "mli_mindr_lb", mindr_lb)

    mindr_lj = ak.min(events.Lightjet.delta_r(events.Lepton[:, 0]), axis=-1)
    events = set_ak_column_f32(events, "mli_mindr_lj", mindr_lj)

    # hww features
    hww = wlnu + wjj
    hww_vis = events.Lepton[:, 0] + wjj

    events = set_ak_column_f32(events, "mli_mjjlnu", hww.mass)
    events = set_ak_column_f32(events, "mli_mjjl", hww_vis.mass)

    # hh system angles
    events = set_ak_column_f32(events, "mli_dphi_bb_jjlnu", abs(hbb.delta_phi(hww)))
    events = set_ak_column_f32(events, "mli_dr_bb_jjlnu", hbb.delta_r(hww))

    events = set_ak_column_f32(events, "mli_dphi_bb_jjl", abs(hbb.delta_phi(hww_vis)))
    events = set_ak_column_f32(events, "mli_dr_bb_jjl", hbb.delta_r(hww_vis))

    events = set_ak_column_f32(events, "mli_dphi_bb_nu", abs(hbb.delta_phi(events.MET)))
    events = set_ak_column_f32(events, "mli_dphi_jj_nu", abs(wjj.delta_phi(events.MET)))
    events = set_ak_column_f32(events, "mli_dr_bb_l", hbb.delta_r(events.Lepton[:, 0]))
    events = set_ak_column_f32(events, "mli_dr_jj_l", hbb.delta_r(events.Lepton[:, 0]))

    # hh features
    hh = hbb + hww
    hh_vis = hbb + hww_vis

    events = set_ak_column_f32(events, "mli_mbbjjlnu", hh.mass)
    events = set_ak_column_f32(events, "mli_mbbjjl", hh_vis.mass)

    s_min = (
        2 * events.MET.pt * ((hh_vis.mass ** 2 + hh_vis.energy ** 2) ** 0.5 -
        hh_vis.pt * np.cos(hh_vis.delta_phi(events.MET)) + hh_vis.mass ** 2)
    ) ** 0.5
    events = set_ak_column_f32(events, "mli_s_min", s_min)

    # fill nan/none values of all produced columns
    for col in self.ml_input_columns:
        events = set_ak_column(events, col, ak.fill_none(ak.nan_to_none(events[col]), ZERO_PADDING_VALUE))

    return events


@sl_ml_inputs.init
def sl_ml_inputs_init(self: Producer) -> None:
    # define ML input separately to self.produces
    self.config_inst.x.ml_input_columns = self.ml_input_columns = {
        # event features
        "mli_ht", "mli_lt", "mli_n_jet", "mli_n_deepjet",
        "mli_deepjetsum", "mli_b_deepjetsum", "mli_l_deepjetsum",
        # bb system
        "mli_dr_bb", "mli_dphi_bb", "mli_mbb",
        # jj system
        "mli_dr_jj", "mli_dphi_jj", "mli_mjj",
        # lnu system
        "mli_dphi_lnu", "mli_mlnu",
        # angles to lepton
        "mli_mindr_lb", "mli_mindr_lj",
        "mli_dphi_wl",
        # ww system
        "mli_mjjlnu", "mli_mjjl",
        # HH system
        "mli_dphi_bb_jjlnu", "mli_dr_bb_jjlnu",
        "mli_dphi_bb_jjl", "mli_dr_bb_jjl", "mli_dphi_bb_nu", "mli_dphi_jj_nu", "mli_dr_bb_l", "mli_dr_jj_l",
        "mli_mbbjjlnu", "mli_mbbjjl", "mli_mindr_jj",
        "mli_s_min",
        # VBF features
        "mli_vbf_deta", "mli_vbf_invmass", "mli_vbf_tag",
        # low-level features
        "mli_lep_pt", "mli_lep_eta", "mli_met_pt",
    } | set(
        f"mli_{obj}_{var}"
        for obj in ["b1", "b2", "j1", "j2"]
        for var in ["btagDeepFlavB", "pt", "eta"]
    ) | set(
        f"mli_{obj}_{var}"
        for obj in ["fj"]
        for var in ["pt", "eta", "phi", "mass", "msoftdrop"]
    )
    self.produces |= self.ml_input_columns

    # add variable instances to config
    add_ml_variables(self.config_inst)


@producer(
    uses={
        prepare_objects,
        "HbbJet.msoftdrop",
        "Jet.btagDeepFlavB", "Bjet.btagDeepFlavB",
    } | four_vec(
        {"Electron", "Muon", "MET", "Jet", "Bjet", "HbbJet", "VBFJet"},
    ),
    # produced columns set in the init function
)
def dl_ml_inputs(self: Producer, events: ak.Array, **kwargs) -> ak.Array:
    # add behavior and define new collections (e.g. Lepton)
    events = self[prepare_objects](events, **kwargs)

    # object padding
    events = set_ak_column(events, "Bjet", ak.pad_none(events.Bjet, 2))
    events = set_ak_column(events, "HbbJet", ak.pad_none(events.HbbJet, 1))
    events = set_ak_column(events, "Lepton", ak.pad_none(events.Lepton, 2))
    events = set_ak_column(events, "VBFJet", ak.pad_none(events.VBFJet, 2))

    # low-level features
    events = set_ak_column_f32(events, "mli_met_pt", events.MET.pt)
    for var in ["pt", "eta", "btagDeepFlavB"]:
        events = set_ak_column_f32(events, f"mli_b1_{var}", events.Bjet[:, 0][var])
        events = set_ak_column_f32(events, f"mli_b2_{var}", events.Bjet[:, 1][var])

    for var in ["pt", "eta"]:
        events = set_ak_column_f32(events, f"mli_lep_{var}", events.Lepton[:, 0][var])
        events = set_ak_column_f32(events, f"mli_lep2_{var}", events.Lepton[:, 1][var])

    # H->bb FatJet
    for var in ["pt", "eta", "phi", "mass", "msoftdrop"]:
        events = set_ak_column_f32(events, f"mli_fj_{var}", events.HbbJet[:, 0][var])

    # general
    events = set_ak_column_f32(events, "mli_ht", ak.sum(events.Jet.pt, axis=1))
    events = set_ak_column_f32(events, "mli_lt", ak.sum(events.Lepton.pt, axis=1) + events.MET.pt)
    events = set_ak_column_f32(events, "mli_n_jet", ak.num(events.Jet.pt, axis=1))

    # vbf jet pair features
    events = set_ak_column_f32(events, "mli_vbf_deta", abs(events.VBFJet[:, 0].eta - events.VBFJet[:, 1].eta))
    events = set_ak_column_f32(events, "mli_vbf_invmass", (events.VBFJet[:, 0] + events.VBFJet[:, 1]).mass)
    vbf_tag = ak.sum(events.VBFJet.pt > 0, axis=1) >= 2
    events = set_ak_column_f32(events, "mli_vbf_tag", vbf_tag)

    # bjets in general
    wp_med = self.config_inst.x.btag_working_points.deepjet.medium
    events = set_ak_column_f32(events, "mli_n_deepjet", ak.num(events.Jet[events.Jet.btagDeepFlavB > wp_med], axis=1))
    events = set_ak_column_f32(events, "mli_deepjetsum", ak.sum(events.Jet.btagDeepFlavB, axis=1))
    events = set_ak_column_f32(events, "mli_b_deepjetsum", ak.sum(events.Bjet.btagDeepFlavB, axis=1))

    # create ll object and ll variables
    ll = (events.Lepton[:, 0] + events.Lepton[:, 1])
    deltaR_ll = events.Lepton[:, 0].delta_r(events.Lepton[:, 1])
    events = set_ak_column_f32(events, "mli_ll_pt", ll.pt)
    events = set_ak_column_f32(events, "mli_mll", ll.mass)
    events = set_ak_column_f32(events, "mli_mllMET", (ll + events.MET[:]).mass)
    events = set_ak_column_f32(events, "mli_dr_ll", deltaR_ll)
    events = set_ak_column_f32(events, "mli_dphi_ll", events.Lepton[:, 0].delta_phi(events.Lepton[:, 1]))

    # minimum deltaR between lep and jet
    lljj_pairs = ak.cartesian([events.Lepton, events.Bjet], axis=1)
    lep, jet = ak.unzip(lljj_pairs)
    min_dr_lljj = (ak.min(lep.delta_r(jet), axis=-1))
    events = set_ak_column_f32(events, "mli_min_dr_llbb", min_dr_lljj)

    # bb pt
    hbb = events.Bjet[:, 0] + events.Bjet[:, 1]
    events = set_ak_column_f32(events, "mli_mbb", hbb.pt)
    events = set_ak_column_f32(events, "mli_dr_bb", events.Bjet[:, 0].delta_r(events.Bjet[:, 1]))
    events = set_ak_column_f32(events, "mli_dphi_bb", abs(events.Bjet[:, 0].delta_phi(events.Bjet[:, 1])))
    mindr_lb = ak.min(events.Bjet.delta_r(events.Lepton[:, 0]), axis=-1)
    events = set_ak_column_f32(events, "mli_mindr_lb", mindr_lb)

    events = set_ak_column_f32(events, "mli_bb_pt", hbb.pt)
    events = set_ak_column_f32(events, "mli_mbbllMET", (ll + hbb + events.MET[:]).mass)
    events = set_ak_column_f32(events, "mli_dr_bb_llMET", hbb.delta_r(ll + events.MET[:]))
    events = set_ak_column_f32(events, "mli_dphi_bb_nu", abs(hbb.delta_phi(events.MET)))
    events = set_ak_column_f32(events, "mli_dphi_bb_llMET", hbb.delta_phi(ll + events.MET[:]))

    # TODO: variable to reconstruct top quark resonances (e.g. mT(lepton + met + b))

    # fill nan/none values of all produced columns
    for col in self.ml_columns:
        events = set_ak_column(events, col, ak.fill_none(ak.nan_to_none(events[col]), ZERO_PADDING_VALUE))

    return events


@dl_ml_inputs.init
def dl_ml_inputs_init(self: Producer) -> None:
    # define ML input separately to self.produces
    self.ml_columns = {
        # event features
        "mli_ht", "mli_lt", "mli_n_jet", "mli_n_deepjet",
        "mli_deepjetsum", "mli_b_deepjetsum",
        # bb system
        "mli_dr_bb", "mli_dphi_bb", "mli_mbb", "mli_bb_pt",
        "mli_mindr_lb",
        # ll system
        "mli_mll", "mli_dr_ll", "mli_dphi_ll", "mli_ll_pt",
        "mli_min_dr_llbb",
        "mli_dphi_bb_nu", "mli_dphi_bb_llMET", "mli_mllMET",
        "mli_mbbllMET", "mli_dr_bb_llMET",
        # VBF features
        "mli_vbf_deta", "mli_vbf_invmass", "mli_vbf_tag",
        # low-level features
        "mli_met_pt",
    } | set(
        f"mli_{obj}_{var}"
        for obj in ["b1", "b2"]
        for var in ["pt", "eta", "btagDeepFlavB"]
    ) | set(
        f"mli_{obj}_{var}"
        for obj in ["lep", "lep2"]
        for var in ["pt", "eta"]
    ) | set(
        f"mli_{obj}_{var}"
        for obj in ["fj"]
        for var in ["pt", "eta", "phi", "mass", "msoftdrop"]
    )
    self.produces |= self.ml_columns

    # add variable instances to config
    add_dl_ml_variables(self.config_inst)


@producer(
    uses={
        prepare_objects,
        "HbbJet.msoftdrop",
        "Jet.btagDeepFlavB", "Bjet.btagDeepFlavB", "Lightjet.btagDeepFlavB",
    } | four_vec(
        {"Electron", "Muon", "MET", "Jet", "Bjet", "Lightjet", "HbbJet", "VBFJet"},
    ),
    # produced columns set in the init function
)
def sl_res_ml_inputs(self: Producer, events: ak.Array, **kwargs) -> ak.Array:

    # add behavior and define new collections (e.g. Lepton)
    events = self[prepare_objects](events, **kwargs)

    # object padding
    events = set_ak_column(events, "Lightjet", ak.pad_none(events.Lightjet, 2))
    events = set_ak_column(events, "Bjet", ak.pad_none(events.Bjet, 2))
    # events = set_ak_column(events, "FatJet", ak.pad_none(events.FatJet, 1))
    events = set_ak_column(events, "HbbJet", ak.pad_none(events.HbbJet, 1))
    events = set_ak_column(events, "VBFJet", ak.pad_none(events.VBFJet, 2))

    # low-level features
    # TODO: this could be more generalized
    for var in ["pt", "eta"]:
        events = set_ak_column_f32(events, f"mli_b1_{var}", events.Bjet[:, 0][var])
        events = set_ak_column_f32(events, f"mli_b2_{var}", events.Bjet[:, 1][var])
        events = set_ak_column_f32(events, f"mli_j1_{var}", events.Lightjet[:, 0][var])
        events = set_ak_column_f32(events, f"mli_j2_{var}", events.Lightjet[:, 1][var])
        events = set_ak_column_f32(events, f"mli_lep_{var}", events.Lepton[:, 0][var])
        events = set_ak_column_f32(events, f"mli_met_{var}", events.MET[var])

    # H->bb FatJet
    for var in ["pt", "eta", "phi", "mass", "msoftdrop"]:
        events = set_ak_column_f32(events, f"mli_fj_{var}", events.HbbJet[:, 0][var])

    # jets in general
    events = set_ak_column_f32(events, "mli_ht", ak.sum(events.Jet.pt, axis=1))
    events = set_ak_column_f32(events, "mli_n_jet", ak.num(events.Jet.pt, axis=1))

    # all possible jet pairs
    jet_pairs = ak.combinations(events.Jet, 2)
    dr = jet_pairs[:, :, "0"].delta_r(jet_pairs[:, :, "1"])
    events = set_ak_column_f32(events, "mindr_jj", ak.min(dr, axis=1))

    # vbf jet pair features
    events = set_ak_column_f32(events, "mli_vbf_deta", abs(events.VBFJet[:, 0].eta - events.VBFJet[:, 1].eta))
    events = set_ak_column_f32(events, "mli_vbf_invmass", (events.VBFJet[:, 0] + events.VBFJet[:, 1]).mass)
    vbf_tag = ak.sum(events.VBFJet.pt > 0, axis=1) >= 2
    events = set_ak_column_f32(events, "mli_vbf_tag", vbf_tag)

    # bjets in general
    wp_med = self.config_inst.x.btag_working_points.deepjet.medium
    events = set_ak_column_f32(events, "mli_n_deepjet", ak.num(events.Jet[events.Jet.btagDeepFlavB > wp_med], axis=1))
    events = set_ak_column_f32(events, "mli_deepjetsum", ak.sum(events.Jet.btagDeepFlavB, axis=1))
    events = set_ak_column_f32(events, "mli_b_deepjetsum", ak.sum(events.Bjet.btagDeepFlavB, axis=1))
    events = set_ak_column_f32(events, "mli_l_deepjetsum", ak.sum(events.Lightjet.btagDeepFlavB, axis=1))

    # hbb features
    events = set_ak_column_f32(events, "mli_dr_bb", events.Bjet[:, 0].delta_r(events.Bjet[:, 1]))
    events = set_ak_column_f32(events, "mli_dphi_bb", abs(events.Bjet[:, 0].delta_phi(events.Bjet[:, 1])))

    hbb = events.Bjet[:, 0] + events.Bjet[:, 1]
    events = set_ak_column_f32(events, "mli_mbb", hbb.mass)
    events = set_ak_column_f32(events, "mli_pt_bb", hbb.pt)
    events = set_ak_column_f32(events, "mli_eta_bb", hbb.eta)
    events = set_ak_column_f32(events, "mli_phi_bb", hbb.phi)

    mindr_lb = ak.min(events.Bjet.delta_r(events.Lepton[:, 0]), axis=-1)
    events = set_ak_column_f32(events, "mli_mindr_lb", mindr_lb)

    # wjj features
    events = set_ak_column_f32(events, "mli_dr_jj", events.Lightjet[:, 0].delta_r(events.Lightjet[:, 1]))
    events = set_ak_column_f32(events, "mli_dphi_jj", abs(events.Lightjet[:, 0].delta_phi(events.Lightjet[:, 1])))

    wjj = events.Lightjet[:, 0] + events.Lightjet[:, 1]
    events = set_ak_column_f32(events, "mli_mjj", wjj.mass)
    events = set_ak_column_f32(events, "mli_pt_jj", wjj.pt)
    events = set_ak_column_f32(events, "mli_eta_jj", wjj.eta)
    events = set_ak_column_f32(events, "mli_phi_jj", wjj.phi)

    mindr_lj = ak.min(events.Lightjet.delta_r(events.Lepton[:, 0]), axis=-1)
    events = set_ak_column_f32(events, "mli_mindr_lj", mindr_lj)

    # wlnu features
    wlnu = events.MET + events.Lepton[:, 0]
    events = set_ak_column_f32(events, "mli_dphi_lnu", abs(events.Lepton[:, 0].delta_phi(events.MET)))
    # NOTE: this column can be set to nan value
    events = set_ak_column_f32(events, "mli_mlnu", wlnu.mass)
    events = set_ak_column_f32(events, "mli_pt_lnu", wlnu.pt)
    events = set_ak_column_f32(events, "mli_eta_lnu", wlnu.eta)
    events = set_ak_column_f32(events, "mli_phi_lnu", wlnu.phi)

    # hww features
    hww = wlnu + wjj
    hww_vis = events.Lepton[:, 0] + wjj

    events = set_ak_column_f32(events, "mli_mjjlnu", hww.mass)
    events = set_ak_column_f32(events, "mli_pt_jjlnu", hww.pt)
    events = set_ak_column_f32(events, "mli_phi_jjlnu", hww.phi)
    events = set_ak_column_f32(events, "mli_eta_jjlnu", hww.eta)
    events = set_ak_column_f32(events, "mli_mjjl", hww_vis.mass)
    events = set_ak_column_f32(events, "mli_pt_jjl", hww_vis.pt)
    events = set_ak_column_f32(events, "mli_eta_jjl", hww_vis.eta)
    events = set_ak_column_f32(events, "mli_phi_jjl", hww_vis.phi)

    # angles
    events = set_ak_column_f32(events, "mli_dphi_bb_jjlnu", abs(hbb.delta_phi(hww)))
    events = set_ak_column_f32(events, "mli_dr_bb_jjlnu", hbb.delta_r(hww))

    events = set_ak_column_f32(events, "mli_dphi_bb_jjl", abs(hbb.delta_phi(hww_vis)))
    events = set_ak_column_f32(events, "mli_dr_bb_jjl", hbb.delta_r(hww_vis))

    events = set_ak_column_f32(events, "mli_dphi_bb_nu", abs(hbb.delta_phi(events.MET)))
    events = set_ak_column_f32(events, "mli_dphi_jj_nu", abs(wjj.delta_phi(events.MET)))
    events = set_ak_column_f32(events, "mli_dr_bb_l", hbb.delta_r(events.MET))
    events = set_ak_column_f32(events, "mli_dr_jj_l", hbb.delta_r(events.MET))

    # hh features
    hh = hbb + hww
    hh_vis = hbb + hww_vis

    events = set_ak_column_f32(events, "mli_mbbjjlnu", hh.mass)
    events = set_ak_column_f32(events, "mli_mbbjjl", hh_vis.mass)

    s_min = (
        2 * events.MET.pt * ((hh_vis.mass ** 2 + hh_vis.energy ** 2) ** 0.5 -
        hh_vis.pt * np.cos(hh_vis.delta_phi(events.MET)) + hh_vis.mass ** 2)
    ) ** 0.5
    events = set_ak_column_f32(events, "mli_s_min", s_min)

    # fill nan/none values of all produced columns
    for col in self.ml_columns:
        events = set_ak_column(events, col, ak.fill_none(ak.nan_to_none(events[col]), ZERO_PADDING_VALUE))

    return events


@sl_res_ml_inputs.init
def sl_res_ml_inputs_init(self: Producer) -> None:
    # define ML input separately to self.produces
    self.ml_columns = {
        "mli_ht", "mli_n_jet", "mli_n_deepjet",
        "mli_deepjetsum", "mli_b_deepjetsum", "mli_l_deepjetsum",
        "mli_dr_bb", "mli_dphi_bb", "mli_mbb", "mli_mindr_lb", "mli_dr_jj", "mli_dphi_jj", "mli_mjj", "mli_mindr_lj",
        "mli_dphi_lnu", "mli_mlnu", "mli_mjjlnu", "mli_mjjl", "mli_dphi_bb_jjlnu", "mli_dr_bb_jjlnu",
        "mli_dphi_bb_jjl", "mli_dr_bb_jjl", "mli_dphi_bb_nu", "mli_dphi_jj_nu", "mli_dr_bb_l", "mli_dr_jj_l",
        "mli_mbbjjlnu", "mli_mbbjjl", "mli_s_min",
        "mli_vbf_deta", "mli_vbf_invmass", "mli_vbf_tag",
        "mli_pt_jj", "mli_eta_jj", "mli_phi_jj",
        "mli_pt_lnu", "mli_eta_lnu", "mli_phi_lnu",
        "mli_pt_jjlnu", "mli_eta_jjlnu", "mli_phi_jjlnu",
        "mli_pt_jjl", "mli_eta_jjl", "mli_phi_jjl",
        "mli_pt_bb", "mli_eta_bb", "mli_phi_bb",

    } | set(
        f"mli_{obj}_{var}"
        for obj in ["b1", "b2", "j1", "j2", "lep", "met"]
        for var in ["pt", "eta"]
    ) | set(
        f"mli_{obj}_{var}"
        for obj in ["fj"]
        for var in ["pt", "eta", "phi", "mass", "msoftdrop"]
    )
    self.produces |= self.ml_columns

    # add variable instances to config
    add_sl_res_ml_variables(self.config_inst)
