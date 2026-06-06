# SPDX-License-Identifier: MPL-2.0
"""
arduino_app_bricks 版本号

此文件是静态兜底版本（取代原 setuptools_scm 动态生成）：

- pyproject.toml [project] 段使用 ``version = "attr: arduino._version.__version__"``
  直接读取本文件中的值作为 wheel 元数据版本。
- ``arduino-bricks-list-modules -p`` 等 CLI 工具通过
  ``from arduino._version import __version__`` 获取版本号来写 compose 文件。

任何**打 tag 的 release**（如 ``release/0.10.0rc3``）都应在此处同步更新 ``__version__``。
"""

__version__ = "0.9.0"
