#
# Copyright (c) 2020 jintian.
#
# This file is part of CenterNet_Pro_Max
# (see jinfagang.github.io).
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#

from typing import Any, Dict, List

import torch
from torch.optim.lr_scheduler import OneCycleLR

from .lr_scheduler import WarmupCosineLR, WarmupMultiStepLR


def build_optimizer(cfg, model: torch.nn.Module) -> torch.optim.Optimizer:
    """
    Build an optimizer from config.SOLVER.OPTIMIZER
    """
    if cfg.NAME == "SGD":
        params: List[Dict[str, Any]] = []
        for key, value in model.named_parameters():
            if not value.requires_grad:
                continue
            lr = cfg.BASE_LR
            weight_decay = cfg.WEIGHT_DECAY
            if key.endswith("norm.weight") or key.endswith("norm.bias"):
                weight_decay = cfg.WEIGHT_DECAY_NORM
            elif key.endswith(".bias"):
                # NOTE: unlike Detectron v1, we now default BIAS_LR_FACTOR to 1.0
                # and WEIGHT_DECAY_BIAS to WEIGHT_DECAY so that bias optimizer
                # hyperparameters are by default exactly the same as for regular
                # weights.
                lr = cfg.BASE_LR * cfg.BIAS_LR_FACTOR
                weight_decay = cfg.WEIGHT_DECAY_BIAS
            params += [{"params": [value], "lr": lr, "weight_decay": weight_decay}]
        optimizer = torch.optim.SGD(params, lr, momentum=cfg.MOMENTUM)
    elif cfg.NAME == "AdamW":
        lr = cfg.BASE_LR
        optimizer = torch.optim.AdamW(
            model.parameters(),
            lr=lr,
            betas=cfg.BETAS,
            weight_decay=cfg.WEIGHT_DECAY,
            amsgrad=cfg.AMSGRAD
        )
    elif cfg.NAME == "Adam":
        lr = cfg.BASE_LR
        optimizer = torch.optim.Adam(
            model.parameters(),
            lr=lr,
            weight_decay=cfg.WEIGHT_DECAY,
            amsgrad=cfg.AMSGRAD
        )

    return optimizer


def build_lr_scheduler(
        cfg, optimizer: torch.optim.Optimizer
) -> torch.optim.lr_scheduler._LRScheduler:
    """
    Build a LR scheduler from config.
    """
    name = cfg.NAME
    if name == "WarmupMultiStepLR":
        return WarmupMultiStepLR(
            optimizer,
            cfg.STEPS,
            cfg.GAMMA,
            warmup_factor=cfg.WARMUP_FACTOR,
            warmup_iters=cfg.WARMUP_ITERS,
            warmup_method=cfg.WARMUP_METHOD,
        )
    elif name == "WarmupCosineLR":
        return WarmupCosineLR(
            optimizer,
            cfg.MAX_ITER,
            warmup_factor=cfg.WARMUP_FACTOR,
            warmup_iters=cfg.WARMUP_ITERS,
            warmup_method=cfg.WARMUP_METHOD,
        )
    elif name == "OneCycleLR":
        return OneCycleLR(
            optimizer,
            cfg.MAX_LR,
            total_steps=cfg.MAX_ITER,
            pct_start=cfg.PCT_START,
            base_momentum=cfg.BASE_MOM,
            max_momentum=cfg.MAX_MOM,
            div_factor=cfg.DIV_FACTOR
        )
    else:
        raise ValueError("Unknown LR scheduler: {}".format(name))
