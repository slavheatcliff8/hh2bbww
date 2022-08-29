# coding: utf-8

"""
Configuration of the 2017 HH -> bbWW analysis.
"""

import os
import re

import yaml
from scinum import Number, REL
import order as od
import cmsdb
import cmsdb.campaigns.run2_2017

from columnflow.util import DotDict, get_root_processes_from_campaign
from hbw.config.categories import add_categories
from hbw.config.variables import add_variables

from hbw.config.analysis_hbw import analysis_hbw

thisdir = os.path.dirname(os.path.abspath(__file__))

#
# 2017 standard config
#

# copy the campaign, which in turn copies datasets and processes
campaign_run2_2017 = cmsdb.campaigns.run2_2017.campaign_run2_2017.copy()

# get all root processes
procs = get_root_processes_from_campaign(campaign_run2_2017)

# create a config by passing the campaign, so id and name will be identical
config_2017 = analysis_hbw.add_config(campaign_run2_2017)

# add processes we are interested in
config_2017.add_process(procs.n.data)
config_2017.add_process(procs.n.st)
config_2017.add_process(procs.n.tt)
config_2017.add_process(procs.n.hh_ggf_kt_1_kl_0_bbww_sl)
config_2017.add_process(procs.n.hh_ggf_kt_1_kl_1_bbww_sl)
config_2017.add_process(procs.n.hh_ggf_kt_1_kl_2p45_bbww_sl)
config_2017.add_process(procs.n.hh_ggf_kt_1_kl_5_bbww_sl)

# add datasets we need to study
dataset_names = [
    "data_e_b",
    "data_e_c",
    "data_e_d",
    "data_e_e",
    "data_e_f",
    "data_mu_b",
    "data_mu_c",
    "data_mu_d",
    "data_mu_e",
    "data_mu_f",
    "tt_sl_powheg",
    "tt_dl_powheg",
    "tt_fh_powheg",
    "st_tchannel_t_powheg",
    "st_tchannel_tbar_powheg",
    "st_twchannel_t_powheg",
    "st_twchannel_tbar_powheg",
    "st_schannel_lep_amcatnlo",
    "st_schannel_had_amcatnlo",
    "hh_ggf_kt_1_kl_0_bbww_sl_powheg",
    "hh_ggf_kt_1_kl_1_bbww_sl_powheg",
    "hh_ggf_kt_1_kl_2p45_bbww_sl_powheg",
    "hh_ggf_kt_1_kl_5_bbww_sl_powheg",
]
for dataset_name in dataset_names:
    dataset = config_2017.add_dataset(campaign_run2_2017.get_dataset(dataset_name))
    
    # reduce n_files to 2 for testing purposes
    for k in dataset.info.keys():
        dataset[k].n_files = 2

    # add aux info to datasets
    if dataset.name.startswith(("st", "tt")):
        dataset.x.has_top = True
    if dataset.name.startswith("tt"):
        dataset.x.is_ttbar = True
        dataset.x.event_weights = ["top_pt_weight"]

# default calibrator, selector, producer, ml model and inference model
config_2017.set_aux("default_calibrator", "test")
config_2017.set_aux("default_selector", "default")
config_2017.set_aux("default_producer", "features")
config_2017.set_aux("default_ml_model", None)
config_2017.set_aux("default_inference_model", "test")

# process groups for conveniently looping over certain processs
# (used in wrapper_factory and during plotting)
config_2017.set_aux("process_groups", {
    "default": ["st", "tt", "hh_ggf_kt_1_kl_1_bbww_sl"],
    "signal": ["hh_ggf_kt_1_kl_0_bbww_sl", "hh_ggf_kt_1_kl_1_bbww_sl",
               "hh_ggf_kt_1_kl_2p45_bbww_sl", "hh_ggf_kt_1_kl_5_bbww_sl"],
    "bkg": ["st", "tt"],
})

# dataset groups for conveniently looping over certain datasets
# (used in wrapper_factory and during plotting)
config_2017.set_aux("dataset_groups", {})

# category groups for conveniently looping over certain categories
# (used during plotting)
config_2017.set_aux("category_groups", {})

# variable groups for conveniently looping over certain variables
# (used during plotting)
config_2017.set_aux("variable_groups", {})

# shift groups for conveniently looping over certain shifts
# (used during plotting)
config_2017.set_aux("shift_groups", {})

# selector step groups for conveniently looping over certain steps
# (used in cutflow tasks)
config_2017.set_aux("selector_step_groups", {
    "default": ["Lepton", "Jet"],
})

# 2017 luminosity with values in inverse pb and uncertainties taken from
# https://twiki.cern.ch/twiki/bin/view/CMS/TWikiLUM?rev=176#LumiComb
config_2017.set_aux("luminosity", Number(41480, {
    "lumi_13TeV_2017": (REL, 0.02),
    "lumi_13TeV_1718": (REL, 0.006),
    "lumi_13TeV_correlated": (REL, 0.009),
}))

# 2017 minimum bias cross section in mb (milli) for creating PU weights, values from
# https://twiki.cern.ch/twiki/bin/viewauth/CMS/PileupJSONFileforData?rev=44#Pileup_JSON_Files_For_Run_II
config_2017.set_aux("minbiasxs", Number(69.2, (REL, 0.046)))

# location of JEC txt files
config_2017.set_aux("jec", DotDict.wrap({
    "source": "https://raw.githubusercontent.com/cms-jet/JECDatabase/master/textFiles",
    "campaign": "Summer19UL17",
    "version": "V6",
    "jet_type": "AK4PFchs",
    "levels": ["L1FastJet", "L2Relative", "L2L3Residual", "L3Absolute"],
    "data_eras": ["RunB", "RunC", "RunD", "RunE", "RunF"],
    "uncertainty_sources": [
        # comment out most for now to prevent large file sizes
        # "AbsoluteStat",
        # "AbsoluteScale",
        # "AbsoluteSample",
        # "AbsoluteFlavMap",
        # "AbsoluteMPFBias",
        # "Fragmentation",
        # "SinglePionECAL",
        # "SinglePionHCAL",
        # "FlavorQCD",
        # "TimePtEta",
        # "RelativeJEREC1",
        # "RelativeJEREC2",
        # "RelativeJERHF",
        # "RelativePtBB",
        # "RelativePtEC1",
        # "RelativePtEC2",
        # "RelativePtHF",
        # "RelativeBal",
        # "RelativeSample",
        # "RelativeFSR",
        # "RelativeStatFSR",
        # "RelativeStatEC",
        # "RelativeStatHF",
        # "PileUpDataMC",
        # "PileUpPtRef",
        # "PileUpPtBB",
        # "PileUpPtEC1",
        # "PileUpPtEC2",
        # "PileUpPtHF",
        # "PileUpMuZero",
        # "PileUpEnvelope",
        # "SubTotalPileUp",
        # "SubTotalRelative",
        # "SubTotalPt",
        # "SubTotalScale",
        # "SubTotalAbsolute",
        # "SubTotalMC",
        "Total",
        # "TotalNoFlavor",
        # "TotalNoTime",
        # "TotalNoFlavorNoTime",
        # "FlavorZJet",
        # "FlavorPhotonJet",
        # "FlavorPureGluon",
        # "FlavorPureQuark",
        # "FlavorPureCharm",
        # "FlavorPureBottom",
        # "TimeRunA",
        # "TimeRunB",
        # "TimeRunC",
        # "TimeRunD",
        "CorrelationGroupMPFInSitu",
        "CorrelationGroupIntercalibration",
        "CorrelationGroupbJES",
        "CorrelationGroupFlavor",
        "CorrelationGroupUncorrelated",
    ],
}))

config_2017.set_aux("jer", DotDict.wrap({
    "source": "https://raw.githubusercontent.com/cms-jet/JRDatabase/master/textFiles",
    "campaign": "Summer19UL17",
    "version": "JRV2",
    "jet_type": "AK4PFchs",
}))


# helper to add column aliases for both shifts of a source
def add_aliases(shift_source, aliases):
    for direction in ["up", "down"]:
        shift = config_2017.get_shift(od.Shift.join_name(shift_source, direction))
        # format keys and values
        inject_shift = lambda s: re.sub(r"\{([^_])", r"{_\1", s).format(**shift.__dict__)
        _aliases = {inject_shift(key): inject_shift(value) for key, value in aliases.items()}
        # extend existing or register new column aliases
        shift.set_aux("column_aliases", shift.get_aux("column_aliases", {})).update(_aliases)


# register shifts
config_2017.add_shift(name="nominal", id=0)
config_2017.add_shift(name="tune_up", id=1, type="shape", aux={"disjoint_from_nominal": True})
config_2017.add_shift(name="tune_down", id=2, type="shape", aux={"disjoint_from_nominal": True})
config_2017.add_shift(name="hdamp_up", id=3, type="shape", aux={"disjoint_from_nominal": True})
config_2017.add_shift(name="hdamp_down", id=4, type="shape", aux={"disjoint_from_nominal": True})
config_2017.add_shift(name="minbias_xs_up", id=7, type="shape")
config_2017.add_shift(name="minbias_xs_down", id=8, type="shape")
add_aliases("minbias_xs", {"pu_weight": "pu_weight_{name}"})
config_2017.add_shift(name="top_pt_up", id=9, type="shape")
config_2017.add_shift(name="top_pt_down", id=10, type="shape")
add_aliases("top_pt", {"top_pt_weight": "top_pt_weight_{direction}"})

with open(os.path.join(thisdir, "jec_sources.yaml"), "r") as f:
    all_jec_sources = yaml.load(f, yaml.Loader)["names"]
for jec_source in config_2017.x.jec["uncertainty_sources"]:
    idx = all_jec_sources.index(jec_source)
    config_2017.add_shift(name=f"jec_{jec_source}_up", id=5000 + 2 * idx, type="shape")
    config_2017.add_shift(name=f"jec_{jec_source}_down", id=5001 + 2 * idx, type="shape")
    add_aliases(f"jec_{jec_source}", {"Jet.pt": "Jet.pt_{name}", "Jet.mass": "Jet.mass_{name}"})

config_2017.add_shift(name="jer_up", id=6000, type="shape")
config_2017.add_shift(name="jer_down", id=6001, type="shape")
add_aliases("jer", {"Jet.pt": "Jet.pt_{name}", "Jet.mass": "Jet.mass_{name}"})


def make_jme_filenames(jme_aux, sample_type, names, era=None):
    """Convenience function to compute paths to JEC files."""

    # normalize and validate sample type
    sample_type = sample_type.upper()
    if sample_type not in ("DATA", "MC"):
        raise ValueError(f"Invalid sample type '{sample_type}'. Expected either 'DATA' or 'MC'.")

    jme_full_version = "_".join(s for s in (jme_aux.campaign, era, jme_aux.version, sample_type) if s)

    return [
        f"{jme_aux.source}/{jme_full_version}/{jme_full_version}_{name}_{jme_aux.jet_type}.txt"
        for name in names
    ]


# TODO check names
# external files
config_2017.set_aux("external_files", DotDict.wrap({
    # files from TODO
    "lumi": {
        "golden": ("/afs/cern.ch/cms/CAF/CMSCOMM/COMM_DQM/certification/Collisions17/13TeV/Legacy_2017/Cert_294927-306462_13TeV_UL2017_Collisions17_GoldenJSON.txt", "v1"),  # noqa
        "normtag": ("/afs/cern.ch/user/l/lumipro/public/Normtags/normtag_PHYSICS.json", "v1"),
    },

    # files from https://twiki.cern.ch/twiki/bin/viewauth/CMS/PileupJSONFileforData?rev=44#Pileup_JSON_Files_For_Run_II
    "pu": {
        "json": ("/afs/cern.ch/cms/CAF/CMSCOMM/COMM_DQM/certification/Collisions17/13TeV/PileUp/UltraLegacy/pileup_latest.txt", "v1"),  # noqa
        "mc_profile": ("https://raw.githubusercontent.com/cms-sw/cmssw/435f0b04c0e318c1036a6b95eb169181bbbe8344/SimGeneral/MixingModule/python/mix_2017_25ns_UltraLegacy_PoissonOOTPU_cfi.py", "v1"),  # noqa
        "data_profile": {
            "nominal": ("/afs/cern.ch/cms/CAF/CMSCOMM/COMM_DQM/certification/Collisions17/13TeV/PileUp/UltraLegacy/PileupHistogram-goldenJSON-13tev-2017-69200ub-99bins.root", "v1"),  # noqa
            "minbias_xs_up": ("/afs/cern.ch/cms/CAF/CMSCOMM/COMM_DQM/certification/Collisions17/13TeV/PileUp/UltraLegacy/PileupHistogram-goldenJSON-13tev-2017-72400ub-99bins.root", "v1"),  # noqa
            "minbias_xs_down": ("/afs/cern.ch/cms/CAF/CMSCOMM/COMM_DQM/certification/Collisions17/13TeV/PileUp/UltraLegacy/PileupHistogram-goldenJSON-13tev-2017-66000ub-99bins.root", "v1"),  # noqa
        },
    },

    # jet energy correction
    "jec": {
        "mc": [
            (fname, "v1")
            for fname in make_jme_filenames(config_2017.x.jec, "mc", names=config_2017.x.jec.levels)
        ],
        "data": {
            era: [
                (fname, "v1")
                for fname in make_jme_filenames(config_2017.x.jec, "data", names=config_2017.x.jec.levels, era=era)
            ]
            for era in config_2017.x.jec.data_eras
        },
    },

    # jec energy correction uncertainties
    "junc": {
        "mc": [(make_jme_filenames(config_2017.x.jec, "mc", names=["UncertaintySources"])[0], "v1")],
        "data": {
            era: [(make_jme_filenames(config_2017.x.jec, "data", names=["UncertaintySources"], era=era)[0], "v1")]
            for era in config_2017.x.jec.data_eras
        },
    },

    # jet energy resolution (pt resolution)
    "jer": {
        "mc": [(make_jme_filenames(config_2017.x.jer, "mc", names=["PtResolution"])[0], "v1")],
    },

    # jet energy resolution (data/mc scale factors)
    "jersf": {
        "mc": [(make_jme_filenames(config_2017.x.jer, "mc", names=["SF"])[0], "v1")],
    },

}))

# columns to keep after certain steps
config_2017.set_aux("keep_columns", DotDict.wrap({
    "cf.ReduceEvents": {
        "run", "luminosityBlock", "event",
        "nJet", "Jet.pt", "Jet.eta", "Jet.btagDeepFlavB",
        "Deepjet.pt", "Deepjet.eta", "Deepjet.btagDeepFlavB",
        "nMuon", "Muon.pt", "Muon.eta",
        "nElectron", "Electron.pt", "Electron.eta",
        "mc_weight", "PV.npvs", "category_ids", "deterministic_seed",
    },
    "cf.MergeSelectionMasks": {
        "mc_weight", "normalization_weight", "process_id", "category_ids", "cutflow.*",
    },
}))

# event weight columns
config_2017.set_aux("event_weights", ["normalization_weight", "pu_weight"])

# versions per task family and optionally also dataset and shift
# None can be used as a key to define a default value
config_2017.set_aux("versions", {
})

# add categories
add_categories(config_2017)

# add variables
add_variables(config_2017)
