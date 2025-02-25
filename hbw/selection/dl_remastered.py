# coding: utf-8

"""
Selection modules for HH -> bbWW(lnulnu).
"""

from collections import defaultdict
from typing import Tuple

from columnflow.util import maybe_import
from columnflow.selection import Selector, SelectionResult, selector

from hbw.selection.common import masked_sorted_indices, pre_selection, post_selection
from hbw.selection.lepton import lepton_definition
from hbw.selection.jet import jet_selection, sl_boosted_jet_selection, vbf_jet_selection
from hbw.production.weights import event_weights_to_normalize

np = maybe_import("numpy")
ak = maybe_import("awkward")
coffea = maybe_import("coffea")
maybe_import("coffea.nanoevents.methods.nanoaod")


@selector(
    uses={lepton_definition, "Electron.charge", "Muon.charge"},
    produces={lepton_definition},
)
def dl_lepton_selection(
        self: Selector,
        events: ak.Array,
        stats: defaultdict,
        **kwargs,
) -> Tuple[ak.Array, SelectionResult]:
    """
    Lepton Selector for the DL channel. Produces:

    Steps:
    - TripleLeptonVeto
    - Lep_mm, Lep_ee, Lep_emu, Lep_mue
    - Dilepton (logical or of the previous 4)

    Objects:
    - Electron (fakeable Electron + pt > 15)
    - Muon (fakeable Muon + pt > 15)
    """
    # load default lepton definition

    events, lepton_results = self[lepton_definition](events, stats, **kwargs)

    # number of electrons
    lepton_results.steps["nRecoElectron2"] = ak.num(events.Electron) >= 2
    lepton_results.steps["nLooseElectron2"] = events.cutflow.n_loose_electron >= 2
    lepton_results.steps["nFakeableElectron2"] = events.cutflow.n_fakeable_electron >= 2
    lepton_results.steps["nTightElectron2"] = events.cutflow.n_tight_electron >= 2

    # number of muons
    lepton_results.steps["nRecoMuon2"] = ak.num(events.Muon) >= 2
    lepton_results.steps["nLooseMuon2"] = events.cutflow.n_loose_muon >= 2
    lepton_results.steps["nFakeableMuon2"] = events.cutflow.n_fakeable_muon >= 2
    lepton_results.steps["nTightMuon2"] = events.cutflow.n_tight_muon >= 2

    lepton_results.steps["TripleLooseLeptonVeto"] = (
        events.cutflow.n_loose_electron + events.cutflow.n_loose_muon
    ) <= 2
    lepton_results.steps["TripleFakeableLeptonVeto"] = (
        events.cutflow.n_fakeable_electron + events.cutflow.n_fakeable_muon
    ) <= 2
    lepton_results.steps["TripleTightLeptonVeto"] = (
        events.cutflow.n_tight_electron + events.cutflow.n_tight_muon
    ) <= 2

    # select events
    mu_mask_fakeable = lepton_results.x.mu_mask_fakeable
    e_mask_fakeable = lepton_results.x.e_mask_fakeable

    # NOTE: leading lepton pt could be reduced to trigger threshold + 1
    leading_mu_mask = (mu_mask_fakeable) & (events.Muon.pt > 25)
    leading_e_mask = (e_mask_fakeable) & (events.Electron.pt > 25)

    # NOTE: we might need pt > 15 for lepton SFs. Needs to be checked in Run 3.
    subleading_mu_mask = (mu_mask_fakeable) & (events.Muon.pt > 15)
    subleading_e_mask = (e_mask_fakeable) & (events.Electron.pt > 15)

    # For further analysis after Reduction, we consider all tight leptons with pt > 15 GeV
    lepton_results.objects["Electron"]["Electron"] = masked_sorted_indices(subleading_e_mask, events.Electron.pt)
    lepton_results.objects["Muon"]["Muon"] = masked_sorted_indices(subleading_mu_mask, events.Muon.pt)

    electron = events.Electron[subleading_e_mask]
    muon = events.Muon[subleading_mu_mask]

    # Create a temporary lepton collection
    lepton = ak.concatenate(
        [
            electron * 1,
            muon * 1,
        ],
        axis=1,
    )
    lepton = lepton_results.aux["lepton"] = lepton[ak.argsort(lepton.pt, axis=-1, ascending=False)]

    lepton_results.steps["TripleLeptonVeto"] = ak.num(lepton, axis=1) <= 2
    lepton_results.steps["Charge"] = ak.sum(electron.charge, axis=1) + ak.sum(muon.charge, axis=1) == 0

    # lepton channel masks
    lepton_results.steps["Lep_mm"] = mm_mask = (
        lepton_results.steps.TripleLeptonVeto &
        (ak.sum(leading_mu_mask, axis=1) >= 1) &
        (ak.sum(subleading_mu_mask, axis=1) >= 2)
    )
    lepton_results.steps["Lep_ee"] = ee_mask = (
        lepton_results.steps.TripleLeptonVeto &
        (ak.sum(leading_e_mask, axis=1) >= 1) &
        (ak.sum(subleading_e_mask, axis=1) >= 2)
    )
    lepton_results.steps["Lep_emu"] = emu_mask = (
        lepton_results.steps.TripleLeptonVeto &
        (ak.sum(leading_e_mask, axis=1) >= 1) &
        (ak.sum(subleading_mu_mask, axis=1) >= 1)
    )
    lepton_results.steps["Lep_mue"] = mue_mask = (
        lepton_results.steps.TripleLeptonVeto &
        (ak.sum(leading_mu_mask, axis=1) >= 1) &
        (ak.sum(subleading_e_mask, axis=1) >= 1)
    )

    lepton_results.steps["Dilepton"] = (mm_mask | ee_mask | emu_mask | mue_mask)

    # define (but not apply) steps on how to separate between Fake Region and Signal Region
    lepton_results.steps["Fake"] = (
        lepton_results.steps.Dilepton &
        (ak.sum(electron.is_tight, axis=1) + ak.sum(muon.is_tight, axis=1) <= 1)
    )
    lepton_results.steps["SR"] = (
        lepton_results.steps.Dilepton &
        (ak.sum(electron.is_tight, axis=1) + ak.sum(muon.is_tight, axis=1) == 2)
    )

    for channel, trigger_columns in self.trigger.items():
        # apply the "or" of all triggers of this channel
        trigger_mask = ak.any([events.HLT[trigger_column] for trigger_column in trigger_columns], axis=0)
        lepton_results.steps[f"Trigger_{channel}"] = trigger_mask

        # ensure that Lepton channel is in agreement with trigger
        lepton_results.steps[f"TriggerAndLep_{channel}"] = (
            lepton_results.steps[f"Trigger_{channel}"] & lepton_results.steps[f"Lep_{channel}"]
        )

    # combine results of each individual channel
    lepton_results.steps["Trigger"] = ak.any([
        lepton_results.steps[f"Trigger_{channel}"]
        for channel in self.trigger.keys()
    ], axis=0)

    lepton_results.steps["TriggerAndLep"] = ak.any([
        lepton_results.steps[f"TriggerAndLep_{channel}"]
        for channel in self.trigger.keys()
    ], axis=0)

    return events, lepton_results


@dl_lepton_selection.init
def dl_lepton_selection_init(self: Selector) -> None:
    # update selector steps labels
    self.config_inst.x.selector_step_labels = self.config_inst.x("selector_step_labels", {})
    self.config_inst.x.selector_step_labels.update({
        "TripleLooseLeptonVeto": r"$N_{lepton}^{loose} \leq 2$",
        "TripleFakeableLeptonVeto": r"$N_{lepton}^{fakeable} \leq 2$",
        "TripleTightLeptonVeto": r"$N_{lepton}^{tight} \leq 2$",
        "Charge": r"Opposite-charge leptons",
        "Dilepton": r"$N_{lepton} = 2$",
        "Lep_mm": r"$N_{\mu} = 2$ and $N_{e} = 0$",
        "Lep_ee": r"$N_{\mu} = 0$ and $N_{e} = 2$",
        "Lep_emu": r"Leading e, subleading $\mu$",
        "Lep_mue": r"Leading $\mu$, subleading e",
        "Fake": r"$N_{lepton}^{tight} \leq 1$",
        "SR": r"$N_{lepton}^{tight} = 2$",
        "TriggerAndLep": "Trigger matches Lepton Channel",
    })

    # Trigger setup, only required when running SelectEvents
    if self.task and self.task.task_family == "cf.SelectEvents":
        year = self.config_inst.campaign.x.year

        if year == 2017:
            self.trigger = {
                "mm": [
                    "IsoMu27",
                    "Mu17_TrkIsoVVL_Mu8_TrkIsoVVL",
                    "Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ",
                    "Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_Mass3p8",
                    "Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_Mass8",
                ],
                "ee": [
                    "Ele35_WPTight_Gsf",
                    "Ele23_Ele12_CaloIdL_TrackIdL_IsoVL_DZ",
                ],
                "emu": [
                    "IsoMu27",
                    "Ele35_WPTight_Gsf",
                    "Mu8_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL",
                    "Mu8_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_DZ",
                ],
                "mue": [
                    "IsoMu27",
                    "Ele35_WPTight_Gsf",
                    "Mu23_TrkIsoVVL_Ele12_CaloIdL_TrackIdL_IsoVL",
                    "Mu23_TrkIsoVVL_Ele12_CaloIdL_TrackIdL_IsoVL",
                ],
            }
        elif year == 2022:
            self.trigger = {
                "mm": [
                    "IsoMu24",
                    "Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_Mass3p8",
                ],
                "ee": [
                    "Ele30_WPTight_Gsf",
                    "Ele23_Ele12_CaloIdL_TrackIdL_IsoVL",
                ],
                "emu": [
                    "IsoMu24",
                    "Ele30_WPTight_Gsf",
                    "Mu8_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL",  # TODO: recommentations (unprescaled?)
                ],
                "mue": [
                    "IsoMu24",
                    "Ele30_WPTight_Gsf",
                    "Mu23_TrkIsoVVL_Ele12_CaloIdL_TrackIdL_IsoVL",  # TODO: recommentations (unprescaled?)
                ],
            }
        else:
            raise Exception(f"Dilepton trigger not implemented for year {year}")

        # add all required trigger to the uses
        for trigger_columns in self.trigger.values():
            for column in trigger_columns:
                self.uses.add(f"HLT.{column}")

    return


@selector(
    uses={
        pre_selection, post_selection,
        vbf_jet_selection, sl_boosted_jet_selection,
        jet_selection, dl_lepton_selection,
    },
    produces={
        pre_selection, post_selection,
        vbf_jet_selection, sl_boosted_jet_selection,
        jet_selection, dl_lepton_selection,
    },
    exposed=True,
)
def dl1(
    self: Selector,
    events: ak.Array,
    stats: defaultdict,
    **kwargs,
) -> Tuple[ak.Array, SelectionResult]:
    # prepare events
    events, results = self[pre_selection](events, stats, **kwargs)

    # lepton selection
    events, lepton_results = self[dl_lepton_selection](events, stats, **kwargs)
    results += lepton_results

    # jet selection
    events, jet_results = self[jet_selection](events, lepton_results, stats, **kwargs)
    results += jet_results

    # boosted selection
    events, boosted_results = self[sl_boosted_jet_selection](events, lepton_results, jet_results, stats, **kwargs)
    results += boosted_results

    # vbf_jet selection
    events, vbf_jet_results = self[vbf_jet_selection](events, results, stats, **kwargs)
    results += vbf_jet_results

    results.steps["Resolved"] = (results.steps.nJet1 & results.steps.nBjet1)
    results.steps["ResolvedOrBoosted"] = (
        (results.steps.nJet1 & results.steps.nBjet1 | results.steps.HbbJet)
    )

    # combined event selection after all steps except b-jet selection
    results.steps["all_but_bjet"] = (
        results.steps.cleanup &
        (results.steps.nJet1 | results.steps.HbbJet_no_bjet) &
        results.steps.ll_lowmass_veto &
        results.steps.ll_zmass_veto &
        results.steps.TripleLooseLeptonVeto &
        results.steps.Charge &
        results.steps.Dilepton &
        results.steps.Trigger &
        results.steps.TriggerAndLep
    )

    # combined event selection after all steps
    results.steps["all"] = results.event = (
        results.steps.all_but_bjet &
        ((results.steps.nJet1 & results.steps.nBjet1) | results.steps.HbbJet)
    )

    # build categories
    events, results = self[post_selection](events, results, stats, **kwargs)

    return events, results


@dl1.init
def dl1_init(self: Selector) -> None:
    # define mapping from selector step to labels used in cutflow plots
    self.config_inst.x.selector_step_labels = self.config_inst.x("selector_step_labels", {})
    self.config_inst.x.selector_step_labels.update({
        "Resolved": r"$N_{jets}^{AK4} \geq 1$ and $N_{jets}^{BTag} \geq 1$",
        "ResolvedOrBoosted": (
            r"($N_{jets}^{AK4} \geq 3$ and $N_{jets}^{BTag} \geq 1$) "
            r"or $N_{H \rightarrow bb}^{AK8} \geq 1$"
        ),
    })

    if not getattr(self, "dataset_inst", None) or self.dataset_inst.is_data:
        return

    self.uses.add(event_weights_to_normalize)
    self.produces.add(event_weights_to_normalize)
