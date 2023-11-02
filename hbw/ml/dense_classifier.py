# coding: utf-8

"""
ML models using the MLClassifierBase and Mixins
"""

from __future__ import annotations

from typing import Sequence

import law
import order as od

from columnflow.util import maybe_import

from hbw.ml.base import MLClassifierBase
from hbw.ml.mixins import DenseModelMixin, ModelFitMixin

np = maybe_import("numpy")
ak = maybe_import("awkward")

logger = law.logger.get_logger(__name__)


class DenseClassifier(ModelFitMixin, DenseModelMixin, MLClassifierBase):

    processes = [
#    "ggHH_kl_1_kt_1_sl_hbbhww",
        "graviton_hh_ggf_bbww_m250",
        "tt",
        "st",
        "w_lnu",
        "dy_lep",
    ]

    ml_process_weights = {
 #       "ggHH_kl_1_kt_1_sl_hbbhww": 1,
        "graviton_hh_ggf_bbww_m250": 1,
        "tt": 2,
        "st": 2,
        "w_lnu": 2,
        "dy_lep": 2,
    } 

    dataset_names = {
     #   "ggHH_kl_1_kt_1_sl_hbbhww_powheg",
        "graviton_hh_ggf_bbww_m250_madgraph",
        # TTbar
        "tt_sl_powheg",
        "tt_dl_powheg",
        "tt_fh_powheg",
        # SingleTop
        "st_tchannel_t_powheg",
        #"st_tchannel_tbar_powheg",
        "st_twchannel_t_powheg",
        "st_twchannel_tbar_powheg", 
        "st_schannel_lep_amcatnlo",
       # "st_schannel_had_amcatnlo",
        # WJets
        "w_lnu_ht70To100_madgraph",
        "w_lnu_ht100To200_madgraph",
        "w_lnu_ht200To400_madgraph",
        "w_lnu_ht400To600_madgraph",
        "w_lnu_ht600To800_madgraph",
        "w_lnu_ht800To1200_madgraph",
        "w_lnu_ht1200To2500_madgraph",
        "w_lnu_ht2500_madgraph",
        # DY
        "dy_lep_m50_ht70to100_madgraph",
        "dy_lep_m50_ht100to200_madgraph",
        "dy_lep_m50_ht200to400_madgraph",
        "dy_lep_m50_ht400to600_madgraph",
        "dy_lep_m50_ht600to800_madgraph",
        "dy_lep_m50_ht800to1200_madgraph",
        "dy_lep_m50_ht1200to2500_madgraph",
        "dy_lep_m50_ht2500_madgraph",
    }

    input_features = [
        # "ht",
        # "m_bb",
        # "deltaR_bb",
        "mli_ht", "mli_n_jet", "mli_n_deepjet",
        # "mli_deepjetsum", "mli_b_deepjetsum", "mli_l_deepjetsum",
        "mli_dr_bb", "mli_dphi_bb", "mli_mbb", "mli_mindr_lb", "mli_dr_jj", "mli_dphi_jj", "mli_mjj", "mli_mindr_lj",
        "mli_dphi_lnu", "mli_mlnu", "mli_mjjlnu", "mli_mjjl", "mli_dphi_bb_jjlnu", "mli_dr_bb_jjlnu",
        "mli_dphi_bb_jjl", "mli_dr_bb_jjl", "mli_dphi_bb_nu", "mli_dphi_jj_nu", "mli_dr_bb_l", "mli_dr_jj_l",
        "mli_mbbjjlnu", "mli_mbbjjl", "mli_s_min",
        #"mli_pt_jj","mli_eta_jj","mli_phi_jj",
        #"mli_pt_lnu","mli_eta_lnu","mli_phi_lnu",
        #!"mli_pt_jjlnu","mli_eta_jjlnu","mli_phi_jjlnu",
       #! "mli_pt_jjl","mli_eta_jjl","mli_phi_jjl",
       # "mli_pt_bbjjlnu","mli_eta_bbjjlnu","mli_phi_bbjjlnu",
       # "mli_pt_bbjjl","mli_eta_bbjjl","mli_phi_bbjjl",
       #! "mli_pt_bb","mli_eta_bb","mli_phi_bb",
    ] + [
        f"mli_{obj}_{var}"
        for obj in ["b1", "b2", "j1", "j2", "lep", "met"]
        for var in ["pt", "eta"]
    ] + [
        f"mli_{obj}_{var}"
        for obj in ["fj"]
        for var in ["pt", "eta", "phi", "mass", "msoftdrop", "deepTagMD_HbbvsQCD"]
    ] 

    store_name = "inputs_v1"

    folds = 2
    validation_fraction = 0.20
    learningrate = 0.00050
    negative_weights = "handle"

    # overwriting DenseModelMixin parameters
    activation = "relu"
    layers = (100, 200, 100)
    dropout = 0.50

    # overwriting ModelFitMixin parameters
    callbacks = {
        "backup", "checkpoint", "reduce_lr",
        # "early_stopping",
    }
    remove_backup = True
    reduce_lr_factor = 0.8
    reduce_lr_patience = 3
    epochs = 100
    batchsize = 8000

    # parameters to add into the `parameters` attribute and store in a yaml file
    bookkeep_params = [
        # base params
        "processes", "dataset_names", "input_features", "validation_fraction", "ml_process_weights",
        "negative_weights", "folds",
        # DenseModelMixin
        "activation", "layers", "dropout",
        # ModelFitMixin
        "callbacks", "reduce_r_factor", "reduce_lr_patience",
        "epochs", "batchsize",
    ]

    def __init__(
            self,
            *args,
            **kwargs,
    ):
        super().__init__(*args, **kwargs)

    def setup(self):
        # dynamically add variables for the quantities produced by this model
        # NOTE: since these variables are only used in ConfigTasks,
        #       we do not need to add these variables to all configs
        for proc in self.processes:
            if f"mlscore.{proc}" not in self.config_inst.variables:
                self.config_inst.add_variable(
                    name=f"mlscore.{proc}",
                    null_value=-1,
                    binning=(40, 0., 1.),
                    x_title=f"DNN output score {self.config_inst.get_process(proc).x.ml_label}",
                )
                self.config_inst.add_variable(
                    # TODO: to be used for rebinning
                    name=f"mlscore.{proc}_manybins",
                    expression=f"mlscore.{proc}",
                    null_value=-1,
                    binning=(1000, 0., 1.),
                    x_title=f"DNN output score {self.config_inst.get_process(proc).x.ml_label}",
                )
                hh_bins = [0.0, .4, .45, .5, .55, .6, .65, .7, .75, .8, .85, .92, 1.0]
                bkg_bins = [0.0, 0.4, 0.7, 1.0]
                self.config_inst.add_variable(
                    # used for inference as long as we don't have our rebin task in place
                    name=f"mlscore.{proc}_rebin",
                    expression=f"mlscore.{proc}",
                    null_value=-1,
                    binning=hh_bins if "HH" in proc else bkg_bins,
                    x_title=f"DNN output score {self.config_inst.get_process(proc).x.ml_label}",
                )

    def training_configs(self, requested_configs: Sequence[str]) -> list[str]:
        # default config
        if len(requested_configs) == 1:
            return list(requested_configs)
        else:
            # use config_2017 per default
            return ["l17"]

    def training_calibrators(self, config_inst: od.Config, requested_calibrators: Sequence[str]) -> list[str]:
        # fix MLTraining Phase Space
        return ["skip_jecunc"]

    def training_selector(self, config_inst: od.Config, requested_selector: str) -> str:
        # fix MLTraining Phase Space
        selector = "sl"
        if self.config_inst.has_tag("is_sl" or "is_res"):
            selector = "sl" 
        #if self.config_inst.has_tag("is_res"):
       #     selector = "sl_res" 
        if self.config_inst.has_tag("is_dl"):
            selector = "dl" 

        return selector

    def training_producers(self, config_inst: od.Config, requested_producers: Sequence[str]) -> list[str]:
        # fix MLTraining Phase Space
        return ["ml_inputs"]


# copies of the default DenseClassifier for testing hard-coded changes
for i in range(10):
    dense_copy = DenseClassifier.derive(f"dense_{i}")

cls_dict_test = {
    "epochs": 4,
    "processes": ["ggHH_kl_1_kt_1_sl_hbbhww", "qqHH_CV_1_C2V_1_kl_1_sl_hbbhww", "tt", "st", "v_lep"],
    "dataset_names": {
        "ggHH_kl_1_kt_1_sl_hbbhww_powheg", "qqHH_CV_1_C2V_1_kl_1_sl_hbbhww_madgraph", "tt_dl_powheg",
        "st_tchannel_t_powheg", "w_lnu_ht400To600_madgraph",
    },
}

# ML Model with reduced number of datasets
dense_test = DenseClassifier.derive("dense_test", cls_dict=cls_dict_test)

# our default MLModel
dense_default = DenseClassifier.derive("dense_default", cls_dict={})

# for running the default setup with different numbers of epochs
for n_epochs in (5, 10, 20, 50, 100, 200, 500):
    _dnn = DenseClassifier.derive(f"dense_epochs_{n_epochs}", cls_dict={"epochs": n_epochs})

# for testing different number of nodes per layer
for n_nodes in (64, 128, 256, 512):
    _dnn = DenseClassifier.derive(f"dense_3x{n_nodes}", cls_dict={"layers": (n_nodes, n_nodes, n_nodes)})

# for testing different modes of handling negative weights
for negative_weights_mode in ("handle", "ignore", "abs"):
    _dnn = DenseClassifier.derive(
        f"dense_w_{negative_weights_mode}",
        cls_dict={"negative_weights": negative_weights_mode},
    )

# for testing different learning rates
for learningrate in (0.05000, .00500, 0.00050, 0.00010, 0.00005, 0.00001):
    _dnn = DenseClassifier.derive(
        f"dense_lr_{str(learningrate).replace('.', 'p')}",
        cls_dict={"learningrate": learningrate},
    )

# for testing different batchsizes
for batchsize in (11, 12, 13, 14, 15, 16, 17):
    _dnn = DenseClassifier.derive(
        f"dense_bs_2pow{batchsize}",
        cls_dict={"batchsize": 2 ** batchsize},
    )

# for testing different dropout rates
for dropout in (0, 0.1, 0.2, 0.3, 0.4, 0.5):
    _dnn = DenseClassifier.derive(
        f"dense_dropout_{str(dropout).replace('.', 'p')}",
        cls_dict={"dropout": dropout},
    )

# for testing different weights between signal and backgrounds
for bkg_weight in (1, 2, 4, 8, 16):
    ml_process_weights = {proc_name: bkg_weight for proc_name in DenseClassifier.processes}
    ml_process_weights["ggHH_kl_1_kt_1_sl_hbbhww"] = 1
    _dnn = DenseClassifier.derive(
        f"dense_bkgw_{str(bkg_weight)}",
        cls_dict={"ml_process_weights": ml_process_weights},
    )
