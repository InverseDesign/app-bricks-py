# SPDX-FileCopyrightText: Copyright (C) ARDUINO SRL (http://www.arduino.cc)
#
# SPDX-License-Identifier: MPL-2.0
"""DEPRECATED — 不再被构建系统加载。

历史背景：本模块原本是 pyproject.toml 中 ``build-backend = "builder"`` 的自定义
setuptools 后端，负责在 sdist 构建时执行 ``run_preprocessing()``，生成
``src/arduino/app_bricks/static/{bricks-list,models-list}.yaml`` 等资源，
并调用 ``docs_generator.runner.run_docs_generator()`` 生成 ``docs/``。

现状（``app-bricks-py312`` 分支）：

- ``pyproject.toml`` 的 ``build-backend`` 已切回标准 ``setuptools.build_meta``，
  本模块不再是构建入口，``run_preprocessing()`` 钩子不会再被触发。
- ``setuptools_scm`` 已被移除（Python 3.12 降级 + mediapipe 兼容），本模块顶部
  的 ``from setuptools_scm import get_version`` 在导入时会立即失败，因此本
  文件目前**无法被 import**。如果以后还需要运行该预处理，需要先把它从
  setuptools_scm 依赖中解耦。
- 静态资源（``static/*.yaml``、``docs/``）的预生成已改为可选，运行时如果
  检测到缺失会走 ``models-list.yaml`` 静默跳过路径（见
  ``arduino.app_tools.module_listing.main()``）。

如需彻底删除本文件，请同步清理：

- ``pyproject.toml`` 中关于 builder 的所有历史引用（已无残留）
- ``build-opencv-wheel.yml`` 等 workflow 中如果引用 ``arduino-bricks-release``
  生成静态资源的部分
"""

import os
import sys
from setuptools.build_meta import build_wheel as _orig_build_wheel
from setuptools.build_meta import build_sdist as _orig_build_sdist
from setuptools.build_meta import build_editable as _orig_build_editable
from setuptools.build_meta import (
    get_requires_for_build_editable as _orig_get_requires_for_build_editable,
    prepare_metadata_for_build_editable as _orig_prepare_metadata_for_build_editable,
)
from setuptools_scm import get_version  # DEPRECATED: 见模块顶部说明
import subprocess
import shutil


def run_preprocessing(dev_mode: bool = False) -> None:  # DEPRECATED
    registry = os.getenv("PUBLIC_IMAGE_REGISTRY_BASE", None)
    if dev_mode:
        version = os.getenv("DEV_TAG_VERSION", "dev-latest")
    else:
        version = get_version(
            version_scheme="only-version", local_scheme="no-local-version", tag_regex=r"^(?:ai|release)/(?P<version>v?\d+(?:\.\d+)*(?:rc\d+)?)$"
        )

    cache_folder_path = "src/arduino/app_bricks/static"
    if os.path.exists(cache_folder_path) and os.path.isdir(cache_folder_path):
        shutil.rmtree(cache_folder_path)
    os.makedirs(cache_folder_path, exist_ok=True)

    try:
        print(f"################################## Building bricks list Version: {version} - Dev Mode: {dev_mode} ##################################")
        cmd = ["arduino-bricks-release", "-o", f"{cache_folder_path}/bricks-list.yaml", "--version", f"{version}"]
        if registry:
            cmd.append("--registry")
            cmd.append(registry)
        if dev_mode:
            cmd.append("--dev")

        subprocess.run(cmd, check=True, cwd=os.getcwd())
    except Exception as e:
        print(f"Error: {e}.")
        raise

    try:
        print(f"################################## Pre-provision bricks list #######################################################################")
        cmd = ["arduino-bricks-list-modules", "-p", "-b", "-c", f"{cache_folder_path}"]
        subprocess.run(cmd, check=True, cwd=os.getcwd())
    except Exception as e:
        print(f"Error: {e}.")
        raise

    try:
        print(f"################################## Embed models list ###############################################################################")
        shutil.copyfile("models/models-list.yaml", f"{cache_folder_path}/models-list.yaml")
    except Exception as e:
        print(f"Error: {e}.")
        raise

    try:
        print("################################### Docs generation #################################################################################")
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
        print(f"Project root: {project_root}")
        if project_root not in sys.path:
            print(f"Adding project root to sys.path: {project_root}")
        sys.path.insert(0, project_root)
        from docs_generator import runner

        runner.run_docs_generator()
    except Exception as e:
        print(f"Error while generating docs: {e}.")
        raise
    finally:
        if project_root in sys.path:
            sys.path.remove(project_root)


def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):
    return _orig_build_wheel(wheel_directory, config_settings, metadata_directory)


def build_sdist(sdist_directory, config_settings=None):
    dev_mode = False
    if config_settings and "build_type" in config_settings:
        dev_mode = config_settings["build_type"] == "dev"
    run_preprocessing(dev_mode)
    return _orig_build_sdist(sdist_directory, config_settings)


def build_editable(editable_build_directory, config_settings=None, metadata_directory=None):
    return _orig_build_editable(editable_build_directory, config_settings, metadata_directory)


def get_requires_for_build_editable(config_settings=None):
    return _orig_get_requires_for_build_editable(config_settings)


def prepare_metadata_for_build_editable(metadata_directory, config_settings=None):
    return _orig_prepare_metadata_for_build_editable(metadata_directory, config_settings)
