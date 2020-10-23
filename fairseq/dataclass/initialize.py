# Copyright (c) Facebook, Inc. and its affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging
import os

from typing import Dict, Any

from hydra.core.config_store import ConfigStore
from hydra.core.global_hydra import GlobalHydra
from hydra.experimental import initialize

from fairseq.dataclass.configs import FairseqConfig

from fairseq.models import MODEL_DATACLASS_REGISTRY
from fairseq.tasks import TASK_DATACLASS_REGISTRY
from fairseq.registry import REGISTRIES


logger = logging.getLogger(__name__)


def hydra_init():
    cs = ConfigStore.instance()
    register_hydra_cfg(cs)

    if not GlobalHydra().is_initialized():
        # configs will be in fairseq/config after installation
        config_path = os.path.join("..", "config")
        if not os.path.exists(config_path):
            # in case of "--editable" installs we need to go one dir up
            config_path = os.path.join("..", "..", "config")

        initialize(config_path=config_path, strict=True)


def register_module_dataclass(
    cs: ConfigStore, registry: Dict[str, Any], group: str
) -> None:
    """register dataclasses defined in modules in config store, for example, in migrated tasks, models, etc."""
    # note that if `group == model`, we register all model archs, not the model name.
    for k, v in registry.items():
        node_ = v()
        node_._name = k
        cs.store(name=k, group=group, node=node_, provider="fairseq")


def register_hydra_cfg(cs: ConfigStore, name: str = "default") -> None:
    """cs: config store instance, register common training configs"""

    for k in FairseqConfig.__dataclass_fields__:
        v = FairseqConfig.__dataclass_fields__[k].default
        try:
            cs.store(name=k, node=v)
        except BaseException:
            logger.error(f"{k} - {v}")
            raise

    register_module_dataclass(cs, TASK_DATACLASS_REGISTRY, "task")
    register_module_dataclass(cs, MODEL_DATACLASS_REGISTRY, "model")

    for k, v in REGISTRIES.items():
        register_module_dataclass(cs, v["dataclass_registry"], k)
